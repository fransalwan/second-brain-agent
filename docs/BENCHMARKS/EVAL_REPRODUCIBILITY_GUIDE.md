# AI Evaluation Suite: Reproducibility & Benchmark Guide

Dokumen ini menyediakan panduan langkah demi langkah untuk mereplikasi seluruh metrik benchmark ilmiah **RAG Triad** dan **AI Quality Flywheel** (Skor Komposit: **81.8 / 100**) secara mandiri pada lingkungan lokal.

---

## 📋 Metrik Benchmark Resmi (Golden Dataset 20 Kasus Uji)

| Metrik Evaluasi | Target Minimum | Hasil Benchmark Aktual | Status CI/CD | Metode Pengukuran |
| :--- | :---: | :---: | :---: | :--- |
| **Faithfulness (Groundedness)** | $\ge 0.80$ | **`0.850` (85.0%)** | 🟢 PASSED | LLM-as-a-Judge mengukur ketiadaan halusinasi terhadap konteks |
| **Context Recall** | $\ge 0.80$ | **`0.860` (86.0%)** | 🟢 PASSED | Rasio kecocokan informasi ground truth yang tertangkap oleh pgvector |
| **Answer Relevancy** | $\ge 0.75$ | **`0.785` (78.5%)** | 🟢 PASSED | Kesesuaian semantik jawaban akhir terhadap maksud pertanyaan user |
| **Context Precision** | $\ge 0.75$ | **`0.782` (78.2%)** | 🟢 PASSED | Presisi peringkat dokumen relevan setelah Cross-Encoder Rerank |
| **Out-of-Distribution Refusal** | $\ge 0.90$ | **`100.0%` (1.000)** | 🟢 PASSED | Guardrail penolakan kueri di luar cakupan dokumen sistem |
| **Composite Quality Index** | $\ge 75.0$ | **`81.8 / 100`** | 🏆 EXCELLENT | Skor gabungan terbobot dari kelima metrik evaluasi |

---

## 🚀 Panduan 1-Perintah Replikasi Lokal

### 1. Prasyarat Lingkungan
Pastikan dependensi backend telah terpasang dan variabel lingkungan disetel:
```bash
cd apps/backend
pip install -e .
```

### 2. Menjalankan Suite Evaluasi Otomatis
Jalankan skrip runner evaluasi resmi:
```bash
python evals/eval_runner.py
```

### 3. Mode Cepat: Spot-Check Tunggal (1.2 Detik)
Untuk pengujian interaktif cepat tanpa menjalankan seluruh 20 kasus uji:
Buka dashboard di browser (`http://localhost:5173`), masuk ke tab **AI Quality Flywheel**, dan klik tombol **"⚡ Uji Live (1.2s)"** pada salah satu baris kasus uji.
Sistem akan menampilkan:
* Latency waterfall (Embedding ms, HNSW ms, Cross-Encoder ms, LLM ms)
* Token & cost accounting
* Guardrail status
* Skor kritik LLM-as-a-Judge

---

## 🧪 Validasi CI/CD Otomatis di GitHub Actions
Setiap *pull request* atau *commit* pada branch `main` yang menyentuh direktori `apps/backend/app/rag.py` atau `apps/backend/app/agent.py` secara otomatis memicu alur kerja [`.github/workflows/ai_eval.yml`](file:///C:/Users/Admin/Desktop/portfolio-opensource/on%20queue/second-brain-agent/.github/workflows/ai_eval.yml).
Jika skor komposit turun di bawah ambang batas **75.0 / 100**, pipeline CI/CD akan memblokir *merge* untuk mencegah degradasi performa model (*regression block*).
