# Alur Kerja 04: Preview Realtime dan Rendering Final MP4

## 1. Instalasi Awal Template Remotion

Sebelum menjalankan server preview atau perintah render:

```bash
cd remotion-template
npm install
```

---

## 2. Preview Interaktif (Live Development Server)

Untuk memeriksa tata letak video di browser sebelum proses rendering:

```bash
cd remotion-template
npm run dev
```
Atau:
```bash
npx remotion preview
```

Server preview aktif pada `http://localhost:3000`.

### Poin Verifikasi Visual:
1. **Pemeriksaan Zona Aman**: Pada editor props Remotion, aktifkan `"showSafeZone": true` untuk memunculkan garis batas overlay merah dan hijau guna memastikan tidak ada teks yang menabrak elemen antarmuka TikTok.
2. **Sinkronisasi Subtitle**: Gerakkan timeline (scrub) untuk memastikan highlight kuning menyala tepat saat kata diucapkan pembicara.
3. **Pemeriksaan Outro CTA**: Periksa 90 frame terakhir (3 detik akhir) untuk memastikan Outro Redirection Banner tampil dengan benar.
4. **Pemeriksaan Aset**: Subtitle tidak tertutup speaker badge/kartu, judul screenshot terbaca sebelum scroll, B-roll tidak menutupi wajah saat punchline, kredit lisensi tampil.
5. **Style B**: Pilih komposisi `FullBleedClip` di sidebar Studio. Pastikan setiap segmen crop memperlihatkan wajah utuh dan overlay muncul di zona bawah.

### Cek Frame Kunci Tanpa Studio (lebih cepat)
Render still di frame hook, tiap B-roll/mockup, text slam, dan outro (frame = detik klip × 30):
```bash
cd remotion-template
npx remotion still src/index.ts ContentRewardVideo out/check-f20.png --props=remotion-props.json --frame=20
```

---

## 3. Rendering Video Final

Jalankan perintah render Remotion menggunakan file props yang telah digenerate:

```bash
cd remotion-template
npx remotion render src/index.ts ContentRewardVideo out/final-clip.mp4 --props=remotion-props.json --concurrency=3
```

### Style B (Fullbleed Speaker)
Gunakan komposisi `FullBleedClip` (nama komposisi juga tertulis di output JSON `export_remotion.py`):
```bash
cd remotion-template
npx remotion still src/index.ts FullBleedClip out/check-f5.png --props=remotion-props.json --frame=5
npx remotion render src/index.ts FullBleedClip out/final-clip.mp4 --props=remotion-props.json --concurrency=3
```
Cek still frame: frame 5 (shot pembuka), tiap jenis shot (close-up host, close-up tamu, wide shot), overlay foto (kredit terbaca), dan CTA di 2,5 detik terakhir. Klip 50 detik ±5 menit render, ±57 MB.

### Batasi Konkurensi (Penting di Laptop RAM 16 GB)
Concurrency tinggi (6–8) membuka banyak instance Chrome sekaligus; saat RAM penuh, Windows memperbesar `C:\pagefile.sys` (teramati +6 GB) dan ruang drive C: berkurang drastis. Gunakan `--concurrency=3`. Klip 25 detik selesai ±2,5 menit.

Opsi tambahan bila GPU mendukung:

```bash
npx remotion render src/index.ts ContentRewardVideo out/final-clip.mp4 \
  --props=remotion-props.json \
  --concurrency=3 \
  --gl=angle \
  --codec=h264
```

### Catatan Windows
- **EPERM saat rename di akhir render**: file output sedang terbuka di video player. Tutup player atau render ke nama file baru; hasil yang sudah selesai tersimpan sebagai `*.remotion-in-progress` dan bisa di-rename manual.
- Cache `%TEMP%\remotion-v4.*-assets*` tidak dibersihkan otomatis; aman dihapus saat tidak ada render berjalan.

---

## 4. Spesifikasi Teknis Video Output

Output render memenuhi standar teknis platform video pendek:
- **Resolusi**: 1080 x 1920 (Vertikal 9:16)
- **Framerate**: 30 fps stabil
- **Video Codec**: H.264 (High Profile)
- **Audio Codec**: AAC 48kHz Stereo (dialog dari kartu A-roll + SFX otomatis pada volume master 0,35)
- **Pixel Aspect Ratio**: 1:1

File hasil render tersimpan pada path `remotion-template/out/final-clip.mp4`.
