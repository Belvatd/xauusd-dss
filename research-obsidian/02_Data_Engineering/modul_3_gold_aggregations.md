---
tags: [data-engineering]
---

# MODUL PRAKTIKUM 3
## Gold Layer, SQL Analytics, dan Dashboard
**Silver → Gold → SQL Analytics → Dashboard dengan Genie Code**

| Informasi | Detail |
| :--- | :--- |
| **Platform** | Databricks Free Edition |
| **Kasus** | Early Warning System Kesehatan Mental Remaja DKI Jakarta |
| **Sasaran** | Praktikan (Mahasiswa) |
| **Versi** | Agustus 2026 |

Modul berfokus pada langkah teknis, source code, hasil, verifikasi, dan troubleshooting.

---

### 1. Informasi Teknis
| Komponen | Keterangan |
| :--- | :--- |
| **Notebook** | `P03_MentalHealth_Gold_Analytics` |
| **Input** | `katalog_[nim].kesehatan_mental.silver_telemetri_remaja`, `silver_asesmen_remaja`, `silver_konseling_remaja` |
| **Output Tables** | `katalog_[nim].kesehatan_mental.gold_mentalhealth_dashboard_detail`, `gold_mentalhealth_kpi`, `gold_wilayah_performance`, `gold_stressor_performance` |
| **Output Dashboard** | `D03_MentalHealth_EarlyWarning_Dashboard` (5 KPI Cards, 5 Charts, 4 Filters, 1 Forecast) |
| **Durasi** | ±180 menit |
| **Bahasa** | Python (PySpark) dan SQL |

---

### 2. Tujuan Teknis
1. Membuat *business-ready* **Gold detail table** (`gold_mentalhealth_dashboard_detail`) dari penggabungan 3 tabel Silver.
2. Membuat KPI dan tabel agregasi (wilayah, faktor stres, kelompok usia, dan rujukan medis).
3. Melakukan **rekonsiliasi data** (*data reconciliation & assertions*) lintas tabel Gold.
4. Membuat Dashboard visual interaktif secara otomatis melalui **prompt Genie Code**.
5. Mengaudit formula, filter, visualisasi, dan *forecast* pada Dashboard sebelum dipublikasikan.

---

### 3. Prasyarat & Definisi Business Metric

#### Prasyarat
- Modul 2 (Silver Layer) telah selesai dieksekusi.
- Tabel-tabel Silver (`silver_telemetri_remaja`, `silver_asesmen_remaja`, `silver_konseling_remaja`) telah tersedia di schema `katalog_[nim].kesehatan_mental`.

#### Definisi Business Metric (Early Warning System)
| Metrik | Definisi & Formula |
| :--- | :--- |
| **Total Remaja Terdaftar** | Jumlah unik `user_id_masked` pada dataset telemetri. |
| **Kasus Rujukan Medis** | Jumlah sesi konseling dengan status tindak lanjut ke *Puskesmas* atau *Rumah Sakit Jiwa*. |
| **Average Screen Time** | `AVG(durasi_layar_jam)` pengguna per hari. |
| **High Crisis Score** | Jumlah asesmen dengan total skor kombinasi (PHQ-9 + GAD-7) ≥ 22. |
| **Rate Rujukan (%)** | `ROUND(100.0 * Total Kasus Rujukan / Total Remaja Terdaftar, 2)`. |

---

### 4. Membuat Gold Tables di Notebook (`P03_MentalHealth_Gold_Analytics`)

Buat Notebook baru `P03_MentalHealth_Gold_Analytics` di Databricks dengan language default **Python**.

#### 4.1 Inisialisasi Environment
```python
from pyspark.sql import functions as F

catalog_name = "katalog_[nim]" # Ganti [nim] dengan NIM Anda
schema_name = "kesehatan_mental"

silver_telemetri = f"{catalog_name}.{schema_name}.silver_telemetri_remaja"
silver_asesmen = f"{catalog_name}.{schema_name}.silver_asesmen_remaja"
silver_konseling = f"{catalog_name}.{schema_name}.silver_konseling_remaja"

gold_detail_table = f"{catalog_name}.{schema_name}.gold_mentalhealth_dashboard_detail"
gold_kpi_table = f"{catalog_name}.{schema_name}.gold_mentalhealth_kpi"
gold_wilayah_table = f"{catalog_name}.{schema_name}.gold_wilayah_performance"
gold_stressor_table = f"{catalog_name}.{schema_name}.gold_stressor_performance"
gold_age_table = f"{catalog_name}.{schema_name}.gold_age_group_performance"
```

