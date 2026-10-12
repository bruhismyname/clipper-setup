# Panduan Operasional AI Agent: Sistem Video Clipper (v5.0.0, 2026 Edition)

Dokumen ini berisi instruksi teknis bagi AI agent untuk menjalankan pipeline kliping video YouTube menjadi video vertikal (1080x1920) yang mematuhi standar antarmuka mobile 2026 dan aturan Content Rewards.

Tersedia dua style editing:
- **Style A, Editorial Card** (`ContentRewardVideo`, 20–45 detik): kartu A-roll, headline, caption karaoke. Untuk momen pendek dengan satu punchline.
- **Style B, Fullbleed Speaker** (`FullBleedClip`, 45–90 detik): hasil ATM fan clipper @dailyyskchaos. Crop 9:16 penuh ke pembicara, caption satu kata, overlay kata kunci tiap 3–5 detik. Untuk satu topik utuh dengan banyak benda/konsep yang bisa divisualkan. Spesifikasi: `architecture/04_STYLE_B_FULLBLEED.md`.

Pilih style per momen, atau ikuti pilihan user.

---

## 1. Struktur Repositori

```
clipper-setup/
├── AGENT_INSTRUCTIONS.md        # Panduan operasional agent ini
├── README.md                    # Dokumentasi umum repositori
├── .gitignore                   # Konfigurasi filter Git
├── architecture/
│   ├── 01_ZERO_UI_CLASH_2026.md # Spesifikasi zona aman dan koordinat vertikal
│   ├── 02_10_LAYER_MOTION_STACK.md # Rincian 10 lapisan visual Remotion + lapisan audio
│   ├── 03_ASSET_PIPELINE.md     # SFX, B-roll, screenshot, dan overlay tanpa AI
│   └── 04_STYLE_B_FULLBLEED.md  # Style B: ATM @dailyyskchaos, geometri, layer, props, takaran
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
│   │   ├── export_remotion.py   # Pemotong video, B-roll episode, dan pembuat file props Remotion
│   │   ├── sfx_fetch.py         # Library SFX CC0 (Openverse, tanpa API key)
│   │   ├── broll_fetch.py       # B-roll stok Pixabay/Openverse (filter anti-AI, manifest lisensi)
│   │   ├── web_capture.py       # Screenshot halaman asli untuk mockup browser
│   │   ├── crop_plan.py         # Style B: deteksi cut + contact sheet ber-grid + crop-plan.json
│   │   ├── overlay_fetch.py     # Style B: emoji Noto + foto Openverse/Pixabay untuk overlay kata kunci
│   │   └── ...                  # Modul scoring, heatmap, dan transkrip
│   └── references/              # Referensi formula hook dan scoring rubric
└── remotion-template/           # Engine rendering video (React dan TypeScript)
    ├── package.json             # Dependensi Remotion
    ├── remotion.config.ts       # Konfigurasi rendering
    ├── remotion-props.example.json            # Contoh props Style A
    ├── remotion-props.fullbleed.example.json  # Contoh props Style B
    ├── public/                  # Direktori aset media (clip.mp4)
    └── src/
        ├── ContentRewardVideo.tsx # Komposisi Style A (1080x1920)
        ├── FullBleedClip.tsx    # Komposisi Style B (1080x1920)
        └── components/          # Komponen modular motion stack
```

---

## 2. Sistem Koordinat Zero UI Clash (1080x1920)

Semua elemen visual wajib mengikuti batasan koordinat berikut:
- **Top Exclusion Zone**: Y: 0-285px (Dilarang menempatkan teks atau badge informasi karena area ini ditempati search bar TikTok, tombol navigasi, dan notch perangkat).
- **Attention Badge**: top: 295px (Frame 0-90 / Detik 0-3).
- **Hook Headline Banner**: top: 355px (Lebar maksimal 820px, rata tengah).
- **Sticker / Stat Counter**: top: 505px, right: 110px.
- **Talking Head Badge**: default `bottom-left` = top: 1190px, left: 110px (celah antara kartu video dan subtitle); `top-left` = top: 615px.
- **Kartu B-Roll / Mockup HTML**: lebar 840px, top: 46%; area screenshot browser 560px.
- **A-Roll Video Card**: top: 47% (Pusat vertikal kartu pada Y sekitar 660px sampai 1144px).
- **Subtitle Golden Band**: top: 1350px-1450px (Lebar maksimal 840px).
- **Bottom Exclusion Zone**: Y: 1480px-1920px (Dilarang menempatkan teks penting karena area ini tertutup username, caption panjang, dan audio marquee).
- **Right Action Rail**: X: 980px-1080px (Dilarang menempatkan grafis penting karena area ini ditempati ikon like, comment, bookmark, dan share).
- **Outro CTA Banner**: Wajib aktif pada 90 frame terakhir (3 detik penutup) untuk mengarahkan audiens ke channel YouTube resmi.

