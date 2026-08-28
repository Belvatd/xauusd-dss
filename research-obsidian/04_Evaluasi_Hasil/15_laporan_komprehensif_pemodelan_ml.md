---
tags: [evaluasi-hasil]
---

# 15. Laporan Komprehensif: Rekayasa Fitur, Teori Statistik, dan Pemodelan Prediktif Machine Learning (DSS)

Dokumen ini disusun sebagai **Laporan Akademis Formal** yang menyajikan landasan teoritis konvensional, metodologi rekayasa fitur (*feature engineering*), uji inferensi statistik, arsitektur *Machine Learning*, hingga evaluasi sistem pendukung keputusan (*Decision Support System* / DSS) pada pergerakan harga Emas (XAUUSD).

---

## DAFTAR ISI
1. [BAB I: Paradigma & Arsitektur Pemodelan](#bab-i-paradigma--arsitektur-pemodelan)
2. [BAB II: Rekayasa Fitur (Feature Engineering)](#bab-ii-rekayasa-fitur-feature-engineering)
3. [BAB III: Landasan Teori Konvensional Seleksi Fitur](#bab-iii-landasan-teori-konvensional-seleksi-fitur)
   - [3.1 Uji Chi-Square ($\chi^2$) untuk Fitur Kategorikal](#31-uji-chi-square-chi2-untuk-fitur-kategorikal)
   - [3.2 Uji ANOVA ($F$-Test) untuk Fitur Numerikal](#32-uji-anova-f-test-untuk-fitur-numerikal)
4. [BAB IV: Protokol Validasi Data Deret Waktu (Anti-Leakage)](#bab-iv-protokol-validasi-data-deret-waktu-anti-leakage)
5. [BAB V: Algoritma Machine Learning & Kalibrasi Probabilitas](#bab-v-algoritma-machine-learning--kalibrasi-probabilitas)
   - [5.1 Model Garis Dasar (*Tiered Baseline* - Logistic Regression)](#51-model-garis-dasar-tiered-baseline---logistic-regression)
   - [5.2 Model Utama (*LightGBM Classifier*)](#52-model-utama-lightgbm-classifier)
   - [5.3 Kalibrasi Probabilitas (*Isotonic Regression*)](#53-kalibrasi-probabilitas-isotonic-regression)
6. [BAB VI: Metrik Evaluasi & Kebijakan Keputusan (Abstain Zone)](#bab-vi-metrik-evaluasi--kebijakan-keputusan-abstain-zone)
7. [BAB VII: Interpretabilitas Model via SHAP (Explainable AI)](#bab-vii-interpretabilitas-model-via-shap-explainable-ai)
8. [BAB VIII: Panduan Alur Eksekusi Skrip (*Notebook*)](#bab-viii-panduan-alur-eksekusi-skrip-notebook)

---

## BAB I: Paradigma & Arsitektur Pemodelan

### 1.1 Masalah Klasifikasi Pasar Finansial
Dalam perdagangan valuta asing dan komoditas, fenomena penembusan level likuiditas harian (*Previous Daily High/Low*) dan mingguan (*Previous Weekly High/Low*) terbagi menjadi dua sifat utama:
1. **True Breakout (Kelanjutan Tren):** Harga menembus level dan melanjutkan momentum searah penembusan.
2. **Liquidity Sweep (Jebakan Likuiditas):** Harga menembus level hanya untuk memicu *stop-loss* pelaku pasar ritel, lalu berbalik arah secara tajam (*reversal*).

### 1.2 Pendekatan Hierarkis Dua Tingkat (M1 & M2)
Alih-alih memaksa satu model menyelesaikan 4 kelas sekaligus (*multiclass classification*) yang rawan mengalami ketidakstabilan probabilitas (*class imbalance*), riset ini menggunakan pendekatan hierarkis:
* **Model M1 (Struktural - Biner):** Memprediksi apakah suatu penembusan akan menjadi **Breakout Murni ($Y=1$)** atau **Pembalikan Arah / Sweep ($Y=0$)**.
* **Model M2 (Kondisional - Kecepatan):** Khusus untuk data yang terprediksi *Sweep*, model kedua memprediksi apakah pembalikan terjadi cepat (*Immediate Sweep*) atau lambat (*Delayed Sweep*).

---

## BAB II: Rekayasa Fitur (*Feature Engineering*)

Data mentah OHLCV (Open, High, Low, Close, Volume) ditransformasikan menjadi petunjuk kontekstual (*contextual features*) pada saat candle penembus ($T_0$) ditutup.

| Famili Fitur | Nama Kolom | Tipe Data | Definisi Operasional & Rasional Ilmiah |
| :--- | :--- | :---: | :--- |
| **Temporal (Waktu)** | `hour_of_day` | Numerik | Jam penembusan (0–23 UTC) untuk menangkap puncak likuiditas jam tertentu. |
| | `day_of_week` | Kategorik | Hari perdagangan (0=Senin, 4=Jumat). Hari Senin dan Jumat memiliki karakteristik unik (efek awal pekan dan *closing* akhir pekan). |
| | `session` | Kategorik | Sesi pasar dominan (`ASIA`, `LONDON`, `NY`, `OFF_SESSION`). Likuiditas London & NY jauh lebih volatil daripada Asia. |
| | `is_weekend_cross` | Biner | Bernilai 1 jika jendela observasi terpotong libur akhir pekan, 0 jika mulus. |
| **Tingkat Likuiditas** | `level_type` | Kategorik | Menandakan level yang ditembus (`PDH`, `PDL`, `PWH`, `PWL`). Level mingguan memiliki magnitudo likuiditas yang lebih masif. |
| **Aksi Harga & Volatilitas** | `breakout_depth` | Numerik | Kedalaman tusukan harga melewati level garis: $\text{High} - \text{Level}$ (untuk level atas) atau $\text{Level} - \text{Low}$ (untuk level bawah). |
| | `crossover_volume` | Numerik | Besaran *tick volume* pada saat candle penembus terbentuk. |
| | `window_hours` | Numerik | Durasi jam aktual observasi jendela 6-candle. |

---

## BAB III: Landasan Teori Konvensional Seleksi Fitur

Sebelum fitur-fitur tersebut disuapkan ke algoritma *Machine Learning*, dilakukan penyaringan statistik menggunakan metode parametrik dan non-parametrik konvensional guna menghindari jebakan dimensi (*Curse of Dimensionality*) dan korelasi semu (*spurious correlation*).

```text
[ Seluruh Kandidat Fitur ]
       |
       +---> Fitur Kategorikal ---> UJI CHI-SQUARE (χ²) ---> Hanya Lolos jika p-value < 0.05
       |
       +---> Fitur Numerikal   ---> UJI ANOVA (F-Test)  ---> Hanya Lolos jika p-value < 0.05
       |
       v
[ Subkumpulan Fitur Terpilih (Selected Features) ] ---> Masuk ke Algoritma LightGBM
```

---

### 3.1 Uji Chi-Square ($\chi^2$) untuk Fitur Kategorikal

#### A. Konsep Dasar & Definisi
Uji Chi-Square Independensi adalah uji statistik non-parametrik yang digunakan untuk menguji apakah ada hubungan yang signifikan secara statistik antara **dua variabel kategorikal** (misalnya: *Sesi Perdagangan* terhadap *Hasil Penembusan Breakout/Sweep*).

* **Hipotesis Nol ($H_0$):** Tidak ada hubungan antara fitur kategorikal dengan hasil pergerakan harga (independen).
* **Hipotesis Alternatif ($H_1$):** Terdapat hubungan signifikan antara fitur kategorikal dengan hasil pergerakan harga.

#### B. Rumus Matematis
$$\chi^2 = \sum_{i=1}^{r} \sum_{j=1}^{c} \frac{(O_{ij} - E_{ij})^2}{E_{ij}}$$

*Di mana:*
* $O_{ij}$ = Frekuensi Observasi (data nyata di lapangan pada baris $i$, kolom $j$).
* $E_{ij}$ = Frekuensi Harapan teoritis jika $H_0$ benar, dihitung dengan rumus:
  $$E_{ij} = \frac{\text{Total Baris } i \times \text{Total Kolom } j}{\text{Total Seluruh Observasi } (N)}$$
* Derajat Bebas (*Degrees of Freedom*): $df = (r - 1) \times (c - 1)$.

#### C. Kriteria Keputusan
Fitur dinyatakan memiliki daya pisah yang signifikan dan **lolos seleksi** jika nilai signifikansi $p\text{-value} < 0,05$ (tingkat signifikansi $\alpha = 5\%$).

#### D. Mengapa Memilih Chi-Square?
* Data sesi (`ASIA`, `LONDON`, `NY`) dan tipe level (`PDH`, `PWH`) berbentuk nominal diskrit tanpa asumsi distribusi normal.
* Perhitungannya transparan dan menghasilkan matriks kontingensi yang mudah diverifikasi secara manual pada sidang skripsi.

#### E. Opsi Lain yang Dipertimbangkan & Alasan Tidak Dipakai:
1. **Mutual Information (MI):** Bagus untuk non-linier, namun menghasilkan skor skalar absolut tanpa nilai *p-value* pasti untuk pengujian hipotesis formal.
2. **Fisher’s Exact Test:** Sangat akurat untuk tabel kontingensi kecil ($2 \times 2$), namun sangat lambat dan tidak efisien secara komputasi untuk tabel multi-kategori ($4 \times 2$) pada data ribuan baris.

---

### 3.2 Uji ANOVA ($F$-Test) untuk Fitur Numerikal

#### A. Konsep Dasar & Definisi
*Analysis of Variance* (ANOVA Satu Arah) digunakan untuk menguji apakah terdapat perbedaan rata-rata (*mean*) yang signifikan secara statistik pada **suatu variabel numerik kontinu** di antara kelompok label target (Kelompok Breakout vs Kelompok Sweep).

* **Hipotesis Nol ($H_0$):** $\mu_{\text{Breakout}} = \mu_{\text{Sweep}}$ (Rata-rata nilai fitur pada kedua kelompok adalah sama).
* **Hipotesis Alternatif ($H_1$):** $\mu_{\text{Breakout}} \neq \mu_{\text{Sweep}}$ (Terdapat perbedaan rata-rata nilai fitur yang signifikan).

#### B. Rumus Matematis
$$F = \frac{\text{Varians Antar-Kelompok (Between-Group Variance)}}{\text{Varians Dalam-Kelompok (Within-Group Variance)}} = \frac{MSB}{MSW}$$

*Di mana:*
* $MSB = \frac{SSB}{k - 1}$ (Rata-rata jumlah kuadrat antar kelompok).
* $MSW = \frac{SSW}{N - k}$ (Rata-rata jumlah kuadrat galat di dalam kelompok).
* $SSB = \sum n_j (\bar{X}_j - \bar{X}_{\text{total}})^2$
* $SSW = \sum (X - \bar{X}_j)^2$

#### C. Kriteria Keputusan
Jika nilai $F$-hitung menghasilkan $p\text{-value} < 0,05$, maka $H_0$ ditolak. Artinya, besaran fitur numerik tersebut (seperti `breakout_depth` atau `volume`) terbukti berbeda secara signifikan ketika pasar sedang melakukan *Breakout* dibanding saat *Sweep*.

#### D. Opsi Lain yang Dipertimbangkan & Alasan Tidak Dipakai:
1. **Uji Mann-Whitney U (Kruskal-Wallis):** Merupakan uji non-parametrik berbasis peringkat. Meskipun tahan *outlier*, ANOVA $F$-test lebih selaras dengan linearitas pembagian partisi pohon keputusan dan standar pelaporan inferensial kuantitatif.
2. **Information Value (IV) / Weight of Evidence (WoE):** Standar industri perbankan/skoring kredit, namun mengharuskan proses *binning* diskretisasi yang dapat menghilangkan variansi kontinu harga emas.

---

## BAB IV: Protokol Validasi Data Deret Waktu (*Anti-Leakage*)

```text
[ Data 2016 - 2024 ] ===================================> [ Data 2025 - 2026 ]
  Fold 1: [ Train 2016-2018 ] --(Embargo 6H)--> [ Val 2019 ]       |
  Fold 2: [ Train 2016-2019 ] --(Embargo 6H)--> [ Val 2020 ]       |
  Fold 3: [ Train 2016-2020 ] --(Embargo 6H)--> [ Val 2021 ]       | (DIKUNCI / OOS)
  Fold 4: [ Train 2016-2021 ] --(Embargo 6H)--> [ Val 2022 ]       | Dievaluasi tepat 1x
  Fold 5: [ Train 2016-2022 ] --(Embargo 6H)--> [ Val 2023 ]       | pada akhir riset!
  Fold 6: [ Train 2016-2023 ] --(Embargo 6H)--> [ Val 2024 ]       |
```

### 4.1 Larangan *K-Fold Cross-Validation* Acak
Pada data deret waktu finansial, pembagian acak (*Random Shuffle*) menyebabkan **kebocoran data masa depan (*Look-Ahead Bias*)**. Jika model belajar dari data hari Rabu untuk menebak hari Selasa, akurasi yang diperoleh adalah palsu (*overfitting semu*).

### 4.2 Purged Expanding Walk-Forward CV
Metodologi yang digunakan adalah *Expanding Window*:
1. Model dilatih dari tahun awal secara kronologis dan diuji pada 1 tahun berikutnya.
2. **Purging & Embargo 6-Jam:** Membuang 6 baris terakhir di batas akhir masa latih agar jendela observasi ($T_1 \dots T_6$) tidak menyentuh periode validasi.

### 4.3 Penguncian *Out-of-Sample* (OOS) 2025–2026
Data periode 1 Januari 2025 hingga 31 Juli 2026 (469 event) **dikunci total di awal** dan tidak pernah disentuh oleh proses seleksi fitur maupun *training*. Data ini berfungsi sebagai ujian kelulusan akhir (*final out-of-sample test*).

---

## BAB V: Algoritma Machine Learning & Kalibrasi Probabilitas

### 5.1 Model Garis Dasar (*Tiered Baseline* - Logistic Regression B2)
Sesuai prinsip metodologi *Parsimony*, model *Gradient Boosting* yang kompleks harus mampu mengalahkan model garis dasar linier:
$$P(Y=1 \mid X) = \frac{1}{1 + e^{-(\beta_0 + \beta_1 X_1 + \dots + \beta_k X_k)}}$$
Jika LightGBM tidak mampu mengungguli skor Regresi Logistik teratur (L2) secara signifikan, maka model linier yang lebih sederhana yang harus dipilih.

### 5.2 Model Utama: *LightGBM Classifier*
*LightGBM (Light Gradient Boosting Machine)* dipilih sebagai algoritma utama karena:
1. **Pertumbuhan Ranting Berbasis Daun (*Leaf-wise Tree Growth*):** Memilih daun dengan penurunan *loss* terbesar, menghasilkan akurasi yang jauh lebih tinggi dibanding pertumbuhan *depth-wise* standar.
2. **Penanganan Alami Fitur Kategorikal:** Mampu memproses kolom nominal seperti `session` secara langsung tanpa *one-hot encoding* yang memicu dimensi membengkak.
3. **Pemberat Kelas Seimbang (`class_weight='balanced'`):** Mengkompensasi proporsi data *Breakout* yang minoritas secara otomatis pada fungsi loss:
   $$w_j = \frac{N}{k \times n_j}$$

### 5.3 Kalibrasi Probabilitas (*Isotonic Regression*)
Model pohon (*tree-based*) umumnya menghasilkan estimasi skor probabilitas yang terlalu percaya diri (*overconfident* di dekat 0 atau 1). Agar skor keluaran mencerminkan probabilitas empiris riil, model dibungkus dengan **`CalibratedClassifierCV`** menggunakan metode **Isotonic Regression**:
$$\min \sum_{i=1}^n (y_i - \hat{m}(f_i))^2 \quad \text{dengan syarat } \hat{m} \text{ bersifat monoton naik}$$

---

## BAB VI: Metrik Evaluasi & Kebijakan Keputusan (Abstain Zone)

### 6.1 Metrik Evaluasi Probabilistik
* **Brier Score (Ketajaman Probabilitas):** Mengukur kuadrat kesalahan probabilitas:
  $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N (P_i - y_i)^2 \quad (\text{Skor } 0 = \text{Sempurna, } 0.25 = \text{Tebakan Koin Acak})$$
* **PR-AUC (Area Under Precision-Recall Curve):** Metrik utama untuk data *imbalance*, mengukur kemampuan model dalam menangkap kelas positif (*Breakout*) tanpa memicu alarm palsu (*False Positives*).

### 6.2 Kebijakan Keputusan DSS: Zona Abstain (*Abstain Zone*)
Sistem Pendukung Keputusan tidak boleh memaksakan eksekusi saat model berada dalam ketidakpastian.

```text
       0.0%                    35.0%                     65.0%                   100.0%
P(Breakout) [--- SWEEP ZONE ---] [--- ABSTAIN ZONE ---] [--- BREAKOUT ZONE ---]
             (Fade / Reversal)         (NO TRADE / WAIT)       (Follow Trend)
```

* **$P(\text{Breakout}) \ge 65,0\%$:** Sinyal Terkonfirmasi Kuat **BREAKOUT (Follow)**.
* **$P(\text{Breakout}) \le 35,0\%$:** Sinyal Terkonfirmasi Kuat **SWEEP (Fade/Reversal)**.
* **$35,0\% < P(\text{Breakout}) < 65,0\%$:** **ZONA ABSTAIN (No Trade)** $\rightarrow$ Menolak transaksi untuk memproteksi modal dari pergerakan pasar yang *noisy*.

---

## BAB VII: Interpretabilitas Model via SHAP (Explainable AI)

Untuk mencegah model menjadi kotak hitam (*black box*), digunakan metode **SHAP (SHapley Additive exPlanations)** berbasis teori permainan (*cooperative game theory*):

$$\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|! (|F| - |S| - 1)!}{|F|!} \left[ f(S \cup \{i\}) - f(S) \right]$$

1. **Global Feature Importance (Bar Plot):** Mengurutkan fitur dari yang paling dominan mempengaruhi keputusan model secara keseluruhan.
2. **Beeswarm Summary Plot:** Memperlihatkan arah pengaruh nilai fitur (misal: apakah *volume* tinggi mendorong ke arah *Breakout* atau ke arah *Sweep*).

---

## BAB VIII: Panduan Alur Eksekusi Skrip (*Notebook*)

Seluruh alur metodologi di atas telah diimplementasikan dalam skrip terpadu di repositori:
👉 **[`databricks_pipelines/04_machine_learning_dss.ipynb`](file:///Users/belvatalithadwiyanti/Documents/Projects/research/databricks_pipelines/04_machine_learning_dss.ipynb)**

### Struktur Eksekusi Notebook:
1. **Sel 1 (Ingesti & Lock-Out):** Memuat data (otomatis mendeteksi Databricks / CSV lokal) dan mengunci 469 baris data OOS (2025–2026).
2. **Sel 2 (Feature Engineering & Stats):** Membuat 5 famili fitur dan mengeksekusi uji $\chi^2$ serta ANOVA ($p < 0.05$).
3. **Sel 3 (Training & OOS Eval):** Melatih LightGBM dengan *Purged Walk-Forward CV*, mengkalibrasi probabilitas via *Isotonic Regression*, dan menghitung *Brier Score*, *PR-AUC*, serta distribusi Zona Abstain.
4. **Sel 4 (SHAP Plotting):** Menghitung nilai Shapley dan merender grafik batang (*Importance*) serta *Beeswarm plot*.
