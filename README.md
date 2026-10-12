# Content Reward Video Clipper (v5.0.0, 2026 Edition)

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
4. **Pipeline Aset Tanpa AI** (`architecture/03_ASSET_PIPELINE.md`):
   - SFX otomatis dari library CC0 (impact, whoosh, hit, pop, ding) pada hook, B-roll, text slam, dan outro.
   - B-roll dari footage episode sendiri (`--broll-from`) dan stok berlisensi Pixabay/Openverse (`broll_fetch.py`) dengan filter anti-AI dan kredit lisensi otomatis.
   - Screenshot halaman asli (Wikipedia, Genius, berita) ke mockup browser (`web_capture.py`).
   - Transkrip Whisper untuk podcast multi-pembicara (caption otomatis YouTube sering mengacak urutan kata).
5. **Style B "Fullbleed Speaker"** (`architecture/04_STYLE_B_FULLBLEED.md`), hasil ATM fan clipper podcast @dailyyskchaos (9 video teratas 1,2–3,9 jt views):
   - Crop 9:16 penuh ke pembicara aktif per shot (`crop_plan.py`: deteksi cut ffmpeg + contact sheet ber-grid, tanpa auto-reframe AI).
   - Caption satu kata (Montserrat) dan overlay "kamus visual" sinkron kata kunci tiap 3–5 detik (`overlay_fetch.py`: emoji Noto + foto Openverse/Pixabay berfilter anti-AI).
   - Durasi 45–90 detik, hook di detik 0,0, CTA YouTube minimal, dan pemeriksaan takaran otomatis anti low-effort.
6. **Kepatuhan Aturan Campaign**:
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
├── .env.example                 # Template API key (salin ke .env)
├── architecture/                # Dokumen arsitektur dan sistem koordinat
│   ├── 01_ZERO_UI_CLASH_2026.md # Spesifikasi zona aman dan koordinat vertikal
│   ├── 02_10_LAYER_MOTION_STACK.md # Spesifikasi 10 lapisan render Remotion + lapisan audio
│   ├── 03_ASSET_PIPELINE.md     # SFX, B-roll, screenshot, dan overlay tanpa AI
│   └── 04_STYLE_B_FULLBLEED.md  # Style B: ATM @dailyyskchaos, geometri, layer, props
├── workflow/                    # Alur kerja operasional bertahap
│   ├── 01_DATA_EXTRACTION.md    # Ekstraksi metadata YouTube dan transkrip Whisper
│   ├── 02_AI_CURATION_RUBRIC.md # Rubrik penilaian kandidat klip
│   ├── 03_REMOTION_BRIDGE.md    # Pemotongan video dan sinkronisasi props Remotion
│   ├── 04_RENDERING_PREVIEW.md  # Panduan preview server dan render video
│   └── 05_CAMPAIGN_COMPLIANCE.md# Aturan kepatuhan submission program rewards
├── hook-radar/                  # Modul Python untuk analisis dan kurasi
│   ├── requirements.txt         # Daftar paket Python yang dibutuhkan
│   ├── scripts/                 # run.py, export_remotion.py, sfx_fetch.py, broll_fetch.py, web_capture.py, crop_plan.py, overlay_fetch.py, dll.
│   └── references/              # Referensi formula hook dan scoring
└── remotion-template/           # Mesin rendering video berbasis React dan TypeScript
    ├── package.json             # Dependensi Node.js
    ├── remotion.config.ts       # Konfigurasi bundler Remotion
    ├── public/                  # Lokasi file media (clip.mp4)
    └── src/                     # Komposisi ContentRewardVideo (Style A) & FullBleedClip (Style B) + komponen
```

---

## Prasyarat Sistem

- Node.js 18+ dan npm
- Python 3.10+
- FFmpeg (terdaftar dalam PATH sistem)
- Google Chrome atau Microsoft Edge (dipakai Playwright untuk screenshot, tanpa `playwright install`)

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

### 3. API Key & Library SFX (sekali saja)
```bash
cp .env.example .env                       # isi PIXABAY_API_KEY (gratis, lihat komentar di file)
python hook-radar/scripts/sfx_fetch.py     # unduh 30 SFX CC0 ke remotion-template/public/sfx/
```
Tanpa langkah ini render tetap jalan, hanya tanpa SFX dan tanpa B-roll video stok.

---

## Alur Eksekusi

### 1. Ekstraksi Data dari YouTube
Jalankan script untuk mengunduh kurva retensi, video master, dan transkrip per kata (Whisper untuk podcast multi-pembicara):
```bash
python hook-radar/scripts/run.py "https://www.youtube.com/watch?v=W8E6f5F7_aE" --min 20 --max 45 --top 6 --download-video --transcript whisper --whisper-model small --language en --force
```
Periksa `words.json` di rentang klip dan koreksi kata yang salah dengar sebelum export.

### 1b. Siapkan Aset (Opsional)
```bash
python hook-radar/scripts/web_capture.py "https://en.m.wikipedia.org/wiki/Sheldon_Cooper" --name sheldon-cooper-wiki
python hook-radar/scripts/broll_fetch.py "green beans" --kind photo --count 2
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
Opsi aset: `--broll-from 143.5-145.5@10.8` (B-roll dari episode), `--broll-asset broll/x.jpg@17.4+1.8` (stok), `--html-type browser --html-screenshot screens/x.png --html-at 6.6`, `--text-slam "..." --text-slam-at 20.3`, `--start/--end` (window manual). Daftar lengkap: `workflow/03_REMOTION_BRIDGE.md`.

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
npx remotion render src/index.ts ContentRewardVideo out/final-clip.mp4 --props=remotion-props.json --concurrency=3
```

File hasil render akan disimpan pada path `remotion-template/out/final-clip.mp4`.

### Alternatif: Style B (Fullbleed Speaker)
```bash
python hook-radar/scripts/run.py "<LINK>" --min 45 --max 90 --top 6 --download-video --transcript whisper --whisper-model small --language en --force
python hook-radar/scripts/crop_plan.py <VIDEO_ID> --candidate b01 --start <S> --end <E>   # lalu isi crop-plan.json
python hook-radar/scripts/overlay_fetch.py --emoji 🤔 😳 🌭
python hook-radar/scripts/export_remotion.py <VIDEO_ID> --style fullbleed --candidate b01 --start <S> --end <E> \
  --overlay emoji:🤔@7.75+1.2 --outro-series "NEW YORK NIGHTS WITH STEVEN SAVOCA"
cd remotion-template
npx remotion render src/index.ts FullBleedClip out/final-clip.mp4 --props=remotion-props.json --concurrency=3
```
Langkah lengkap: `workflow/03_REMOTION_BRIDGE.md` §6.

---

## Ketentuan Submission Campaign

1. **Batas Waktu Submit 30 Menit**: Tautan video TikTok harus disubmit ke dashboard campaign maksimal 30 menit setelah waktu posting.
2. **Batas Hashtag**: Gunakan maksimal 5 hashtag yang relevan pada caption TikTok.
3. **Frekuensi Upload**: Maksimal 2 video per hari untuk setiap akun TikTok.
4. **Outro Redirection CTA**: Klip wajib memuat pengalihan ke channel YouTube resmi.

---

## Dokumentasi untuk Agent

AI agent yang mengelola repositori ini wajib membaca [AGENT_INSTRUCTIONS.md](./AGENT_INSTRUCTIONS.md) sebelum menjalankan eksekusi tugas.
