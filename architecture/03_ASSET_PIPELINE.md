# Spesifikasi Arsitektur: Pipeline Aset (SFX, B-Roll, Screenshot) Tanpa AI

## 1. Prinsip Dasar

Campaign melarang **AI editing dan AI video generator**. Seluruh aset tambahan pada klip wajib berasal dari:
1. Footage episode itu sendiri, atau
2. Library berlisensi yang terdokumentasi (CC0, CC BY, CC BY-SA, Pixabay Content License), atau
3. Tangkapan layar halaman web nyata.

Tidak ada aset yang dihasilkan AI (Higgsfield, generator video/gambar, SFX AI seperti ElevenLabs). Setiap aset tercatat di manifest beserta sumber dan lisensinya.

---

## 2. Komponen Pipeline

```
                       +----------------------------+
 sfx_fetch.py  ------> | public/sfx/<kategori>/*.wav | --+
 (Openverse CC0)       | sfx-manifest.json           |   |
                       | src/sfx-library.json        |   |
                       +----------------------------+   |
                                                         |   +---------------------------+
 broll_fetch.py -----> | public/broll/*.mp4|jpg     | ---+-->| export_remotion.py        |
 (Pixabay / Openverse) | broll-manifest.json        |   |   |  --broll-from (episode)    |
                                                         |   |  --broll-asset (stok)      |
 web_capture.py -----> | public/screens/*.png       | ---+   |  --html-screenshot         |
 (Playwright + Chrome) | screens-manifest.json      |       |  -> remotion-props.json    |
                                                             +-------------+-------------+
                                                                           |
                                                       ContentRewardVideo (SfxLayer, BRollLayer,
                                                       HtmlMotionLayer) -> render MP4
```

| Script | Sumber | Butuh key | Output |
| :--- | :--- | :---: | :--- |
| `sfx_fetch.py` | Openverse (Freesound, filter CC0) | Tidak | `public/sfx/`, `src/sfx-library.json` |
| `broll_fetch.py` | Pixabay Videos / Openverse Images | Pixabay: ya (`.env`) | `public/broll/` |
| `web_capture.py` | Halaman web nyata via Chrome/Edge terpasang | Tidak | `public/screens/` |
| `export_remotion.py --broll-from` | `source.mp4` episode | Tidak | `<cand>-broll-NN.mp4` di `public/` |
| `overlay_fetch.py` (Style B) | Emoji Noto 2D / foto Openverse / foto Pixabay | Pixabay: ya (`.env`) | `public/overlays/`, `overlays-manifest.json` |
| `crop_plan.py` (Style B) | `source.mp4` episode (filter `scene` ffmpeg) | Tidak | `crop-plan.json`, `crop-sheet.jpg` di `runs/<id>/remotion/<cand>/` |

---

## 3. Lapisan Audio (SFX)

### 3.1 Library
- 10 kategori x 3 variasi: `impact`, `hit`, `whoosh`, `swipe`, `pop`, `riser`, `ding`, `glitch`, `record-scratch`, `shutter`.
- Setiap file: jeda hening awal dipotong (cue tepat di frame), panjang dibatasi per kategori, fade-out 50 ms, peak-normalize ke -1 dBFS, WAV 48 kHz stereo.
- ID Openverse yang ditolak disimpan permanen di `excluded_ids` pada manifest.

### 3.2 Penempatan Otomatis (`SfxLayer.tsx`)

| Event visual | Kategori SFX | Volume relatif |
| :--- | :--- | :---: |
| Hook impact flash (frame 0) | `impact` | 1.0 |
| Text slam (`textMotion`) | `hit` (`glitch` bila `type: "glitch"`) | 0.9 |
| B-roll masuk | `whoosh` | 0.8 |
| Mockup HTML masuk | `whoosh` (notification: `pop`) | 0.8 |
| Sticker / stat counter | `pop` | 0.6 / 0.7 |
| Outro CTA (durasi − 90 frame) | `ding` | 0.8 |

- `masterVolume` default **0,35** agar suara pembicara tetap dominan.
- Cue yang berjarak < `minGapFrames` (8) dari cue sebelumnya dibuang.
- Variasi diputar bergiliran per kategori agar cue berulang tidak terdengar identik.
- Cue manual: `"sfx": {"cues": [{"frame": 210, "category": "record-scratch"}]}`.
- Bila `sfx-library.json` kosong (`{}`), SfxLayer diam tanpa error. Jalankan `sfx_fetch.py` sekali untuk mengisinya.

