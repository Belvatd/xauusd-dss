---
tags: [data-engineering]
---

# MODUL PRAKTIKUM 4
## Pipeline Automation & Workflow Orchestration
**Otomatisasi Pipeline Data: Parameterized Notebooks → SQL Batch → Validasi Lintas Layer → Databricks Jobs**

| Informasi | Detail |
| :--- | :--- |
| **Platform** | Databricks Free Edition |
| **Kasus** | Early Warning System Kesehatan Mental Remaja DKI Jakarta |
| **Sasaran** | Praktikan (Mahasiswa) |
| **Versi** | Agustus 2026 |

---

### 1. Informasi Teknis
| Komponen | Keterangan |
| :--- | :--- |
| **Notebook SQL Batch** | `P04_MentalHealth_SQL_Batch` |
| **Validation Notebook** | `P04_MentalHealth_Pipeline_Validation` |
| **Job (Workflow)** | `J04_MentalHealth_Lakehouse_Workflow` |
| **Input Data** | Tabel Bronze, Silver, dan Gold (`katalog_[nim].kesehatan_mental.*`) |
| **Output Utama** | Tiga Delta Tables hasil batch (`pipeline_demo_*`) dan Status Validasi Job (PASS/FAIL) |
| **Durasi** | ±180 menit |
| **Bahasa** | Python (PySpark), SQL, dan Databricks Utilities (`dbutils`) |

---

### 2. Tujuan Pembelajaran
Setelah menyelesaikan modul ini, Anda diharapkan mampu:

1. Memahami konsep otomatisasi *Data Pipeline* dan penjadwalan *Job* pada Databricks.
2. Membuat Notebook yang dinamis menggunakan parameter (*Parameterized Notebook*).
3. Menjalankan pemrosesan data secara kolektif menggunakan kueri *SQL Batch*.
4. Membangun skrip penguji (*Validation Notebook*) untuk memastikan keutuhan data lintas tabel.
5. Membangun dan mengelola aliran tugas (*Workflow*) menggunakan fitur **Databricks Jobs**, serta menangani kegagalan eksekusi (*Repair Run*).

---

### 3. Penjelasan Istilah Teknis (Glosarium Sederhana)

Sebelum memulai praktikum, pahami istilah-istilah penting berikut:

| Istilah Teknis | Penjelasan Sederhana & Analogi |
| :--- | :--- |
| **Data Pipeline** | **Pipa Aliran Data**: Urutan langkah otomatis untuk mengalirkan data mentah (Bronze), membersihkannya (Silver), hingga menyajikannya menjadi laporan siap pakai (Gold). |
| **Databricks Job / Workflow** | **Jadwal Kerja Otomatis**: Fitur di Databricks yang bertugas menjalankan beberapa Notebook secara otomatis sesuai urutan yang sudah ditentukan, tanpa perlu diklik manual satu per satu. |
| **Parameterized Notebook** | **Notebook Dinamis**: Notebook yang kodenya bisa menerima variabel masukan dari luar (seperti nama kota atau tanggal), sehingga kodenya fleksibel dan tidak perlu diubah-ubah. |
| **SQL Batch Processing** | **Pemrosesan Data Sekaligus**: Metode mengolah data dalam jumlah besar secara sekaligus (dalam satu gelombang) menggunakan perintah SQL. |
| **Validation Notebook** | **Skrip Pemeriksa Kualitas**: Notebook khusus yang berfungsi sebagai "satpam" untuk mengecek apakah jumlah baris atau nilai data di akhir alur sudah sesuai dengan data awal. |
| **Task & Dependency** | **Tugas & Ketergantungan**: *Task* adalah unit kerja (misal: satu notebook). *Dependency* adalah aturan urutan, di mana Task B baru boleh berjalan setelah Task A selesai dengan sukses. |
| **Repair Run** | **Jalan Ulang Perbaikan**: Fitur untuk menjalankan kembali *Job* yang sempat gagal, hanya pada bagian yang rusak saja, tanpa mengulang dari awal. |

