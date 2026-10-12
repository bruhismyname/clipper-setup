# Alur Kerja 03: Aset & Bridge Hook Radar ke Remotion

## 1. Fungsi Script Bridge

Script `hook-radar/scripts/export_remotion.py` berfungsi menghubungkan output analisis Python ke konfigurasi render Remotion.

Fungsi otomatis script:
1. Memotong video master `source.mp4` (CFR 30 fps, GOP 1 intra-frame, faststart) berdasarkan window kandidat atau `--start/--end`.
2. Memotong transkrip kata agar sinkron mulai dari detik 0.000 pada klip, serta menghapus marker pergantian pembicara seperti `>>`.
3. Memotong B-roll dari episode (`--broll-from`) dan memasang B-roll stok (`--broll-asset`) beserta kredit lisensinya.
4. Memasang screenshot halaman asli ke mockup browser (`--html-screenshot`), atau untuk Style B memasang rencana crop dan overlay kata kunci (`--style fullbleed`, §6).
5. Menyalin klip ke `remotion-template/public/` dan menulis `remotion-template/remotion-props.json`, termasuk SFX otomatis dan outro CTA.

---

## 2. Persiapan Aset (Sebelum Bridge)

Detail arsitektur ada di `architecture/03_ASSET_PIPELINE.md`.

```bash
# Sekali saja: library SFX CC0 (tanpa API key)
python hook-radar/scripts/sfx_fetch.py

# Screenshot halaman asli (mobile 840px, pas dengan kartu browser)
python hook-radar/scripts/web_capture.py "https://en.m.wikipedia.org/wiki/Sheldon_Cooper" --name sheldon-cooper-wiki
python hook-radar/scripts/web_capture.py "<URL_BERITA>" --name headline --selector "article h1" --device desktop

# Stok berlisensi: video Pixabay (butuh PIXABAY_API_KEY di .env) atau foto Openverse
python hook-radar/scripts/broll_fetch.py "green beans" --count 2
python hook-radar/scripts/broll_fetch.py "green beans" --kind photo --count 2
```

Selalu periksa visual hasil `broll_fetch.py` sebelum dipakai. Hasil bertag AI dan yang tidak relevan sudah difilter, tetapi makna visual tetap harus dicek manusia.

Untuk mencari wide shot / reaksi di episode: buat contact sheet (`ffmpeg -vf "fps=1/2,scale=320:-2,tile=5x5"`) atau deteksi potongan kamera (`select='gt(scene,0.3)'`), lalu verifikasi frame awal dan akhir rentang yang dipilih.

---

## 3. Sintaks Perintah Bridge

Jalankan perintah berikut di folder `clipper-setup/`:

```bash
python hook-radar/scripts/export_remotion.py <VIDEO_ID_ATAU_RUN_DIR> \
  --candidate <CANDIDATE_ID> \
  --headline "<HOOK_HEADLINE_TEXT>" \
  --speaker-name "<SPEAKER_NAME>" \
  --speaker-tag "<SPEAKER_ROLE>" \
  --attention-badge "MUST WATCH" \
  --outro-channel "<YOUTUBE_CHANNEL_NAME>" \
  --outro-series "<SERIES_OR_SHOW_NAME>" \
  --outro-cta "WATCH FULL EPISODE ON YOUTUBE"
```

### Contoh Lengkap (semua fitur)
```bash
python hook-radar/scripts/export_remotion.py 2acQX8r0oyY \
  --candidate m01 --start 195.0 --end 220.75 \
  --headline "HE SAID HIS MOM IS BASICALLY SHELDON" --attention-badge "😂 WAIT FOR IT" \
  --speaker-name "DYLAN AGUILAR" --speaker-tag "LOVE ON THE SPECTRUM" \
  --sticker-text "NEW YORK NIGHTS" --sticker-sub "W/ STEVEN SAVOCA" \
  --html-type browser --html-screenshot screens/sheldon-cooper-wiki.png --html-at 6.6 --html-duration 2.1 \
  --broll-from 143.5-145.5@10.8 \
  --broll-asset broll/green-beans-02.jpg@17.4+1.8 \
  --text-slam "I'M A GROWN MAN" --text-slam-at 20.3 --text-slam-duration 1.6 \
  --outro-series "NEW YORK NIGHTS WITH STEVEN SAVOCA"
```

