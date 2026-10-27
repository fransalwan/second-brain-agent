# Model Card: Circadian & Burnout Anomaly Radar (Isolation Forest)

## 📌 Deskripsi Model
* **Nama Model:** Circadian Anomaly Radar Engine
* **Tipe Algoritma:** Unsupervised Isolation Forest (`sklearn.ensemble.IsolationForest`)
* **Tujuan:** Mendeteksi anomali pola hidup, degradasi tidur, dan risiko burnout akademik secara real-time sub-2ms tanpa biaya token LLM.
* **Lisensi:** MIT

---

## 🔬 Fitur Input (5-Dimensi)
Vektor input kontinu $\mathbf{x} \in \mathbb{R}^5$:
1. `sleep_hours` ($[3.0, 10.0]$): Rata-rata jam tidur harian.
2. `sleep_debt_hours` ($[0.0, 30.0]$): Akumulasi kekurangan tidur terhadap standar 8 jam/hari dalam jendela 14 hari.
3. `midnight_sessions_count` ($[0, 14]$): Frekuensi sesi timer atau commit git yang aktif setelah pukul 23:00 WIB.
4. `overdue_tasks_ratio` ($[0.0, 1.0]$): Rasio tugas kuliah aktif yang telah melewati batas waktu (*deadline*).
5. `water_intake_liters` ($[0.5, 4.0]$): Volume asupan cairan harian mahasiswa.

---

## ⚙️ Spesifikasi & Hyperparameter
* `n_estimators`: 100 pohon keputusan isolasi.
* `max_samples`: 256 instance per pohon (sub-sampling optimal untuk isolasi anomali).
* `contamination`: 0.08 (ekspektasi 8% periode anomali kritis).
* `random_state`: 42 (deterministik).
* **Threshold Pemicu Intervensi GenAI:** Skor anomali $< -0.150$.

---

## ⏱️ Karakteristik Kinerja Produksi
* **Inference Latency:** **0.8ms – 1.4ms** per evaluasi (pure in-memory NumPy/C-extension).
* **RAM Footprint:** $< 1.2\text{ MB}$ saat model dimuat.
* **Token Cost:** **\$0.00** pada operasi rutin harian.
* **Throughput:** $> 2.500$ evaluasi per detik pada single CPU core.