Koordinat di atas untuk Style A. Style B: video full-bleed, caption satu kata di center Y ≈ 880 px, zona overlay Y 960–1440 px (lebar maks 820 px), CTA minimal di center Y ≈ 1180 px pada 75 frame terakhir. Detail: `architecture/04_STYLE_B_FULLBLEED.md` §3.

---

## 3. Langkah Operasional Bertahap

Jika user meminta kliping dari tautan YouTube:

### Langkah 1: Ekstraksi Data
Jalankan script ekstraksi data (Whisper untuk podcast multi-pembicara):
```bash
python hook-radar/scripts/run.py "<YOUTUBE_URL>" --min 20 --max 45 --top 6 --download-video --transcript whisper --whisper-model small --language en --force
```
Output tersimpan di `hook-radar/workspace/runs/<video_id>/` (`candidates.json`, `words.json`, `transcript_packed.md`, `heatmap.json`, `source.mp4`). Baca `words.json` di rentang klip dan koreksi kata yang salah dengar (bandingkan dengan caption YouTube).

### Langkah 2: Kurasi Berdasarkan Rubrik 6 Dimensi
Periksa isi `runs/<video_id>/candidates.json`. Terapkan kriteria seleksi berikut:
- **Target Durasi**: Style A 20–45 detik; Style B 45–90 detik (satu topik utuh sampai payoff). Untuk Style B jalankan `run.py` dengan `--min 45 --max 90`.
- **Tanpa Jeda Hening di 3 Detik Pertama**: bila ada, pakai `--start/--end` untuk memulai setelah jeda.
- **Formula Hook ATM** (wajib Style B): kata pertama di detik 0,0 berupa pertanyaan relatable, dilema/would-you-rather, klaim aneh, atau misteri sehari-hari (`workflow/02_AI_CURATION_RUBRIC.md`).
- **Struktur Kalimat Pembuka**: Mandiri, memiliki konteks yang jelas, dan tidak dimulai dengan kata sambung menggantung.
- **Skor Total**: Pilih kandidat dengan evaluasi tertinggi (umumnya `c01` atau `c02`).

### Langkah 2b: Siapkan Aset (Tanpa AI)
Rencanakan timeline (detik relatif klip), lalu siapkan aset sesuai `architecture/03_ASSET_PIPELINE.md`:
```bash
python hook-radar/scripts/web_capture.py "<URL_HALAMAN>" --name <nama>
python hook-radar/scripts/broll_fetch.py "<benda yang disebut>" --kind photo --count 2
```
Periksa visual setiap aset. Jangan pernah memakai generator gambar/video/SFX AI.

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
Tambahkan opsi aset bila direncanakan: `--broll-from SRC_S-SRC_E@AT`, `--broll-asset broll/<file>@AT+DUR`, `--html-type browser --html-screenshot screens/<file>.png --html-at AT`, `--text-slam "..." --text-slam-at AT`. SFX dan outro CTA terpasang otomatis.

Output memotong klip video ke `remotion-template/public/<cand>-clip.mp4` dan memperbarui `remotion-template/remotion-props.json`.

### Langkah 3B: Bridge Style B (Fullbleed Speaker)
Langkah lengkap ada di `workflow/03_REMOTION_BRIDGE.md` §6:
```bash
python hook-radar/scripts/crop_plan.py <video_id> --candidate b01 --start <S> --end <E>
#   baca crop-sheet.jpg, isi centerX / zoom / centerY / who per segmen di runs/<video_id>/remotion/b01/crop-plan.json
python hook-radar/scripts/overlay_fetch.py "<benda>" --source pixabay --count 1     # cek visual hasilnya
python hook-radar/scripts/overlay_fetch.py --emoji 🤔 😳
python hook-radar/scripts/export_remotion.py <video_id> --style fullbleed --candidate b01 --start <S> --end <E> \
  --overlay overlays/<file>.jpg@<AT>+<DUR> --overlay emoji:🤔@<AT>+<DUR> \
  --outro-series "<NAMA_SERIES>"
```
Perhatikan peringatan takaran dari script (jeda overlay, host <20%, durasi). Klip tanpa overlay **tidak boleh dirilis** (`rules.md`: *plain cuts + auto-captions* ditolak).

