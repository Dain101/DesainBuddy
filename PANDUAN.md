# Panduan DesainBuddy untuk yang belum pernah mengoding

Kamu tidak perlu mengetik kode apa pun. Kamu hanya perlu mengunggah folder ini, menempel satu kunci rahasia, lalu menekan tombol. Lakukan di laptop atau komputer, karena mengunggah banyak berkas lebih mudah di layar besar.

## Isi paket

- `app.py` dan `logika.py`: otak aplikasi. Jangan diubah kalau belum paham.
- `materi/`: enam berkas materi (bab 1 sampai 5 dan tugas praktik poster). Ini bahan yang dipakai chatbot untuk menjawab.
- `kuis.json`: 20 soal latihan (4 soal per bab, bab 1 sampai 5).
- `requirements.txt`: daftar pustaka yang dipasang otomatis oleh server.
- `.streamlit/config.toml`: pengaturan warna tampilan.
- `.streamlit/secrets.toml.example`: contoh isi kotak Secrets (bukan rahasia asli).
- `uji_logika.py`: pengujian otomatis (opsional, untuk lampiran skripsi).

## Langkah A. Ambil kunci API Gemini

1. Buka https://aistudio.google.com/apikey lalu masuk dengan akun Google.
2. Klik **Create API key** dan salin kuncinya. Simpan di tempat aman dan jangan kirim ke siapa pun.
3. Buka https://ai.google.dev/gemini-api/docs/models dan catat satu nama model Flash yang tersedia untuk paket gratis, misalnya `gemini-3.8-flash`. Nama model dan kuota gratis bisa berubah, jadi cek halaman Rate limits dan Pricing di situs yang sama.

Catatan privasi: pada paket gratis, Google dapat memakai input dan output untuk memperbaiki produknya. Karena itu siswa wajib diingatkan agar tidak menulis data pribadi. Aplikasi ini sudah menyamarkan email dan nomor HP secara otomatis, tetapi itu bukan jaminan penuh.

## Langkah B. Unggah folder ke GitHub

1. Buat akun di https://github.com lalu masuk.
2. Klik tanda **+** di kanan atas, pilih **New repository**. Beri nama `desainbuddy`, pilih **Public** atau **Private**, lalu klik **Create repository**.
3. Di halaman repository, klik tulisan **uploading an existing file**.
4. Ekstrak berkas ZIP dari saya. Buka folder hasil ekstrak, pilih semua isinya, lalu seret ke halaman GitHub. Pastikan folder `materi` ikut terunggah.
5. Klik **Commit changes**.

Jangan pernah mengunggah kunci API asli ke GitHub. Kunci hanya ditempel di Langkah C.

Kalau folder `.streamlit` tidak ikut terseret (folder berawalan titik kadang tersembunyi), tidak apa-apa. Aplikasi tetap jalan, hanya warna temanya memakai pengaturan bawaan.

## Langkah C. Pasang online di Streamlit Community Cloud

1. Buka https://share.streamlit.io lalu masuk dengan akun GitHub-mu.
2. Klik **Create app** (atau **New app**), lalu pilih deploy dari repository yang sudah ada.
3. Pilih repository `desainbuddy`, cabang `main`, dan berkas utama `app.py`.
4. Klik **Advanced settings**. Pada kolom **Secrets**, tempel tiga baris berikut dengan isimu sendiri:

```
GEMINI_API_KEY = "kunci-api-milikmu"
GEMINI_MODEL = "nama-model-dari-langkah-A"
ADMIN_PASSWORD = "kata-sandi-buatanmu"
```

5. Klik **Save**, lalu **Deploy**. Tunggu beberapa menit. Setelah jadi, kamu mendapat alamat berakhiran `.streamlit.app`. Alamat itulah yang dibagikan ke siswa.

Untuk mengubah Secrets setelah aplikasi jadi, buka pengaturan aplikasi di halaman workspace Streamlit.

## Langkah D (opsional). Menjalankan di laptop

