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

---

## 3. Rendering Video Final

Jalankan perintah render Remotion menggunakan file props yang telah digenerate:

```bash
cd remotion-template
npx remotion render ContentRewardVideo out/final-clip.mp4 --props=remotion-props.json
```

### Opsi Optimasi Kecepatan Render (Windows dan Multi-Core):
Tambahkan konkurensi thread dan akselerasi grafis untuk mempercepat render:

```bash
npx remotion render ContentRewardVideo out/final-clip.mp4 \
  --props=remotion-props.json \
  --concurrency=6 \
  --gl=angle \
  --codec=h264
```

---

## 4. Spesifikasi Teknis Video Output

Output render memenuhi standar teknis platform video pendek:
- **Resolusi**: 1080 x 1920 (Vertikal 9:16)
- **Framerate**: 30 fps stabil
- **Video Codec**: H.264 (High Profile)
- **Audio Codec**: AAC 48kHz Stereo 320kbps
- **Pixel Aspect Ratio**: 1:1

File hasil render tersimpan pada path `remotion-template/out/final-clip.mp4`.
