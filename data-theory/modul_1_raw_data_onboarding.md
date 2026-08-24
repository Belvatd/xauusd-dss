# MODUL PRAKTIKUM 1
## Raw Data Onboarding & Bronze Layer Formulation
**CSV → Unity Catalog Volume → Bronze Delta Table**

| Informasi | Detail |
| :--- | :--- |
| **Platform** | Databricks Free Edition (dengan dukungan Unity Catalog) |
| **Kasus** | Early Warning System Kesehatan Mental Remaja DKI Jakarta |
| **Sasaran** | Praktikan (Mahasiswa) |
| **Versi** | Agustus 2026 |

---

### 1. Informasi Teknis
| Komponen | Keterangan |
| :--- | :--- |
| **Notebook** | `P01_MentalHealth_Ingestion_Bronze` |
| **Input** | 3 File Dataset CSV (Telemetri, Asesmen, Konseling) @100.000 rows |
| **Output** | `katalog_[nim].kesehatan_mental.bronze_telemetri_remaja`, dll. |
| **Durasi** | ±120 menit |
| **Bahasa** | Python (PySpark) dan SQL |

### 1.0 Latar Belakang & Narasi Studi Kasus

#### 🏛️ Konteks & Permasalahan Faktual
Di DKI Jakarta, fenomena gaya hidup digital *always-on* di kalangan remaja dan generasi muda (usia 12–24 tahun) memicu tantangan kesehatan masyarakat yang serius. Kombinasi antara **durasi layar harian yang tinggi (*high screen time*)**, **penggunaan media sosial hingga larut malam**, serta **kualitas tidur yang buruk** berkorelasi kuat dengan peningkatan kasus kecemasan (*anxiety*) dan depresi. Selain faktor digital, tekanan akademik ujian sekolah, perundungan siber (*cyberbullying*), dan masalah keuangan keluarga menjadi pemicu utama krisis mental.

Selama ini, penanganan kesehatan mental di masyarakat bersifat **pasif**—pemerintah baru mengetahui ada warga yang krisis ketika mereka sudah dalam kondisi parah dan datang sendiri ke Puskesmas atau Rumah Sakit Jiwa (RSJ). Oleh karena itu, **Dinas Kesehatan DKI Jakarta** berinisiatif membangun **Early Warning System (EWS) Kesehatan Mental** berbasis data terintegrasi. Sistem ini bertujuan mendeteksi indikasi krisis remaja secara dini agar intervensi tele-konseling sebaya dan rujukan medis cepat dapat dilakukan sebelum terlambat.

#### 📊 3 Sumber Data Utama (Total 300.000 Baris Data Mentah)
Dalam studi kasus ini, Anda berperan sebagai **Junior Data Engineer di Dinas Kesehatan DKI Jakarta**. Anda diberikan akses ke 3 file dataset CSV mentah (masing-masing 100.000 baris, total 300.000 baris) yang mewakili 3 pilar data kesehatan mental remaja:

1. **`telemetri_digital_remaja.csv` (Data Perilaku Digital)**: Log otomatis penggunaan perangkat, durasi layar, waktu media sosial malam, durasi tidur, dan tipe perangkat.
2. **`asesmen_psikologis_remaja.csv` (Data Kuesioner Medis)**: Hasil evaluasi psikologis mandiri mencakup skor kecemasan GAD-7 (0–21), skor depresi PHQ-9 (0–27), faktor stres utama, dan kelompok usia.
3. **`konseling_intervensi_sebaya.csv` (Data Layanan Kesehatan)**: Sesi tele-konseling dengan konselor sebaya mencakup topik konseling, skor kepuasan, analisis sentimen pesan, dan keputusan rujukan medis ke Puskesmas/RSJ.

#### 🎯 Tugas Anda pada Modul 1
Tugas pertama Anda adalah mengonfigurasi infrastruktur **Unity Catalog** (`katalog_[nim].kesehatan_mental.raw_dataset`), mengunggah ketiga file CSV mentah ke Unity Catalog Volume, lalu membacanya menggunakan PySpark dengan skema data yang presisi (`StructType`) untuk disimpan ke dalam **Bronze Layer Delta Tables**.

---

### 1.1 Kamus Data (Data Dictionary)

Berikut adalah struktur dan penjelasan setiap kolom dari ketiga tabel sumber mentah (*raw datasets*):

