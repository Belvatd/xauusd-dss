---
tags: [evaluasi-hasil]
---

# 12. Alur Evaluasi dan Implementasi Machine Learning

Dokumen ini menjelaskan rancangan arsitektur pelatihan (*training*), pengujian (*testing*), serta metrik evaluasi yang digunakan pada model *Machine Learning* untuk Sistem Pendukung Keputusan (DSS) pada Fase 3.

Pendekatan pada data finansial (*time-series*) ini sengaja didesain dengan tingkat ketat yang tinggi (*defensive*) untuk mencegah kebocoran data (*Data Leakage*) dan *overfitting*.

---

## 1. Protokol Pembagian Data (*Purged Expanding Walk-Forward CV*)

Karena data pasar uang berurutan berdasarkan waktu, pembagian acak (*Random Train-Test Split*) dilarang keras. Riset ini menggunakan metode **Purged Expanding Walk-Forward Cross-Validation**. 
Model diajarkan secara kronologis layaknya seorang *trader* yang belajar dari pengalaman masa lalu untuk menghadapi tahun yang baru.

### Skenario Pelatihan (*Training*) & Validasi (*Validation*)
Proses latihan model diperluas (*expanding*) dari tahun ke tahun:
* **Fold 1:** Latihan Data 2016–2018 $\rightarrow$ Validasi Tahun 2019
* **Fold 2:** Latihan Data 2016–2019 $\rightarrow$ Validasi Tahun 2020
* **Fold 3:** Latihan Data 2016–2020 $\rightarrow$ Validasi Tahun 2021
* **Fold 4:** Latihan Data 2016–2021 $\rightarrow$ Validasi Tahun 2022
* **Fold 5:** Latihan Data 2016–2022 $\rightarrow$ Validasi Tahun 2023
* **Fold 6:** Latihan Data 2016–2023 $\rightarrow$ Validasi Tahun 2024

*(Catatan: Terdapat **Embargo 6-jam** di antara akhir masa latihan dan awal masa validasi untuk memastikan tidak ada pergerakan harga yang tumpang tindih bocor ke masa depan).*

### Pengujian Akhir (*Out-of-Sample Final Test*)
* Data dari **Tahun 2025 hingga Juli 2026** dikunci sepenuhnya dari model selama masa iterasi dan latihan.
* Data ini bertindak sebagai Ujian Kelulusan Akhir (*Final Test*) dan **hanya dieksekusi tepat 1 (satu) kali**. Angka performa pada data OOS (*Out-of-Sample*) inilah yang menjadi kesimpulan valid di naskah skripsi akhir.

---

## 2. Metrik Evaluasi Performa Model

Dalam dunia *trading*, persentase "Akurasi" (Benar/Salah) konvensional tidaklah cukup dan sering menyesatkan, terutama jika jumlah data *Sweep* dan *Breakout* tidak seimbang. Oleh karena itu, riset ini menggunakan 3 metrik kelas berat:

### A. PR-AUC (*Precision-Recall Area Under Curve*)
Fokus utamanya adalah pada kepastian kelas positif (misalnya memprediksi *Pure Breakout*).
* **Makna:** Metrik ini tidak peduli seberapa sering model benar menebak hal lain; ia hanya berfokus, *"Jika model membunyikan alarm bahwa ini adalah Breakout, berapa persen jaminan bahwa itu benar-benar Breakout asli (bukan jebakan institusi)?"*
* Cocok untuk mendeteksi sinyal presisi tinggi agar *trader* tidak tertipu masuk ke pasar secara gegabah.

### B. Kalibrasi Probabilitas (*Brier Score* & *Expected Calibration Error / ECE*)
DSS tidak hanya menghasilkan keputusan mutlak, melainkan mengeluarkan nilai persentase keyakinan (Probabilitas).
* **Makna:** Jika AI mengatakan ada kemungkinan **80%** untuk *Liquidity Sweep*, metrik ECE menguji realitanya: *"Apakah dari 100 prediksi serupa yang diberikan AI, 80 di antaranya benar-benar berakhir sebagai Sweep?"*
* Semakin kecil nilai ECE dan Brier Score, semakin dapat dipercaya nilai probabilitas (persentase) yang dikeluarkan oleh AI tersebut.

### C. MCC (*Matthews Correlation Coefficient*)
* **Makna:** Sebuah metrik penyeimbang yang merangkum matriks *True Positive, False Positive, True Negative, False Negative* menjadi satu angka dari -1 hingga +1. MCC memastikan bahwa tebakan model valid dan tidak sekadar menebak kelas mayoritas membabi buta.

*(Perlu diingat: Uji statistik seperti Chi-Square hanya digunakan di Fase 2 untuk menyeleksi fitur/indikator secara manual, bukan untuk mengevaluasi akurasi akhir dari prediksi Machine Learning di Fase 3).*

---

## 3. Eksekusi Hasil: Sistem Pendukung Keputusan (DSS) dengan *Abstain Zone*

Tujuan akhir riset bukanlah menciptakan robot *trading* otomatis (EA) yang asal berdagang, melainkan sebuah penasihat bagi manusia (DSS). Hal ini diimplementasikan melalui **Kebijakan Ambang Batas Probabilitas (*Probability Thresholds*)**:

1. **Sinyal Masuk Pasar (*Actionable Signal*):** Jika probabilitas prediksi model sangat tinggi (misalnya **$P > 75\%$**), sistem menyarankan *trader* untuk bersiap mengambil posisi.
2. **Zona Abstain (*Abstain Zone*):** Jika prediksi model berada di wilayah ragu-ragu (misalnya probabilitas antara **40% hingga 60%**), DSS dengan sengaja memberikan rekomendasi **"Jangan Trading / Berdiam Diri"**.

Menolak untuk memaksakan perdagangan di tengah ketidakpastian tinggi adalah esensi paling murni dari manajemen risiko profesional.