---

## 4. Referensi Argumen

| Argumen | Default | Deskripsi |
| :--- | :---: | :--- |
| `--candidate` | `c01` | ID kandidat dari `candidates.json` (atau ID bebas bila memakai `--start/--end`) |
| `--start` / `--end` | — | Window kurasi manual di video sumber (detik atau `MM:SS`), menggantikan window kandidat |
| `--source-video` | `runs/<id>/source.mp4` | Path video master bila berada di tempat lain |
| `--broll-from` | — | `START-END@AT`: potong B-roll dari episode; `@AT` = detik di dalam klip (bisa diulang) |
| `--broll-asset` | — | `FILE@AT[+DUR]`: pasang file dari `public/` (mis. `broll/x.jpg@17.4+1.8`); default 3 dtk video / 2,5 dtk foto (bisa diulang) |
| `--broll-src` / `--broll-start` / `--broll-duration` | — / 6.0 / 3.0 | Cara lama: satu file B-roll arbitrer |
| `--broll-caption` | auto | Caption kartu B-roll (default `FROM THE EPISODE` / kata kunci stok) |
| `--html-type` | "" | `browser`, `tweet`, `search`, atau `notification` |
| `--html-screenshot` | "" | Screenshot asli untuk mockup `browser` (mis. `screens/x.png`); URL terisi otomatis |
| `--html-at` / `--html-duration` | 2.0 / 3.5 | Waktu dan durasi mockup HTML |
| `--text-slam` | "" | Teks animasi typography penekanan di tengah layar |
| `--text-slam-at` / `--text-slam-duration` | 3.0 / 1.8 | Sinkronkan text slam dengan kata yang diucapkan |
| `--stat-number` / `--stat-prefix` / `--stat-suffix` / `--stat-label` | — | Animasi counter angka |
| `--sticker-text` / `--sticker-sub` | "" | Teks lencana sticker tape |
| `--sfx-volume` | 0.35 / 0.25 | Volume master SFX otomatis (0–1); default 0.35 Style A, 0.25 Style B |
| `--style` | `card` | `card` = Style A (`ContentRewardVideo`), `fullbleed` = Style B (`FullBleedClip`) |
| `--crop-plan` | `<out-dir>/crop-plan.json` | Style B: rencana crop per shot dari `crop_plan.py` |
| `--overlay` | — | Style B: `FILE@AT[+DUR]` atau `emoji:🤔@AT[+DUR]` (default 1,5 dtk, bisa diulang) |
| `--caption-y` | 880 | Style B: posisi tengah caption satu kata (px) |
| `--no-sfx` | False | Matikan SFX otomatis |
| `--no-outro` | False | Matikan outro CTA (jangan dipakai untuk campaign yang mewajibkan CTA) |
| `--show-safe-zone` | False | Tampilkan garis bantu safe zone |
| `--out-dir` / `--remotion-dir` | auto | Arahkan output ke folder lain (berguna untuk uji coba tanpa menimpa props aktif) |

Berhenti dengan error (sengaja, tidak menebak): `source.mp4` tidak ada di run dir atau `--source-video` salah; ffmpeg gagal memotong klip; `--remotion-dir` / `REMOTION_DIR` tidak berisi `package.json`.

Peringatan otomatis: B-roll > 4 detik, B-roll yang masuk ke 3 detik terakhir (outro), atau total B-roll > 50% durasi (host wajib terlihat ≥ 20%).

---

