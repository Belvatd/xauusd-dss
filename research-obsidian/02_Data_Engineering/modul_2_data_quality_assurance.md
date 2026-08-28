---
tags: [data-engineering]
---

# MODUL PRAKTIKUM 2
## Data Quality Assurance & Silver Layer Engineering
**Bronze → Profiling → Validation (Rules) → Quarantine / Silver Delta Table**

| Informasi | Detail |
| :--- | :--- |
| **Platform** | Databricks Free Edition (Community Edition) |
| **Kasus** | Early Warning System Kesehatan Mental Remaja DKI Jakarta |
| **Sasaran** | Praktikan (Mahasiswa) |
| **Versi** | Agustus 2026 |

---

### 1. Informasi Teknis
| Komponen | Keterangan |
| :--- | :--- |
| **Notebook** | `P02_MentalHealth_DataQuality_Silver` |
| **Input** | `katalog_[nim].kesehatan_mental.bronze_telemetri_remaja`, `bronze_asesmen_remaja`, `bronze_konseling_remaja` |
| **Output Utama** | `katalog_[nim].kesehatan_mental.silver_telemetri_remaja` (Data Valid), dll. |
| **Output Pendukung** | Tabel Quarantine (`katalog_[nim].kesehatan_mental.quarantine_telemetri_remaja`) |
| **Durasi** | ±120 menit |
| **Bahasa** | Python (PySpark) dan SQL |

### 2. Tujuan Teknis
1. Melakukan data profiling (deteksi missing values, rentang data anomali, outlier).
2. Menerapkan aturan Data Quality (DQ Rules) untuk memfilter data kotor (Quarantine).
3. Melakukan transformasi data (Imputasi NULL, standardisasi teks, casting tipe data).
4. Melakukan *Data Masking* (Anonymization) pada ID sensitif (PII).
5. Menyimpan data yang sudah bersih ke dalam format Delta (Silver Layer).

### 3. Langkah-Langkah Praktikum

#### 3.1 Pembuatan Notebook Baru
1. Buka workspace Databricks Anda.
2. Klik tombol **New** -> **Notebook** (atau buat melalui menu **Workspace** -> **Create Notebook**).
3. Beri nama Notebook: `P02_MentalHealth_DataQuality_Silver`.
4. Pilih Default Language: **Python**.
5. Sambungkan (*attach*) Notebook ke Cluster yang sedang berjalan.

#### 3.2 Profiling dan Analisis Outlier
Pertama, analisis distribusi durasi layar.
```python
import pyspark.sql.functions as F

df_bronze = spark.table("katalog_[nim].kesehatan_mental.bronze_telemetri_remaja")
display(df_bronze.describe("durasi_layar_jam", "penggunaan_medsos_malam_menit"))
```
**Penjelasan Anomali / Data Outlier:**
Dari hasil `describe()`, perhatikan nilai maksimum `durasi_layar_jam` yang mencapai **> 20 jam/hari**. Mengapa angka ini dianggap **tidak wajar (anomali)** dan wajib dibersihkan?

1. **Kontekstual Fisiologis (Domain Context)**: Dalam 1 hari (24 jam), seorang remaja membutuhkan waktu tidur biologis minimal 6–8 jam, ditambah aktivitas tanpa perangkat (seperti sekolah, makan, dan berinteraksi fisik). Durasi layar aktif > 20 jam menunjukkan sisa waktu tidak menggunakan perangkat kurang dari 4 jam, yang secara biologis dan realistis sangat tidak wajar.
2. **Penyebab Teknis Data Quality**: Angka ekstrem ini umumnya disebabkan oleh kesalahan sistem telemetri (*bug logging*), layar perangkat yang lupa dimatikan saat pengguna tertidur, atau aplikasi *background* yang menggantung (*session freeze*).
3. **Dampak Terhadap Analisis**: Jika *outlier* ini dibiarkan masuk ke Silver/Gold layer, nilai rata-rata (*mean*) durasi layar per wilayah akan terdistorsi (bias) secara signifikan, sehingga merusak akurasi visualisasi dashboard Early Warning System.