#### A. Tabel 1: Telemetri Digital Remaja (`telemetri_digital_remaja.csv`)
| Nama Kolom | Tipe Data | Deskripsi / Penjelasan Kolom |
| :--- | :--- | :--- |
| `telemetri_id` | String | Identifier unik untuk setiap catatan log aktivitas telemetri harian. |
| `user_id` | String | Identifier unik pengguna/remaja (Plaintext PII - sensitif). |
| `timestamp` | String | Waktu perekaman data log telemetri oleh sistem perangkat. |
| `wilayah_jakarta` | String | Lokasi wilayah administratif pengguna di DKI Jakarta (misal: Jakarta Selatan). |
| `durasi_layar_jam` | Float | Total durasi layar perangkat aktif dalam satu hari (jam). |
| `penggunaan_medsos_malam_menit` | Integer | Durasi penggunaan media sosial di malam hari (22:00 - 04:00) dalam menit. |
| `durasi_tidur_jam` | Float | Estimasi total waktu tidur pengguna dalam satu hari (jam). |
| `indeks_kualitas_tidur` | Integer | Skor subjektif kualitas tidur (skala 1-10, 10 = sangat baik). |
| `aktivitas_fisik_menit` | Integer | Total durasi olahraga atau aktivitas fisik harian (menit). |
| `tipe_perangkat` | String | Jenis sistem operasi perangkat utama pengguna (Android / iOS). |

#### B. Tabel 2: Asesmen Psikologis Remaja (`asesmen_psikologis_remaja.csv`)
| Nama Kolom | Tipe Data | Deskripsi / Penjelasan Kolom |
| :--- | :--- | :--- |
| `asesmen_id` | String | Identifier unik untuk setiap lembar kuesioner asesmen mandiri. |
| `user_id` | String | Identifier unik pengguna/remaja (Plaintext PII - sensitif). |
| `tanggal_asesmen` | String | Tanggal pengisian kuesioner asesmen psikologis. |
| `kategori_usia` | String | Kelompok usia pengguna (Remaja Awal: 12-14, Remaja Akhir: 15-18, Dewasa Muda: 19-24). |
| `skor_gad7` | Integer | Skor skrining tingkat kecemasan Generalized Anxiety Disorder-7 (0-21). |
| `skor_phq9` | Integer | Skor skrining tingkat depresi Patient Health Questionnaire-9 (0-27). |
| `faktor_stres_utama` | String | Penyebab utama tekanan/stres (Akademik, Media Sosial, Keluarga, Bullying, dll.). |
| `tingkat_kecemasan` | String | Kategori klinis kecemasan (Rendah, Sedang, Tinggi, Sangat Tinggi). |
| `tingkat_depresi` | String | Kategori klinis depresi (Minimal, Ringan, Sedang, Berat). |
| `status_risiko_krisis` | String | Indikator tingkat risiko krisis kesehatan mental pengguna. |

#### C. Tabel 3: Konseling Intervensi Sebaya (`konseling_intervensi_sebaya.csv`)
| Nama Kolom | Tipe Data | Deskripsi / Penjelasan Kolom |
| :--- | :--- | :--- |
| `sesi_id` | String | Identifier unik untuk setiap sesi intervensi/konseling. |
| `user_id` | String | Identifier unik pengguna/remaja (Plaintext PII - sensitif). |
| `konselor_id` | String | Identifier unik konselor sebaya atau tenaga medis pendamping. |
| `tanggal_sesi` | String | Tanggal dilaksanakannya sesi konseling. |
| `modalitas_sesi` | String | Media komunikasi konseling (Chat Teks, Voice Call, Video Call, Tatap Muka). |
| `durasi_sesi_menit` | Integer | Durasi waktu berlangsungnya sesi konseling (menit). |
| `topik_utama_konseling` | String | Pokok pembahasan utama yang didiskusikan dalam sesi. |
| `skor_kepuasan_user` | Integer | Skor penilaian kepuasan pengguna terhadap sesi (skala 1-5). |
| `status_tindak_lanjut` | String | Keputusan pasca sesi (Selesai, Konseling Lanjutan, Rujukan Puskesmas/RSJ). |
| `skor_sentimen_pesan` | Float | Hasil analisis sentimen percakapan (-1.0 sangat negatif hingga +1.0 positif). |

### 2. Tujuan Teknis
1. Memahami perbedaan antara *Create/Modify table* dan *Upload files to volume* di Databricks.
2. Mengunggah file CSV mentah ke dalam *Volume* di Unity Catalog.
3. Mendefinisikan schema eksplist (StructType) untuk optimasi pembacaan data.
3. Membaca dataset skala besar menjadi Spark DataFrame.
4. Menambahkan metadata *ingestion* (`ingested_at`, `file_source`).
5. Menyimpan DataFrame sebagai Bronze Delta Table yang *persistent* di dalam Unity Catalog Schema yang baru dibuat.

### 3. Langkah-Langkah Praktikum

#### 3.1 Perbedaan Metode Ingestion Databricks
Sebelum mengunggah, penting untuk memahami dua opsi yang disediakan oleh Databricks di menu Data Ingestion:

