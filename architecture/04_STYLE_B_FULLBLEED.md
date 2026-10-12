# Spesifikasi Arsitektur: Style B "Fullbleed Speaker" (v5.0.0)

Style B adalah hasil ATM (Amati, Tiru, Modifikasi) dari akun fan clipper podcast [@dailyyskchaos](https://www.tiktok.com/@dailyyskchaos), yang memotong podcast *You Should Know*. Style A (kartu editorial, `architecture/02_10_LAYER_MOTION_STACK.md`) tetap tersedia. Pilih style per momen:

| | Style A: Editorial Card | Style B: Fullbleed Speaker |
|---|---|---|
| Komposisi Remotion | `ContentRewardVideo` | `FullBleedClip` |
| Layout | Kartu A-roll 860px + latar blur + headline + badge | Crop 9:16 penuh ke pembicara aktif, hard cut ke reaksi |
| Caption | Karaoke beberapa kata, highlight | Satu kata per layar, putih, ±46% tinggi |
| Retensi | Hook animations, text slam, B-roll 1–2× | Overlay "kamus visual" tiap 3–5 detik di setengah bawah |
| Durasi | 20–45 detik | 45–90 detik, satu topik utuh sampai payoff |
| Outro | Kartu CTA YouTube 3 detik | CTA YouTube minimal bergaya caption, 2,5 detik |
| Cocok untuk | Momen pendek dengan satu punchline | Topik debat/cerita dengan banyak benda/konsep yang bisa divisualkan |

Status: ✅ terimplementasi. Klip uji pertama (*New York Nights With Steven Savoca*, 50 detik, 19 segmen crop, host 35%, 13 overlay) disetujui 12 Okt 2026.

---

## 1. Dasar ATM

9 video teratas @dailyyskchaos (dicek 12 Okt 2026; akun 68,9 rb followers, posting harian):

| # | Caption | Views | ER* | Durasi |
|---|---|---|---|---|
| 1 | This iPhone conspiracy actually makes sense 📱😳 | 3,1 jt | 11,9% | 98 dtk |
| 2 | True Love or $1 Billion? Choose One! 🚨💰 | 3,1 jt | 9,5% | 97 dtk |
| 3 | Awkward Fan Encounter 🤣🤦‍♂️ | 2,5 jt | 10,4% | 94 dtk |
| 4 | Trying viral FOOD ILLUSIONS that actually work! 🤯 | 3,9 jt | 7,7% | 128 dtk |
| 5 | Did Cam break the ultimate bro code? 😍 | 1,7 jt | 12,0% | 208 dtk |
| 6 | Do you wash your swimsuit after swimming? 🤔 | 1,7 jt | 10,5% | 64 dtk |
| 7 | Can someone PLEASE explain how cruise ships are actually built?! 🤔🚢 | 1,3 jt | 12,4% | 138 dtk |
| 8 | How do pool tables ACTUALLY work?! 🤯🎱 | 1,2 jt | 8,6% | 225 dtk |
| 9 | Peyton Reveals His Bizarre Hidden Talent 😂 | 1,7 jt | 5,6% | 251 dtk |

*ER = (likes + komentar + share) / views.

Pola yang konsisten di semua video:
1. Kata pertama terdengar di detik 0,0. Kalimat pembuka berupa pertanyaan relatable, dilema/would-you-rather, klaim aneh, atau misteri sehari-hari.
2. Crop 9:16 penuh ke pembicara aktif, hard cut ke wajah yang bereaksi. Rata-rata satu shot 1,8–3,6 detik.
3. Caption satu kata, putih, outline tipis, ±46% tinggi layar.
4. Overlay gambar sinkron kata kunci, rata-rata satu tiap 3–4 detik, di setengah bawah layar.
5. Tanpa headline, badge, progress bar, atau outro.
6. Topik debat yang bisa dijawab penonton menghasilkan komentar 10× lebih banyak (video 1 dan 6: >11 rb komentar).

## 2. Modifikasi untuk Campaign Lyrical Lemonade TV
- **CTA YouTube wajib** (`rules.md` §4): dibuat minimal, bergaya caption, di 2,5 detik terakhir.
- **Anti low-effort** (`rules.md` §3 menolak *"plain video cuts with standard auto-captions"*): overlay kata kunci dan cut reaksi **wajib**. Klip berisi crop + caption saja dilarang dirilis.
- **Tanpa AI**: crop ditentukan per shot dari contact sheet (deteksi cut memakai filter `scene` ffmpeg, bukan auto-reframe AI). Overlay hanya dari sumber non-AI dan tanpa AI background removal.
- **Meme cutout** (jas + kepala emoji) diganti emoji/ikon, karena asal-usul dan lisensinya tidak jelas.
- **Durasi** 45–90 detik dulu, sampai data feedback loop cukup.

---

## 3. Geometri Kanvas 1080×1920

| Elemen | Posisi / Ukuran | Catatan |
|---|---|---|
| A-roll crop | Penuh 1080×1920 | Sumber 1920×1080: jendela crop 607,5×1080 px, di-upscale 1,78×. Sumber wajib 1080p |
| Wajah pembicara | Idealnya Y 300–850 px | Diatur lewat `centerX` (horizontal) dan `zoom` (1,0–1,25) per segmen |
| Caption 1 kata | Center Y ≈ 880 px (46%, ubah dengan `--caption-y`), lebar maks 860 px | Montserrat 78 px weight 800, putih, stroke hitam 5 px, bayangan `0 4px 12px rgba(0,0,0,.45)` |
| Zona overlay | Y 960–1440 px, lebar maks 820 px, center X 540 | Foto: sudut membulat 28 px. PNG/emoji: tanpa kartu, maks 380 px. Tidak melewati Y 1470 (UI bawah TikTok) |
| B-roll full-screen | Penuh 1080×1920, `objectFit: cover` | Video dari `--broll-from` / `--broll-asset` |
| CTA minimal | Center Y ≈ 1180 px | Baris 1 gaya caption ("watch the full episode on YouTube 👇"), baris 2 pil merah "▶ Lyrical Lemonade TV", baris 3 nama series |
| Safe zone | X 110–970, Y 285–1470 | Hanya caption, overlay, dan CTA yang wajib di dalamnya; video boleh full-bleed |

Catatan footage New York Nights: close-up-nya jauh lebih rapat daripada YSK. Pada close-up ekstrem, caption jatuh di hidung dan overlay menutupi mulut/dagu. Letakkan overlay foto di shot medium atau di shot lawan bicara bila bisa.

## 4. Layer Stack Style B (bawah → atas)
```
[ AUDIO: SfxLayer ]            -> pop (master 0.25) saat overlay masuk, whoosh saat B-roll full-screen, ding saat CTA
[ LAYER 5: MinimalOutroCta ]   -> 75 frame terakhir (2,5 dtk), fade + slide-up 8 frame
[ LAYER 4: OneWordCaption ]    -> 1 token per layar, pop scale 0.92→1 dalam 3 frame, tanpa highlight warna
[ LAYER 3: KeywordOverlayLayer]-> pop-in scale 0.6→1 (6 frame, overshoot), keluar fade 4 frame, durasi 30–75 frame
[ LAYER 2: Full-screen B-roll ] -> maks 2 per klip, ≤60 frame, muted
[ LAYER 1: SpeakerCropLayer ]  -> segmen crop dengan hard cut; zoom untuk wide shot / punch-in
```
- Audio dialog hanya dari A-roll. B-roll selalu di-mute.
- Overlay disembunyikan otomatis saat CTA tampil.
- Dimatikan di Style B: latar blur, kartu A-roll, headline, attention badge, speaker badge, sticker, progress bar, film grain, vignette, impact flash, camera slam, text slam.

## 5. Komponen & Script

| Bagian | Lokasi | Fungsi |
|---|---|---|
| `FullBleedClip` | `remotion-template/src/FullBleedClip.tsx` (terdaftar di `Root.tsx`) | Komposisi Style B, pakai ulang `SfxLayer` dan `SafeZoneGuide` |
| `SpeakerCropLayer` | `remotion-template/src/components/` | Crop per segmen dari `speakerCrop[]` (clamp agar tidak keluar frame) |
| `OneWordCaption` | `remotion-template/src/components/` | Caption 1 kata. Angka + satuan ("$1 billion") jadi satu token, huruf kecil di awal kalimat (kecuali "I"), kata <3 frame digabung |
| `KeywordOverlayLayer` | `remotion-template/src/components/` | Foto/PNG/emoji pop-in di zona bawah, kredit lisensi kecil untuk CC BY/BY-SA |
| `MinimalOutroCta` | `remotion-template/src/components/` | CTA YouTube gaya caption |
| `crop_plan.py` | `hook-radar/scripts/` | Deteksi cut (ffmpeg `scene`) + `crop-sheet.jpg` ber-grid X 0,1–0,9 + template `crop-plan.json` |
| `overlay_fetch.py` | `hook-radar/scripts/` | Emoji Noto 2D PNG 512 px + foto Openverse/Pixabay (filter AI), lebar maks 900 px, `overlays-manifest.json` |
| `export_remotion.py` | `--style fullbleed`, `--crop-plan`, `--overlay` (bisa diulang), `--caption-y` | Menulis props `FullBleedClip` dan mengecek takaran |

Font caption: `@remotion/google-fonts` (Montserrat), versi disamakan dengan Remotion (4.0.533).

## 6. Skema Props `FullBleedClip`
```json
{
  "style": "fullbleed",
  "videoSrc": "b01-clip.mp4",
  "sourceWidth": 1920,
  "sourceHeight": 1080,
  "durationInFrames": 1511,
  "fps": 30,
  "captions": [{"text": "You", "startFrame": 2, "endFrame": 20}],
  "speakerCrop": [
    {"from": 0,   "to": 11,  "centerX": 0.54,  "centerY": 0.5,  "zoom": 1.0,  "who": "guest"},
    {"from": 11,  "to": 43,  "centerX": 0.40,  "centerY": 0.5,  "zoom": 1.0,  "who": "host"},
    {"from": 561, "to": 649, "centerX": 0.735, "centerY": 0.45, "zoom": 1.25, "who": "guest"}
  ],
  "overlays": [
    {"src": "overlays/pretzel-px-01.jpg", "from": 26, "duration": 48, "kind": "photo", "credit": ""},
    {"src": "overlays/emoji/emoji_u1f914.png", "from": 233, "duration": 36, "kind": "emoji", "credit": ""}
  ],
  "brolls": [{"src": "b01-broll-01.mp4", "type": "video", "mode": "fullscreen", "startFrame": 600, "endFrame": 654}],
  "caption": {"enabled": true, "centerY": 880, "fontSize": 78},
  "outroCta": {"enabled": true, "style": "minimal", "channelName": "Lyrical Lemonade TV",
               "seriesName": "New York Nights With Steven Savoca", "ctaText": "watch the full episode on YouTube 👇",
               "durationInFrames": 75},
  "sfx": {"enabled": true, "auto": true, "masterVolume": 0.25, "minGapFrames": 8}
}
```
- `speakerCrop` menutup seluruh durasi tanpa celah. `who` dipakai untuk menghitung host ≥20%.
- `centerX` = posisi tengah wajah dibagi lebar sumber (0–1).
- Contoh lengkap: `remotion-template/remotion-props.fullbleed.example.json`.

## 7. Aturan Takaran (dicek otomatis oleh `export_remotion.py`)
- **Overlay**: 1 per 3–5 detik. Overlay pertama ≤2 detik setelah mulai. Durasi 1–2,5 detik. Total ≤45% durasi. Harus relevan dengan kata yang sedang diucapkan.
- **Cut**: rata-rata satu shot 2–4 detik. Pindah ke wajah lawan bicara saat tertawa, kaget, atau menjawab.
- **B-roll full-screen**: maks 2 per klip, ≤2 detik, tidak di kalimat punchline.
- **Host ≥20%** (segmen `who: "host"`) dan CTA YouTube di 2,5 detik terakhir.
- **Durasi** 45–90 detik.

## 8. Sumber Aset Overlay (tanpa AI)

| # | Sumber | Lisensi | Kapan |
|---|---|---|---|
| 1 | Frame/potongan episode sendiri | Aman | Saat merujuk kejadian di episode |
| 2 | Screenshot halaman asli (`web_capture.py`) | Kutipan wajar | Tokoh, acara, lagu, berita |
| 3 | Emoji Noto Color Emoji 2D (`googlefonts/noto-emoji/2D/png/512`) | Apache 2.0 / OFL 1.1, tanpa atribusi | Emosi/reaksi/benda: 🤔 😳 🤤 🙅 🌭 ⚾ 🥤 |
| 4 | Foto Openverse (CC0/CC BY/CC BY-SA) / Pixabay foto | Kredit kecil otomatis untuk CC BY/BY-SA | Benda atau konsep yang disebut |
| ❌ | Gambar AI, AI background removal (rembg dll.), meme cutout tanpa sumber jelas | — | Dilarang |

Pengalaman uji pertama:
- Openverse kadang memberi foto yang meleset (mainan bermerek di toples pretzel, kaleng Tab untuk "soda").
- Pixabay lebih bersih untuk benda sehari-hari, tetapi hanya cocok dengan **kata tunggal** ("pretzel", bukan "soft pretzel").
- Selalu cek visual. Bila tidak ada foto yang bagus, emoji benda jadi pengganti yang aman.

Langkah kerja lengkap ada di `workflow/03_REMOTION_BRIDGE.md` §6 dan checklist QC di `AGENT_INSTRUCTIONS.md`.
