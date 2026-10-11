# Alur Kerja 05: Kepatuhan Aturan Campaign dan Prosedur Submission

## 1. Ikhtisar Ketentuan Program Content Rewards

Agar klip video disetujui kurator campaign dan berhak mendapatkan reward, proses produksi dan submission wajib mematuhi 7 ketentuan berikut:

---

## 2. Rincian 7 Ketentuan Wajib

### 1. Outro Redirection CTA ke YouTube
* **Aturan**: Klip video wajib memuat arahan kepada penonton untuk menonton episode penuh di channel YouTube resmi.
* **Implementasi**: Komponen `OutroCtaBanner` muncul otomatis pada 3 detik terakhir video (90 frame terakhir) yang menampilkan nama channel YouTube dan ajakan bertindak ("WATCH FULL EPISODE ON YOUTUBE").

### 2. Visibilitas Host atau Bintang Utama (Minimal 20% Durasi)
* **Aturan**: Wajah narasumber atau host wajib terlihat secara visual minimal 20% dari total durasi video.
* **Implementasi**: Tata letak kartu video utama A-Roll menampilkan feed wajah pembicara sepanjang durasi video secara konsisten.

### 3. Batas Waktu Submission: Maksimal 30 Menit Setelah Upload
* **Aturan**: Tautan video TikTok wajib disubmit ke dashboard campaign dalam waktu maksimal 30 menit terhitung sejak video dipublikasikan di TikTok.
* **Catatan**: Submission yang melewati batas 30 menit akan ditolak otomatis oleh sistem verifikasi.

### 4. Batas Maksimal Upload Harian
* **Aturan**: Maksimal 2 posting video per hari per akun TikTok.
* **Distribusi**: Unggah video pertama pada rentang 12:00 - 13:00 dan video kedua pada 19:00 - 21:00.

### 5. Ketentuan Hashtag (Maksimal 5 Hashtag di TikTok)
* **Aturan**: Gunakan maksimal 5 hashtag yang relevan. Algoritma TikTok membatasi performa posting yang menggunakan tag berlebih.
* **Struktur 5 Hashtag**:
  1. `#[TagarWajibCampaign]` (contoh: `#nocomfort`)
  2. `#[NamaChannelOriginal]` (contoh: `#lyricallemonade`)
  3. `#[SubjekVideo]` (contoh: `#steamchalice`)
  4. `#[KategoriKonten]` (contoh: `#podcastclips`)
  5. `#[AudienceNiche]` (contoh: `#rapculture`)

### 6. Akun Terdaftar (Dedicated Account)
* **Aturan**: Akun TikTok yang digunakan harus berstatus akun klip podcast yang telah terhubung pada dashboard Content Rewards.

### 7. Diferensiasi Visual
* **Aturan**: Klip wajib melalui proses editing dan penyesuaian tata letak agar tidak terdeteksi sebagai reupload mentah oleh sistem hak cipta platform.

---

## 3. Format Template Caption

Gunakan format caption berikut saat posting ke TikTok:

```text
[Ringkasan premis atau kutipan dialog utama video]

Tonton episode lengkapnya di YouTube: [Nama Channel]

#[TagarWajib] #[TagarKanal] #[TagarTopik] #podcastclips #[TagarNiche]
```

### Contoh Penerapan:
```text
Pengakuan Steam Chalice tentang momen awal karirnya yang tidak banyak diketahui publik.

Tonton episode lengkapnya di YouTube: Lyrical Lemonade TV

#nocomfort #lyricallemonade #steamchalice #podcastclips #rapculture
```

---

## 4. Checklist Prosedur Submission 30 Menit

1. [ ] Render video selesai (`out/final-clip.mp4`).
2. [ ] Upload video ke aplikasi TikTok melalui smartphone.
3. [ ] Masukkan caption dan tepat 5 hashtag.
4. [ ] Tekan tombol Posting.
5. [ ] Salin tautan video (Share > Copy Link) segera setelah posting berhasil.
6. [ ] Buka dashboard Content Rewards sebelum 30 menit terlampaui.
7. [ ] Masukkan tautan video TikTok dan kirim formulir submission.
8. [ ] Pastikan status submission tercatat sebagai Pending Review atau Submitted.