- **Create or modify table**: Digunakan jika data sudah bersih dan siap diubah langsung menjadi tabel SQL terkelola (*managed table*). Sangat instan, namun mem-bypass proses transformasi (*wrangling*).
- **Upload to a Volume in Unity Catalog**: Menyimpan file mentah (seperti `.csv`, `.json`, gambar) ke dalam penyimpanan berbasis *cloud object storage* yang dikelola oleh Databricks. Ini adalah opsi terbaik untuk membangun arsitektur Medallion (Bronze Layer) karena memungkinkan kita membaca data mentah tersebut dengan PySpark untuk *data wrangling*.

#### 3.2 Memahami Hierarki Unity Catalog (Catalog, Schema, Volume)
Saat Anda akan menyimpan file mentah, Anda perlu memahami hierarki penyimpanan 3-tingkat (3-level namespace) di Unity Catalog:

- **Catalog**: Level tertinggi (wadah utama). Mirip seperti *hard drive* atau environment proyek (Contoh: `main` atau `workspace`).
- **Schema (Database)**: Sub-kategori di dalam Catalog yang berfungsi mengelompokkan aset secara logis berdasarkan divisi/proyek (Contoh: `default` atau `klinis_remaja`).
- **Volume**: Direktori penyimpanan khusus di dalam Schema yang dirancang untuk menyimpan file *unstructured/semi-structured* secara fisik (seperti CSV, PDF, Gambar, Audio). Berbeda dengan *Table*, file di dalam Volume belum bisa di-query dengan SQL sebelum diproses (di-ingest).

#### 3.3 Upload Dataset ke Unity Catalog Volume
1. Buka workspace Databricks. Pilih menu **New** -> **Data Ingestion** (atau melalui menu **Catalog** -> **Add Data**).
2. Pilih menu **Upload to a Volume in Unity Catalog**.
3. Pada *dialog box* "Upload files to a Volume in Unity Catalog", *drag and drop* atau *browse* ketiga file CSV (`asesmen_psikologis_remaja.csv`, `konseling_intervensi_sebaya.csv`, `telemetri_digital_remaja.csv`).
4. Pada bagian **Destination volume**, klik kolom *Search by volume, catalog, or schema name* lalu klik **+ Create volume**.
5. Pada jendela "Create a new volume", buat struktur dari awal dengan standar penamaan berikut:
   - **Catalog**: Klik dropdown *Select a catalog*, gulir ke bawah, lalu klik **+ Create a new catalog**.
     - Pada jendela *Create a new catalog*, masukkan **Catalog name**: `katalog_[nim_anda]` (contoh: `katalog_123456`).
     - Pastikan kotak **Storage location** tercentang pada opsi *Use default storage*.
     - Klik tombol **Create catalog**.
   - **Schema**: Setelah katalog terbuat, klik dropdown *Select a schema*, gulir ke bawah, lalu klik **+ Create a new schema**. Beri nama skema `kesehatan_mental`.
   - **Volume name**: Ketik `raw_dataset` (pilih tipe *Managed volume*).
   - Terakhir, klik tombol **Create**.
6. Setelah kembali ke menu awal dan *Destination volume* terisi dengan format `katalog_[nim].kesehatan_mental.raw_dataset`, klik tombol **Upload**.

#### 3.4 Proses Ingestion ke Bronze Layer (Per Dataset)
Buat notebook baru `P01_MentalHealth_Ingestion_Bronze`. Di notebook ini, kita akan mendefinisikan *schema* dan membaca file dari *Volume* ke dalam DataFrame secara bertahap.

**A. Setup Library PySpark**
Jalankan *cell* pertama ini untuk mengimpor pustaka yang dibutuhkan:
```python
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType
from pyspark.sql import functions as F
```

**B. Ingestion Dataset Telemetri**
Pada *cell* berikutnya, jalankan kode berikut:
```python
# 1. Definisi Schema Telemetri
schema_telemetri = StructType([
    StructField("telemetri_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("wilayah_jakarta", StringType(), True),
    StructField("durasi_layar_jam", FloatType(), True),
    StructField("penggunaan_medsos_malam_menit", IntegerType(), True),
    StructField("durasi_tidur_jam", FloatType(), True),
    StructField("indeks_kualitas_tidur", IntegerType(), True),
    StructField("aktivitas_fisik_menit", IntegerType(), True),
    StructField("tipe_perangkat", StringType(), True)
])

# 2. Ingestion dengan Schema Eksplisit (Dari Unity Catalog Volume)
# Ganti [nim] dengan NIM Anda sesuai nama katalog yang dibuat
path_telemetri = "/Volumes/katalog_[nim]/kesehatan_mental/raw_dataset/telemetri_digital_remaja.csv"
df_raw_telemetri = spark.read.option("header", "true").schema(schema_telemetri).csv(path_telemetri)

# 3. Penambahan Metadata dan Simpan ke Bronze Layer
# Tambahkan informasi audit/tracking untuk melacak kapan data masuk
df_bronze_telemetri = df_raw_telemetri \
    .withColumn("ingested_at", F.current_timestamp()) \
    .withColumn("file_source", F.col("_metadata.file_path"))

# Simpan sebagai Delta Table
df_bronze_telemetri.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("katalog_[nim].kesehatan_mental.bronze_telemetri_remaja")

display(spark.table("katalog_[nim].kesehatan_mental.bronze_telemetri_remaja").limit(5))
```