Selain outlier tersebut, perhatikan juga **anomali logika** antara durasi layar dan penggunaan medsos malam. Secara matematis, penggunaan medsos malam (dalam menit) tidak mungkin lebih besar dari total durasi layar (jika dikonversi ke menit). Anomali semacam ini sering terjadi akibat *bug sensor* dan harus dibatasi (*capping*).

#### 3.3 Data Quality Validation & Splitting (Valid vs Quarantine)
Kita akan memisahkan record dengan `durasi_layar_jam` > 18 ke tabel Quarantine.

```python
# Rule: Durasi Layar <= 18 Jam
df_valid_telemetri = df_bronze.filter(F.col("durasi_layar_jam") <= 18.0)
df_quarantine_telemetri = df_bronze.filter(F.col("durasi_layar_jam") > 18.0)

# Simpan Quarantine
df_quarantine_telemetri.write.format("delta").mode("overwrite").saveAsTable("katalog_[nim].kesehatan_mental.quarantine_telemetri_remaja")
```

#### 3.4 Transformasi dan Pembersihan Silver Layer (Per Dataset)
Pada tahap ini, kita akan membersihkan data Bronze yang valid, menangani nilai NULL (*imputation*), menyelaraskan format teks (*standardization*), serta melakukan pengacakan/penyamaran ID pengguna (*Data Masking/Anonymization*) demi menjaga privasi.

**A. Transformasi Tabel Telemetri Digital**
Jalankan kode berikut untuk memproses data telemetri valid:
```python
# Imputasi Missing Values pada Indeks Kualitas Tidur, Cast Timestamp (menggunakan try_to_timestamp agar tidak error ANSI), dan Masking User_ID
df_silver_telemetri = df_valid_telemetri \
    .withColumn("timestamp_clean", F.coalesce(
        F.expr("try_to_timestamp(timestamp, 'yyyy-MM-dd HH:mm:ss')"),
        F.expr("try_to_timestamp(timestamp, 'MM/dd/yyyy HH:mm:ss')"),
        F.expr("try_to_timestamp(timestamp, 'dd/MM/yyyy HH:mm:ss')")
    )) \
    .withColumn("indeks_kualitas_tidur_clean", F.coalesce(
        F.col("indeks_kualitas_tidur"), 
        F.round(F.col("durasi_tidur_jam") * 1.1).cast("int")
    )) \
    .withColumn("penggunaan_medsos_malam_menit", F.when(
        F.col("penggunaan_medsos_malam_menit") > (F.col("durasi_layar_jam") * 60), 
        F.round(F.col("durasi_layar_jam") * 60).cast("int")
    ).otherwise(F.col("penggunaan_medsos_malam_menit"))) \
    .withColumn("user_id_masked", F.sha2(F.col("user_id"), 256)) \
    .drop("timestamp", "indeks_kualitas_tidur", "user_id")

# Simpan ke Silver Table
df_silver_telemetri.write.format("delta").mode("overwrite") \
    .saveAsTable("katalog_[nim].kesehatan_mental.silver_telemetri_remaja")

print(f"Silver Telemetri berhasil disimpan: {df_silver_telemetri.count()} baris")
```

**B. Transformasi Tabel Asesmen Psikologis**
Pada *cell* baru, jalankan kode berikut untuk menstandarkan format kapitalisasi teks (*Capitalize/Initcap*), menghitung total skor kecemasan & depresi, serta mengacak *user_id*:
```python
df_bronze_asesmen = spark.table("katalog_[nim].kesehatan_mental.bronze_asesmen_remaja")

df_silver_asesmen = df_bronze_asesmen \
    .withColumn("tingkat_kecemasan_clean", F.initcap(F.trim(F.col("tingkat_kecemasan")))) \
    .withColumn("tingkat_depresi_clean", F.initcap(F.trim(F.col("tingkat_depresi")))) \
    .withColumn("total_skor_kombinasi", F.col("skor_gad7") + F.col("skor_phq9")) \
    .withColumn("user_id_masked", F.sha2(F.col("user_id"), 256)) \
    .drop("user_id")

# Simpan ke Silver Table
df_silver_asesmen.write.format("delta").mode("overwrite") \
    .saveAsTable("katalog_[nim].kesehatan_mental.silver_asesmen_remaja")

print(f"Silver Asesmen berhasil disimpan: {df_silver_asesmen.count()} baris")
```