---

### 4. Langkah-Langkah Praktikum

#### 4.1 Menyiapkan Parameter pada Notebook (`P04_MentalHealth_SQL_Batch`)

Buat Notebook baru bernama `P04_MentalHealth_SQL_Batch` dengan bahasa default **Python**.

Agar Notebook dapat menerima parameter masukan dari *Job*, kita menggunakan perintah `dbutils.widgets`. Ketik kode berikut pada sel pertama:

```python
# 1. Perintah membuat fungsi pengambil parameter otomatis
def get_parameter(parameter_name, default_value):
    try:
        return dbutils.widgets.get(parameter_name)
    except Exception:
        dbutils.widgets.text(parameter_name, str(default_value))
        return dbutils.widgets.get(parameter_name)

# 2. Mengambil parameter catalog, schema, dan wilayah target
catalog_name = get_parameter("catalog_name", "katalog_[nim]") # Ganti [nim] dengan NIM Anda
schema_name = get_parameter("schema_name", "kesehatan_mental")
target_wilayah = get_parameter("target_wilayah", "Jakarta Selatan")

print(f"✅ Parameter Terpasang:")
print(f"   - Catalog Target : {catalog_name}")
print(f"   - Schema Target  : {schema_name}")
print(f"   - Wilayah Target : {target_wilayah}")
```

---

#### 4.2 Pemrosesan SQL Batch (SQL Batch Processing)

Ubah bahasa sel menjadi **SQL** (`%sql`) untuk menjalankan transformasi data secara bertahap.

##### Sel 1: Menentukan Konteks Katalog dan Skema
```sql
%sql
USE CATALOG katalog_[nim];
USE SCHEMA kesehatan_mental;
```

##### Sel 2: Batch 1 — Menyaring Data Valid ke Tabel Silver Baru (`pipeline_demo_silver_valid`)
```sql
%sql
CREATE OR REPLACE TABLE katalog_[nim].kesehatan_mental.pipeline_demo_silver_valid
USING DELTA
AS
SELECT
    t.telemetri_id,
    t.user_id_masked,
    t.wilayah_jakarta,
    CAST(t.durasi_layar_jam AS FLOAT) AS durasi_layar_jam,
    CAST(t.penggunaan_medsos_malam_menit AS INT) AS penggunaan_medsos_malam_menit,
    CAST(t.durasi_tidur_jam AS FLOAT) AS durasi_tidur_jam,
    CAST(t.indeks_kualitas_tidur_clean AS INT) AS indeks_kualitas_tidur_clean,
    t.tipe_perangkat,
    t.timestamp_clean
FROM katalog_[nim].kesehatan_mental.silver_telemetri_remaja t
WHERE t.durasi_layar_jam <= 18.0; -- Menyaring data wajar (durasi layar di bawah 18 jam)
```

##### Sel 3: Batch 2 — Menghitung Agregasi Performa Wilayah (`pipeline_demo_wilayah_performance`)
```sql
%sql
CREATE OR REPLACE TABLE katalog_[nim].kesehatan_mental.pipeline_demo_wilayah_performance
USING DELTA AS
SELECT 
    wilayah_jakarta,
    COUNT(DISTINCT user_id_masked) AS total_remaja_terdaftar,
    ROUND(AVG(durasi_layar_jam), 2) AS avg_durasi_layar_jam,
    ROUND(AVG(penggunaan_medsos_malam_menit), 1) AS avg_medsos_malam_menit
FROM katalog_[nim].kesehatan_mental.pipeline_demo_silver_valid
GROUP BY wilayah_jakarta;
```