## 5. File Output Hasil Bridge

Setelah script selesai dieksekusi:
- Klip video: `remotion-template/public/<id>-clip.mp4` (dan salinan `clip.mp4`).
- B-roll episode: `remotion-template/public/<id>-broll-NN.mp4`.
- Props: `remotion-template/remotion-props.json` (berisi `brolls`, `htmlMotion`, `textMotion`, `sfx`, `outroCta`, dll.).
- Remotion siap merender tanpa konfigurasi manual tambahan.
- Output JSON script menyebut komposisi yang harus dirender (`"composition": "ContentRewardVideo"` atau `"FullBleedClip"`).

---

## 6. Style B "Fullbleed Speaker" (v5.0.0)

Arsitektur, geometri, dan dasar ATM ada di `architecture/04_STYLE_B_FULLBLEED.md`. Langkahnya:

```bash
# 1. Ekstraksi (sumber 1080p wajib, durasi 45–90 dtk)
python hook-radar/scripts/run.py "<LINK>" --min 45 --max 90 --top 6 --download-video --transcript whisper --whisper-model small --language en --force

# 2. Rencana crop: deteksi cut + crop-sheet.jpg ber-grid per shot + template crop-plan.json
python hook-radar/scripts/crop_plan.py <VIDEO_ID> --candidate b01 --start <S> --end <E>
#    lalu isi centerX / zoom / centerY / who per segmen di hook-radar/workspace/runs/<VIDEO_ID>/remotion/b01/crop-plan.json

# 3. Aset overlay (lihat hasil fotonya!)
python hook-radar/scripts/overlay_fetch.py "pretzel" --source pixabay --count 1
python hook-radar/scripts/overlay_fetch.py --emoji 🤔 😳 🌭

# 4. Bridge (crop-plan.json dibaca otomatis dari runs/<VIDEO_ID>/remotion/<candidate>/)
python hook-radar/scripts/export_remotion.py <VIDEO_ID> --style fullbleed \
  --candidate b01 --start <S> --end <E> \
  --overlay overlays/pretzel-px-01.jpg@0.85+1.6 --overlay emoji:🤔@7.75+1.2 \
  --outro-series "NEW YORK NIGHTS WITH STEVEN SAVOCA"
```

### Mengisi `crop-plan.json`
- `centerX`: posisi tengah wajah dari grid kuning di `crop-sheet.jpg` (0 = kiri, 1 = kanan sumber).
- `who`: `host` / `guest` / `other`. Dipakai untuk menghitung host ≥20%.
- Wide shot dua orang: `zoom: 1.25`, `centerY: 0.45`, dan arahkan `centerX` ke kepala orang yang sedang bicara. Wide shot boleh dipecah manual menjadi beberapa segmen untuk cut antar pembicara.
- Shot pendek di **awal/akhir** klip tetap jadi segmen sendiri. Kilatan <0,3 dtk di tengah klip digabung ke shot sebelumnya.
- `crop_plan.py` menolak menimpa `crop-plan.json` yang sudah diisi (kecuali `--force`), dan `export_remotion.py` menolak plan yang window-nya berbeda.
- Verifikasi dengan still frame: frame 5, tiap jenis shot, wide shot, overlay foto, dan CTA.

### Merencanakan overlay
- Dari `words.json`, tandai benda/konsep/emosi tiap 3–5 detik. Timing `@AT` = detik kata diucapkan dikurangi start klip.
- Foto untuk benda yang jelas (pretzel, hot dog, lomba makan hot dog). Emoji untuk emosi/reaksi (🤔 😳 🤤 🙅) dan sebagai pengganti foto yang jelek.
- Peringatan otomatis: jeda overlay >6 dtk, overlay pertama >2 dtk, cakupan >45%, overlay menumpuk B-roll, host <20%, durasi di luar 45–90 dtk, atau tidak ada overlay sama sekali (klip tidak boleh dirilis).
