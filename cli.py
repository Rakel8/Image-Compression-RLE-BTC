#!/usr/bin/env python3
"""Interactive CLI for image compression with BTC and RLE algorithms."""

import os
import sys
from pathlib import Path

from lossy_btc import (
    compress_btc,
    decompress_btc,
    compress_rle,
    decompress_rle,
    benchmark_folder,
)


def clear_screen():
    """Clear terminal screen."""
    os.system("clear" if os.name == "posix" else "cls")


def print_header():
    """Print application header."""
    print("=" * 70)
    print("  Image Compression CLI - BTC (Lossy) & RLE (Lossless)".center(70))
    print("=" * 70)


def print_menu():
    """Print main menu options."""
    print("\nPilih opsi:")
    print("  1. Compress 1 gambar (Lossy BTC)")
    print("  2. Compress 1 gambar (Lossless RLE)")
    print("  3. Benchmark folder (20+ gambar)")
    print("  4. Exit")
    print()


def input_single_image() -> tuple[str, str]:
    """Get image path and output path from user."""
    image_path = input("Path ke gambar: ").strip()
    
    if not Path(image_path).exists():
        print(f"[ERROR] File tidak ditemukan: {image_path}")
        return None, None
    
    mode_name = input("Nama mode (lossy/lossless) [default: lossy]: ").strip() or "lossy"
    return image_path, mode_name


def execute_single_compression(image_path: str, mode: str):
    """Execute compression for a single image."""
    if not Path(image_path).exists():
        print(f"[ERROR] File tidak ditemukan: {image_path}")
        return
    
    try:
        original_size = os.path.getsize(image_path)
        
        if mode.lower() in ["lossy", "btc"]:
            print(f"\n[PROCESSING] Kompresi BTC (lossy) untuk {image_path}...")
            block_size = input("Block size [default: 4]: ").strip()
            block_size = int(block_size) if block_size else 4
            
            bin_path = compress_btc(image_path, block_size=block_size)
            output_path = str(Path("result/BTC") / f"{Path(image_path).stem}_btc.tiff")
            decompress_btc(bin_path, output_path)
            
            compressed_size = os.path.getsize(bin_path)
            ratio = original_size / compressed_size
            
            print(f"\n[OK] Selesai!")
            print(f"  Ukuran asli:      {original_size:,} bytes")
            print(f"  Ukuran kompresi:  {compressed_size:,} bytes")
            print(f"  Rasio kompresi:   {ratio:.2f}x")
            print(f"  File bin:         {bin_path}")
            print(f"  Hasil dekompresi: {output_path}")
            
        else:
            print(f"\n[PROCESSING] Kompresi RLE (lossless) untuk {image_path}...")
            
            bin_path = compress_rle(image_path)
            output_path = str(Path("result/RLE") / f"{Path(image_path).stem}_rle.tiff")
            decompress_rle(bin_path, output_path)
            
            compressed_size = os.path.getsize(bin_path)
            ratio = original_size / compressed_size
            
            print(f"\n[OK] Selesai!")
            print(f"  Ukuran asli:      {original_size:,} bytes")
            print(f"  Ukuran kompresi:  {compressed_size:,} bytes")
            print(f"  Rasio kompresi:   {ratio:.2f}x")
            print(f"  File bin:         {bin_path}")
            print(f"  Hasil dekompresi: {output_path}")
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")


def input_benchmark_folder() -> tuple[str, str]:
    """Get folder path and extension from user."""
    folder_path = input("Path ke folder dataset: ").strip()
    
    if not Path(folder_path).is_dir():
        print(f"[ERROR] Folder tidak ditemukan: {folder_path}")
        return None, None
    
    images = list(Path(folder_path).glob("*.*"))
    if not images:
        print(f"[ERROR] Tidak ada gambar di folder: {folder_path}")
        return None, None
    
    if len(images) < 20:
        print(f"[WARNING] Folder hanya memiliki {len(images)} gambar (diminta minimal 20)")
        confirm = input("Lanjutkan? (y/n): ").strip().lower()
        if confirm != "y":
            return None, None
    
    extension = input("Ekstensi gambar [default: tiff]: ").strip() or "tiff"
    
    return folder_path, extension


def execute_benchmark(folder_path: str, extension: str):
    """Execute benchmark compression on a folder."""
    if not Path(folder_path).is_dir():
        print(f"[ERROR] Folder tidak ditemukan: {folder_path}")
        return
    
    try:
        block_size = input("Block size untuk BTC [default: 4]: ").strip()
        block_size = int(block_size) if block_size else 4
        
        print(f"\n[PROCESSING] Memproses folder {folder_path} dengan ekstensi .{extension}...\n")
        
        benchmark_folder(folder_path, extension=extension, block_size=block_size)
        
        print(f"\n[OK] Benchmark selesai!")
        print(f"  File bin BTC:     bin/btc/")
        print(f"  File bin RLE:     bin/rle/")
        print(f"  Hasil BTC:        result/BTC/")
        print(f"  Hasil RLE:        result/RLE/")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")


def main():
    """Main CLI loop."""
    while True:
        clear_screen()
        print_header()
        print_menu()
        
        choice = input("Pilihan (1-4): ").strip()
        
        if choice == "1":
            image_path, mode = input_single_image()
            if image_path:
                execute_single_compression(image_path, "lossy")
            input("\nTekan Enter untuk lanjut...")
            
        elif choice == "2":
            image_path, mode = input_single_image()
            if image_path:
                execute_single_compression(image_path, "lossless")
            input("\nTekan Enter untuk lanjut...")
            
        elif choice == "3":
            folder_path, extension = input_benchmark_folder()
            if folder_path:
                execute_benchmark(folder_path, extension)
            input("\nTekan Enter untuk lanjut...")
            
        elif choice == "4":
            print("\n[DONE] Terima kasih! Sampai jumpa.")
            sys.exit(0)
            
        else:
            print("[ERROR] Pilihan tidak valid. Silakan coba lagi.")
            input("Tekan Enter untuk lanjut...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[STOP] Program dihentikan.")
        sys.exit(0)
