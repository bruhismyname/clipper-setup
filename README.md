# Content Reward Video Clipper (v4.0.0, 2026 Edition)

[![Remotion](https://img.shields.io/badge/Remotion-v4.0-blue.svg)](https://www.remotion.dev)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178c6.svg)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org)
[![Whisper](https://img.shields.io/badge/Faster--Whisper-AI-green.svg)](https://github.com/SYSTRAN/faster-whisper)

Pipeline otomatisasi kliping video vertikal dari YouTube ke format pendek (TikTok, Instagram Reels, YouTube Shorts) dengan integrasi aturan Content Rewards dan standar antarmuka mobile 2026.

---

## Fitur Utama

1. **Analisis Kurva Retensi YouTube**:
   - Mengekstrak data titik Most Replayed dari YouTube API.
   - Evaluasi kandidat berbasis 6 dimensi (retensi, hook, kepadatan informasi, kontras emosional, struktur narasi, dan ekspresi visual).
2. **Zero UI Clash (Standar Mobile 2026)**:
   - Area larangan atas (Y: 0-285px) untuk menghindari tabrakan dengan TikTok Persistent Search Bar, tombol navigasi, dan notch/Dynamic Island.
   - Area larangan kanan (X: 980-1080px) untuk menghindari tabrakan dengan Right Action Rail (like, comment, share, bookmark).
   - Area larangan bawah (Y: 1480-1920px) untuk menghindari tabrakan dengan username dan tumpukan caption.
3. **10-Layer Motion Stack**:
   - Pemisahan lapisan render Remotion: Technical Grid, Background Blur, Bokeh Particles, A-Roll Card, B-Roll, HTML Mockup, Stat Counter, Kinetic Subtitle, Hook Slam, dan Color/Grain FX.
4. **Kepatuhan Aturan Campaign**:
   - Outro CTA Banner otomatis pada 3 detik terakhir untuk pengalihan ke episode penuh di YouTube.
   - Penempatan video A-roll konsisten untuk memenuhi syarat visibilitas host minimal 20% durasi.
   - Template caption dengan pembatasan maksimal 5 hashtag.

---

## Struktur Direktori

```
clipper-setup/
├── AGENT_INSTRUCTIONS.md        # Panduan teknis eksekusi untuk AI agent
├── README.md                    # Dokumentasi utama repositori
├── .gitignore                   # Daftar pengecualian Git
├── architecture/                # Dokumen arsitektur dan sistem koordinat
│   ├── 01_ZERO_UI_CLASH_2026.md # Spesifikasi zona aman dan koordinat vertikal
│   └── 02_10_LAYER_MOTION_STACK.md # Spesifikasi 10 lapisan render Remotion
├── workflow/                    # Alur kerja operasional bertahap
│   ├── 01_DATA_EXTRACTION.md    # Ekstraksi metadata YouTube dan transkrip Whisper
│   ├── 02_AI_CURATION_RUBRIC.md # Rubrik penilaian kandidat klip
│   ├── 03_REMOTION_BRIDGE.md    # Pemotongan video dan sinkronisasi props Remotion
│   ├── 04_RENDERING_PREVIEW.md  # Panduan preview server dan render video
│   └── 05_CAMPAIGN_COMPLIANCE.md# Aturan kepatuhan submission program rewards
├── hook-radar/                  # Modul Python untuk analisis dan kurasi
│   ├── requirements.txt         # Daftar paket Python yang dibutuhkan
│   ├── scripts/                 # Script ekstraksi, kurasi, dan bridge props
│   └── references/              # Referensi formula hook dan scoring
└── remotion-template/           # Mesin rendering video berbasis React dan TypeScript
    ├── package.json             # Dependensi Node.js
    ├── remotion.config.ts       # Konfigurasi bundler Remotion
    ├── public/                  # Lokasi file media (clip.mp4)
    └── src/                     # Komponen visual dan komposisi utama
```

---

## Prasyarat Sistem

- Node.js 18+ dan npm
- Python 3.10+
- FFmpeg (terdaftar dalam PATH sistem)

---

## Instalasi

### 1. Dependensi Python
```bash
pip install -r hook-radar/requirements.txt
```

### 2. Dependensi Remotion
```bash
cd remotion-template
npm install
cd ..
```

---

## Alur Eksekusi

### 1. Ekstraksi Data dari YouTube
Jalankan script untuk mengunduh kurva retensi, audio, dan transkrip per kata:
```bash
python hook-radar/scripts/run.py "https://www.youtube.com/watch?v=W8E6f5F7_aE" --keep-source
```

### 2. Evaluasi dan Ekspor Props ke Remotion
Pilih ID kandidat yang memenuhi kriteria (contoh: `c01`), lalu jalankan:
```bash
python hook-radar/scripts/export_remotion.py W8E6f5F7_aE \
  --candidate c01 \
  --headline "SECRET BEHIND THE 100M EMPIRE" \
  --speaker-name "LYRICAL LEMONADE" \
  --speaker-tag "HOST" \
  --attention-badge "MUST WATCH" \
  --outro-channel "LYRICAL LEMONADE TV" \
  --outro-series "NO COMFORT" \
  --outro-cta "WATCH FULL EPISODE ON YOUTUBE"
```

### 3. Preview Interaktif (Opsional)
Jalankan development server untuk memeriksa tata letak visual:
```bash
cd remotion-template
npm run dev
```

### 4. Render Video Akhir
Render video MP4 vertikal (1080x1920, 30 fps):
```bash
cd remotion-template
npx remotion render ContentRewardVideo out/final-clip.mp4 --props=remotion-props.json --concurrency=6 --gl=angle
```

File hasil render akan disimpan pada path `remotion-template/out/final-clip.mp4`.

---

## Ketentuan Submission Campaign

1. **Batas Waktu Submit 30 Menit**: Tautan video TikTok harus disubmit ke dashboard campaign maksimal 30 menit setelah waktu posting.
2. **Batas Hashtag**: Gunakan maksimal 5 hashtag yang relevan pada caption TikTok.
3. **Frekuensi Upload**: Maksimal 2 video per hari untuk setiap akun TikTok.
4. **Outro Redirection CTA**: Klip wajib memuat pengalihan ke channel YouTube resmi.

---

## Dokumentasi untuk Agent

AI agent yang mengelola repositori ini wajib membaca [AGENT_INSTRUCTIONS.md](./AGENT_INSTRUCTIONS.md) sebelum menjalankan eksekusi tugas.