**C. Transformasi Tabel Konseling Intervensi Sebaya**
Pada *cell* baru, jalankan kode ini untuk menangani *null sentiment*, membuat indikator rujukan medis, serta mengacak *user_id*:
```python
df_bronze_konseling = spark.table("katalog_[nim].kesehatan_mental.bronze_konseling_remaja")

df_silver_konseling = df_bronze_konseling \
    .withColumn("skor_sentimen_clean", F.coalesce(F.col("skor_sentimen_pesan"), F.lit(0.0))) \
    .withColumn("butuh_rujukan_medis", 
        F.when(F.col("status_tindak_lanjut").isin("Rujukan Psikolog Puskesmas", "Rujukan Rumah Sakit Jiwa"), 1)
         .otherwise(0)
    ) \
    .withColumn("user_id_masked", F.sha2(F.col("user_id"), 256)) \
    .drop("user_id")

# Simpan ke Silver Table
df_silver_konseling.write.format("delta").mode("overwrite") \
    .saveAsTable("katalog_[nim].kesehatan_mental.silver_konseling_remaja")

print(f"Silver Konseling berhasil disimpan: {df_silver_konseling.count()} baris")
```

### 4. Hasil dan Verifikasi

#### 4.1 Kueri Verifikasi Data Valid vs Quarantine
Pastikan data kotor telah dipisahkan ke Quarantine, dan tabel Silver bebas dari NULL pada kolom kritikal:
```sql
%sql
-- Cek jumlah baris valid vs quarantine
SELECT 'Valid (Silver)' AS Tipe, COUNT(*) FROM katalog_[nim].kesehatan_mental.silver_telemetri_remaja
UNION ALL
SELECT 'Quarantine', COUNT(*) FROM katalog_[nim].kesehatan_mental.quarantine_telemetri_remaja;
```

#### 4.2 Rekapitulasi Pembersihan Data (Before vs After Cleansing Recap)

Berikut adalah tabel komparasi perubahan kualitas data dari **Bronze Layer (Data Mentah)** menuju **Silver Layer (Data Cleaned)**:

| Dataset | Parameter / Kolom | Sebelum Cleansing (Bronze Layer) | Sesudah Cleansing (Silver Layer) | Metode & Solusi Data Quality |
| :--- | :--- | :--- | :--- | :--- |
| **Telemetri Digital** | Outlier Durasi Layar | Terdapat data ekstrem (`durasi_layar_jam` > 20 jam) akibat *glitch logging*. | Filtered: Hanya data ≤ 18 jam yang masuk ke Silver. | Outlier dipisahkan ke tabel `quarantine_telemetri_remaja`. |
| | Anomali Logika (Medsos vs Layar) | Medsos malam (menit) > Total Layar (jam) * 60. | Nilai dikoreksi (*capping*) agar tidak melebih batas maksimal durasi layar. | Menggunakan fungsi kondisional `F.when()`. |
| | Missing Values Tidur | Kolom `indeks_kualitas_tidur` memiliki nilai NULL. | Terisi 100% (`indeks_kualitas_tidur_clean`). | Imputasi berbasis perkiraan `round(durasi_tidur_jam * 1.1)`. |
| | Format Timestamp | Format string heterogen (`yyyy-MM-dd`, `MM/dd/yyyy`). | Terstandar bertipe `TimestampType` (`timestamp_clean`). | Conversion aman menggunakan `coalesce` & `try_to_timestamp`. |
| | Privasi Identitas (PII) | `user_id` berupa teks asli (*plaintext*). | Disamarkan menjadi `user_id_masked`. | Data Anonymization menggunakan Hash SHA-256 (`F.sha2`). |
| **Asesmen Psikologis** | Konsistensi Teks | Kolom `tingkat_kecemasan` campuran huruf kapital ("Tinggi", "SEDANG", "rendah"). | Teks rapi dan terstandar (*Proper Case*). | Standardisasi teks menggunakan fungsi `F.initcap()`. |
| | Metrik Krisis | Skor GAD-7 dan PHQ-9 berdiri sendiri. | Memiliki total skor gabungan (`total_skor_kombinasi`). | Feature Engineering: `skor_gad7 + skor_phq9`. |
| **Konseling Sebaya** | Null Sentimen Pesan | `skor_sentimen_pesan` memuat nilai NULL. | Terisi nilai default `0.0` (`skor_sentimen_clean`). | Imputasi nilai default menggunakan `F.coalesce(..., 0.0)`. |
| | Indikator Rujukan | Rujukan medis berupa deskripsi string. | Terdapat binary flag `butuh_rujukan_medis` (1 / 0). | Transformation: `F.when().isin(...)`. |