**C. Ingestion Dataset Asesmen Psikologis**
Pada *cell* baru, jalankan kode ini:
```python
# 1. Definisi Schema Asesmen
schema_asesmen = StructType([
    StructField("asesmen_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("tanggal_asesmen", StringType(), True),
    StructField("kategori_usia", StringType(), True),
    StructField("skor_gad7", IntegerType(), True),
    StructField("skor_phq9", IntegerType(), True),
    StructField("faktor_stres_utama", StringType(), True),
    StructField("tingkat_kecemasan", StringType(), True),
    StructField("tingkat_depresi", StringType(), True),
    StructField("status_risiko_krisis", StringType(), True)
])

# 2. Baca dari Volume & Tambah Metadata
path_asesmen = "/Volumes/katalog_[nim]/kesehatan_mental/raw_dataset/asesmen_psikologis_remaja.csv"
df_bronze_asesmen = spark.read.option("header", "true").schema(schema_asesmen).csv(path_asesmen) \
    .withColumn("ingested_at", F.current_timestamp()) \
    .withColumn("file_source", F.col("_metadata.file_path"))

# 3. Simpan sebagai Bronze Delta Table
df_bronze_asesmen.write.format("delta").mode("overwrite") \
    .saveAsTable("katalog_[nim].kesehatan_mental.bronze_asesmen_remaja")
```

**D. Ingestion Dataset Konseling Sebaya**
Pada *cell* baru terakhir, jalankan kode ini:
```python
# 1. Definisi Schema Konseling
schema_konseling = StructType([
    StructField("sesi_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("konselor_id", StringType(), True),
    StructField("tanggal_sesi", StringType(), True),
    StructField("modalitas_sesi", StringType(), True),
    StructField("durasi_sesi_menit", IntegerType(), True),
    StructField("topik_utama_konseling", StringType(), True),
    StructField("skor_kepuasan_user", IntegerType(), True),
    StructField("status_tindak_lanjut", StringType(), True),
    StructField("skor_sentimen_pesan", FloatType(), True)
])

# 2. Baca dari Volume & Tambah Metadata
path_konseling = "/Volumes/katalog_[nim]/kesehatan_mental/raw_dataset/konseling_intervensi_sebaya.csv"
df_bronze_konseling = spark.read.option("header", "true").schema(schema_konseling).csv(path_konseling) \
    .withColumn("ingested_at", F.current_timestamp()) \
    .withColumn("file_source", F.col("_metadata.file_path"))

# 3. Simpan sebagai Bronze Delta Table
df_bronze_konseling.write.format("delta").mode("overwrite") \
    .saveAsTable("katalog_[nim].kesehatan_mental.bronze_konseling_remaja")
```

### 4. Hasil dan Verifikasi
Pastikan tabel Bronze telah terbuat di metastore dan jumlah baris sesuai:
```sql
%sql
DESCRIBE DETAIL katalog_[nim].kesehatan_mental.bronze_telemetri_remaja;
SELECT COUNT(*) FROM katalog_[nim].kesehatan_mental.bronze_telemetri_remaja; -- Harus bernilai 100000
```

### 5. Troubleshooting
| Indikasi Error | Penyebab | Solusi |
| :--- | :--- | :--- |
| `AnalysisException: Path does not exist` | Salah pengetikan path file CSV di Volume. | Buka menu *Catalog* -> *Volumes*, salin *path* absolut file secara langsung (biasanya `/Volumes/catalog/schema/volume/nama_file.csv`). |
| `ParseException: mismatched input` | Kesalahan penulisan nama database/katalog. | Pastikan menggunakan format tiga tingkat `katalog_[nim].kesehatan_mental.nama_table` pada fungsi `saveAsTable`. |

---

### 6. Output Pertemuan 1
1. Notebook Praktikum: `P01_MentalHealth_Ingestion_Bronze`
2. Unity Catalog Volume: `katalog_[nim].kesehatan_mental.raw_dataset`
3. Tabel Bronze Telemetri: `katalog_[nim].kesehatan_mental.bronze_telemetri_remaja`
4. Tabel Bronze Asesmen: `katalog_[nim].kesehatan_mental.bronze_asesmen_remaja`
5. Tabel Bronze Konseling: `katalog_[nim].kesehatan_mental.bronze_konseling_remaja`
