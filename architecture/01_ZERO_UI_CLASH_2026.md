# Spesifikasi Arsitektur: Zero UI Clash (Standar Mobile 2026)

## 1. Definisi Masalah

Pada aplikasi video pendek modern (khususnya TikTok dengan antarmuka 2026, Instagram Reels, dan YouTube Shorts), tata letak antarmuka aplikasi menempati sebagian area kanvas video vertikal:

1. **Header Atas**: TikTok menampilkan bilah pencarian persisten (Search Pill `[Find related content / Search]`), tombol kembali `<`, serta area potongan perangkat fisik (notch dan Dynamic Island pada perangkat flagship).
2. **Action Rail Kanan**: Deretan tombol profil, like, comment, bookmark, dan share menempati lebar sekitar 100px pada sisi kanan layar.
3. **Bottom UI Stack**: Nama pengguna pembuat konten (`@username`), deskripsi caption bertingkat, tombol "See more", audio marquee, dan tab navigasi bawah aplikasi.

Jika elemen teks grafis (seperti headline hook, subtitle, atau lencana narasumber) diletakkan di luar area aman, teks tersebut akan tertutup oleh elemen antarmuka aplikasi, menurunkan keterbacaan dan melanggar standar submission campaign.

---

## 2. Kanvas dan Sistem Koordinat (1080 x 1920 px)

Arsitektur kliping menerapkan sistem penempatan vertikal berbasis zona aman:

```
0 px --------------------------------------------------------
     [ZONA LARANGAN ATAS: Y 0 - 285px]
     (Tertutup Dynamic Island, Notch, Tombol Back, Search Bar TikTok)
285px --------------------------------------------------------
295px  Attention Trigger Badge (Detik 0 - 3) [Z-Index: 65]
355px  +--------------------------------------------------+
       | HOOK HEADLINE BANNER (Yellow Pill #FFE600)       |
       | Max Width: 820px, Centered (X: 130px - 950px)    |
485px  +--------------------------------------------------+
505px                          Paperclip Sticker (X: Right 110px)
615px  Talking Head Badge ("LYRICAL LEMONADE // HOST")
660px  +--------------------------------------------------+ |
       |                                                  | |
       |        MAIN A-ROLL TALKING HEAD CARD             | | Right Action Rail
       |        Width: 860px | Height: 484px (16:9)       | | Exclusion Zone
       |        Border: 3px Solid White | Rounded: 24px   | | (X: 980 - 1080px)
       |                                                  | |
1144px +--------------------------------------------------+ |
       
1350px +--------------------------------------------------+
       | SUBTITLE GOLDEN BAND                             |
       | Kinetic Word-Level Highlighting (Yellow/Black)   |
1450px +--------------------------------------------------+
1480px --------------------------------------------------------
     [ZONA LARANGAN BAWAH: Y 1480 - 1920px]
     (Tertutup Username, Caption, Audio Marquee, Bottom Nav)
1920px --------------------------------------------------------
```

---

## 3. Spesifikasi Komponen dan Koordinat

### A. Top Exclusion Zone (Y: 0-285px)
* **Status**: Area larangan konten teks dan grafis penting.
* **Tujuan**: Mencegah tabrakan dengan bilah pencarian TikTok (`[Search]`) dan notch perangkat pada rentang Y 100-260px.
* **Aturan**: Tidak menempatkan teks atau ikon informasi pada zona ini. Elemen visual latar belakang (grid teknis atau blur) tetap mengisi kanvas penuh.

### B. Attention Trigger Badge (Y: 295px)
* **Komponen**: `<AttentionTriggerBadge />` di `HookAnimations.tsx`.
* **Posisi**: `top: 295px`, `left: 50%`, `transform: translateX(-50%)`.
* **Durasi Aktif**: Frame 0-90 (0.0s sampai 3.0s).
* **Format**: Latar belakang `#FF3B30` atau `#1A1A1A`, border kontras, teks uppercase tebal (`MUST WATCH` atau `JANGAN SKIP`).

