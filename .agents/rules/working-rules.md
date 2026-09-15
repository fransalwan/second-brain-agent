# Cara Kerja di Project Ini

Aturan ini mengatur **bagaimana** mengerjakan tugas, bukan aturan teknis kodenya. Untuk aturan teknis, lihat `project-rules.md`.

Aturan ini lahir dari pola yang benar-benar terjadi saat pengembangan project ini, bukan prinsip abstrak.

---

## 1. Kerjakan yang diminta, tidak lebih

Ini aturan terpenting di dokumen ini.

Kalau masalahnya bisa diselesaikan dengan mengubah satu baris teks, ubah satu baris teks. Jangan memperkenalkan mekanisme, abstraksi, atau pustaka baru untuk masalah yang tidak membutuhkannya.

**Contoh nyata dari project ini.** Ada satu nama variabel yang salah di `.env.example`. Perbaikannya: ganti satu baris. Yang sempat diusulkan: memakai `AliasChoices` pydantic agar kedua nama diterima — menambah kerumitan di `config.py` dan membuat salah ketik nama variabel diterima diam-diam alih-alih menimbulkan error.

Tanda kamu sedang melebar:
- Kamu memperkenalkan konsep yang belum ada di codebase ini
- Kamu menyentuh file yang tidak disebut dalam tugas
- Kamu menyelesaikan masalah yang belum dikeluhkan siapa pun
- Solusimu membuat kesalahan di masa depan lebih sulit terdeteksi

Kalau kamu melihat masalah lain di luar tugas, **laporkan sebagai temuan**. Jangan perbaiki tanpa diminta.

## 2. Jangan ubah perilaku yang sudah terverifikasi

Kalau sebuah fungsi sudah diuji dan berjalan, jangan menyentuhnya untuk "memperkuat" atau "mengamankan" tanpa diminta.

**Contoh nyata.** `/connect` sudah terverifikasi. Untuk mencegah dugaan error primary key, logikanya sempat diubah menjadi upsert. Akibatnya sebuah invite code bisa memindahkan profil yang sudah ada ke chat ID lain — jalur pembajakan akun. Error primary key yang hendak dihindari itu justru proteksinya.

Kalau kamu melihat potensi masalah pada kode yang sudah berjalan, sampaikan sebagai pertanyaan, bukan sebagai perubahan.

## 3. Rencana dulu, kode belakangan

Untuk tugas apa pun yang menyentuh lebih dari satu file, laporkan rencananya dan tunggu persetujuan.

Rencana yang baik memuat: file apa yang berubah, apa yang berubah di masing-masing, dan keputusan desain yang masih terbuka. Rencana yang buruk hanya mengulang permintaan dengan kalimat berbeda.

## 4. Verifikasi arah sebelum menyeragamkan

Saat menemukan ketidakkonsistenan — dua nama berbeda untuk hal yang sama, dua pola untuk kebutuhan yang sama — **jangan menebak mana yang benar.**

Baca file yang benar-benar mengkonsumsinya. Kalau perlu, jalankan pengecekan.

Menyeragamkan ke arah yang salah lebih merusak daripada membiarkan tidak konsisten. Di project ini, menyeragamkan `GOOGLE_API_KEY` ke `GEMINI_API_KEY` akan mematikan agent sepenuhnya.

Jangan pula menyimpulkan dari gejala. Fakta bahwa sebuah nilai terbaca saat runtime tidak membuktikan nilai itu dideklarasikan di `Settings` — `extra = "ignore"` membuat variabel tak terdeklarasi lolos diam-diam.

## 5. Jangan tampilkan nilai secret

Jangan pernah mencetak isi `.env`, token, API key, atau connection string ke output — termasuk saat melaporkan hasil audit, termasuk saat debugging.

Kalau perlu memastikan sebuah nilai ada, cetak keberadaannya atau panjangnya:

```python
hasattr(settings, 'GOOGLE_API_KEY')
len(settings.GOOGLE_API_KEY)
```

Kalau perlu membandingkan dua nilai, bandingkan hash-nya:

```bash
python -c "import hashlib,sys; s=sys.argv[1]; print(len(s), hashlib.sha256(s.encode()).hexdigest()[:12])" "$VAR"
```

Bot token project ini pernah terekspos lewat output terminal yang tersalin. Aturan ini bukan formalitas.

