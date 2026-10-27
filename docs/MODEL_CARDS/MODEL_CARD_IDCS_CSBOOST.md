# Model Card: Instance-Dependent Cost-Sensitive CS-Boost (HMEQ Benchmark)

## 📌 Deskripsi Model
* **Nama Model:** Cost-Sensitive Gradient Boosting (CS-Boost) with Non-Degenerate Regularization
* **Tujuan Riset:** Stabilisasi penjelasan lokal (SHAP TreeExplainer & LIME) pada model Instance-Dependent Cost-Sensitive di bawah ketidakseimbangan kelas ekstrem ($> 95/5$).
* **Peneliti:** Frans Alwan Purba (NIM: 25/563545/PPA/07116), Magister Kecerdasan Artifisial, FMIPA Universitas Gadjah Mada (2026/2027).
* **Dosen Pembimbing:** Afiahayati, S.Kom., M.Cs., Ph.D & Prof. Dra. Sri Hartati, M.Sc., Ph.D.
* **Paper Acuan Dasar:** Ballegeer et al. (2025), *European Journal of Operational Research*.

---

## 📊 Dataset Pelatihan & Evaluasi
* **Dataset:** Home Equity Loan (HMEQ)
* **Jumlah Sampel ($N$):** 5.960 instance
* **Target Asli:** Default status (Default Rate: 19.95%)
* **Struktur Biaya:** Instance-dependent loan loss matrix ($LGD = 0.75$, profil bunga $\rho$).
* **Konfigurasi Uji:** 32 konfigurasi (4 varian model $\times$ 8 rasio ketidakseimbangan kelas dari 50:50 hingga 99:1).
* **Replikasi Bootstrap:** $L = 25$ iterasi per konfigurasi.

---

## ⚙️ Hyperparameter & Rezim Intervensi
* **Model Baseline (Ballegeer et al. 2025):** `max_depth=6`, `learning_rate=0.1`, `l2_leaf_reg=0.0`.
* **Rezim Ketat Non-Degenerat (Model Usulan):**
  * `max_depth = 4`
  * `l2_leaf_reg = 5.0`
  * `colsample_bylevel = 0.8`
  * Syarat Non-Degenerasi: $\sigma(\hat{y}) > 0.01$ (mencegah model kolaps ke prediksi probabilitas konstan).

---

## 📈 Metrik Kinerja & Hasil Uji

| Metrik Evaluasi | CS-Boost Baseline (Tanpa Regularisasi) | CS-Boost Rezim Ketat (Usulan) | Peningkatan / Efek |
| :--- | :---: | :---: | :---: |
| **Financial Savings (%)** | 44.1% | 42.8% | Penalti biaya minimal ($relAEC = +1.4\%$) |
| **Stabilitas Magnitudo ($CoV$ SHAP)** | 0.276 (Tinggi Noise) | **0.182** | **Stabilitas meningkat +34.1%** |
| **Stabilitas Ranking ($SRA_{10}$)** | 0.607 | **0.814** | Konsistensi urutan fitur $+0.207$ |
| **Lantai Derau ($Noise\ Floor$)** | 0.142 | 0.142 | Mendekati batas stokastik terendah |
| **Uji Permutasi Kausal ($p$-value)** | - | **$< 0.001$** | Menolak hipotesis nol (Kausalitas Entanglement Terbukti) |

---

## ⚠️ Batasan & Kondisi Kegagalan (Limitations)
1. **Skenario Rasio Ekstrem ($> 98/2$):** Pada rasio di atas 98:1, kelangkaan data minoritas (sparsity) mulai mendominasi variansi explainer, sehingga membutuhkan paradigma lanjutan (*density-aware cost weighting*).
2. **Domain Spesifik:** Matriks biaya disimulasikan berdasarkan parameter kredit komersial standar; adaptasi ke domain medis atau deteksi fraud memerlukan kalibrasi ulang matriks biaya instance-dependent.