### Langkah 4: Render Video Final
Beralih ke folder `remotion-template` dan render klip. Komposisi `ContentRewardVideo` untuk Style A, `FullBleedClip` untuk Style B (nama komposisi tercetak di output JSON `export_remotion.py`):
```bash
cd remotion-template
npx remotion still src/index.ts <KOMPOSISI> out/check.png --props=remotion-props.json --frame=20   # cek frame kunci dulu (Style B: frame 5, tiap jenis shot, CTA)
npx remotion render src/index.ts <KOMPOSISI> out/<video_id>-<cand_id>.mp4 --props=remotion-props.json --concurrency=3
```

### Langkah 5: Berikan Rekomendasi Upload ke User
Informasikan kepada user:
1. Lokasi file hasil render pada path `remotion-template/out/<video_id>-<cand_id>.mp4`.
2. Batas waktu submission dashboard campaign: tautan TikTok wajib disubmit dalam 30 menit setelah waktu posting.
3. Rekomendasi teks caption siap pakai dengan maksimal 5 hashtag yang relevan. Pola ATM: pertanyaan/klaim dengan 1–2 kata KAPITAL + 1–2 emoji, ajakan memilih sisi di komentar, set hashtag inti tetap (`#lyricallemonade #<show> #podcastclips #<host>`), lihat `workflow/05_CAMPAIGN_COMPLIANCE.md`.

### Checklist QC Style B (sebelum menyerahkan klip)
1. Kata pertama terdengar di frame 0–3 dan merupakan kalimat hook.
2. Setiap segmen crop memperlihatkan wajah utuh, termasuk shot pendek di awal klip (cek frame 5) dan wide shot.
3. Caption satu kata sinkron dan ejaannya benar.
4. Overlay muncul tiap 3–5 detik, relevan dengan kata yang diucapkan, semuanya non-AI dengan lisensi tercatat di `overlays-manifest.json`.
5. Host terlihat ≥20% durasi (dihitung dari `crop-plan.json`, dicetak oleh `export_remotion.py`).
6. CTA YouTube minimal terbaca di 2,5 detik terakhir.
7. Durasi 45–90 detik, dan setiap 10 detik ada alasan untuk terus menonton.

---

## 4. Penanganan Masalah Umum

| Masalah | Penyebab | Solusi |
| :--- | :--- | :--- |
| File candidates tidak ditemukan | Script run.py belum dijalankan | Jalankan `python hook-radar/scripts/run.py <url>` terlebih dahulu. |
| Subtitle memuat karakter `>>` | Tanda pergantian speaker dari caption VTT | Gunakan versi terbaru `export_remotion.py` yang otomatis membersihkan marker `>>`. |
| Headline banner bertabrakan dengan search bar TikTok | Koordinat Y terlalu kecil (< 285px) | Pastikan komposisi menggunakan `top: 355px` sesuai spesifikasi Zero UI Clash. |
| Outro CTA banner tidak muncul | Parameter bridge tidak lengkap | Pastikan argumen `--outro-channel` dan `--outro-cta` disertakan saat menjalankan script bridge. |
| Drive C: penuh setelah render | Concurrency tinggi memenuhi RAM, pagefile Windows membesar | Render dengan `--concurrency=3`; restart untuk mengecilkan pagefile. |
| Subtitle urutan katanya acak | Caption otomatis YouTube pada percakapan multi-pembicara | Ulangi `run.py` dengan `--transcript whisper --force`. |
| Tidak ada `source.mp4` | `--download-video` tidak dipakai atau gagal | Jalankan ulang dengan `--download-video` (selector H.264 + AAC). |
| B-roll stok tidak relevan / bertag AI | Hasil pencarian Pixabay/Openverse | `broll_fetch.py` sudah memfilter; ganti kata kunci atau pakai `--kind photo`, lalu periksa visual. |
| Render gagal `EPERM ... rename` | File output terbuka di video player | Tutup player atau render ke nama baru; rename file `*.remotion-in-progress`. |
| SFX tidak terdengar | `src/sfx-library.json` masih `{}` | Jalankan `python hook-radar/scripts/sfx_fetch.py`. |
| `Style B needs a crop plan` | `crop-plan.json` belum dibuat | Jalankan `crop_plan.py` dengan `--candidate`, `--start`, `--end` yang sama. |
| `crop-plan.json was made for ...` | Window export berbeda dari window crop plan | Samakan `--start/--end`, atau buat ulang dengan `crop_plan.py --force` (isian manual hilang). |
| Frame pertama Style B salah crop | Shot pendek di awal klip | `crop_plan.py` versi terbaru menjadikannya segmen sendiri; isi `centerX`-nya dan cek frame 5. |
| `--overlay: ... not found` | Aset belum diunduh | `overlay_fetch.py "<kata>"` atau `overlay_fetch.py --emoji <emoji>`. |
| Foto overlay tidak relevan | Hasil Openverse meleset | Coba `--source pixabay` dengan kata tunggal, atau pakai emoji benda. |
