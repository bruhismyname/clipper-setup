# Alur Kerja 01: Ekstraksi Data dan Heatmap Radar

## 1. Tujuan Tahapan

Mengekstrak data primer dari video YouTube target:
1. Kurva retensi penonton (Most Replayed Heatmap) melalui YouTube API.
2. File audio dan video menggunakan `yt-dlp` dan `ffmpeg`.
3. Transkrip per kata (word-level timestamps) menggunakan `faster-whisper`.

---

## 2. Prasyarat Sistem

Pastikan dependensi berikut terpasang:
- Python 3.10+
- FFmpeg (terdaftar dalam PATH sistem)
- Dependensi Python:
  ```bash
  pip install -r hook-radar/requirements.txt
  ```

---

## 3. Perintah Ekstraksi

Jalankan script `run.py` dengan memberikan URL atau video ID YouTube:

```bash
python hook-radar/scripts/run.py "https://www.youtube.com/watch?v=W8E6f5F7_aE"
```

Opsi argumen:
- `--keep-source`: Mengunduh dan mempertahankan file video master `source.mp4`.
- `--whisper-model`: Pilihan model Whisper (default: `base`, opsi lain: `small`, `medium`, `large-v3`).
- `--device`: `cuda` (akselerasi GPU NVIDIA) atau `cpu`.

Contoh eksekusi lengkap dengan GPU:
```bash
python hook-radar/scripts/run.py "https://www.youtube.com/watch?v=W8E6f5F7_aE" --keep-source --device cuda
```

---

## 4. Struktur Direktori Output

Hasil ekstraksi disimpan di folder `runs/<video_id>/`:

```
runs/W8E6f5F7_aE/
├── candidates.json       # Daftar segmen kandidat hasil kalkulasi algoritma
├── words.json            # Transkrip dengan start dan end per kata (detik)
├── heatmap.json          # Titik kurva Most Replayed dari YouTube
├── transcript.txt        # Teks narasi lengkap
├── metadata.json         # Judul, channel, durasi, view count
└── source.mp4            # Video master original
```

---

## 5. Struktur Data candidates.json

Setiap segmen kandidat memuat metadata berikut:

```json
{
  "id": "c01",
  "start": 124.5,
  "end": 185.2,
  "duration": 60.7,
  "start_hms": "00:02:04",
  "end_hms": "00:03:05",
  "first_line": "This is where everything changed...",
  "peak_score": 0.88,
  "scores": {
    "retention": 23.5,
    "hook": 18.0,
    "density": 17.5,
    "emotion": 14.0,
    "loop": 8.5,
    "visual": 9.0,
    "total": 90.5
  }
}
```

Data ini menjadi input langsung untuk tahap kurasi dan pembuatan props Remotion.
