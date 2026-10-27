# ADR-004: Pemisahan (Decoupling) Tahap Pengindeksan Klaster RAPTOR dari Penelusuran Real-Time (Tree Traversal)

## Status
**Accepted / Implemented in Production (Phase 2)**

## Konteks & Masalah
Algoritma RAPTOR (*Recursive Abstractive Processing for Tree-Organized Retrieval*) mengelompokkan dokumen menggunakan model campuran Gaussian (*Gaussian Mixture Models* / GMM) dan merangkum tiap klaster menjadi simpul hierarkis.
Namun, menjalankan pengelompokan GMM dan peringkasan teks LLM secara *on-the-fly* pada saat kueri pengguna masuk (query-time) memakan waktu 15–30 detik dan membakar ribuan token API.

## Keputusan Arsitektur
Kami memisahkan (*decoupling*) siklus hidup RAPTOR menjadi dua tahapan independen:
1. **Asynchronous Ingestion & Tree Construction (Background / Offline):**
   * Pengelompokan semantik GMM dan pembangkitan ringkasan abstrak tingkat tinggi dijalankan secara berkala di latar belakang atau saat batch dokumen baru ditambahkan.
   * Struktur pohon klaster disimpan dalam metadata JSON terindeks pada tabel PostgreSQL.
2. **Deterministic Hierarchical Traversal (Online Retrieval $< 20\text{ms}$):**
   * Saat kueri masuk, sistem melakukan penelusuran pohon hierarkis:
     $$\text{Root Node} \longrightarrow \text{Macro Cluster Node (Top-Level Context)} \longrightarrow \text{Micro Leaf Chunk (Fine-Grained Context)}$$
   * Penelusuran pohon ini dieksekusi secara instan menggunakan pencarian vektor terarah tanpa memicu kalkulasi ulang GMM.

## Konsekuensi & Evaluasi
* **Latensi Kueri Terjaga:** Penelusuran hierarkis pohon pengetahuan selesai dalam waktu **$< 20\text{ms}$**.
* **Makro vs Mikro Konteks:** Memungkinkan agen menjawab pertanyaan abstrak tingkat tinggi (*"Apa peta jalan riset tesis ini?"*) sekaligus pertanyaan detail teknis (*"Berapa learning rate model CatBoost?"*) dengan presisi tinggi.
