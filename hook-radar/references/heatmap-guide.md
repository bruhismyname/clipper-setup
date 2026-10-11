# Panduan Heatmap (Most Replayed)

Kurva Most Replayed YouTube memuat data rewatch audiens yang disampel pada 100 titik di sepanjang video. Data ini memberikan indikator objektif terkait retensi penonton untuk melengkapi evaluasi transkrip teks.

## Nilai Skala Kurva

| Nilai | Keterangan |
|---|---|
| **1.0** | Titik dengan pemutaran ulang terbanyak pada video tersebut |
| **0.5** | Setengah dari intensitas puncak retensi |
| **~0.0** | Titik tanpa aktivitas pemutaran ulang signifikan |

Nilai bersifat relatif terhadap puncak tertinggi video itu sendiri, bukan skala absolut antar-video.

## Algoritma Deteksi Puncak

Modul `heatmap.py` menerapkan empat tahap pemrosesan:

1. **Smoothing (3-point moving average)**: Meredam lonjakan satu sampel (noise).
2. **Uji Prominensi** (`>= 0.18`): Memastikan puncak naik cukup tinggi dibanding lembah terdekat di kiri dan kanan.
3. **Uji Level Relatif** (`>= 0.45`): Berada minimal pada 45% rentang data video tersebut.
4. **Pemisahan Minimum** (8s): Menggabungkan dua lonjakan berjarak kurang dari 8 detik menjadi satu momen.

Puncak diurutkan berdasarkan intensitas (`rank_in_video`), dan 12-15 puncak terkuat digunakan sebagai kandidat pemotongan.

## Pola Bentuk Puncak

Sebuah puncak menunjukkan titik di mana audiens memutar ulang video:

| Pola | Indikasi | Rekomendasi |
|---|---|---|
| **Spike Tajam** | Punchline dialog, pengungkapan data, klaim mengejutkan | Kandidat utama klip. Periksa 5 detik sebelum titik puncak. |
| **Plateau Lebar** | Cerita naratif panjang atau sesi demonstrasi | Cari kalimat terkuat di dalam segmen dan jadikan titik pembuka. |
| **Spike di Awal** | Intro atau teaser yang diputar ulang | Sering kali bukan konten mandiri; evaluasi apakah ada substansi. |

Momen paling relevan biasanya berada sedikit sebelum puncak karena penonton cenderung memutar balik untuk mendengarkan kembali kalimat pembuka.

## Kondisi Tanpa Data Heatmap

Data Most Replayed tidak tersedia pada:
- Video yang baru saja diunggah
- Video dengan jumlah penayangan rendah
- Konten live stream yang belum selesai diproses

Jika data heatmap tidak tersedia:
1. Script menandai `heatmap.available = false`.
2. Skor retensi diset netral (50).
3. Bobot evaluasi dialihkan ke analisis kualitas transkrip (0.65).
4. Agent mencantumkan catatan bahwa penilaian berbasis teks tanpa validasi retensi penonton.

## Batasan Penggunaan

- **Video Musik**: Audiens memutar ulang melodi lagu, bukan dialog. Evaluasi transkrip tidak efektif untuk jenis video ini.
- **Visual Gags**: Adegan komedi fisik tanpa dialog tidak menghasilkan transkrip teks.
- **Live Stream Sangat Panjang**: Resolusi 100 titik pada video berdurasi lebih dari 4 jam terlalu kasar untuk menentukan timestamp 20 detik secara akurat.