## 6. Diagnosis sebelum solusi

Kalau penyebab sebuah masalah belum pasti, jangan langsung mengusulkan perbaikan. Usulkan cara mengeceknya lebih dulu.

Perbaikan atas dugaan yang salah akan menambah perubahan yang tidak perlu, dan menutupi penyebab sebenarnya.

**Cek ini sebelum menduga ada bug di kode:** apakah uvicorn sudah di-restart? `--reload` hanya memantau file `.py`, bukan `.env`. Tiga bug yang tampak berbeda di project ini semuanya berakar pada server yang masih memuat konfigurasi lama.

## 7. Satu perubahan, satu langkah

Kalau sebuah tugas punya beberapa bagian, kerjakan berurutan dan laporkan tiap bagian. Jangan mengerjakan semuanya sekaligus lalu menyerahkan hasil akhir.

Alasannya: kalau lima hal diubah bersamaan dan hasilnya salah, tidak ada cara tahu mana yang bermasalah.

Ini juga berlaku saat memasang instrumentasi debug. Pasang satu, jalankan, lihat hasilnya, baru tentukan langkah berikutnya.

## 8. Bertanya lebih murah daripada berasumsi

Kalau ada yang ambigu, tanya. Jangan pilih tafsiran yang paling mungkin lalu lanjut.

Khususnya untuk hal-hal berikut, selalu tanya:
- Keputusan yang punya konsekuensi keamanan
- Keputusan yang sulit dibatalkan nanti (skema database, identitas pengguna)
- Apa pun yang menghapus atau menulis ulang data
- Apa pun yang mengubah perilaku yang sudah terverifikasi berjalan

## 9. Perintah terminal

Sebelum mengusulkan perintah, pastikan:

- **Tidak ada placeholder yang harus diganti manual.** Jangan tulis `<TOKEN>` atau `<PID>` di perintah yang akan dijalankan — itu pernah diketik apa adanya. Kalau butuh nilai spesifik, minta set variabel dulu, lalu gunakan `$VAR`.
- **Satu perintah per langkah** kalau outputnya dibutuhkan untuk langkah berikutnya.
- **Perintah destruktif diberi peringatan eksplisit** — `rm`, `git reset --hard`, `DROP`, `DELETE`, `taskkill`. Sebutkan apa yang akan hilang.

Environment: Windows 11, Git Bash (MINGW64), venv di `apps/backend/venv`.

Terminalmu **tidak mewarisi venv**. Untuk menjalankan Python, sebut interpreternya secara eksplisit:

```
venv/Scripts/python.exe -c "..."
```

Jangan pakai `python` polos — itu menunjuk ke Python sistem yang tidak punya dependensi project.

Jangan menjalankan `uvicorn --reload`. Itu proses foreground yang akan menggantung terminalmu. Minta saya yang menjalankannya.

## 10. Jangan minta menjalankan file yang isinya tidak terlihat

Kalau kamu membuat skrip di folder scratch lalu memintanya dijalankan, tampilkan isinya lebih dulu. Dialog izin hanya menampilkan path, bukan isi file, sehingga saya tidak bisa menilai apa yang akan dieksekusi.

Untuk pemeriksaan sederhana, lebih baik pakai kode inline, atau berikan SQL-nya agar saya jalankan sendiri di Supabase SQL Editor.

## 11. Hormati keputusan yang sudah diambil

Daftar keputusan mengikat ada di `project-rules.md`. Jangan usulkan membatalkannya kecuali ada informasi baru yang benar-benar mengubah perhitungan.

Boleh menyampaikan trade-off yang terlewat. Tidak boleh mengusulkan jalur yang sudah ditolak seolah pertimbangannya belum pernah terjadi.

## 12. Gaya komunikasi

Bahasa Indonesia santai, istilah teknis tetap bahasa Inggris.

Jelaskan mekanismenya, bukan cuma perintahnya. Ini project belajar — memahami kenapa sesuatu bekerja lebih berharga daripada menyelesaikan tugasnya dengan cepat.

Kalau kamu tidak yakin, katakan tidak yakin. Jangan menyamarkan tebakan sebagai kesimpulan.

Kalau kamu membuat kesalahan, akui langsung dan jelaskan penyebabnya. Jangan membungkusnya dengan pembelaan panjang.