### 3.3 Audio Routing
- Dialog **hanya** dari kartu A-Roll. Video latar blur dan semua video B-roll di-`muted` (mencegah dialog dobel +6 dB).

---

## 4. Lapisan B-Roll

### 4.1 Prioritas Sumber
1. **Footage episode sendiri** (`--broll-from START-END@AT`): wide shot, reaksi, establishing shot. Risiko lisensi nol.
2. **Konten pemilik channel** (music video / episode lain) via `yt-dlp`, dipasang dengan `--broll-asset`.
3. **Screenshot halaman asli** (`web_capture.py` → `--html-screenshot`).
4. **Stok berlisensi** (`broll_fetch.py` → `--broll-asset`), hanya untuk benda/konsep yang disebut.

### 4.2 Filter Stok (`broll_fetch.py`)
- Membuang hasil bertag AI: `ai generated`, `ai-generated`, `ai art`, `artificial intelligence`, `generative`, `midjourney`, `stable diffusion`, `dall-e`.
- Relevansi: tag sama dengan frasa (3) > tag/judul memuat frasa (2) > kata terpisah (1, hanya dengan `--loose`).
- Openverse: lisensi NC dan ND dibuang (`license_type=commercial,modification`).
- Normalisasi: video dipotong `--max-seconds` (default 4), tanpa audio, 720p, GOP 1; foto JPG ≤ 1600px.

### 4.3 Tampilan Kartu (`BRollLayer.tsx`)
- Kartu 840px rasio 16:10 di `top: 46%`, **tanpa badge label**; hanya caption (kiri bawah) dan kredit sumber/lisensi (kanan bawah).
- Video dibungkus `<Sequence from={startFrame}>` sehingga selalu diputar dari detik 0 file B-roll.
- `src` boleh berupa subpath `public/` (mis. `broll/x.mp4`); path absolut otomatis direduksi ke nama file.

---

## 5. Lapisan Screenshot (`HtmlMotionLayer.tsx`, tipe `browser`)
- `web_capture.py` mode mobile: viewport 420 CSS px @2x = 840px (tepat lebar kartu), tinggi tangkapan 2,5 layar.
- Area tampil 560px di bawah URL bar; 40% durasi pertama menahan bagian atas halaman (judul terbaca), lalu scroll halus maksimal ±6 px/frame.
- URL address bar diisi otomatis dari `screens-manifest.json`.

---

## 6. Aturan Takaran
- B-roll 1,5–3 detik; maksimal 1–2 B-roll + 1 mockup per klip.
- Host/pembicara utama terlihat ≥ 20% durasi; jangan menutupi wajah saat punchline.
- Jangan menempatkan aset di 3 detik terakhir (outro CTA).
- Kredit CC BY / CC BY-SA wajib tampil (otomatis dari manifest).
- Takaran di atas untuk Style A. Style B memakai overlay kata kunci jauh lebih sering (1 per 3–5 detik, di zona bawah agar wajah tetap terlihat), lihat bagian 7.

---

## 7. Lapisan Overlay Kata Kunci (Style B, `KeywordOverlayLayer.tsx`)
- Sumber, urutan prioritas: frame episode sendiri, screenshot asli, emoji Noto 2D (Apache 2.0 / OFL 1.1, tanpa atribusi), foto Openverse/Pixabay (filter anti-AI yang sama dengan `broll_fetch.py`).
- **Tanpa AI background removal**: foto tetap persegi panjang (sudut dibulatkan di Remotion), emoji/PNG transparan tampil tanpa kartu.
- Kredit CC BY / CC BY-SA tampil kecil di bawah foto (otomatis dari `overlays-manifest.json`). CC0, Pixabay, dan Noto tanpa kredit.
- Pixabay hanya cocok dengan kata tunggal ("pretzel", bukan "soft pretzel"). Openverse sering meleset, jadi selalu cek visual dan ganti dengan emoji benda bila perlu.
- Spesifikasi lengkap: `architecture/04_STYLE_B_FULLBLEED.md`.
