"""Lossy and lossless grayscale image compression for practicum work.

This script provides two custom image compression workflows:

- BTC (Block Truncation Coding) for lossy compression
- RLE (Run-Length Encoding) for lossless compression

Both work on grayscale images and save their own binary container format.
The script also includes batch benchmarking for a folder of images.
"""

from __future__ import annotations

import argparse
import math
import os
import struct
from pathlib import Path

import cv2
import numpy as np


BTC_MAGIC = b"BTC1"
RLE_MAGIC = b"RLE1"
BIN_DIR = Path("bin")
BTC_BIN_DIR = BIN_DIR / "btc"
RLE_BIN_DIR = BIN_DIR / "rle"
BTC_RESULT_DIR = Path("result") / "BTC"
RLE_RESULT_DIR = Path("result") / "RLE"


def _read_grayscale_image(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Image not found or unreadable: {image_path}")
    return image


def _write_tiff(output_path: str, image: np.ndarray) -> None:
    if not cv2.imwrite(output_path, image):
        raise IOError(f"Failed to write image: {output_path}")


def _prepare_output_dirs() -> None:
    BTC_BIN_DIR.mkdir(parents=True, exist_ok=True)
    RLE_BIN_DIR.mkdir(parents=True, exist_ok=True)
    BTC_RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RLE_RESULT_DIR.mkdir(parents=True, exist_ok=True)


def _bin_output_path(image_path: str, suffix: str, mode: str) -> str:
    source_path = Path(image_path)
    bin_dir = BTC_BIN_DIR if mode == "BTC" else RLE_BIN_DIR
    return str(bin_dir / f"{source_path.stem}{suffix}.bin")


def _result_output_path(image_path: str, suffix: str, mode: str) -> str:
    source_path = Path(image_path)
    result_dir = BTC_RESULT_DIR if mode == "BTC" else RLE_RESULT_DIR
    return str(result_dir / f"{source_path.stem}{suffix}.tiff")


def _compress_btc_block(block: np.ndarray) -> tuple[float, float, bytes]:
    mean = float(block.mean())
    std = float(block.std())
    bitplane = (block > mean).astype(np.uint8).reshape(-1)
    packed = np.packbits(bitplane, bitorder="little").tobytes()
    return mean, std, packed


def _decompress_btc_block(mean: float, std: float, packed_bits: bytes, block_size: int) -> np.ndarray:
    bits_needed = block_size * block_size
    bits = np.unpackbits(np.frombuffer(packed_bits, dtype=np.uint8), bitorder="little")[:bits_needed]

    ones = int(bits.sum())
    zeros = bits_needed - ones
    if ones == 0 or zeros == 0 or std == 0.0:
        low_value = high_value = mean
    else:
        low_value = mean - std * math.sqrt(ones / zeros)
        high_value = mean + std * math.sqrt(zeros / ones)

    block = np.where(bits.reshape(block_size, block_size) == 1, high_value, low_value)
    return np.clip(block, 0, 255).astype(np.uint8)


def compress_btc(image_path: str, block_size: int = 4) -> str:
    """Compress a grayscale image with Block Truncation Coding.

    The output binary stores the original dimensions, the block size, and
    one record per block containing the block mean, block standard deviation,
    and packed bitplane.
    """

    image = _read_grayscale_image(image_path)
    height, width = image.shape
    padded_height = math.ceil(height / block_size) * block_size
    padded_width = math.ceil(width / block_size) * block_size

    padded = np.zeros((padded_height, padded_width), dtype=np.uint8)
    padded[:height, :width] = image

    blocks_vertical = padded_height // block_size
    blocks_horizontal = padded_width // block_size
    bytes_per_block = math.ceil((block_size * block_size) / 8)
    num_blocks = blocks_vertical * blocks_horizontal

    _prepare_output_dirs()
    bin_path = _bin_output_path(image_path, "_btc", "BTC")

    with open(bin_path, "wb") as file:
        file.write(struct.pack("<4sIIIII", BTC_MAGIC, height, width, block_size, num_blocks, bytes_per_block))

        for row_block in range(blocks_vertical):
            for col_block in range(blocks_horizontal):
                y_start = row_block * block_size
                x_start = col_block * block_size
                block = padded[y_start : y_start + block_size, x_start : x_start + block_size]
                mean, std, packed_bits = _compress_btc_block(block)
                packed_bits = packed_bits.ljust(bytes_per_block, b"\x00")
                file.write(struct.pack("<ff", mean, std))
                file.write(packed_bits)

    return bin_path


def decompress_btc(bin_path: str, output_path: str) -> None:
    """Reconstruct a BTC-compressed image and save it as TIFF."""

    with open(bin_path, "rb") as file:
        magic, height, width, block_size, num_blocks, bytes_per_block = struct.unpack("<4sIIIII", file.read(24))
        if magic != BTC_MAGIC:
            raise ValueError("Invalid BTC file format")

        padded_height = math.ceil(height / block_size) * block_size
        padded_width = math.ceil(width / block_size) * block_size
        blocks_vertical = padded_height // block_size
        blocks_horizontal = padded_width // block_size

        reconstructed = np.zeros((padded_height, padded_width), dtype=np.uint8)

        block_index = 0
        for row_block in range(blocks_vertical):
            for col_block in range(blocks_horizontal):
                if block_index >= num_blocks:
                    break

                mean, std = struct.unpack("<ff", file.read(8))
                packed_bits = file.read(bytes_per_block)
                block = _decompress_btc_block(mean, std, packed_bits, block_size)

                y_start = row_block * block_size
                x_start = col_block * block_size
                reconstructed[y_start : y_start + block_size, x_start : x_start + block_size] = block
                block_index += 1

        output = reconstructed[:height, :width]
        _write_tiff(output_path, output)


def compress_rle(image_path: str) -> str:
    """Lossless compression using Run-Length Encoding on grayscale pixels."""

    image = _read_grayscale_image(image_path)
    height, width = image.shape
    flat = image.reshape(-1)

    runs: list[tuple[int, int]] = []
    current_value = int(flat[0])
    current_count = 1

    for value in map(int, flat[1:]):
        if value == current_value and current_count < 0xFFFFFFFF:
            current_count += 1
        else:
            runs.append((current_value, current_count))
            current_value = value
            current_count = 1

    runs.append((current_value, current_count))

    _prepare_output_dirs()
    bin_path = _bin_output_path(image_path, "_rle", "RLE")
    with open(bin_path, "wb") as file:
        file.write(struct.pack("<4sIII", RLE_MAGIC, height, width, len(runs)))
        for value, count in runs:
            file.write(struct.pack("<BI", value, count))

    return bin_path


def decompress_rle(bin_path: str, output_path: str) -> None:
    """Restore a grayscale image compressed with RLE."""

    with open(bin_path, "rb") as file:
        magic, height, width, num_runs = struct.unpack("<4sIII", file.read(16))
        if magic != RLE_MAGIC:
            raise ValueError("Invalid RLE file format")

        pixels: list[int] = []
        for _ in range(num_runs):
            value, count = struct.unpack("<BI", file.read(5))
            pixels.extend([value] * count)

    expected_size = height * width
    if len(pixels) != expected_size:
        raise ValueError("RLE data is corrupted or incomplete")

    image = np.array(pixels, dtype=np.uint8).reshape(height, width)
    _write_tiff(output_path, image)


def _find_images(folder: str, extension: str) -> list[Path]:
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Folder not found: {folder}")
    pattern = f"*.{extension.lstrip('.')}"
    return sorted(folder_path.glob(pattern))


def benchmark_folder(folder: str, extension: str = "jpg", block_size: int = 4) -> None:
    """Run both lossy and lossless compression on a batch of images."""

    images = _find_images(folder, extension)
    if len(images) < 20:
        print(f"Warning: found only {len(images)} image(s). The assignment asks for at least 20.")

    _prepare_output_dirs()

    total_original = 0
    total_btc = 0
    total_rle = 0

    print(f"Found {len(images)} image(s) with extension .{extension}")

    for image_path in images:
        original_size = image_path.stat().st_size
        btc_bin = compress_btc(str(image_path), block_size=block_size)
        rle_bin = compress_rle(str(image_path))

        btc_size = os.path.getsize(btc_bin)
        rle_size = os.path.getsize(rle_bin)

        total_original += original_size
        total_btc += btc_size
        total_rle += rle_size

        print(
            f"{image_path.name}: original={original_size} bytes | BTC={btc_size} bytes | RLE={rle_size} bytes"
        )

        decompress_btc(btc_bin, _result_output_path(str(image_path), "_btc", "BTC"))
        decompress_rle(rle_bin, _result_output_path(str(image_path), "_rle", "RLE"))

    print("\nSummary:")
    print(f"Original total: {total_original} bytes")
    print(f"BTC total:      {total_btc} bytes | CR = {total_original / total_btc:.2f}x")
    print(f"RLE total:      {total_rle} bytes | CR = {total_original / total_rle:.2f}x")


def _demo_image() -> str:
    image_path = "sample_image.tiff"
    sample = np.zeros((256, 256), dtype=np.uint8)
    for row in range(sample.shape[0]):
        for col in range(sample.shape[1]):
            if (row // 32 + col // 32) % 2 == 0:
                sample[row, col] = 90 + (row % 32) * 2
            else:
                sample[row, col] = 180 - (col % 32) * 2
    _write_tiff(image_path, sample)
    return image_path


def _run_single_mode(image_path: str, mode: str, block_size: int) -> None:
    _prepare_output_dirs()

    if mode == "lossy":
        bin_path = compress_btc(image_path, block_size=block_size)
        output_path = _result_output_path(image_path, "_btc", "BTC")
        decompress_btc(bin_path, output_path)
    else:
        bin_path = compress_rle(image_path)
        output_path = _result_output_path(image_path, "_rle", "RLE")
        decompress_rle(bin_path, output_path)

    original_size = os.path.getsize(image_path)
    compressed_size = os.path.getsize(bin_path)
    print(f"Original size:   {original_size} bytes")
    print(f"Compressed size: {compressed_size} bytes")
    print(f"Compression ratio: {original_size / compressed_size:.2f}x")
    print(f"Compressed bin:   {bin_path}")
    print(f"Output image:     {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lossy BTC and lossless RLE image compression")
    parser.add_argument("--mode", choices=["demo", "lossy", "lossless", "benchmark"], default="demo")
    parser.add_argument("--image", help="Path to a grayscale image")
    parser.add_argument("--folder", help="Folder containing at least 20 images for benchmarking")
    parser.add_argument("--extension", default="jpg", help="Image extension for benchmark mode")
    parser.add_argument("--block-size", type=int, default=4, help="BTC block size")
    parser.add_argument("--output", default="output.tiff", help="Output TIFF path for decompression")
    args = parser.parse_args()

    if args.mode == "demo":
        image_path = _demo_image()
        btc_bin = compress_btc(image_path, block_size=args.block_size)
        decompress_btc(btc_bin, _result_output_path(image_path, "_btc", "BTC"))
        rle_bin = compress_rle(image_path)
        decompress_rle(rle_bin, _result_output_path(image_path, "_rle", "RLE"))

        original_size = os.path.getsize(image_path)
        btc_size = os.path.getsize(btc_bin)
        rle_size = os.path.getsize(rle_bin)

        print(f"Demo image: {image_path}")
        print(f"BTC CR: {original_size / btc_size:.2f}x")
        print(f"RLE CR: {original_size / rle_size:.2f}x")
        return

    if args.mode == "benchmark":
        if not args.folder:
            raise ValueError("--folder is required in benchmark mode")
        benchmark_folder(args.folder, extension=args.extension, block_size=args.block_size)
        return

    if not args.image:
        raise ValueError("--image is required for lossy or lossless mode")

    _run_single_mode(args.image, args.mode, args.block_size)


if __name__ == "__main__":
    main()
