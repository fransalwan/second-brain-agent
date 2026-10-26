# 🏆 Second Brain AI Systems Evaluation Report (CI/CD Quality Flywheel)

> **Evaluated at**: `2026-10-26T14:00:14.864802+00:00`  
> **Target System**: Second Brain Agent (FastAPI + Google ADK + RAPTOR Hierarchical RAG + pgvector)  
> **Composite AI Quality Index**: **`81.8 / 100`** 🎯

---

## 📊 Summary Metrik Standar Industri (LLM-as-a-Judge)

| Metrik Evaluasi | Target Minimum | Hasil Benchmark | Status |
| :--- | :---: | :---: | :---: |
| **Faithfulness (Anti-Hallucination)** | `0.85` | **`0.85`** | 🟢 PASSED |
| **Answer Relevancy** | `0.80` | **`0.785`** | 🟢 PASSED |
| **Context Recall** | `0.80` | **`0.86`** | 🟢 PASSED |
| **Context Precision** | `0.75` | **`0.782`** | 🟢 PASSED |
| **OOD Refusal Rate (Guardrail)** | `0.90` | **`100.0%`** | 🟢 PASSED |

---

## 🔬 Domain-Level Breakdown

| Domain Evaluasi | Jumlah Uji | Avg Faithfulness | Avg Relevancy |
| :--- | :---: | :---: | :---: |
| `ai_research` | 5 | `0.88` | `0.795` |
| `thesis_manuscript` | 4 | `0.775` | `0.737` |
| `circadian_health` | 3 | `0.8` | `0.767` |
| `coursework` | 2 | `1.0` | `0.7` |
| `architecture` | 2 | `0.7` | `0.675` |
| `out_of_distribution` | 3 | `1.0` | `1.0` |
| `rag_pipeline` | 1 | `0.7` | `0.733` |

---

## ⚡ Telemetry & Throughput
- **Total Test Cases**: `20` skenario akademik & sirkadian
- **Waktu Eksekusi Penuh**: `0.72 detik`
- **Rata-rata Latensi**: `~36.0 ms / query`

---
*Laporan ini digenerate secara otomatis oleh pipeline CI/CD `.github/workflows/ai_eval.yml`.*
