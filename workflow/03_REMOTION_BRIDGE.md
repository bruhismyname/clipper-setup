# Alur Kerja 03: Bridge Hook Radar ke Remotion

## 1. Fungsi Script Bridge

Script `hook-radar/scripts/export_remotion.py` berfungsi menghubungkan output analisis Python ke konfigurasi render Remotion.

Fungsi otomatis script:
1. Memotong video master `source.mp4` menggunakan FFmpeg berdasarkan timestamp start dan end kandidat.
2. Memotong transkrip kata Whisper agar sinkron mulai dari detik 0.000s pada klip, serta menghapus marker pergantian pembicara seperti `>>`.
3. Menyalin klip video ke folder `remotion-template/public/clip.mp4`.
4. Menghasilkan file konfigurasi props `remotion-template/remotion-props.json`.

---

## 2. Sintaks Perintah Bridge

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

### Contoh Eksekusi:
```bash
python hook-radar/scripts/export_remotion.py W8E6f5F7_aE \
  --candidate c01 \
  --headline "SECRET BEHIND THE 100M EMPIRE" \
  --speaker-name "LYRICAL LEMONADE" \
  --speaker-tag "HOST" \
  --attention-badge "JANGAN SKIP" \
  --outro-channel "LYRICAL LEMONADE TV" \
  --outro-series "NO COMFORT" \
  --outro-cta "WATCH FULL EPISODE ON YOUTUBE"
```

---

## 3. Opsi Argumen Tambahan

| Argumen | Default | Deskripsi |
| :--- | :---: | :--- |
| `--stat-number` | None | Nilai numerik untuk animasi counter angka (contoh: 10) |
| `--stat-prefix` | "" | Simbol awalan angka (contoh: "$") |
| `--stat-suffix` | "" | Simbol akhiran angka (contoh: "M ARR" atau "%") |
| `--stat-label` | "" | Label deskripsi counter |
| `--sticker-text`| "" | Teks lencana sticker tape |
| `--broll-src` | "" | File gambar atau video cutaway B-roll |
| `--broll-start`| 6.0 | Detik kemunculan B-roll |
| `--broll-duration`| 3.0 | Durasi kemunculan B-roll (detik) |
| `--html-type` | "" | Jenis mockup HTML: browser, tweet, atau search |
| `--text-slam` | "" | Teks animasi typography penekanan di tengah layar |
| `--no-outro` | False | Nonaktifkan outro CTA banner jika tidak diperlukan |

---

## 4. File Output Hasil Bridge

Setelah script selesai dieksekusi:
- File klip video tersimpan di `remotion-template/public/<id>-clip.mp4` dan `remotion-template/public/clip.mp4`.
- Konfigurasi props tersimpan di `remotion-template/remotion-props.json`.
- Remotion langsung siap merender video tanpa konfigurasi manual tambahan.
