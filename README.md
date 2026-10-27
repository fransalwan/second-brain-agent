# Second Brain: Autonomous AI Engineering Platform 🧠

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203%20%2B%20Vite-4FC08D.svg)](apps/dashboard)
[![Model Context Protocol](https://img.shields.io/badge/Protocol-Anthropic%20MCP%20Server%20(SSE)-FF5722.svg)](apps/backend)
[![Next-Gen RAG](https://img.shields.io/badge/RAG-CRAG%20%2B%20RAPTOR%20Knowledge%20Tree-3B82F6.svg)](apps/backend)
[![Multimodal VLM](https://img.shields.io/badge/Vision%20AI-Gemini%202.0%20Flash%20VLM-10B981.svg)](apps/backend)
[![Classical ML](https://img.shields.io/badge/Classical%20ML-Isolation%20Forest%20%3C2ms-EC4899.svg)](apps/backend)
[![Go Telemetry](https://img.shields.io/badge/Concurrency-Golang%201.22%20Worker%20(:8085)-00ADD8.svg)](apps/telemetry-worker-go)
[![Vector DB](https://img.shields.io/badge/Database-PostgreSQL%20pgvector%20(768--D%20HNSW)-3ECF8E.svg)](https://supabase.com)
[![AI Evaluation](https://img.shields.io/badge/CI%2FCD%20Evals-Composite%20Index%2081.8%2F100-10B981.svg)](apps/backend/evals)
[![Unit Tests](https://img.shields.io/badge/Unit%20Tests-117%2F117%20Passed%20(100%25)-success.svg)](apps/backend/tests)
[![PWA](https://img.shields.io/badge/PWA-Mobile--First%20Offline%20Ready-6366F1.svg)](apps/dashboard)

> **Autonomous AI Engineering Operating System & Distributed Multi-Agent Platform**  
> *Engineered by **Frans Alwan Purba** · Master of Computer Science in AI Candidate, Universitas Gadjah Mada.*

**Second Brain** adalah platform orkestrasi agen AI produksi berkinerja tinggi yang dirancang untuk mengatasi beban kognitif mahasiswa magister dan software engineer. Sistem ini menggabungkan protokol industri terbuka (**Anthropic Model Context Protocol SSE**), **Corrective RAG (CRAG)** dengan pengelompokan hirarkis **RAPTOR (GMM)**, Computer Vision (**Gemini 2.0 Flash VLM**), deteksi anomali **Classical Machine Learning (< 2ms)**, serta background telemetry berkonkurensi tinggi (**Golang 1.22**).

🌐 **Live Demo Aplikasi (Gratis & Zero Setup):**  
👉 **[https://second-brain-agent.netlify.app/](https://second-brain-agent.netlify.app/)**

---

## 🏗️ Arsitektur Target Sistem

```mermaid
flowchart TD
    subgraph Client & Protocol Layer
        UI["Web Dashboard (Vue 3 / PWA)"]
        ExtClient["External Clients (Claude Desktop / Cursor IDE)"]
        MCPServer["Second Brain MCP Server (FastAPI / SSE :8000/mcp/sse)"]
        UI -->|REST / SSE| MCPServer
        ExtClient -->|JSON-RPC 2.0 / stdio / SSE| MCPServer
    end

    subgraph Agentic Orchestration Layer
        ADKAgent["Google ADK Orchestrator"]
        MCPServer --> ADKAgent
        CRAG["Corrective RAG Controller"]
        ADKAgent --> CRAG
    end

    subgraph Intelligence & Processing Engines
        RAPTOR["Clustering & Hierarchical Summarizer (RAPTOR GMM)"]
        VLM["Multimodal Document AI (Gemini 2.0 Flash VLM)"]
        ClassicalML["Anomaly Radar (Isolation Forest <2ms)"]
        Reranker["Cross-Encoder Reranker (Cosine + Lexical + Overlap)"]
    end

    subgraph Storage & Telemetry
        PG["PostgreSQL + pgvector (768-D HNSW + RLS)"]
        Telemetry["Go Telemetry Engine (:8085 Goroutines Pool)"]
        EvalSuite["CI/CD Evaluation Suite (LLM-as-a-Judge Quality Flywheel)"]
    end

    CRAG --> RAPTOR
    CRAG --> Reranker
    Reranker --> PG
    ADKAgent --> VLM
    ADKAgent --> ClassicalML
    ClassicalML --> Telemetry
    EvalSuite -.->|Continuous Audit Gate| ADKAgent
```

---

## 🚀 5 Pilar Utama AI Engineering (Core Systems)

### 🔹 1. Standardisasi Model Context Protocol (Anthropic MCP SSE)
* **Konektivitas Terbuka**: Server FastAPI mengekspos endpoint transport SSE standar di `/mcp/sse` dan `/mcp/messages/`, serta kompatibilitas mode `stdio` (`mcp_client_config.json`).
* **8 Skema Tool JSON-RPC 2.0**:
  1. `save_note`: Menyimpan catatan & membuat embedding vektor 768-D.
  2. `search_notes`: Pencarian semantik hybrid pgvector (HNSW) + BM25 RRF.
  3. `get_thesis_progress`: Mengambil status milestone Bab 1–5 skripsi.
  4. `log_habit`: Mencatat penyelesaian kebiasaan sirkadian.
  5. `record_focus_session`: Mencatat durasi deep work ke database.
  6. `evaluate_burnout_radar`: Menjalankan evaluasi Isolation Forest (< 2ms).
  7. `upload_visual_document`: Menganalisis artefak visual via Gemini 2.0 VLM.
  8. `run_rag_qa`: Eksekusi pipeline Corrective RAG (CRAG) + RAPTOR tree.
* **ADK Dual Adapter**: Agen Google ADK internal dapat mengimpor dan mengekspor tools format MCP secara dwiarah.

### 🔹 2. Next-Gen RAG (RAPTOR Hierarchical Clustering + Corrective RAG)
* **RAPTOR Knowledge Tree**: Dokumen riset dikelompokkan secara semantik menggunakan **Gaussian Mixture Models (GMM)** dan KMeans pada vektor 768-D. Gemini merangkum tiap klaster menjadi simpul pohon bertingkat untuk *macro-level conceptual retrieval*.
* **Corrective RAG (CRAG) Self-Correction**:
  * 🟢 **CORRECT (> 0.70)**: Presisi tinggi, langsung diteruskan ke LLM generator.
  * 🟡 **AMBIGUOUS (0.35 - 0.70)**: Memicu ekspansi kueri **HyDE (Hypothetical Document Embeddings)** untuk melengkapi konteks yang kurang.
  * 🔴 **INCORRECT (< 0.35)**: Mengaktifkan guardrail *Out-of-Distribution* (OOD Refusal 100%), menolak halusinasi secara tegas.
* **Cross-Encoder Reranker**: Menghitung ulang relevansi Top-10 kandidat memadukan cosine distance (0.50), pencocokan kata leksikal BM25 (0.30), dan bigram overlap (0.20).

### 🔹 3. Multimodal Document Intelligence (Gemini 2.0 Flash VLM)
* **Endpoint Analisis Visual**: `POST /api/v1/notes/upload-visual` menerima file gambar (`PNG`, `JPEG`, `WebP`, `PDF`).
* **Ekstraksi Kurva Loss & Model Training**: Menganalisis kurva konvergensi fungsi loss CatBoost/LightGBM, mendeteksi titik konvergensi stabil (misal: Epoch 350 pada loss 0.118), dan memverifikasi ketiadaan overfitting.
* **OCR Tulisan Tangan & Formula LaTeX**: Mentranskripsikan catatan kuliah tulisan tangan menjadi teks bersih dan rumus matematika format LaTeX monospace yang siap disalin.
* **Auto-Vectorization**: Hasil analisis visual otomatis diindeks ke pgvector 768-D dalam waktu < 50ms.

### 🔹 4. Classical ML Hybrid: Circadian & Burnout Anomaly Radar
* **Ultra-Low Latency (< 2ms)**: Membuktikan kematangan arsitektur dengan menjalankan **Isolation Forest** unsupervised dari `scikit-learn` secara *in-memory* tanpa membakar token LLM pada pemantauan telemetri rutin.
* **Vektor Fitur 5-Dimensi**:
  1. `sleep_hours`: Rata-rata jam tidur harian.
  2. `sleep_debt_hours`: Akumulasi hutang tidur terhadap standar 8 jam.
  3. `midnight_sessions_count`: Frekuensi sesi koding/commit lewat jam 23:00.
  4. `overdue_tasks_ratio`: Rasio backlog tugas kuliah tertunda.
  5. `water_intake_liters`: Volume hidrasi harian.
* **Conditional LLM Intervention**: Token spend tetap 0 saat kondisi optimal. Agen LLM **hanya dipanggil** jika skor anomali $< -0.150$ untuk merumuskan intervensi pemulihan energi yang empatik dan kontekstual.

### 🔹 5. Production Evals & CI/CD Observability (Quality Flywheel)
* **Golden Dataset 20 Kasus Uji**: Meliputi 7 domain akademik terkurasi (AI research, thesis manuscript, circadian health, dan out-of-distribution refusal).
* **Automated LLM-as-a-Judge**: Pengujian otomatis via `apps/backend/evals/eval_runner.py` dan GitHub Actions (`.github/workflows/ai_eval.yml`).
* **Hasil Benchmark Ilmiah (RAG Triad)**:

| Metrik Evaluasi | Target Minimum | Hasil Benchmark | Status CI/CD |
| :--- | :---: | :---: | :---: |
| **Faithfulness (Groundedness / Anti-Halusinasi)** | `0.80` | **`0.850` (85.0%)** | 🟢 PASSED |
| **Context Recall (Presisi Vektor pgvector)** | `0.80` | **`0.860` (86.0%)** | 🟢 PASSED |
| **Answer Relevancy (Kesesuaian Jawaban)** | `0.75` | **`0.785` (78.5%)** | 🟢 PASSED |
| **Context Precision (Cross-Encoder Re-rank)** | `0.75` | **`0.782` (78.2%)** | 🟢 PASSED |
| **Out-of-Distribution Refusal (Guardrail)** | `0.90` | **`100.0%` (1.000)** | 🟢 PASSED |
| **Composite AI Quality Index** | `75.0` | **`81.8 / 100`** | 🏆 EXCELLENT |

---

## 🔬 Tesis S2 & Explainable AI Research Engine: Instance-Dependent Cost-Sensitive (IDCS)

Modul riset akademik yang diselaraskan langsung dengan proposal tesis S2 Magister Kecerdasan Artifisial FMIPA Universitas Gadjah Mada (2026/2027):

* **Peneliti:** Frans Alwan Purba (NIM: `25/563545/PPA/07116`)
* **Dosen Pembimbing:**
  * **Pembimbing I:** Afiahayati, S.Kom., M.Cs., Ph.D (NIP. 197904262005012001)
  * **Pembimbing II:** Prof. Dra. Sri Hartati, M.Sc., Ph.D (NIP. 195701141985032001)
* **Judul Penelitian:** *Stabilisasi Penjelasan Model Instance-Dependent Cost-Sensitive Menggunakan Regularisasi dan Uji Permutasi Biaya Terstratifikasi*
* **Problem & Gap SOTA:** Model IDCS mengoptimasi Average Expected Cost (AEC) di sektor kredit finansial, tetapi penjelasan lokalnya (SHAP & LIME) mengalami lonjakan variansi CoV 3× lipat saat class imbalance > 95/5 (Ballegeer et al., 2025 EJOR). Hipotesis *entanglement* bobot biaya dibuktikan dan dimitigasi melalui desain eksperimen 3 tahap:
  1. **Tahap 1 (Lantai Derau):** Replikasi dataset HMEQ ($N=5,960$) pada 32 konfigurasi ($L=25$ bootstrap) untuk mengisolasi variansi acak kernel explainer (*noise floor*).
  2. **Tahap 2 (Intervensi Dual-Arm):** Lengan 1 menguji kekuatan regularisasi bobot non-degenerat ($\sigma > 0.01$); Lengan 2 menguji manipulasi counterfactual permutasi biaya terstratifikasi (*cost-shuffle* pada 5 random seed).
  3. **Tahap 3 (Uji Hipotesis & Trade-off):** Paired Wilcoxon Signed-Rank, Sign-Flip Permutation Test ($B=2,000$ iterasi), koreksi Benjamini-Hochberg FDR, serta analisis trade-off finansial (*Savings* vs *relAEC*).
* **No-Lose Research Decision Matrix:** Menjamin kontribusi ilmiah bernilai tinggi pada Skenario A (Regularisasi Efektif), Skenario B (Bukti Kausal Entanglement), maupun Skenario C (Interaksi Data Sparsity).
* **Ekspor Tabel LaTeX IEEE:** Satu klik menyalin kode tabel format IEEE / Tesis UGM langsung ke clipboard.

---

## 🎛️ Struktur Navigasi Dashboard Web Baru

Dashboard kini berfokus penuh pada kapabilitas AI Engineer:

| Tab Navigasi | Ikon & Badge | Deskripsi Fitur Utama |
| :--- | :---: | :--- |
| **Ringkasan AI** | 🏠 `Executive` | Bento Grid 2.0 dengan AI Showcase Grid (Fase 1–5), live status klaster Go :8085 + FastAPI :8000 + pgvector, dan controller sesi deep work. |
| **Next-Gen RAG** | 🧠 `CRAG` | Interactive CRAG tester (preset query CatBoost, HNSW, HyDE kafein, & OOD martabak), RAPTOR GMM cluster tree, dan Cross-Encoder table. |
| **Multimodal VLM** | 📸 `Gemini 2.0` | Dropzone gambar & 3 preset 1-klik untuk kurva loss CatBoost, catatan kuliah tulisan tangan, dan diagram arsitektur multi-agent. |
| **ML Radar** | 📊 `<2ms` | 5 slider interaktif fitur sirkadian, gauge skor anomali real-time (-1.0 s.d. +1.0), batas kritis -0.150, dan kartu intervensi empatik otonom LLM. |
| **AI Quality Flywheel** | 🏆 `81.8 Score` | 5 kartu metrik benchmark RAG Triad dan tabel interaktif 20 kasus uji Golden Dataset dengan drawer inspeksi prompt, ground truth, dan kritik juri LLM. |
| **Riset & Tesis** | 🔬 `IDCS XAI` | Arsitektur 3 Tahap Tesis S2 UGM (Noise Floor, Dual-Arm Regularisasi & Cost-Shuffle), No-Lose Decision Matrix, logbook bimbingan dospem, dan **generator tabel LaTeX IEEE 1-klik**. |
| **MCP & Telemetry** | 🔌 `SSE Std` | Katalog 8 skema tool MCP, live JSON-RPC 2.0 simulator, audit logs worker Go, dan pipeline webhook 3 repositori akademik. |

---

## ⚡ Mode Demo Instan & Recruiter Walkthrough Tour (60 Detik)

Untuk mempermudah Tech Lead, Engineering Manager, dan Recruiter menguji kapabilitas sistem tanpa proses registrasi:

* **⚡ 1-Click Instant Recruiter Preview:**
  * Tombol akses cepat di halaman login yang langsung memuat lingkungan simulasi dengan data akademik realistis Frans Alwan Purba (analisis metrik CatBoost, Tubes Machine Learning, hidrasi harian, dan ringkasan AI).
* **✨ Guided Tour Interaktif (60 Detik):**
  * Klik pill `✨ Demo (Tour 60s)` di navbar atas untuk membuka walkthrough interaktif 5 langkah:
    1. **Arsitektur Polyglot & Anthropic MCP**: Hubungan FastAPI SSE `:8000` dan worker Go `:8085`.
    2. **Next-Gen RAG & RAPTOR Tree**: Pengelompokan GMM, CRAG routing, dan Cross-Encoder.
    3. **Multimodal VLM & Classical ML Radar**: Gemini 2.0 VLM dan Isolation Forest < 2ms.
    4. **AI Quality Flywheel & Evals**: RAG Triad, skor komposit 81.8/100, dan Golden Dataset.
    5. **Profil Rekayasa Frans Alwan Purba**: Informasi riset magister AI di UGM dan link kontak.

---

## 🐙 Integrasi GitHub Repositori Akademik (Kuliah & Riset)

Second Brain terintegrasi secara dua arah dengan ekosistem GitHub mahasiswa — baik saat bekerja di komputer lokal (*Git post-commit hook*) maupun saat push ke GitHub (*GitHub Webhooks*):

* 🎓 **[materi-kuliah](https://github.com/fransalwan/materi-kuliah):** Setiap commit yang mencantumkan tugas atau mata kuliah otomatis menandai tugas (`CourseAssignment`) sebagai selesai dan mencatat habit belajar harian.
* 📝 **[thesis-manuscripts](https://github.com/fransalwan/thesis-manuscripts):** Setiap commit naskah (misal: `feat(bab 3): metodologi progres 80%`) otomatis memperbarui progres Bab 1–5 skripsi. Jika commit mencatat arahan pembimbing (`bimbingan`, `dospem`), sistem otomatis mencatat notulensi ke log riset.
* 🧪 **[thesis-experiments](https://github.com/fransalwan/thesis-experiments):** Setiap commit evaluasi model AI (misal: `eval CatBoost: acc=95.1% f1=94.4% loss=0.118 epoch=350`) otomatis mengekstrak metrik evaluasi & hyperparameter ke database untuk siap diekspor ke tabel LaTeX Bab 4.

---

## 💻 Menjalankan di Komputer Lokal

### 1. Prasyarat
- Python 3.11+
- Node.js 18+ & npm
- Golang 1.22+ (opsional untuk background worker)

### 2. Frontend Web Dashboard
```bash
cd apps/dashboard
npm install
npm run dev
```
Akses dashboard lokal di `http://localhost:5173`.

### 3. Backend AI Engine & MCP SSE
```bash
cd apps/backend
pip install -e .
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Akses endpoint MCP SSE di `http://127.0.0.1:8000/mcp/sse`.

### 4. Background Telemetry Worker (Golang)
```bash
cd apps/telemetry-worker-go
go run main.go
```
Daemon telemetri berjalan di port `:8085`.

### 5. Menjalankan Automated Test Suite
```bash
# Menjalankan 117 unit tests backend
pytest apps/backend/tests

# Menjalankan AI Quality Flywheel Evals (LLM-as-a-Judge)
python apps/backend/evals/eval_runner.py
```

---

## 📄 Lisensi & Kontribusi

Project ini berlisensi **MIT**. Terbuka untuk kontribusi komunitas di seluruh Indonesia.

*Dibuat dengan ❤️ oleh Frans Alwan Purba untuk kemajuan rekayasa sistem kecerdasan buatan Indonesia.*
