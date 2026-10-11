# Panduan Operasional AI Agent: Sistem Video Clipper (v4.0.0, 2026 Edition)

Dokumen ini berisi instruksi teknis bagi AI agent untuk menjalankan pipeline kliping video YouTube menjadi video vertikal (1080x1920) yang mematuhi standar antarmuka mobile 2026 dan aturan Content Rewards.

---

## 1. Struktur Repositori

```
clipper-setup/
├── AGENT_INSTRUCTIONS.md        # Panduan operasional agent ini
├── README.md                    # Dokumentasi umum repositori
├── .gitignore                   # Konfigurasi filter Git
├── architecture/
│   ├── 01_ZERO_UI_CLASH_2026.md # Spesifikasi zona aman dan koordinat vertikal
│   └── 02_10_LAYER_MOTION_STACK.md # Rincian 10 lapisan visual Remotion
├── workflow/
│   ├── 01_DATA_EXTRACTION.md    # Ekstraksi YouTube, kurva heatmap, dan Whisper
│   ├── 02_AI_CURATION_RUBRIC.md # Rubrik penilaian kurasi 6 dimensi
│   ├── 03_REMOTION_BRIDGE.md    # Pemotongan klip dan pembuatan props Remotion
│   ├── 04_RENDERING_PREVIEW.md  # Instruksi preview dan render MP4
│   └── 05_CAMPAIGN_COMPLIANCE.md# Aturan kepatuhan program Content Rewards
├── hook-radar/                  # Modul Python untuk analisis dan kurasi
│   ├── requirements.txt         # Dependensi Python
│   ├── scripts/
│   │   ├── run.py               # Orchestrator download, heatmap, dan Whisper
│   │   ├── export_remotion.py   # Pemotong video dan pembuat file props Remotion
│   │   └── ...                  # Modul scoring, heatmap, dan transkrip
│   └── references/              # Referensi formula hook dan scoring rubric
└── remotion-template/           # Engine rendering video (React dan TypeScript)
    ├── package.json             # Dependensi Remotion
    ├── remotion.config.ts       # Konfigurasi rendering
    ├── remotion-props.example.json
    ├── public/                  # Direktori aset media (clip.mp4)
    └── src/
        ├── ContentRewardVideo.tsx # Komposisi utama (1080x1920)
        └── components/          # Komponen modular motion stack
```

---

## 2. Sistem Koordinat Zero UI Clash (1080x1920)

Semua elemen visual wajib mengikuti batasan koordinat berikut:
- **Top Exclusion Zone**: Y: 0-285px (Dilarang menempatkan teks atau badge informasi karena area ini ditempati search bar TikTok, tombol navigasi, dan notch perangkat).
- **Attention Badge**: top: 295px (Frame 0-90 / Detik 0-3).
- **Hook Headline Banner**: top: 355px (Lebar maksimal 820px, rata tengah).
- **Sticker / Stat Counter**: top: 505px, right: 110px.
- **Talking Head Badge**: top: 615px, left: 110px.
- **A-Roll Video Card**: top: 47% (Pusat vertikal kartu pada Y sekitar 660px sampai 1144px).
- **Subtitle Golden Band**: top: 1350px-1450px (Lebar maksimal 840px).
- **Bottom Exclusion Zone**: Y: 1480px-1920px (Dilarang menempatkan teks penting karena area ini tertutup username, caption panjang, dan audio marquee).
- **Right Action Rail**: X: 980px-1080px (Dilarang menempatkan grafis penting karena area ini ditempati ikon like, comment, bookmark, dan share).
- **Outro CTA Banner**: Wajib aktif pada 90 frame terakhir (3 detik penutup) untuk mengarahkan audiens ke channel YouTube resmi.

---

## 3. Langkah Operasional Bertahap

Jika user meminta kliping dari tautan YouTube:

### Langkah 1: Ekstraksi Data
Jalankan script ekstraksi data:
```bash
python hook-radar/scripts/run.py "<YOUTUBE_URL>" --keep-source
```
Output tersimpan di direktori `runs/<video_id>/` yang berisi file `candidates.json`, `words.json`, `heatmap.json`, dan `source.mp4`.

### Langkah 2: Kurasi Berdasarkan Rubrik 6 Dimensi
Periksa isi `runs/<video_id>/candidates.json`. Terapkan kriteria seleksi berikut:
- **Target Durasi**: 60-85 detik (memenuhi ketentuan durasi program reward).
- **Struktur Kalimat Pembuka**: Mandiri, memiliki konteks yang jelas, dan tidak dimulai dengan kata sambung menggantung.
- **Skor Total**: Pilih kandidat dengan evaluasi tertinggi (umumnya `c01` atau `c02`).

### Langkah 3: Eksekusi Bridge ke Remotion
Jalankan `export_remotion.py` dengan parameter lengkap:
```bash
python hook-radar/scripts/export_remotion.py <video_id> \
  --candidate <cand_id> \
  --headline "<HOOK_HEADLINE_HURUF_KAPITAL>" \
  --speaker-name "<NAMA_PEMBICARA>" \
  --speaker-tag "HOST" \
  --attention-badge "MUST WATCH" \
  --outro-channel "<NAMA_CHANNEL_YOUTUBE>" \
  --outro-series "<NAMA_SERIES>" \
  --outro-cta "WATCH FULL EPISODE ON YOUTUBE"
```
Output memotong klip video ke `remotion-template/public/clip.mp4` dan memperbarui `remotion-template/remotion-props.json`.

### Langkah 4: Render Video Final
Beralih ke folder `remotion-template` dan render klip:
```bash
cd remotion-template
npx remotion render ContentRewardVideo out/<video_id>-<cand_id>.mp4 --props=remotion-props.json --concurrency=6 --gl=angle
```

### Langkah 5: Berikan Rekomendasi Upload ke User
Informasikan kepada user:
1. Lokasi file hasil render pada path `remotion-template/out/<video_id>-<cand_id>.mp4`.
2. Batas waktu submission dashboard campaign: tautan TikTok wajib disubmit dalam 30 menit setelah waktu posting.
3. Rekomendasi teks caption siap pakai dengan maksimal 5 hashtag yang relevan.

---

## 4. Penanganan Masalah Umum

| Masalah | Penyebab | Solusi |
| :--- | :--- | :--- |
| File candidates tidak ditemukan | Script run.py belum dijalankan | Jalankan `python hook-radar/scripts/run.py <url>` terlebih dahulu. |
| Subtitle memuat karakter `>>` | Tanda pergantian speaker dari caption VTT | Gunakan versi terbaru `export_remotion.py` yang otomatis membersihkan marker `>>`. |
| Headline banner bertabrakan dengan search bar TikTok | Koordinat Y terlalu kecil (< 285px) | Pastikan komposisi menggunakan `top: 355px` sesuai spesifikasi Zero UI Clash. |
| Outro CTA banner tidak muncul | Parameter bridge tidak lengkap | Pastikan argumen `--outro-channel` dan `--outro-cta` disertakan saat menjalankan script bridge. |
| Kecepatan render lambat | Konkurensi default satu core | Gunakan argumen `--concurrency=6 --gl=angle` pada perintah render. |