#### 4.2 Gold Dashboard Detail Table
```python
spark.sql(f"""
CREATE OR REPLACE TABLE {gold_detail_table} USING DELTA AS
WITH latest_asesmen AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id_masked ORDER BY tanggal_asesmen DESC) AS rn
    FROM {silver_asesmen}
),
latest_konseling AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id_masked ORDER BY tanggal_sesi DESC) AS rn
    FROM {silver_konseling}
)
SELECT
    t.telemetri_id,
    a.asesmen_id,
    k.sesi_id,
    t.user_id_masked,
    t.wilayah_jakarta,
    t.durasi_layar_jam,
    t.penggunaan_medsos_malam_menit,
    t.durasi_tidur_jam,
    t.indeks_kualitas_tidur_clean,
    t.tipe_perangkat,
    a.tanggal_asesmen,
    a.kategori_usia,
    a.skor_gad7,
    a.skor_phq9,
    a.total_skor_kombinasi,
    a.faktor_stres_utama,
    a.tingkat_kecemasan_clean,
    a.tingkat_depresi_clean,
    a.status_risiko_krisis,
    k.konselor_id,
    k.tanggal_sesi,
    k.modalitas_sesi,
    k.durasi_sesi_menit,
    k.topik_utama_konseling,
    k.skor_kepuasan_user,
    k.status_tindak_lanjut,
    k.skor_sentimen_clean,
    k.butuh_rujukan_medis,
    CASE WHEN a.total_skor_kombinasi >= 22 THEN 1 ELSE 0 END AS high_crisis_flag,
    CURRENT_TIMESTAMP() AS gold_processed_at
FROM {silver_telemetri} t
JOIN latest_asesmen a ON t.user_id_masked = a.user_id_masked AND a.rn = 1
JOIN latest_konseling k ON t.user_id_masked = k.user_id_masked AND k.rn = 1
""")
```

> **💡 Mengapa Menggunakan CTE `ROW_NUMBER()`?**  
> Satu pengguna (`user_id_masked`) memiliki banyak catatan di tabel Telemetri, Asesmen, dan Konseling. Jika langsung di-`JOIN` hanya berdasarkan `user_id_masked`, akan terjadi **Join Explosion (Perkalian Data Banyak-ke-Banyak)** sehingga jumlah baris membengkak menjadi 1,5 juta baris. Menggunakan `ROW_NUMBER() ... AND a.rn = 1` memastikan setiap log telemetri dipasangkan dengan profil asesmen & konseling terbaru dari remaja tersebut.

> **🔍 Penjelasan Mengapa Hasil Akhir Menjadi 91.635 Baris (Irisan INNER JOIN):**  
> Tabel `silver_telemetri_remaja` memiliki 94.980 baris data valid. Ketika digabungkan menggunakan `INNER JOIN` dengan `latest_asesmen` dan `latest_konseling`, SQL hanya mempertahankan remaja yang memiliki catatan di **ketiga tabel sekaligus** (irisan 3 himpunan). Sebanyak ~875 remaja (~3.345 log telemetri) belum pernah mengisi asesmen atau belum pernah ikut sesi konseling, sehingga secara otomatis tereliminasi dari *Inner Join*, menghasilkan **91.635 baris data medis lengkap**.

#### 4.3 Gold KPI Table
```python
spark.sql(f"""
CREATE OR REPLACE TABLE {gold_kpi_table} USING DELTA AS
SELECT
    COUNT(DISTINCT user_id_masked) AS total_remaja_terdaftar,
    COUNT(DISTINCT telemetri_id) AS total_records_telemetri,
    COUNT(DISTINCT asesmen_id) AS total_records_asesmen,
    COUNT(DISTINCT sesi_id) AS total_records_konseling,
    COUNT(DISTINCT CASE WHEN butuh_rujukan_medis = 1 THEN user_id_masked END) AS total_kasus_rujukan,
    COUNT(DISTINCT CASE WHEN high_crisis_flag = 1 THEN user_id_masked END) AS total_kasus_krisis_tinggi,
    ROUND(AVG(durasi_layar_jam), 2) AS avg_durasi_layar_jam,
    ROUND(AVG(penggunaan_medsos_malam_menit), 1) AS avg_medsos_malam_menit,
    ROUND(AVG(skor_phq9), 2) AS avg_skor_phq9_depresi,
    ROUND(AVG(skor_gad7), 2) AS avg_skor_gad7_kecemasan,
    ROUND(100.0 * SUM(butuh_rujukan_medis) / COUNT(DISTINCT user_id_masked), 2) AS rate_rujukan_percent
FROM {gold_detail_table}
""")
```

