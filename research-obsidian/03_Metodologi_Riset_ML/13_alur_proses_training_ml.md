---
tags: [metodologi-riset-ml]
---

# 13. Alur dan *Tech Stack* Proses Training Machine Learning

Dokumen ini menjelaskan alur kerja operasional (*workflow*) serta alat atau *library* spesifik yang digunakan pada saat mengeksekusi pelatihan model *Machine Learning* (Fase 3) di dalam *notebook* Databricks.

Karena data keluaran dari *pipeline Data Engineering* (Tabel Gold) sudah padat dan terstruktur (3.148 baris), tahapan pelatihannya tidak lagi menggunakan `PySpark`, melainkan menggunakan pustaka pengolahan data **Python murni** agar kompatibel dengan algoritma kecerdasan buatan standar industri.

---

## *Tech Stack* (Alat & Pustaka Utama)

| Pustaka / Alat | Fungsi Spesifik di dalam Riset |
| :--- | :--- |
| **Databricks Notebook** | *Environment* eksekusi kode berbasis cloud (Python). |
| **Pandas** | Mentransformasi data tabel Gold menjadi format matriks yang ringan dan cepat. |
| **Scikit-Learn (`sklearn`)** | Menghitung metrik (PR-AUC, Brier), menyiapkan pemisahan data urutan waktu (*TimeSeriesSplit*), dan melakukan Kalibrasi Probabilitas. |
| **LightGBM / XGBoost** | Algoritma *Gradient Boosting* inti (otak utama) yang dilatih untuk memprediksi probabilitas *Sweep* vs *Breakout*. |
| **Optuna / GridSearchCV** | Melakukan eksperimen iteratif secara otomatis untuk mencari setelan parameter terbaik (*Hyperparameter Tuning*). |
| **MLflow** | Merekam (*logging*) hasil pengujian, akurasi, dan parameter setiap percobaan agar model terbaik dapat diselamatkan (*registry*). |
| **SHAP** | Modul XAI (*Explainable AI*) untuk membedah alasan dan petunjuk apa yang membuat model memprediksi suatu arah (menghindari sifat *Black Box*). |

---

## 6 Langkah Alur Pelatihan Model (*Training Workflow*)

Proses pelatihannya terdiri dari 6 tahapan linear yang dieksekusi secara berurutan:

### 1. Ingesti Data ke Pandas
* **Proses:** Membaca tabel `smt7_research.xauusd.xauusd_liquidity_gold` menggunakan perantara `spark.table().toPandas()`. 
* **Tindakan:** Data dipisah menjadi **Matriks X** (Kumpulan *Feature/Petunjuk* seperti Sesi, RSI, ATR, dll) dan **Vektor Y** (Target Kelas seperti `IMMEDIATE_SWEEP`, `PURE_BREAKOUT`).

### 2. Pengaturan Jadwal Validasi Waktu
* **Proses:** Mengatur logika *Purged Expanding Walk-Forward CV* menggunakan turunan fungsi `TimeSeriesSplit`.
* **Tindakan:** Komputer tidak boleh mengacak data. Model dipaksa melakukan simulasi simulasi historis berjenjang (misalnya, *Train* 2016-2018 $\rightarrow$ *Test* 2019, kemudian melangkah maju satu tahun).

### 3. Penyetelan *Hyperparameter* Secara Otomatis
* **Proses:** Menyerahkan tugas pencarian setelan konfigurasi kepada `Optuna`.
* **Tindakan:** *Optuna* akan menjalankan puluhan simulasi ringan untuk mencari angka *Learning Rate*, kedalaman pohon (*max_depth*), dan jumlah iterasi (*n_estimators*) yang memberikan keseimbangan terbaik agar model pintar tapi tidak *overfitting*.

### 4. Pelatihan Utama (*Model Fitting*)
* **Proses:** Melatih model `lightgbm` menggunakan setelan terbaik hasil dari langkah 3.
* **Tindakan:** Mengeksekusi perintah `model.fit(X_train, Y_train)`. Di sinilah model memanfaatkan mekanisme *Gradient Boosting*, yakni terus-menerus memperbaiki kesalahan prediksinya secara mandiri lapis demi lapis pada data pelatihan.

### 5. Kalibrasi Probabilitas
* **Proses:** Menggunakan fungsi `CalibratedClassifierCV` (dengan metode *Platt Scaling* atau *Isotonic Regression*).
* **Tindakan:** Mengkoreksi prediksi mentah dari model agar sejalan dengan frekuensi peluang di dunia nyata. Hal ini memastikan persentase yang dikeluarkan (*misal 80% kemungkinan Breakout*) benar-benar merepresentasikan probabilitas lapangan, bukan sekadar angka kepercayaan semu.

### 6. Pencatatan Rapor dan Registrasi Model (MLflow)
* **Proses:** Menilai model pada data validasi *Out-of-Sample* menggunakan fungsi prediksi (`predict_proba`).
* **Tindakan:** Menghitung Brier Score, PR-AUC, dan MCC. Kemudian, perintah `mlflow.log_metric()` dan `mlflow.lightgbm.log_model()` dieksekusi agar semua parameter, nilai ujian, serta wujud asli model tesimpan rapi di dalam *Workspace Registry* Databricks.
