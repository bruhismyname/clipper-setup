# Alur Kerja 01: Ekstraksi Data dan Heatmap Radar

## 1. Tujuan Tahapan

Mengekstrak data primer dari video YouTube target:
1. Kurva retensi penonton (Most Replayed Heatmap).
2. Video master `source.mp4` (H.264 + AAC) menggunakan `yt-dlp` dan `ffmpeg`.
3. Transkrip per kata (word-level timestamps): caption YouTube (json3) atau `faster-whisper`.

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

### A. Podcast / Interview Multi-Pembicara (disarankan untuk podcast)
Caption otomatis YouTube pada percakapan dua orang sering **mengacak urutan kata** (contoh: "Could from The Big Bang Theory because he's nice Leonard"), sehingga subtitle salah dan klip berisiko ditolak sebagai low-effort. Gunakan Whisper:

```bash
python hook-radar/scripts/run.py "<YOUTUBE_URL>" --min 20 --max 45 --top 6 --download-video --transcript whisper --whisper-model small --language en --force
```

Untuk **Style B (Fullbleed Speaker)** ganti rentang durasi menjadi `--min 45 --max 90`. Video sumber wajib 1080p (default `--max-height 1080`), karena crop 9:16 di-upscale ±1,78×.

### B. Video Satu Pembicara dengan Caption Rapi
```bash
python hook-radar/scripts/run.py "<YOUTUBE_URL>" --min 20 --max 45 --top 5 --download-video
```

### Opsi Argumen
| Argumen | Default | Fungsi |
| :--- | :---: | :--- |
| `--download-video` | off | Unduh `source.mp4` (H.264 + AAC, ≤ `--max-height`). Wajib untuk Whisper dan rendering. |
| `--max-height` | 1080 | Resolusi maksimum video yang diunduh. |
| `--transcript` | `auto` | `auto` (caption bila ada, lalu Whisper), `captions`, atau `whisper`. |
| `--whisper-model` | `small` | `tiny`, `base`, `small`, `medium`, `large-v3`. |
| `--whisper-device` | `auto` | `cpu`, `cuda`, atau `auto`. |
| `--language` | `auto` | Kode bahasa caption/Whisper (mis. `en`). |
| `--min` / `--max` | 15 / 45 | Rentang durasi kandidat (detik). Fase 1.000 views: 20–45. |
| `--top` | 10 | Jumlah kandidat yang disimpan. |
| `--force` | off | Abaikan cache: ambil ulang metadata **dan ulangi transkrip**. |

Whisper `small` di CPU butuh ±2–3 menit untuk video 13 menit.

---

## 4. Struktur Direktori Output

Hasil ekstraksi disimpan di `hook-radar/workspace/runs/<video_id>/`:

```
runs/<video_id>/
├── candidates.json       # Kandidat segmen + skor + evidence
├── words.json            # Transkrip per kata {start, end, text}: sumber kebenaran untuk potongan & subtitle
├── phrases.json          # Transkrip per frasa
├── sentences.json        # Transkrip per kalimat
├── transcript_packed.md  # Tampilan baca: satu baris per frasa dengan [start-end]
├── heatmap.json          # Puncak kurva Most Replayed + baseline
├── report.md             # Ringkasan untuk manusia
├── audio.wav             # (Whisper) audio hasil ekstraksi
└── source.mp4            # (--download-video) video master
```

---

## 5. Verifikasi Transkrip (Wajib Sebelum Export)

1. Baca `words.json` pada rentang klip yang dipilih.
2. Bandingkan dengan caption YouTube: **Whisper benar urutannya, caption YouTube sering benar ejaannya** (nama, istilah).
3. Koreksi kata yang salah dengar langsung di `words.json` (contoh nyata: `grievance` → `green beans`, `Mutters` → `mothers`).
4. Catatan: menjalankan ulang dengan `--force` menghapus koreksi manual.

---

## 6. Struktur Data candidates.json

Setiap segmen kandidat memuat metadata berikut:

```json
{
  "id": "c01",
  "start": 124.5,
  "end": 185.2,
  "duration": 60.7,
  "start_hms": "2:04.50",
  "end_hms": "3:05.20",
  "first_line": "This is where everything changed...",
  "scores": {"hook": 52.0, "retention": 50.0, "fit": 99.9, "composite": 63.8}
}
```

Data ini menjadi input langsung untuk tahap kurasi dan pembuatan props Remotion.