#### 4.4 Gold Aggregate Tables (Wilayah, Stressor, & Age Group)
```python
# 1. Gold Wilayah Performance
spark.sql(f"""
CREATE OR REPLACE TABLE {gold_wilayah_table} USING DELTA AS
SELECT 
    wilayah_jakarta,
    COUNT(DISTINCT user_id_masked) AS total_remaja,
    ROUND(AVG(durasi_layar_jam), 2) AS avg_durasi_layar_jam,
    ROUND(AVG(penggunaan_medsos_malam_menit), 1) AS avg_medsos_malam_menit,
    ROUND(AVG(skor_phq9), 2) AS avg_skor_phq9_depresi,
    ROUND(AVG(skor_gad7), 2) AS avg_skor_gad7_kecemasan,
    COUNT(DISTINCT CASE WHEN butuh_rujukan_medis = 1 THEN user_id_masked END) AS total_rujukan_medis
FROM {gold_detail_table}
GROUP BY wilayah_jakarta
""")

# 2. Gold Stressor Performance
spark.sql(f"""
CREATE OR REPLACE TABLE {gold_stressor_table} USING DELTA AS
SELECT 
    faktor_stres_utama,
    COUNT(asesmen_id) AS total_kasus,
    ROUND(AVG(total_skor_kombinasi), 2) AS avg_skor_krisis,
    COUNT(DISTINCT CASE WHEN high_crisis_flag = 1 THEN user_id_masked END) AS total_krisis_tinggi
FROM {gold_detail_table}
GROUP BY faktor_stres_utama
""")
```

---

### 5. Rekonsiliasi Gold Layer (Data Quality Assertions)
Eksekusi pengujian integritas data berikut di Notebook:

```python
# Hitung unique remaja yang butuh rujukan medis dari masing-masing table
detail_total_rujukan = spark.table(gold_detail_table).filter(F.col("butuh_rujukan_medis") == 1).select("user_id_masked").distinct().count()
kpi_total_rujukan = spark.table(gold_kpi_table).select("total_kasus_rujukan").first()[0]
wilayah_total_rujukan = spark.table(gold_wilayah_table).agg(F.sum("total_rujukan_medis")).first()[0]

# Assertion Test
assert detail_total_rujukan == kpi_total_rujukan == wilayah_total_rujukan
print(f"✅ Rekonsiliasi Sukses! Total Kasus Rujukan Medis Terverifikasi: {detail_total_rujukan}")
```

---

### 6. Membuat Dashboard dengan Genie Code

Istilah resmi: Fitur pembuat dashboard berbantuan AI pada Databricks UI disebut **Genie Code** (*Create a dashboard with Genie*).

#### 6.1 Membuat Dashboard Kosong
1. Pada sidebar navigasi Databricks, klik **+ New** -> **Dashboard**.
2. Beri nama Dashboard: **`D03_MentalHealth_EarlyWarning_Dashboard`**.
3. Pilih Compute: **Serverless SQL Warehouse** (atau cluster aktif).
4. Buka kotak dialog **"Create a dashboard with Genie"** (seperti pada tampilan UI *Create a dashboard with Genie*).

#### 6.2 Prompt Final Genie Code (Sudah Diaudit)
Salin dan tempelkan (**copy-paste**) *prompt Genie Code final* berikut ke dalam kotak dialog Genie Code:

