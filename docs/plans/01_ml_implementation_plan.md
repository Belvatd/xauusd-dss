## Goal Description
The objective is to implement **Phase 2 (Diagnostic) and Phase 3 (Predictive DSS)** utilizing Python and Databricks. 
The pipeline will start from the Gold dataset (`xauusd_liquidity_gold`), perform Feature Engineering (generating contextual clues), conduct statistical Feature Selection (Chi-Square and Information Value), and finally train the Hierarchical Machine Learning Models (M1 and M2) with Probability Calibration and Abstain Zone logic.

## User Review Required
> [!IMPORTANT]
> **Data Lock-Out Period:** The Out-of-Sample (OOS) test set is strictly defined as `2025-01-01` to `2026-07-31`. The model and feature selection (Chi-Square) will **not** touch this data to prevent leakage. Is this lock-out period acceptable?

> [!WARNING]
> **Abstain Zone Thresholds:** The proposed thresholds are `P >= 65%` for Sweep, `P <= 35%` for Breakout, and `35% - 65%` as the Abstain Zone (No Trade). Are you comfortable with these exact threshold percentages?

## Proposed Changes

### 1. Phase 2 & 3 DSS Script
We will create a comprehensive Python script that covers both diagnostic feature selection and predictive modeling.

#### [NEW] `databricks_pipelines/04_machine_learning_dss.py`
This script will execute the following logical blocks:

**A. Tahap Diagnostik (Phase 2: Feature Engineering & Selection)**
1. **Data Ingestion:** Load `smt7_research.xauusd.xauusd_liquidity_gold`.
2. **Feature Engineering (5 Famili):**
   - *Time/Session Features:* Ekstraksi Sesi (ASIA, LONDON, NY), hari dalam seminggu, jam.
   - *Volatility Features:* Jarak harga tempuh (ATR), persentase ADR yang sudah terpakai hari ini.
   - *Momentum Features:* RSI (Relative Strength Index) pada saat crossover.
   - *Price Action Features:* Ukuran body candle penembus, rasio sumbu atas/bawah (wick).
   - *Context Features:* Apakah ini sentuhan pertama level Harian (PDH) atau Mingguan (PWH)?
3. **Uji Statistik & Pemilihan Fitur (Feature Selection):**
   - **Chi-Square Test ($\chi^2$):** Menguji hubungan independensi antara fitur kategorikal (misal: Sesi LONDON) terhadap Target Label (Sweep vs Breakout). Jika p-value < 0.05, fitur terbukti memiliki daya pisah.
   - **Information Value (IV) / ANOVA:** Menguji fitur numerik (misal: ATR, RSI). Hanya fitur dengan nilai statistik kuat yang lolos ke tahap ML untuk mencegah *"Curse of Dimensionality"*.

**B. Tahap Prediktif & DSS (Phase 3: Machine Learning)**
1. **Purged Walk-Forward CV Setup:** Implementasi *TimeSeriesSplit* dengan embargo 6-jam agar model dilatih merayap dari tahun 2016 hingga 2024 secara kronologis tanpa membocorkan masa depan.
2. **Hierarchical Model M1 (Sweep vs Breakout):**
   - **Baseline (B2):** *Logistic Regression* menggunakan fitur top-5 dari uji statistik (Chi-Square/IV) sebelumnya.
   - **Main Model:** *LightGBM classifier*.
   - **Calibration:** Menerapkan `CalibratedClassifierCV` (Isotonic/Platt) agar tebakan LightGBM menjadi persentase probabilitas murni.
3. **Hierarchical Model M2 (Sweep Speed):**
   - Memfilter tabel khusus untuk event Sweep, lalu melatih LightGBM kedua untuk membedakan *Immediate Sweep* (Cepat) vs *Delayed Sweep* (Lambat).
4. **Evaluasi & MLflow Logging:**
   - Menghitung PR-AUC, Brier Score, ECE, dan MCC.
   - Mencatat seluruh metrik dan visualisasi Chi-Square ke dalam MLflow Databricks.
5. **DSS Abstain Zone Logic & SHAP:**
   - Memetakan hasil persentase ML ke dalam aksi rekomendasi (Breakout, Abstain, atau Sweep).
   - Menggambar grafik SHAP untuk menerjemahkan ke bahasa manusia (XAI).

### 2. Jupyter Notebook Conversion
After generating the `.py` script, we will convert it to a `.ipynb` format.

#### [NEW] `databricks_pipelines/04_machine_learning_dss.ipynb`
This will be the final artifact uploaded to Databricks.

## Verification Plan

### Automated Tests
- Menambahkan `assert` untuk memastikan data pengujian statistik (Chi-Square) dan ML benar-benar dipotong sebelum tanggal `2025-01-01` (Zero Leakage Protocol).

### Manual Verification
- Pengguna menjalankan *notebook* di Databricks dan memverifikasi tabel hasil uji Chi-Square (melihat nilai p-value setiap fitur).
- Pengguna meninjau MLflow UI untuk melihat grafik kalibrasi dan kurva PR-AUC.
