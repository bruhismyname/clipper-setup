# Spesifikasi Arsitektur: 10-Layer Motion Stack

## 1. Konsep Pemisahan Lapisan

Rendering video vertikal dibagi menjadi 10 lapisan visual terisolasi (*10-layer motion stack*). Pembagian lapisan ini menjamin:

1. **Isolasi Hierarki Tata Letak**: Komponen diposisikan menggunakan koordinat absolut terpisah sehingga modifikasi satu elemen tidak merusak posisi elemen lain.
2. **Efisiensi Evaluasi Render**: Elemen statis dan elemen dinamis dievaluasi secara independen oleh pipeline Remotion.
3. **Standar Kualitas Visual**: Menghasilkan tata letak terstruktur dengan kontras dan keterbacaan teks yang konsisten.

---

## 2. Struktur Lapisan dan Hierarki Z-Index

```
+------------------------------------------------------------------------+
| Z-Index 90: Layer 10 - Cine-Optics FX (Grain, Vignette, Chromatic)     |
+------------------------------------------------------------------------+
| Z-Index 80: Layer 09 - Hook Camera Slam & Retention Scrubber Bar       |
+------------------------------------------------------------------------+
| Z-Index 70: Layer 08 - Word-Level Kinetic Subtitles & Text Slams       |
+------------------------------------------------------------------------+
| Z-Index 60: Layer 07 - Stickers, Animated Stats, & Attention Badges   |
+------------------------------------------------------------------------+
| Z-Index 50: Layer 06 - HTML Mockups (Browser, Tweet, Search)           |
+------------------------------------------------------------------------+
| Z-Index 40: Layer 05 - B-Roll Cutaways & Archival Video/Image Inserts  |
+------------------------------------------------------------------------+
| Z-Index 30: Layer 04 - Main A-Roll Card & Speaker Spotlight Badge     |
+------------------------------------------------------------------------+
| Z-Index 20: Layer 03 - Floating Ambient Bokeh Particles                |
+------------------------------------------------------------------------+
| Z-Index 10: Layer 02 - Full-Bleed Video Background Blur                |
+------------------------------------------------------------------------+
| Z-Index 00: Layer 01 - Technical Blueprint Grid                        |
+------------------------------------------------------------------------+
```

---

## 3. Rincian Teknis Tiap Lapisan

### Layer 01: Technical Blueprint Grid (`EditorialGridBackground.tsx`)
* **Z-Index**: `0-5`
* **Deskripsi**: Pola grid teknis berukuran 60px dengan latar belakang `#09090B` dan opasitas garis `rgba(255, 255, 255, 0.04)`.
* **Fungsi**: Memberikan struktur geometris pada latar belakang.

### Layer 02: Full-Bleed Video Background Blur
* **Z-Index**: `10`
* **Deskripsi**: Duplikasi stream video A-roll utama yang diskalakan mengisi seluruh kanvas (1080x1920) dengan filter:
  `filter: blur(40px) brightness(0.28) contrast(1.15);`
* **Fungsi**: Mengisi ruang vertikal kosong di luar rasio 16:9 kartu video utama.

### Layer 03: Floating Ambient Bokeh Particles (`BodyAnimations.tsx`)
* **Z-Index**: `20`
* **Deskripsi**: 16-24 partikel bokeh halus dengan variasi opasitas dan posisi berbasis fungsi matematika kontinu.
* **Fungsi**: Menjaga kedalaman visual pada latar belakang selama video berlangsung.

### Layer 04: Main A-Roll Talking Head Card (`TalkingHeadLayer.tsx`)
* **Z-Index**: `30`
* **Deskripsi**: Kartu video utama dengan rasio 16:9 (lebar 860px, tinggi 484px), border 3px solid, radius sudut 24px, dan drop shadow pekat.
* **Fitur**:
  - **Dynamic Punch-Zoom**: Perubahan skala halus (1.0x ke 1.05x) pada poin penting dialog.
  - **Speaker Spotlight Badge**: Penanda nama dan peran pembicara di atas kartu video.

### Layer 05: B-Roll Cutaways (`BRollLayer.tsx`)
* **Z-Index**: `40`
* **Deskripsi**: Sisipan video atau gambar pendukung narasi dengan transisi spring.
* **Fitur**: Animasi pan dan zoom (Ken Burns) dengan label sumber referensi.

### Layer 06: HTML Mockups (`HtmlMotionLayer.tsx`)
* **Z-Index**: `50`
* **Deskripsi**: Render komponen UI web berupa browser window, tweet feed, atau search query.
* **Fungsi**: Menampilkan materi pembuktian kontekstual yang dibahas dalam dialog.

### Layer 07: Stickers, Stat Counters, dan Attention Badges (`HookAnimations.tsx`)
* **Z-Index**: `60`
* **Deskripsi**:
  - **Attention Trigger Badge**: Lencana penarik perhatian di Y: 295px (Frame 0-90).
  - **Hook Headline Banner**: Banner utama kuning di Y: 355px.
  - **Animated Stat Counter**: Perhitungan angka beranimasi berbasis spring.
  - **Paperclip Sticker**: Label tape di Y: 505px.

### Layer 08: Word-Level Kinetic Subtitles (`KineticTextMotion.tsx`)
* **Z-Index**: `70`
* **Deskripsi**: Subtitle berbasis per kata yang disinkronkan dengan timestamp dari Whisper.
* **Mekanisme**: Kata yang aktif disorot dengan warna kuning (`#FFE600`) dan teks hitam, berada pada rentang Subtitle Golden Band (Y: 1350px-1450px).

### Layer 09: Hook Impact dan Retention Scrubber Bar (`BodyAnimations.tsx`)
* **Z-Index**: `80`
* **Deskripsi**:
  - **Impact Flash (Detik 0.0-0.2)**: Flash putih singkat untuk transisi awal.
  - **Camera Slam (Detik 0.0-0.5)**: Efek guncangan skala kecil teredam menggunakan kurva pegas (spring physics).
  - **Retention Scrubber Bar**: Indikator progres durasi video di Y: 1470px.

### Layer 10: Cine-Optics FX (`AdvancedVisualEffects.tsx`)
* **Z-Index**: `90`
* **Deskripsi**: Lapisan efek visual komposit teratas:
  - **Dynamic Vignette**: Penggelapan gradual di sudut layar.
  - **Chromatic Aberration Pulse**: Pemisahan kanal warna pada transisi aksen.
  - **Anamorphic Light Leak**: Efek pencahayaan pada transisi pembuka.
  - **Film Grain Overlay**: Tekstur film noise halus untuk menyatukan elemen visual grafis dan video.