1. Pasang Python dari python.org dan centang **Add Python to PATH**.
2. Buka folder ini, klik kolom alamat, ketik `cmd`, tekan Enter.
3. Ketik `pip install -r requirements.txt` lalu Enter.
4. Buat folder bernama `.streamlit` (kalau belum ada), lalu salin `secrets.toml.example` menjadi `secrets.toml` dan isi nilainya.
5. Ketik `streamlit run app.py` lalu Enter. Browser akan terbuka sendiri.

## Cara memakai

- Siswa masuk dengan **kode siswa** (misalnya S01 sampai S36) yang kamu bagikan. Jangan pakai nama asli.
- Ada empat mode: Belajar, Latihan, Praktik, dan Tanya Bebas.
- Kamu masuk sebagai peneliti dengan kode siswa apa saja (misalnya PENELITI), lalu buka **Panel peneliti** di sidebar dan isi `ADMIN_PASSWORD`. Di sana ada ringkasan dan tombol unduh CSV percakapan serta jawaban kuis.

## Masalah yang sering muncul

- **Muncul pesan nama model tidak ditemukan.** Ganti nilai `GEMINI_MODEL` di Secrets dengan nama model yang benar dari Google AI Studio.
- **Muncul pesan kuota penuh.** Tunggu satu menit. Kalau sering terjadi saat satu kelas memakai bersamaan, minta siswa bergiliran atau pertimbangkan paket berbayar.
- **Aplikasi lambat saat pertama dibuka.** Server gratis bisa tertidur kalau lama tidak dipakai. Buka sekali beberapa menit sebelum pelajaran dimulai.
- **Data riwayat hilang.** Penyimpanan di server gratis tidak dijamin permanen. Unduh CSV dari Panel peneliti setiap selesai pertemuan.
- **Pesan galat lain.** Salin isi kotak **Detail teknis** dan kirim ke saya.

## Mengganti materi dan soal

- Materi ada di folder `materi/`. Tiap subjudul diawali tanda `## ` dan itulah satuan potongan yang dicari chatbot. Kamu boleh mengganti isinya dengan modul gurumu. Mulai tiap berkas dengan satu baris judul berawalan `# `.
- Soal ada di `kuis.json`. Kalau mau menambah atau mengganti soal, kirim materi barunya ke saya dan saya buatkan.
- Isi materi dan soal bawaan adalah draf awal dari saya. Sebelum dipakai untuk penelitian, wajib divalidasi oleh ahli materi desain grafis dan guru Informatika.

## Untuk bahan skripsimu

| Bagian sistem | Fungsinya di penelitian |
|---|---|
| Basis pengetahuan (`materi/`) | Sumber isi yang membatasi jawaban chatbot |
| Pencarian TF-IDF di `logika.py` | Versi ringan dari konsep RAG: potongan materi yang relevan dikirim ke AI sebagai konteks |
| Kuis dan petunjuk bertahap | Data skor latihan dan jumlah petunjuk per siswa |
| Rating 👍 dan 👎 | Data persepsi kualitas jawaban |
| Log percakapan | Bahan analisis pola pertanyaan dan interaksi |
| Mode Praktik dan rubrik | Umpan balik hasil praktik poster |
| `uji_logika.py` | Bukti pengujian otomatis untuk bagian logika (lampiran uji fungsional) |

Hal yang harus kamu tulis jujur di skripsi:

- Pencarian materi memakai TF-IDF (pencocokan kata), bukan embedding neural. Ini lebih sederhana dan mudah dijelaskan, tetapi kurang peka terhadap sinonim.
- Pretest dan posttest dibuat terpisah (kertas atau Google Form), tidak ada di dalam aplikasi.
- Kuota gratis, nama model, dan kebijakan data Google bisa berubah. Catat tanggal pengambilan informasinya.
- Penilaian AI terhadap poster adalah umpan balik belajar, bukan penilaian resmi. Pakai penilaian guru atau dua penilai manusia untuk data penelitian.
- Metode `generateContent` yang dipakai aplikasi ini ditandai Google sebagai versi lama (legacy) di dokumentasinya, dan Google menyarankan Interactions API untuk proyek baru. Metode lama masih didokumentasikan saat paket ini dibuat. Kalau suatu saat berhenti bekerja, minta saya memperbaruinya.