##### Sel 4: Batch 3 — Menghitung Agregasi Faktor Stres (`pipeline_demo_stressor_performance`)
```sql
%sql
CREATE OR REPLACE TABLE katalog_[nim].kesehatan_mental.pipeline_demo_stressor_performance
USING DELTA AS
SELECT 
    a.faktor_stres_utama,
    COUNT(a.asesmen_id) AS total_kasus,
    ROUND(AVG(a.total_skor_kombinasi), 2) AS avg_skor_krisis
FROM katalog_[nim].kesehatan_mental.silver_asesmen_remaja a
GROUP BY a.faktor_stres_utama;
```

##### Sel 5: Batch 4 — Verifikasi Jumlah Baris Hasil Batch
```sql
%sql
SELECT 'Pipeline Silver Valid' AS nama_tabel, COUNT(*) AS total_baris FROM katalog_[nim].kesehatan_mental.pipeline_demo_silver_valid
UNION ALL
SELECT 'Pipeline Wilayah Summary' AS nama_tabel, COUNT(*) AS total_baris FROM katalog_[nim].kesehatan_mental.pipeline_demo_wilayah_performance
UNION ALL
SELECT 'Pipeline Stressor Summary' AS nama_tabel, COUNT(*) AS total_baris FROM katalog_[nim].kesehatan_mental.pipeline_demo_stressor_performance;
```

> **💡 Mengapa Menggunakan `CREATE OR REPLACE TABLE` di Notebook `P04_MentalHealth_SQL_Batch`?**  
> Notebook batch ini dirancang untuk dijalankan secara berulang-ulang (*re-run*) oleh Databricks Job. Jika menggunakan `INSERT INTO`, data baru akan terus ditumpuk di bawah data lama sehingga jumlah baris membengkak dari 100.000 menjadi 200.000, 300.000, dst. Menggunakan `CREATE OR REPLACE TABLE ... USING DELTA AS SELECT ...` menjamin bahwa setiap kali Job berjalan, data lama akan **di-overwrite secara bersih** sehingga jumlah data tetap stabil.

> **⚠️ Penting — Penanganan Error `TABLE_OR_VIEW_NOT_FOUND`:**  
> Jika Anda lupa mencantumkan namespace tiga tingkat (`katalog_[nim].kesehatan_mental.nama_tabel`), Databricks secara default akan mencari tabel di katalog `workspace.default`. Hal ini menyebabkan error `[TABLE_OR_VIEW_NOT_FOUND] The table or view ... cannot be found`. Selalu gunakan format tiga tingkat atau jalankan sel `USE CATALOG` dan `USE SCHEMA` di awal sesi.

---

#### 4.3 Membuat Notebook Validasi (`P04_MentalHealth_Pipeline_Validation`)

Buat Notebook baru bernama `P04_MentalHealth_Pipeline_Validation` dengan bahasa **Python**. 

Notebook ini bertindak sebagai "pemeriksa otomatis". Jika jumlah data di akhir alur tidak sesuai dengan target, Notebook akan memunculkan pesan error (*ValueError*) untuk menghentikan aliran *Job*.

```python
# 1. Definisi fungsi helper pengambil parameter (Wajib disalin di Notebook baru ini)
def get_parameter(parameter_name, default_value):
    try:
        return dbutils.widgets.get(parameter_name)
    except Exception:
        dbutils.widgets.text(parameter_name, str(default_value))
        return dbutils.widgets.get(parameter_name)

# 2. Mengambil parameter ekspektasi jumlah baris
catalog_name = get_parameter("catalog_name", "katalog_[nim]")
schema_name = get_parameter("schema_name", "kesehatan_mental")
expected_rows = int(get_parameter("expected_rows", "100000"))

def get_table_path(table_name):
    return f"{catalog_name}.{schema_name}.{table_name}"

# 3. Daftar pemeriksaan integritas data lintas layer
checks = [
    ("Bronze Telemetri Rows", expected_rows, spark.table(get_table_path("bronze_telemetri_remaja")).count()),
    ("Bronze Asesmen Rows", expected_rows, spark.table(get_table_path("bronze_asesmen_remaja")).count()),
    ("Bronze Konseling Rows", expected_rows, spark.table(get_table_path("bronze_konseling_remaja")).count()),
]

# 4. Mengeksekusi pengujian dan menampilkan hasil PASS / FAIL
failed_checks = []
for check_name, expected_val, actual_val in checks:
    status = "PASS" if expected_val == actual_val else "FAIL"
    print(f"[{status}] | {check_name} | Target: {expected_val} | Hasil Nyata: {actual_val}")
    if status == "FAIL":
        failed_checks.append(check_name)

# 5. Hentikan Job jika ada pemeriksaan yang FAIL
if failed_checks:
    raise ValueError(f"❌ Validasi Pipeline Gagal pada komponen: {', '.join(failed_checks)}")
else:
    print("🎉 Seluruh pemeriksaan data LULUS (PASS)! Pipeline aman.")
```