### C. Hook Headline Banner (Y: 355px)
* **Komponen**: `<HookHeadlineBanner />` di `ContentRewardVideo.tsx`.
* **Posisi**: `top: 355px`, `left: 50%`, `transform: translateX(-50%)`.
* **Dimensi**: `max-width: 820px`, padding `16px 28px`.
* **Gaya**: Latar belakang `#FFE600`, teks hitam `#000000`, font weight 900, drop shadow `0 16px 36px rgba(0,0,0,0.65)`.
* **Batas Bawah**: Berakhir pada Y sekitar 485px, menyisakan jarak aman minimal 20px sebelum elemen sticker.

### D. Paperclip Sticker dan Stat Callout (Y: 505px)
* **Posisi**: `top: 505px`, `right: 110px` (aman dari Action Rail di sisi kanan X > 970px).
* **Fungsi**: Label referensi dokumen atau data metrik tambahan.
* **Stat Counter**: Animasi angka dengan format font monospaced tabular figures.

### E. Kartu Video Utama (A-Roll) (Y: 660px - 1144px)
* **Komponen**: `<TalkingHeadCard />` di `ContentRewardVideo.tsx`.
* **Posisi**: `top: 47%`, `transform: translate(-50%, -50%)`.
* **Dimensi**: Lebar 860px, rasio aspek 16:9 standar YouTube (tinggi sekitar 484px).
* **Border dan Bayangan**: `border: 3px solid rgba(255, 255, 255, 0.95)`, `border-radius: 24px`, shadow `0 24px 60px rgba(0, 0, 0, 0.8)`.
* **Latar Belakang**: Blur video duplikat (`filter: blur(40px) brightness(0.28)`) ditambah kisi-kisi teknis editorial (`#18181B`).

### F. Speaker Badge (Y: 615px atau Bottom: 480px)
* **Komponen**: `<TalkingHeadBadge />` di `TalkingHeadLayer.tsx`.
* **Posisi**: `top: 615px`, `left: 110px` (terletak tepat di atas sudut kiri kartu video) atau `bottom: 480px`, `left: 110px`.
* **Tujuan**: Menghindari tabrakan dengan nama pengguna TikTok di kiri bawah layar.
* **Format**: `[NAMA PEMBICARA] // [PERAN]`.

### G. Subtitle Golden Band (Y: 1350px - 1450px)
* **Komponen**: Word-level kinetic subtitle.
* **Posisi**: `top: 1350px-1450px`, `left: 50%`, `transform: translateX(-50%)`.
* **Lebar Maksimal**: 840px.
* **Tipografi**: Ukuran 42px-48px sans-serif tebal, penyorotan kata aktif berwarna kuning (`#FFE600`) dengan teks hitam, kata tidak aktif berwarna putih dengan opasitas parsial.
* **Jarak Aman**: Terletak minimal 30px di atas batas awal deskripsi caption TikTok (1480px).

### H. Outro CTA Banner (90 Frame Terakhir / 3 Detik Penutup)
* **Posisi**: `top: 660px`, `left: 50%`, `transform: translateX(-50%)`.
* **Fungsi**: Memenuhi ketentuan kampanye Content Rewards untuk pengalihan ke video YouTube original.
* **Format**: Kartu penutup dengan nama channel YouTube dan teks ajakan bertindak `WATCH FULL EPISODE ON YOUTUBE`.

---

## 4. Daftar Verifikasi Zona Aman

Sebelum melakukan render final, periksa poin berikut:

- [ ] Teks Hook Headline dimulai pada Y >= 350px (bebas dari bilah pencarian TikTok).
- [ ] Lebar maksimal elemen teks <= 840px (menyisakan margin minimal 120px di kiri dan kanan).
- [ ] Margin kanan bebas dari teks atau tombol penting pada X > 970px (bebas dari Action Rail).
- [ ] Subtitle berada dalam rentang Y: 1350px sampai Y: 1450px (bebas dari area caption TikTok).
- [ ] Badge narasumber diposisikan pada Y: 615px (di atas kartu video) dan bukan pada sudut kiri bawah (Y > 1600px).
