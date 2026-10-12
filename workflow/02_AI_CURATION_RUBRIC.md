# Alur Kerja 02: Rubrik Penilaian Kurasi 6 Dimensi

## 1. Tujuan Evaluasi

Segmen yang dihasilkan oleh `hook-radar` dievaluasi menggunakan rubrik penilaian 6 dimensi dengan skor total maksimal 100 poin untuk menentukan kelayakan publikasi.

---

## 2. Rincian Dimensi Penilaian

| Dimensi | Bobot | Deskripsi dan Kriteria |
| :--- | :---: | :--- |
| **1. Retention Heatmap Peak** | **25 Poin** | Keselarasan segmen dengan puncak kurva Most Replayed pada video original. Segmen pada puncak lonjakan retensi mendapat skor maksimal (20-25). |
| **2. Hook Strength (0-3s)** | **20 Poin** | Kualitas kalimat pembuka di detik 0-3. Memuat premis yang jelas, fakta menarik, atau pertanyaan terbuka yang mengarahkan konteks video. |
| **3. Information Density** | **20 Poin** | Kepadatan dialog dan substansi topik. Meminimalkan jeda hening berkepanjangan dan transisi narasi yang tidak efisien. |
| **4. Emotional Contrast** | **15 Poin** | Dinamika nada bicara atau perubahan topik pembicara (perdebatan, klarifikasi, humor, atau pemaparan data mengejutkan). |
| **5. Narrative Completeness** | **10 Poin** | Keutuhan struktur narasi (memiliki premis awal, isi pembahasan, dan simpulan yang dapat dipahami tanpa perlu menonton episode utuh). |
| **6. Visual & Speaker Presence** | **10 Poin** | Kejelasan ekspresi pembicara utama dan keterpenuhan syarat tampilan wajah host (minimal 20% durasi total). |

---

## 3. Standar Kelayakan Skor

- **Skor 85-100 (Tier S)**: Kualitas optimal. Prioritas utama untuk langsung diproses render dan dipublikasikan.
- **Skor 70-84 (Tier A)**: Memenuhi standar. Layak diproses dengan penajaman headline hook banner atau penambahan B-roll pendukung.
- **Skor < 70 (Tier B/C)**: Tidak memenuhi standar. Narasi terpotong atau tempo pembicaraan terlalu lambat untuk format video pendek.

---

## 4. Prosedur Seleksi Kandidat

Dalam memilih kandidat dari file `runs/<id>/candidates.json`:

1. **Pemeriksaan Durasi & Pilihan Style**:
   - **Style A (Editorial Card)**: **20–45 detik**, untuk momen pendek dengan satu punchline. Completion rate tinggi.
   - **Style B (Fullbleed Speaker)**: **45–90 detik**, untuk satu topik utuh (debat, cerita) yang punya banyak benda/konsep untuk divisualkan dan reaksi lawan bicara sebagai titik cut. Dasar ATM: 4 video teratas @dailyyskchaos berdurasi 94–128 detik (`architecture/04_STYLE_B_FULLBLEED.md`).
   - Catat style di feedback loop agar bisa dibandingkan performanya.
2. **Pemeriksaan Kalimat Pembuka**:
   - Hindari klip yang diawali kalimat tidak lengkap seperti kata sambung tanpa konteks ("And then", "Like I said").
   - Pilih klip yang langsung menyatakan subjek atau masalah utama di kalimat pertama.
   - **Tanpa jeda hening di 3 detik pertama.** Bila pertanyaan pembuka diikuti jeda panjang, mulai klip setelah jeda (`--start/--end` di `export_remotion.py`) dan biarkan headline membawa konteks pertanyaannya.
   - **Framing respek**: tertawa *bersama* narasumber, bukan menertawakan. Ini penting untuk tamu yang rentan, misalnya peserta *Love on the Spectrum*.
   - **Formula Hook ATM** (wajib Style B, disarankan Style A): kata pertama di detik 0,0 berupa salah satu dari 4 tipe:

     | Tipe | Contoh |
     |---|---|
     | Pertanyaan relatable | "Has anybody noticed it's getting a lot harder to type on your iPhone?" |
     | Dilema / would-you-rather | "Would you punch Sarah in the face… for a billion dollars?" |
     | Klaim aneh | "Banana and avocado is supposed to taste like ice cream." |
     | Misteri sehari-hari | "Where the hell do they build cruise ships?" |

     Jika kalimat itu muncul di tengah, geser `--start` ke kata pertamanya. Topik debat yang bisa dijawab penonton memancing komentar jauh lebih banyak.
3. **Rencana Timeline Aset** (detik relatif di dalam klip):
   - Screenshot halaman asli saat tokoh/acara disebut; B-roll episode saat host bertanya; B-roll stok saat benda disebut; text slam tepat saat punchline diucapkan.
   - Maksimal 1–2 B-roll + 1 mockup, masing-masing 1,5–3 detik; jangan menutupi wajah saat punchline; jangan masuk 3 detik terakhir.
   - Style B: rencana overlay kata kunci (1 per 3–5 detik, foto untuk benda, emoji untuk emosi) dan rencana crop per shot, lihat `workflow/03_REMOTION_BRIDGE.md` §6.
4. **Penyusunan Hook Headline** (Style A saja; Style B tidak memakai headline):
   - Tentukan teks headline ringkas (maksimal 6-8 kata, huruf kapital).
   - Contoh: `10M ARR DALAM 60 HARI`, `FAKTA DI BALIK KASUS VIRAL`, `JANGAN LAKUKAN KESALAHAN INI`.