---

#### 4.4 Merangkai Databricks Job / Workflow (`J04_MentalHealth_Lakehouse_Workflow`)

1. Pada menu di sebelah kiri Databricks, klik **Workflows** (atau **Jobs**), lalu klik tombol **Create Job**.
2. Beri nama Job pada bagian kiri atas: **`J04_MentalHealth_Lakehouse_Workflow`**.
3. Tambahkan 5 Tugas (*Tasks*) sesuai urutan ketergantungan berikut:

| Nama Task | Tipe Task | Path Notebook Target | Ketergantungan (*Depends On*) |
| :--- | :--- | :--- | :--- |
| `01_ingest_bronze` | Notebook | `P01_MentalHealth_Ingestion_Bronze` | — *(Tugas Pertama)* |
| `02_build_silver` | Notebook | `P02_MentalHealth_DataQuality_Silver` | `01_ingest_bronze` |
| `02b_sql_batch` | Notebook | `P04_MentalHealth_SQL_Batch` | `01_ingest_bronze` |
| `03_build_gold` | Notebook | `P03_MentalHealth_Gold_Analytics` | `02_build_silver` |
| `04_validate_outputs` | Notebook | `P04_MentalHealth_Pipeline_Validation` | `03_build_gold` DAN `02b_sql_batch` |

4. Pada panel kanan di bagian **Job Parameters**, tambahkan parameter berikut:
   - `catalog_name`: `katalog_[nim]`
   - `schema_name`: `kesehatan_mental`
   - `expected_rows`: `100000`

##### Simulasi Kegagalan & Perbaikan (*Repair Run*):
- Klik tombol **Run Now** untuk menguji eksekusi alur secara menyeluruh.
- **Simulasi Gagal**: Ubah nilai parameter `expected_rows` dari `100000` menjadi `100001`. Jalankan Job kembali. Amatilah bahwa Task `04_validate_outputs` akan berwarna merah (*Failed*) karena jumlah data tidak sesuai.
- **Perbaikan (*Repair Run*)**: Kembalikan nilai `expected_rows` menjadi `100000`, lalu klik tombol **Repair Run**. Databricks hanya akan mengulang Task yang gagal tanpa perlu mengulang Task awal yang sudah sukses.

---

#### 4.5 Peninjauan Kode dengan Databricks Assistant di Notebook `P04_MentalHealth_SQL_Batch`

Gunakan fitur AI (**Databricks Assistant**) langsung pada sel-sel spesifik di Notebook `P04_MentalHealth_SQL_Batch` untuk meninjau dan memverifikasi kualitas kode sebelum dieksekusi oleh *Job*:

1. **Uji pada Sel 2 (Batch 1 — Pemfilteran Data Valid `pipeline_demo_silver_valid`)**:
   - Klik pada **Sel 2** yang berisi kueri `CREATE TABLE ... WHERE durasi_layar_jam <= 18.0`.
   - Tekan pintasan `Cmd + I` (Mac) / `Ctrl + I` (Windows) atau klik ikon ✨ **Assistant** pada sel tersebut.
   - Ketik **Prompt 1 (Penjelasan Alur Batch 1)**:  
     > *"Jelaskan input tabel sumber, syarat pemfilteran durasi_layar_jam <= 18.0, serta kolom output pada sel SQL Batch 1 ini secara singkat. Jangan mengubah atau menjalankan kode."*