> **🤖 Prompt Final Genie Code:**  
> Buatkan dashboard business analytics Early Warning System Kesehatan Mental Remaja menggunakan kumpulan dataset berikut:  
> 1. `katalog_[nim].kesehatan_mental.gold_mentalhealth_dashboard_detail` (Untuk tren dan korelasi)
> 2. `katalog_[nim].kesehatan_mental.gold_wilayah_performance` (Untuk data wilayah)
> 3. `katalog_[nim].kesehatan_mental.gold_stressor_performance` (Untuk faktor stres)
> 4. `katalog_[nim].kesehatan_mental.gold_mentalhealth_kpi` (Untuk metrik KPI)
>  
> **DATASET UTAMA:**  
> Dataset `gold_mentalhealth_dashboard_detail` memuat log telemetri, asesmen psikologis, dan status konseling.  
> Kolom yang digunakan: `telemetri_id`, `user_id_masked`, `wilayah_jakarta`, `durasi_layar_jam`, `penggunaan_medsos_malam_menit`, `kategori_usia`, `skor_gad7`, `skor_phq9`, `total_skor_kombinasi`, `faktor_stres_utama`, `status_tindak_lanjut`, `butuh_rujukan_medis`, `high_crisis_flag`.  
>  
> **HALAMAN:**  
> Buat satu halaman bernama **Early Warning Overview**.  
>  
> **FILTER HORIZONTAL:**  
> 1. `wilayah_jakarta`  
> 2. `kategori_usia`  
> 3. `faktor_stres_utama`  
> 4. `status_tindak_lanjut`  
> Filter memengaruhi semua widget visualisasi.  
>  
> **KPI CARDS (Gunakan tabel `gold_mentalhealth_kpi`):**  
> 1. Total Remaja Terdaftar.  
> 2. Total Kasus Rujukan Medis.  
> 3. Avg Screen Time Jakarta, format 1 desimal.  
> 4. Avg Skor Depresi PHQ-9, format 2 desimal.  
> 5. Total Kasus Krisis Tinggi.  
>  
> **VISUALISASI:**  
> 1. Depresi & Kecemasan per Wilayah (Gunakan tabel `gold_wilayah_performance`): Tampilkan `wilayah_jakarta` vs rata-rata skor depresi dan kecemasan, descending.  
> 2. Distribusi Faktor Stres Utama (Gunakan tabel `gold_stressor_performance`): Tampilkan `faktor_stres_utama` vs total kasus, pie chart.  
> 3. Tren Risiko per Kelompok Usia (Gunakan tabel `gold_mentalhealth_dashboard_detail`): `kategori_usia` vs `AVG(total_skor_kombinasi)`, stacked bar chart berdasarkan `faktor_stres_utama`.  
> 4. Korelasi Screen Time vs Medsos Malam (Gunakan tabel `gold_mentalhealth_dashboard_detail`): `durasi_layar_jam` vs `penggunaan_medsos_malam_menit`, scatter plot.  
> 5. Peringkat Wilayah Kasus Rujukan (Gunakan tabel `gold_wilayah_performance`): `wilayah_jakarta` vs total rujukan, top bar chart.  
>  
> **FORECAST:**  
> Tambahkan Simple Linear Trend Forecast 30 hari untuk tren kasus krisis sebagai widget terpisah. Gunakan bridge row untuk menyambungkan actual dan prediction serta tampilkan lower/upper bound.  
>  
> **STYLING:**  
> - Filter diletakkan di bagian paling atas.  
> - KPI cards berada di baris setelah filter.  
> - Spacing widget rapi dan tidak boleh overlap.  
> - Gunakan default dashboard theme.  
>  
> **ATURAN:**  
> - Tampilkan rencana perubahan terlebih dahulu sebelum menerapkan dan jangan langsung publish.

---

### 7. Troubleshooting

| Masalah / Error | Penyebab | Penanganan / Solusi |
| :--- | :--- | :--- |
| **Filter Horizontal Tidak Memengaruhi Widget** | Menggunakan dataset terpisah dengan mapping field berbeda. | Pastikan seluruh widget menggunakan satu dataset utama (`gold_mentalhealth_dashboard_detail`). |
| **Genie Code Output Error SQL** | Nama kolom pada prompt tidak sesuai skema Gold. | Periksa spasi dan nama kolom skema (`user_id_masked`, `butuh_rujukan_medis`). |
| **Layout Overlap** | AI menghasilkan ukuran widget acak. | Minta Genie Code melalui obrolan: *"Tolong rapikan spacing dan layout widget agar tidak overlap."* |
| **Forecast Tidak Muncul** | SQL Warehouse tidak mendukung fungsi windowing sequence. | Pastikan mengggunakan Serverless SQL Warehouse aktif saat menjalankan prompt. |

---

### 8. Output Pertemuan 3
1. Notebook Praktikum: `P03_MentalHealth_Gold_Analytics`
2. Tabel Gold Detail: `katalog_[nim].kesehatan_mental.gold_mentalhealth_dashboard_detail`
3. Tabel Gold KPI: `katalog_[nim].kesehatan_mental.gold_mentalhealth_kpi`
4. Tabel Gold Agregasi Wilayah: `katalog_[nim].kesehatan_mental.gold_wilayah_performance`
5. Tabel Gold Agregasi Faktor Stres: `katalog_[nim].kesehatan_mental.gold_stressor_performance`
6. Dashboard Resmi: `D03_MentalHealth_EarlyWarning_Dashboard`