#### 4.3 Kueri Ringkasan Komparasi
Jalankan blok kode Python berikut di Notebook untuk menampilkan perbandingan statistik secara langsung:
```python
# Komparasi Statistik Sebelum (Bronze) vs Sesudah (Silver)
print("=== TELEMETRI DIGITAL ===")
print(f"Max Durasi Layar (Bronze) : {spark.table('katalog_[nim].kesehatan_mental.bronze_telemetri_remaja').select(F.max('durasi_layar_jam')).collect()[0][0]} jam")
print(f"Max Durasi Layar (Silver) : {spark.table('katalog_[nim].kesehatan_mental.silver_telemetri_remaja').select(F.max('durasi_layar_jam')).collect()[0][0]} jam")
print(f"Jumlah Data Quarantine    : {spark.table('katalog_[nim].kesehatan_mental.quarantine_telemetri_remaja').count()} baris")

print("\n=== ASESMEN PSIKOLOGIS ===")
print("Variasi Teks Kecemasan (Bronze):")
spark.table("katalog_[nim].kesehatan_mental.bronze_asesmen_remaja").select("tingkat_kecemasan").distinct().show(3)
print("Variasi Teks Kecemasan (Silver):")
spark.table("katalog_[nim].kesehatan_mental.silver_asesmen_remaja").select("tingkat_kecemasan_clean").distinct().show(3)
```

### 5. Troubleshooting
| Indikasi Error | Penyebab | Solusi |
| :--- | :--- | :--- |
| `CANNOT_PARSE_TIMESTAMP` / `IllegalArgumentException` | Spark ANSI mode gagal mem-parse format string tanggal karena `to_timestamp` melemparkan exception jika format tidak cocok secara presisi. | Gunakan `try_to_timestamp` (misal via `F.expr("try_to_timestamp(col, 'format')")`) yang mengembalikan `NULL` secara aman saat format tidak cocok, dikombinasikan dengan `F.coalesce()`. |
| Data Valid Kosong | Syarat `.filter()` terlalu ketat atau tipe data salah (string vs float). | Cek schema tabel bronze. Cast nilai ke `float` sebelum operasi perbandingan `>`. |

---

### 6. Output Pertemuan 2
1. Notebook Praktikum: `P02_MentalHealth_DataQuality_Silver`
2. Tabel Quarantine Telemetri: `katalog_[nim].kesehatan_mental.quarantine_telemetri_remaja`
3. Tabel Silver Telemetri: `katalog_[nim].kesehatan_mental.silver_telemetri_remaja`
4. Tabel Silver Asesmen: `katalog_[nim].kesehatan_mental.silver_asesmen_remaja`
5. Tabel Silver Konseling: `katalog_[nim].kesehatan_mental.silver_konseling_remaja`
