# Second Brain: Autonomous AI Productivity Agent 🎓

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203-4FC08D.svg)](https://vuejs.org)
[![Vite](https://img.shields.io/badge/Bundler-Vite-646CFF.svg)](https://vitejs.dev)
[![Supabase](https://img.shields.io/badge/Backend-Supabase%20Postgres%20%2B%20RLS-3ECF8E.svg)](https://supabase.com)
[![Notifications](https://img.shields.io/badge/Alerts-Web%20Push%20%26%20In--App%20Center-FF6F00.svg)](apps/dashboard)
[![Quick Capture](https://img.shields.io/badge/Input-Ctrl%2BK%20%26%20Voice%20Dictation-8B5CF6.svg)](apps/dashboard)
[![Simulator](https://img.shields.io/badge/Academic-Grade%20%26%20GPA%20Simulator-3B82F6.svg)](apps/dashboard)
[![Anti Ghosting](https://img.shields.io/badge/Thesis-Anti--Ghosting%20Dospem-EC4899.svg)](apps/dashboard)
[![Pomodoro Focus](https://img.shields.io/badge/Focus-Pomodoro%20%26%20Deep%20Work-E11D48.svg)](apps/dashboard)
[![Guide](https://img.shields.io/badge/Guide-In--App%20Handbook-6366F1.svg)](apps/dashboard)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Zero%20Tracking-10B981.svg)](apps/dashboard)
[![Mobile First](https://img.shields.io/badge/Design-Mobile--First%20PWA-indigo.svg)](apps/dashboard)
[![Zero Cost](https://img.shields.io/badge/Deploy-100%25%20Free%20Tier-success.svg)](netlify.toml)
[![AI Architecture](https://img.shields.io/badge/AI%20Engine-Gemini%20ADK%20%2B%20pgvector%20RAG-7928CA.svg)](apps/backend)
[![Go Telemetry](https://img.shields.io/badge/Concurrency-Golang%20Worker%20Engine-00ADD8.svg)](apps/telemetry-worker-go)
[![AI Evaluation](https://img.shields.io/badge/Evaluation-Quality%20Flywheel%20%E2%89%A590%25-10B981.svg)](apps/backend/tests)

> **Personalized Life & Academic Operating System (Master's Thesis Research)**  
> *"Lulus Skripsi & Kuliah Sukses, Tetap Sehat, dan Me-Time Tanpa Rasa Bersalah."*

**Second Brain: Autonomous AI Productivity Agent** adalah platform manajemen hidup dan produktivitas mandiri (*Autonomous Life & Study Balance Hub*) berbasis web **Mobile-First** yang dirancang khusus untuk memecahkan beban mental mahasiswa: tugas menumpuk, skripsi macet, pola tidur rusak, dan *burnout*. 

Kini hadir sepenuhnya **End-to-End Standalone di Web Dashboard**, lengkap dengan **Tanya AI & Semantic Search (pgvector + RAG)**, **Concurrent Go Telemetry Engine**, **Simulator Target Nilai & IPK Semester**, **Tab Panduan Penggunaan Interaktif**, **Universal Quick Capture Bar (`Ctrl + K` / Suara)**, **Pusat Notifikasi Cerdas (In-App Notification Center)**, dan **Browser Web Push Notification** tanpa memerlukan bot pihak ketiga.

🌐 **Akses Aplikasi (Gratis):**  
👉 **[https://second-brain-agent.netlify.app/](https://second-brain-agent.netlify.app/)**

---

## 🧭 4 Pilar Kehidupan Mahasiswa

Second Brain mengatur ritme hidup mahasiswa dengan prinsip prioritas deterministik teruji:

| No | Pilar | Prioritas | Fitur Unggulan Sistem |
|:---:|:---|:---:|:---|
| **#1** | **🩺 Kesehatan & Vitalitas** | Paling Utama | Hidrasi 8 gelas/hari, pelacak durasi & kualitas tidur (*Sleep Debt*), jam malam (*Bedtime Guardian*), & radar risiko *burnout*. |
| **#2** | **🎓 Kuliah & Akademik** | Prioritas #2 | **Simulator Target Nilai Ujian & IPK Semester**, bobot nilai %, sortir tenggat waktu (*deadline*), *Tubes Milestone Tracker*, dan kisi-kisi UTS/UAS. |
| **#3** | **🔬 Riset & Skripsi** | Prioritas #3 | Pelacak progres Bab 1–5, *Anti-Ghosting Dospem Radar* (>14 hari), telemetri eksperimen CatBoost, & **1-klik ekspor tabel LaTeX IEEE/Overleaf**. |
| **#4** | **⚡ Agent Ops & Telemetry** | Prioritas #4 | Monitoring cluster worker Go (`:8085`), inferensi hybrid vector RAG pgvector (768-D), dan sinkronisasi Git commit hook/webhook 3 repo akademik. |

---

## ⚡ Mode Demo Instan & Recruiter Walkthrough Tour (60 Detik)

Untuk mempermudah Tech Lead, Engineering Manager, dan Recruiter menguji kapabilitas sistem tanpa proses registrasi:

* **⚡ 1-Click Instant Recruiter Preview:**
  * Tombol akses cepat di halaman login yang langsung memuat lingkungan simulasi dengan data akademik realistis Frans Alwan Purba (analisis metrik CatBoost, Tubes Machine Learning, hidrasi harian, dan ringkasan AI).
* **✨ Guided Tour Interaktif (60 Detik):**
  * Klik pill `✨ Demo (Tour 60s)` di navbar atas untuk membuka walkthrough interaktif 4 langkah:
    1. **Arsitektur Polyglot:** Hubungan antara FastAPI AI Engine dan Go Telemetry Worker.
    2. **Hybrid Vector RAG:** Implementasi pgvector 768-D dan Reciprocal Rank Fusion (RRF).
    3. **Academic Git Pipeline:** Integrasi otomatis commit Git lokal & GitHub Webhooks dari 3 repo.
    4. **Profil Rekayasa Frans Alwan Purba:** Informasi riset magister AI di UGM dan link kontak.

---

## 🎛️ Raycast-Style Command Palette (`Ctrl + K` / `Cmd + K`) & Omnibar

Pusat kendali navigasi dan pencarian semantik instan yang dapat diakses dari halaman mana pun:

* **Mode `>` (Sistem & Navigasi):** Ketik `>` untuk berpindah tab secara instan, membuka Tech Specs, atau menginspeksi kebijakan privasi data.
* **Mode `?` (Vector AI Search):** Ketik `? [pertanyaan]` untuk langsung melakukan pencarian semantik ke database pgvector (RAG) atas seluruh catatan kuliah dan eksperimen skripsi.
* **Natural Quick Capture:** Ketik langsung teks bebas (misal: `! deadline besok Tubes ML Bab 3`) untuk menyimpan tugas dengan ekstraksi regex otomatis.
* **Keyboard First Navigation:** Dukungan penuh navigasi panah atas/bawah (`↑` / `↓`), `Enter`, dan `Esc`.

---

## 🍱 Bento Grid 2.0 & Shimmer Skeleton Loading

Halaman utama (**Ringkasan**) mengadopsi standar desain asimetris **Bento Grid**:

* **Hero Briefing Card (8 Kolom):** Sapaan cerdas, status briefing akademik, dan sorotan tugas berstatus mendesak (*urgent*).
* **Cluster Telemetry Monitor (4 Kolom):** Indikator denyut real-time background worker Go, konektivitas pgvector, dan status sinkronisasi 3 repositori akademik.
* **Focus Session Bar:** Pengendali sesi *Deep Work* langsung dari grid utama dengan visual animasi detak fokus.
* **Filter Tugas Fleksibel:** Tombol filter instan termasuk filter khusus `🔥 Mendesak` untuk memprioritaskan pekerjaan krusial.

---

## 📖 Tab Panduan Penggunaan Mahasiswa (In-App Student Handbook)

Agar mahasiswa baru dapat langsung menguasai ritme aplikasi tanpa kebingungan, kini tersedia tab khusus **📖 Panduan**:

* **🌅 4 Langkah Alur Harian:** Panduan alur konkret dari briefing pagi (05:00), catat tugas kuliah siang, sesi riset sore, hingga cutoff malam (23:00).
* **🎯 Kupas Tuntas 4 Pilar:** Alasan ilmiah di balik urutan prioritas Kesehatan (#1) > Kuliah (#2) > Riset (#3) > Agent Ops (#4).
* **⚡ Cheat Sheet Interaktif:** Daftar sintaks Quick Capture dengan tombol **1-Klik Salin (Copy)** dan tombol **Langsung Coba Palette**.
* **❓ FAQ Mahasiswa:** Jawaban lengkap tentang keamanan cloud (Supabase RLS), cara install PWA di HP, dan tanpa biaya langganan.

---

## 🎯 Simulator Nilai Ujian & Target IPK Semester (Academic Simulator)

Menghapus kecemasan mahasiswa menjelang musim ujian akhir:

* **🎯 Target Skor Ujian (Komponen Silabus Dosen):**
  * Masukkan bobot komponen silabus dosen: Tugas (20%), Kuis/Lab (15%), UTS (30%), UAS (35%).
  * Masukkan nilai yang sudah didapat dan pilih target huruf mutu akhir (A / AB / B / BC / C).
  * Sistem menghitung secara otomatis nilai UAS minimal yang harus dicapai:
    > *"Kamu butuh nilai minimal **78.5 pada UAS** untuk mengamankan nilai **A (4.0)**."*
  * Jika target mustahil (> 100), sistem otomatis merekomendasikan target terbaik berikutnya.
* **📈 Simulator IPK Semester & Kumulatif:**
  * Input SKS per mata kuliah dan target nilai huruf (A, AB, B, BC, C, D, E).
  * Menghitung proyeksi **IPS (Indeks Prestasi Semester)** dan proyeksi **IPK Kumulatif Baru** beserta indikator kenaikan/penurunan (contoh: `+0.08` 🔺) dan status predikat (*Cum Laude / Sangat Memuaskan*).
  * Tersimpan otomatis per akun secara lokal (*localStorage persistent*).

---

## 🍅 Focus Pomodoro Hub & Stasiun Pemulihan Energi Mahasiswa

Beban belajar mahasiswa menuntut ritme kerja terstruktur tanpa memicu kelelahan mental (*brain fog*):

* **Live Navbar Timer Pill (`🍅 25:00`):**
  * Terpasang langsung di bilah navigasi atas dashboard. Timer tetap berdetak dan berkedip aktif (*pulse animation*) saat mahasiswa berpindah-pindah antar tab (*Coursework, Research, Health, Agent Ops*).
* **Multi-Preset Durasi Deep Work:**
  * **🍅 25m (Standar Pomodoro):** Pilihan optimal untuk kuis, latihan soal, atau membaca materi kuliah.
  * **🎯 45m (Deep Work):** Sesi mendalam untuk modul koding, analisis data, atau pengerjaan tugas besar (*tubes*).
  * **📖 50m (Penulisan Skripsi):** Sesi intensif untuk menyusun draf bab naskah tugas akhir.
  * **☕ 5m (Short Break):** Jeda rileksasi mata dan peregangan leher/bahu.
  * **🌿 15m (Long Break):** Istirahat panjang setiap menyelesaikan 4 siklus fokus.
* **Auto-Chime & Browser Push:**
  * Lonceng lembut sintetis berbunyi instan via Web Audio API saat timer usai, disertai pesan notifikasi resmi browser.
* **Target Fokus & Rekap Sesi Harian:**
  * Kolom catatan fokus: *"Sedang fokus pada: [Tugas/Bab]"*.
  * Pelacak akumulasi harian: *"🔥 4 Sesi (100 Menit Fokus) hari ini"*.
* **Status Pemulihan Mental Interaktif (Health Tab):**
  * Tombol 1-klik untuk memilih kondisi fisik/mental hari ini: **🟢 Prima (20)**, **🟡 Lelah (50)**, **🟠 Overload/Ngebul (75)**, atau **🔴 Drop/Zombie Mode (95)** yang tersimpan ke cloud Supabase realtime.

---

## ⚡ Universal Quick Capture & Voice Input (`Ctrl + K` & FAB `+`)

Mencatat tugas kuliah atau ide riset kini tidak perlu lagi mengisi form panjang yang melelahkan:

* **Akses Cepat 1 Detik:**
  * **Di Laptop:** Tekan shortcut keyboard **`Ctrl + K`** (atau `Cmd + K` di Mac).
  * **Di Smartphone / HP:** Tap tombol bulat **`+`** (FAB) melayang di pojok kanan bawah layar.
* **Smart Client-Side Regex Parser:** Ketik bebas satu baris, sistem otomatis mengenali kategori & tenggat waktunya:
  * 🎓 `tugas kuis kalkulus besok mendesak` ➔ Otomatis masuk jadi **Tugas Kuliah** dengan deadline besok & badge *Urgent*.
  * 💧 `minum 300ml` (atau `minum 2 gelas`) ➔ Otomatis menambah log hidrasi **Kesehatan**.
  * 😴 `tidur 7.5 jam` ➔ Otomatis tercatat di log tidur.
  * ⏱️ `fokus: riset paper IEEE` ➔ Otomatis menyalakan timer sesi fokus deep work.
  * 💡 `ide: arsitektur state management` ➔ Otomatis jadi catatan baru & simpul baru di **Knowledge Graph**.
* **Dikte Suara (Voice to Text 🎤):** Cukup klik tombol mic dan bicara dalam Bahasa Indonesia menggunakan *Web Speech Recognition* bawaan browser (100% gratis, tanpa kuota AI server).
* **Template Cepat:** Tombol chip 1-klik untuk input instan (`+ Tugas Kuliah`, `+ Minum 250ml`, `+ Tidur 7.5 Jam`, `+ Mulai Timer`).

---

## 🔔 In-App Notification Center & Web Push Engine

Tidak perlu lagi bergantung pada aplikasi chat eksternal. Semua pengingat dan briefing penting dikelola langsung dari dalam dashboard:

* **Lonceng Notifikasi di Navbar:** Dilengkapi *Badge Counter* merah yang berdenyut aktif jika ada tugas mendesak (*urgent*).
* **Notification Drawer Interaktif:**
  * ☀️ **Morning Briefing:** Rangkuman otomatis tugas pending dan target fokus setiap pagi (05.00–12.00).
  * 🌙 **Night Wind-Down:** Peringatan ramah saat kamu masih membuka tugas melewati jam tidur malam (`23:00`).
  * 🚨 **Alert Deadline:** Peringatan tugas yang jatuh tempo hari ini atau H-2 dengan tombol aksi langsung.
  * 🧘 **Habit Reminder:** Peringatan kebiasaan aktif yang belum dicentang hari ini.
  * ⏱️ **Active Focus Session:** Indikator waktu deep work yang sedang berjalan.
* **Browser Push Notification (PWA):** Cukup klik *"Aktifkan 🔔"*, dan perangkatmu (HP & Laptop) akan memunculkan pop-up notifikasi resmi bahkan saat tab browser sedang diminimalkan.
* **Gentle Sound Chime (Web Audio API):** Efek suara sintetis lembut bawaan browser tanpa perlu aset audio eksternal.

---

## ⚡ Kontrol Interaktif End-to-End di Web

Seluruh pengelolaan dapat diselesaikan langsung dalam genggaman:

* **Daily Briefing Card Adaptif:** Menyapa ramah di beranda, menyajikan 4 metrik kilat (Pending, Selesai, Waktu Fokus, Habit), dan kartu tugas genting yang bisa diceklis langsung.
* **Centang Tugas Instan:** Tombol ceklis `[✓]` di samping setiap tugas pada daftar.
* **Timer Fokus Terintegrasi:** Masukkan nama proyek di Riwayat Fokus, tekan `▶️ Mulai`, dan akhiri dengan tombol `⏹️ Selesai Sesi Fokus` kapan saja.
* **Checklist Kebiasaan 1-Tap:** Ketuk kartu habit untuk langsung mencatat pencapaian harian dan menghitung streak berturut-turut.
* **Interactive Knowledge Graph:** Graf simpul catatan ide dan koneksi riset yang dapat digeser dan ditata langsung via layar sentuh (*touch gestures*).

---

## 💬 Curhat & Feedback Mahasiswa Terintegrasi

Dashboard dilengkapi saluran masukan langsung agar mahasiswa bisa memberikan feedback, lapor kendala, atau request fitur baru:

* **Tombol Melayang:** `💬 Curhat / Request Fitur` di pojok kiri bawah dashboard.
* **Modal Penilaian Instan:** Pilih kategori (*Request Fitur*, *Lapor Bug*, *Review*), beri rating 1–5 ⭐, dan tuliskan pesan yang langsung tersimpan di database.
* **Script Generator Google Form:** Disediakan script otomatis Google Apps Script di [`scripts/google_form_creator.js`](scripts/google_form_creator.js) untuk menghasilkan form kuesioner evaluasi 9 pertanyaan dalam 1 klik via [script.new](https://script.new).

---

## 📱 Mobile-First Design (Thumb Zone)

Dashboard web didesain dengan filosofi **True Mobile-First**:

* **Bottom Floating Navigation Bar:** Navigasi 4 pilar di bawah layar ramah jempol (*Thumb Zone*), mempermudah navigasi satu tangan di smartphone.
* **Touch Target Nyaman (44px+):** Seluruh tombol dan form dirancang empuk dan bebas dari gangguan auto-zoom pada browser smartphone.
* **Zero-Friction Student Onboarding:** Mahasiswa dapat mendaftar langsung menggunakan email kampus atau pribadi dengan verifikasi otomatis instan.

---

## 📲 Progressive Web App (PWA) & Pasang di Layar Utama HP

Aplikasi ini dapat dipasang (*install*) layaknya aplikasi *native* langsung ke layar utama smartphone (Android & iOS) tanpa perlu mengunduh dari toko aplikasi:

* **Android (Chrome / Edge):** Banner otomatis akan muncul ("📲 Pasang di Layar Utama HP"). Cukup tap **"Pasang Aplikasi"**, dan ikon Second Brain akan langsung berada di home screen dan app drawer HP kamu.
* **iOS / iPhone / iPad (Safari):** Tap ikon **Share (Bagikan)** di bilah bawah Safari, lalu pilih **"Add to Home Screen" (Tambahkan ke Layar Utama)**. Panduan interaktif visual tersedia langsung di dalam aplikasi.
* **Standalone Experience:** Berjalan dalam layar penuh (*full screen*) tanpa bilah URL browser, memberikan *feel* aplikasi native yang responsif dan fokus.
* **Offline-Ready Caching (`sw.js`):** Asset inti aplikasi (*app shell*) di-cache secara otomatis via Service Worker untuk pemuatan halaman secepat kilat (*instant loading*) bahkan saat jaringan internet kampus sedang lambat.

---

## 🏗️ Arsitektur 100% Free Tier ($0 / Bulan)

Aplikasi berjalan sepenuhnya tanpa biaya server cloud:

```mermaid
flowchart TD
    subgraph Client ["Pengguna (Smartphone & Laptop)"]
        UI["Vue 3 SPA Dashboard<br/>(PWA Mobile-First)"]
        QC["Universal Quick Capture<br/>(Ctrl+K + Web Speech API)"]
        NOTIF["In-App Notification Hub<br/>+ Web Push API"]
        GRAPH["Interactive Knowledge Graph<br/>(Canvas Touch-Ready)"]
    end

    subgraph Cloud ["100% Free Cloud Infrastructure"]
        NETLIFY["Netlify Free Hosting<br/>(SSL + Global CDN)"]
        SUPABASE[("Supabase Cloud Free Tier<br/>PostgreSQL + Auth + Row Level Security")]
    end

    NETLIFY -->|Serve Static SPA| UI
    UI <-->|Auth, RLS Query & Realtime Data| SUPABASE
    UI --> QC
    UI --> NOTIF
    UI --> GRAPH
```

1. **Frontend Dashboard di Netlify (100% Free):** Hosting statis SPA yang terhubung langsung ke Supabase client-side. Live 24/7 di `https://second-brain-agent.netlify.app`.
2. **Database & Auth di Supabase (100% Free):** PostgreSQL cloud dengan proteksi data ketat via *Row Level Security* (RLS).
3. **Optional Backend (FastAPI / Bot Daemon):** Tersedia di folder `apps/backend` bagi pengguna tingkat lanjut yang ingin mengaktifkan sinkronisasi bot Telegram headless di komputer lokal.

---

## 🚀 Panduan Memulai Cepat

### 1. Buka Web Dashboard
Kunjungi dashboard resmi di:
👉 **[https://second-brain-agent.netlify.app/](https://second-brain-agent.netlify.app/)**

### 2. Buat Akun Mahasiswa
1. Di tab **Daftar Baru (Sign Up)**, isi Nama Lengkap, Email Kampus/Pribadi, dan Password.
2. Klik **Buat Akun Mahasiswa Baru** — akun langsung aktif dan otomatis masuk ke dashboard.

### 3. Aktifkan Notifikasi & Quick Capture
1. Klik ikon lonceng **🔔** di kanan atas navbar ➔ klik **Aktifkan 🔔** untuk mengizinkan Web Push.
2. Tekan **`Ctrl + K`** (atau tombol **`+`** di HP) untuk langsung mencoba mencatat tugas pertamamu!

---

## 💻 Menjalankan di Komputer Lokal

Jika ingin mengembangkan dashboard secara lokal:

```bash
# 1. Clone repository
git clone https://github.com/fransalwan/second-brain-agent.git
cd second-brain-agent/apps/dashboard

# 2. Pasang dependensi
npm install

# 3. Jalankan server lokal
npm run dev
```
Buka browser di `http://localhost:5173`.

---

## 🔬 Modul Riset & Skripsi: Anti-Ghosting Dospem Radar & LaTeX Ready

Di tab **🔬 Riset**, mahasiswa mendapatkan suite lengkap pendampingan tugas akhir/skripsi:

### 1. Radar Anti-Ghosting & Generator WhatsApp Dospem Santun
Menghilangkan kecemasan dan *social anxiety* mahasiswa saat harus menghubungi dosen pembimbing yang sibuk:
* **Indikator Radar Telemetri:**
  * 🟢 **Konsisten:** Bimbingan terakhir $\le 7$ hari lalu.
  * 🟡 **Waktunya Hubungi Dosen:** Bimbingan $8 - 14$ hari lalu.
  * 🔴 **Peringatan Anti-Ghosting:** $> 14$ hari tanpa bimbingan (banner merah peringatan muncul otomatis agar skripsi tidak mandek).
* **Generator Chat WhatsApp Formal 1-Klik:**
  * Pilihan 4 skenario template etika akademik:
    1. **Minta Jadwal Bimbingan Lanjutan:** Permohonan waktu temu sopan yang fleksibel mengikuti kesibukan dosen.
    2. **Kirim Draft Bab & Catatan Revisi:** Konfirmasi pengiriman file naskah baru ke email/Google Drive dosen.
    3. **Follow-Up Santun (Anti-Ghosting):** Pengingat ramah dan diplomatis apabila dosen belum sempat membalas pesan terdahulu.
    4. **Permohonan Persetujuan ACC / Sempro:** Pengajuan kelayakan naskah akhir menjelang batas pendaftaran seminar proposal/sidang.
  * Dilengkapi tombol **Salin Teks** dan **Buka WhatsApp Langsung (`wa.me`)** tanpa perlu mengarang kata dari nol. Profil dospem tersimpan secara privat di browser lokal (*localStorage*).

### 2. Pelacak Progres 5 Bab Skripsi & Action Items Revisi
* Slider persentase mandiri untuk Bab 1 (Pendahuluan) hingga Bab 5 (Kesimpulan).
* Checklist interaktif *Action Items* per sesi bimbingan yang tersimpan ke cloud Supabase secara realtime.

### 3. Generator Tabel Komparasi IEEE LaTeX & Markdown
Klik tombol **"LaTeX"**, dan sistem otomatis menghasilkan kode tabel standar IEEE yang siap di-paste langsung ke naskah Overleaf kamu:

```latex
% Generated by Second Brain: Autonomous AI Productivity Agent
\begin{table}[htbp]
\centering
\caption{Ringkasan Eksperimen dan Evaluasi Model}
\label{tab:thesis_experiments}
\begin{tabular}{|l|c|r|}
\hline
\textbf{Model / Arsitektur} & \textbf{Parameter} & \textbf{Metrik Hasil} \\
\hline
Boosted Tree (IDCS Rate 0.15) & Runs: 5 iter & SRA: 0.7201, FDR: p<0.05 \\
ResNet-18 Benchmark & Batch: 64 & Akurasi: 88.2\% \\
\hline
\end{tabular}
\end{table}
```

---

## 🐙 Integrasi GitHub Repositori Akademik (Kuliah & Riset)

Second Brain terintegrasi secara dua arah dengan ekosistem GitHub mahasiswa — baik saat bekerja di komputer lokal (*Git post-commit hook*) maupun saat push ke GitHub (*GitHub Webhooks*):

### 1. Repositori Terintegrasi
* 🎓 **[materi-kuliah](https://github.com/fransalwan/materi-kuliah):** Setiap commit yang mencantumkan tugas atau mata kuliah otomatis menandai tugas (`CourseAssignment`) sebagai selesai dan mencatat habit belajar harian.
* 📝 **[thesis-manuscripts](https://github.com/fransalwan/thesis-manuscripts):** Setiap commit naskah (misal: `feat(bab 3): metodologi progres 80%`) otomatis memperbarui progres Bab 1–5 skripsi. Jika commit mencatat arahan pembimbing (`bimbingan`, `dospem`), sistem otomatis mencatat notulensi ke log riset.
* 🧪 **[thesis-experiments](https://github.com/fransalwan/thesis-experiments):** Setiap commit evaluasi model AI (misal: `eval XGBoost: acc=94.5% f1=93.8% loss=0.12 epoch=100`) otomatis mengekstrak metrik evaluasi & hyperparameter ke database untuk siap diekspor ke tabel LaTeX Bab 4.

### 2. Pemasangan Git Hook Lokal (1-Klik)
Jalankan perintah ini di terminal laptop:
```bash
python apps/desktop-agent/install_git_hook.py --academic
```
Hook akan otomatis terpasang di `.git/hooks/post-commit`. Setiap kali Anda menjalankan `git commit` di terminal, Second Brain akan memberikan konfirmasi langsung tanpa mengganggu alur kerja git.

### 3. Pemasangan GitHub Webhooks (Cloud)
Untuk integrasi otomatis saat melakukan push ke GitHub:
1. Masuk ke tab **Settings ➔ Webhooks ➔ Add webhook** di repository GitHub Anda.
2. Masukkan Payload URL: `https://<backend-domain>/api/v1/github/webhook`
3. Content type: `application/json`
4. Trigger events: `Just the push event`
5. Klik **Add webhook**.

---

## 🧠 Arsitektur AI & RAG Knowledge Hub (pgvector + Reciprocal Rank Fusion)

Untuk mendukung riset dan pencarian cerdas catatan akademik mahasiswa tingkat magister, Second Brain dilengkapi sistem **Retrieval-Augmented Generation (RAG)** hibrida:

* **PostgreSQL + pgvector (768-D Embeddings):** Menggunakan representasi vektor `text-embedding-004` dengan indeks **HNSW (Hierarchical Navigable Small World)** untuk pencarian kosinus berkecepatan sub-milidetik.
* **Hybrid Search (Reciprocal Rank Fusion - RRF):** Menggabungkan keunggulan pencarian kata kunci eksak (*Full-Text Keyword Search*) dan kedekatan makna (*Vector Cosine Similarity*) dengan formula:
  $$\text{RRF}(d) = \frac{w_{\text{kw}}}{60 + \text{rank}_{\text{kw}}(d)} + \frac{w_{\text{vec}}}{60 + \text{rank}_{\text{vec}}(d)}$$
* **Grounded Academic Q&A:** Fitur **Tanya AI (RAG)** di dashboard menyajikan jawaban berbasis sitasi catatan nyata mahasiswa tanpa risiko halusinasi.

---

## ⚡ High-Concurrency Background Telemetry Worker (Golang Engine)

Memadukan kekuatan ekosistem **Python (AI Agent)** dan **Golang (Sistem Konkurensi Tinggi)**:

* **Arsitektur Polyglot:** Layanan background worker mandiri di [`apps/telemetry-worker-go`](apps/telemetry-worker-go) dibangun dengan **Go 1.22+**.
* **Worker Pool & Goroutines:** Memproses evaluasi telemetri mahasiswa (peringatan jam malam, deteksi sleep debt 7 hari, peringatan tugas <24 jam, dan *anti-ghosting dospem*) secara non-blocking melalui antrean channel.
* **Exponential Backoff Resilience:** Mengirim notifikasi dengan mekanisme retry eksponensial otomatis untuk kehandalan pengiriman alert.
* **Observabilitas & Metrik:** Menyediakan endpoint `/health` dan `/metrics` untuk pemantauan throughput evaluasi dan penggunaan memori.

---

## 🧪 Quality Flywheel: Automated LLM Evaluation Suite

Memastikan reliabilitas agen sesuai standar industri dan metodologi *Quality Flywheel*:

* **Intent Classification Accuracy ($\ge 90\%$):** Dataset evaluasi 12 skenario menguji ketepatan triase kebutuhan mahasiswa (Akademik, Riset, Kesehatan, Recharge).
* **Latency Benchmark Sub-50ms (P95):** Menjamin waktu inferensi embedding dan parsing lokal berada di bawah ambang batas responsivitas cepat.
* **Semantic Separation Verification:** Memvalidasi kemampuan ruang embedding dalam memisahkan topik lintas domain secara matematis ($\text{sim}_{\text{domain}} > \text{sim}_{\text{cross}}$).

---

## 📄 Lisensi & Kontribusi

Project ini berlisensi **MIT**. Terbuka untuk kontribusi komunitas di seluruh Indonesia.

*Dibuat dengan ❤️ untuk produktivitas & kesehatan mental mahasiswa.*