2. **Uji pada Sel 3 (Batch 2 — Agregasi Performa Wilayah `pipeline_demo_wilayah_performance`)**:
   - Klik pada **Sel 3** yang berisi kueri `GROUP BY wilayah_jakarta`.
   - Buka Databricks Assistant pada sel tersebut, lalu ketik **Prompt 2 (Audit Logika Agregasi)**:  
     > *"Periksa apakah kueri pada sel ini sudah benar menggunakan COUNT(DISTINCT user_id_masked) untuk menghitung total remaja terdaftar per wilayah Jakarta."*

3. **Uji pada Sel 5 (Batch 4 — Verifikasi Jumlah Baris Hasil Batch)**:
   - Klik pada **Sel 5** yang berisi kueri `UNION ALL`.
   - Ketik **Prompt 3 (Pemeriksaan & Perbaikan Sintaks SQL)**:  
     > *"Periksa apakah kueri UNION ALL pada sel ini sudah menggunakan nama catalog dan schema tiga tingkat (katalog_[nim].kesehatan_mental.*) secara benar agar tidak mengalami error TABLE_OR_VIEW_NOT_FOUND."*

---

### 5. Troubleshooting (Penanganan Masalah Umum)

| Masalah / Kendala | Penyebab | Solusi / Cara Mengatasi |
| :--- | :--- | :--- |
| **Error `NameError: name 'get_parameter' is not defined`** | Fungsi `get_parameter` dibuat di Notebook pertama (`P04_MentalHealth_SQL_Batch`) tetapi belum didefinisikan di Notebook baru (`P04_MentalHealth_Pipeline_Validation`). Setiap Notebook di Databricks berjalan pada konteks memori terpisah. | Salin kembali fungsi pendefinisian `def get_parameter(...)` ke sel pertama Notebook baru `P04_MentalHealth_Pipeline_Validation`. |
| **Error `[TABLE_OR_VIEW_NOT_FOUND] The table or view ... cannot be found`** | Kueri SQL dipanggil tanpa nama catalog dan schema (sehingga Databricks mencarinya di `workspace.default`), atau sel Batch 3 belum dieksekusi. | Tuliskan nama tabel secara lengkap dengan format tiga tingkat: `katalog_[nim].kesehatan_mental.pipeline_demo_stressor_performance`, atau pastikan sel `USE CATALOG` dan `USE SCHEMA` sudah di-run di awal sesi. |
| **Parameter Job Tidak Terbaca** | Penulisan nama parameter di *Job Parameters* berbeda besar-kecil hurufnya dengan kode `dbutils.widgets.get()`. | Pastikan penulisan nama parameter di panel Job dan di dalam Notebook sama persis (misal: `catalog_name`). |
| **Jumlah Data Terus Bertambah Saat Re-run** | Menggunakan perintah `INSERT INTO` alih-alih `CREATE OR REPLACE TABLE` di Notebook `P04_MentalHealth_SQL_Batch` (Sel 2, 3, 4). | Gunakan `CREATE OR REPLACE TABLE ... USING DELTA` agar tabel lama digantikan dengan data baru secara bersih setiap kali Job di-run. |

---

### 6. Output Pertemuan 4
1. Notebook Batch: `P04_MentalHealth_SQL_Batch`
2. Notebook Validasi: `P04_MentalHealth_Pipeline_Validation`
3. Job Workflow Resmi: `J04_MentalHealth_Lakehouse_Workflow`
4. Tabel Hasil Batch Dinamis: `pipeline_demo_silver_valid`, `pipeline_demo_wilayah_performance`, `pipeline_demo_stressor_performance`
