# Image Compression - BTC & RLE

Aplikasi kompres gambar grayscale menggunakan dua algoritma:
- **BTC (Block Truncation Coding)** - Kompresi lossy
- **RLE (Run-Length Encoding)** - Kompresi lossless

## Fitur

- Kompresi lossy dengan algoritma Block Truncation Coding
- Kompresi lossless dengan Run-Length Encoding
- Benchmark otomatis untuk 20+ gambar dalam satu folder
- CLI interaktif untuk kemudahan penggunaan
- Format binary kustom untuk penyimpanan data terkompresi
- Rekontruksi gambar otomatis dengan kualitas terjaga

## Struktur Folder

```
.
├── cli.py                    # Interface CLI interaktif
├── lossy_btc.py              # Modul kompresi BTC & RLE
├── requirements.txt          # Dependency Python
├── README.md                 # File ini
├── .gitignore               # Git ignore rules
├── dataset_tiff/            # Folder dataset gambar
├── bin/
│   ├── btc/                 # Hasil kompresi BTC (.bin)
│   └── rle/                 # Hasil kompresi RLE (.bin)
└── result/
    ├── BTC/                 # Hasil dekompresi BTC (.tiff)
    └── RLE/                 # Hasil dekompresi RLE (.tiff)
```

## Instalasi

1. Clone atau download proyek ini
2. Buat virtual environment:
   ```bash
   python -m venv venv
   ```

3. Aktivasi virtual environment:
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
   - Windows:
     ```bash
     venv\Scripts\activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Cara Penggunaan

### 1. CLI Interaktif (Recommended)

```bash
python cli.py
```

Menu yang tersedia:
- **Opsi 1**: Kompres 1 gambar dengan BTC (lossy)
- **Opsi 2**: Kompres 1 gambar dengan RLE (lossless)
- **Opsi 3**: Benchmark folder dengan 20+ gambar
- **Opsi 4**: Exit

### 2. Command Line Direct

#### Kompres satu gambar (BTC/Lossy):
```bash
python lossy_btc.py --mode lossy --image dataset_tiff/foto.tiff --block-size 4
```

#### Kompres satu gambar (RLE/Lossless):
```bash
python lossy_btc.py --mode lossless --image dataset_tiff/foto.tiff
```

#### Benchmark folder (20+ gambar):
```bash
python lossy_btc.py --mode benchmark --folder dataset_tiff --extension tiff
```

#### Demo:
```bash
python lossy_btc.py --mode demo
```

## Algoritma

### Block Truncation Coding (BTC) - Lossy

BTC membagi gambar menjadi blok-blok kecil (default 4x4 piksel) dan menyimpan informasi:
- Mean (rata-rata) nilai piksel dalam blok
- Standard Deviation (standar deviasi) 
- Bitplane (bitmap untuk piksel di atas/di bawah mean)

Keuntungan:
- Rasio kompresi tinggi (4-5x atau lebih)
- Ukuran file sangat kecil
- Cocok untuk gambar dengan pola reguler

Kerugian:
- Kualitas berkurang karena lossy
- Efektif untuk gambar dengan kontras tinggi

### Run-Length Encoding (RLE) - Lossless

RLE menyimpan sekuen piksel yang sama sebagai (nilai, jumlah) pairs:
- Rekonstruksi gambar 100% identik dengan asli
- Efektif untuk gambar dengan area berwarna solid besar

Keuntungan:
- Rekontruksi sempurna (lossless)
- Sederhana dan cepat

Kerugian:
- Rasio kompresi buruk untuk gambar dengan banyak variasi
- Bisa lebih besar dari asli pada gambar kompleks

## Contoh Output

Hasil benchmark:
```
Found 20 image(s) with extension .tiff
4.1.01.tiff: original=196748 bytes | BTC=40984 bytes | RLE=292591 bytes
...

Summary:
Original total: 6687436 bytes
BTC total:      1556960 bytes | CR = 4.30x
RLE total:      10632825 bytes | CR = 0.63x
```

CR (Compression Ratio) = Ukuran Original / Ukuran Terkompresi

## Persyaratan

- Python 3.8+
- numpy
- opencv-python (cv2)

Lihat `requirements.txt` untuk versi lengkap.

## File Output

Setelah kompresi, file tersimpan di:

- `bin/btc/nama_gambar_btc.bin` - Binary terkompresi BTC
- `bin/rle/nama_gambar_rle.bin` - Binary terkompresi RLE
- `result/BTC/nama_gambar_btc.tiff` - Gambar hasil dekompresi BTC
- `result/RLE/nama_gambar_rle.tiff` - Gambar hasil dekompresi RLE

## Tips Penggunaan

1. **Untuk dataset kamu**: Taruh 20+ gambar di folder `dataset_tiff/` dengan ekstensi `.tiff`
2. **Block size BTC**: Default 4 sudah optimal. Ubah ke 8 untuk kompresi lebih tinggi tapi kualitas lebih rendah
3. **Pilih algoritma**: 
   - BTC untuk kompresi tinggi (presentasi, distribusi data)
   - RLE untuk kualitas sempurna (arsip, backup)

## Catatan

- Script membaca gambar sebagai grayscale otomatis
- Untuk gambar warna, akan dikonversi ke grayscale
- Padding otomatis diterapkan jika dimensi tidak kelipatan block_size

## Lisensi

Proyek praktikum untuk keperluan akademik.

## Author

Kelompok 6 (Tugas Praktikum Sistem Multimedia)
