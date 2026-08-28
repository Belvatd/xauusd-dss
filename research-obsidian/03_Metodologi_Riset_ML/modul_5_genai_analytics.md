---
tags: [metodologi-riset-ml]
---

# MODUL PRAKTIKUM 5
## Genie Agent dan Natural-Language Analytics
**Eksplorasi Data Bahasa Alami: Business View → Genie Agent Configuration (About, Sources, Instructions, Examples) → Benchmark Evaluation**

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
| **Notebook Preparation** | `P05_MentalHealth_Genie_Preparation` |
| **Business View** | `katalog_[nim].kesehatan_mental.genie_mentalhealth_business_view` |
| **Genie Agent** | `GA05_MentalHealth_Business_Analyst` |
| **Benchmark Suite** | `BM05_MentalHealth_Core_Questions` |
| **Input Table** | `katalog_[nim].kesehatan_mental.gold_mentalhealth_dashboard_detail` |
| **Durasi** | ±180 menit |
| **Bahasa** | SQL, Python, dan Bahasa Alami (*Natural Language*) |

---

### 2. Tujuan Pembelajaran
Setelah menyelesaikan modul ini, Anda diharapkan mampu:

1. Memahami konsep eksplorasi data berbasis bahasa alami (*Natural Language Analytics / Chat with Data*).
2. Membuat tampilan data kontekstual (*Business View*) khusus untuk konsumsi agen AI.
3. Mengonfigurasi 4 Tab Databricks Genie UI: **About**, **Sources**, **Instructions**, dan **Examples**.
4. Memahami fungsi masing-masing tab konfigurasi untuk mengajari AI tentang kamus kata kunci, aturan bisnis, dan kueri terpercaya (*Trusted Queries*).
5. Membangun dan menguji **Benchmark Evaluation Suite** untuk mengukur tingkat akurasi kueri yang dihasilkan AI (*Generated SQL*).

---

### 3. Penjelasan Istilah Teknis (Glosarium Sederhana)

Sebelum memulai praktikum, pahami istilah-istilah penting berikut:

| Istilah Teknis | Penjelasan Sederhana & Analogi |
| :--- | :--- |
| **Genie Agent (Genie Space)** | **Asisten AI Analisis Data**: Agen kecerdasan buatan di Databricks yang dapat menerima pertanyaan dalam bahasa sehari-hari (Bahasa Indonesia), lalu otomatis mengubahnya menjadi perintah SQL untuk mengambil data. |
| **Business View (Semantic View)** | **Tampilan Data Siap-Tanya**: *View SQL* khusus yang memilih dan merapikan kolom-kolom tabel Gold agar fokus dan mudah dipahami oleh mesin kecerdasan buatan. |
| **Tab "About"** | **Identitas Agent**: Tab tempat mengisi nama dan deskripsi peran utama dari agen AI. |
| **Tab "Sources"** | **Sumber Data & Kamus Kata**: Tab untuk mendaftarkan tabel/view sumber serta kata sinonim (misal: "gadget" = `durasi_layar_jam`). |
| **Tab "Instructions"** | **Aturan Main AI**: Tab untuk memasukkan instruksi umum mengenai batasan logika bisnis, format bahasa, dan rumus perhitungan resmi. |
| **Tab "Examples"** | **Contoh Soal & Kunci Jawaban**: Tab untuk memasukkan kueri SQL contoh (*Curated Examples*) dan kueri terpercaya (*Trusted Queries*) agar AI meniru rumus yang 100% akurat. |
| **Generated SQL** | **Kueri SQL Buatan AI**: Perintah SQL yang dirangkai secara otomatis oleh AI berdasarkan pertanyaan bahasa alami yang diajukan oleh pengguna. |
| **Benchmark Evaluation Suite** | **Ujian Kelulusan AI**: Kumpulan pertanyaan standar beserta kunci jawaban nilai ekspektasinya untuk menguji apakah jawaban AI sudah konsisten dan akurat. |

---

### 4. Prasyarat & Catatan Keamanan

#### Prasyarat
- Pertemuan 3 telah selesai dieksekusi dan menghasilkan tabel `gold_mentalhealth_dashboard_detail`.
- Serverless SQL Warehouse / Compute aktif.

#### Catatan Keamanan Databricks
> **⚠️ Catatan Keamanan Context:**  
> *Business View* berfungsi memusatkan konteks visualisasi untuk Genie AI, tetapi **bukan batas keamanan data**. Pembatasan akses keamanan aktual tetap dilakukan melalui hak akses *Unity Catalog privileges*, *row-level filters*, dan *column masks*.

---

### 5. Langkah-Langkah Praktikum

#### 5.1 Pembuatan Business View (Notebook `P05_MentalHealth_Genie_Preparation`)

Jalankan skrip PySpark berikut untuk membuat *Business View* siap-pakai bagi AI Agent:

```python
from pyspark.sql import functions as F

catalog_name = "katalog_[nim]"
schema_name = "kesehatan_mental"

gold_detail = f"{catalog_name}.{schema_name}.gold_mentalhealth_dashboard_detail"
genie_view = f"{catalog_name}.{schema_name}.genie_mentalhealth_business_view"

spark.sql(f"""
CREATE OR REPLACE VIEW {genie_view} AS
SELECT
    telemetri_id,
    user_id_masked,
    wilayah_jakarta,
    durasi_layar_jam,
    penggunaan_medsos_malam_menit,
    durasi_tidur_jam,
    indeks_kualitas_tidur_clean,
    tipe_perangkat,
    kategori_usia,
    skor_gad7,
    skor_phq9,
    total_skor_kombinasi,
    faktor_stres_utama,
    tingkat_kecemasan_clean,
    tingkat_depresi_clean,
    status_risiko_krisis,
    modalitas_sesi,
    durasi_sesi_menit,
    topik_utama_konseling,
    skor_kepuasan_user,
    status_tindak_lanjut,
    skor_sentimen_clean,
    butuh_rujukan_medis,
    high_crisis_flag
FROM {gold_detail}
""")

# Verifikasi Jumlah Baris (Harus sama persis dengan jumlah data Gold Detail setelah pembersihan quarantine)
gold_count = spark.table(gold_detail).count()
view_count = spark.table(genie_view).count()
assert view_count == gold_count, f"Mismatch baris: View ({view_count}) != Gold ({gold_count})"
print(f"✅ Business View berhasil dibuat dan diverifikasi! Total baris valid: {view_count:,} baris.")
```

> **💡 Catatan Jumlah Baris Data Valid (91.635 Baris):**  
> Jumlah baris data pada tabel Gold dan Business View adalah **91.635 baris data medis lengkap**. Hal ini dikarenakan dari 100.000 baris mentah di Bronze, sebanyak **5.020 baris anomali** dipisahkan ke `quarantine_telemetri_remaja` pada Modul 2, dan sebanyak **3.345 log telemetri** yang tidak memiliki riwayat asesmen/konseling tereliminasi secara otomatis oleh operasi `INNER JOIN` pada Modul 3.

---

#### 5.2 Validasi Business View via SQL Analytics
Jalankan kueri SQL berikut untuk memvalidasi angka dasar sebelum dikonfigurasi ke Genie Agent:

```sql
%sql
SELECT 
    COUNT(DISTINCT user_id_masked) AS total_remaja_terdaftar,
    COUNT(DISTINCT CASE WHEN butuh_rujukan_medis = 1 THEN user_id_masked END) AS total_kasus_rujukan,
    COUNT(DISTINCT CASE WHEN high_crisis_flag = 1 THEN user_id_masked END) AS total_kasus_krisis_tinggi,
    ROUND(AVG(durasi_layar_jam), 2) AS avg_durasi_layar_jam,
    ROUND(AVG(skor_phq9), 2) AS avg_skor_depresi,
    ROUND(AVG(skor_gad7), 2) AS avg_skor_kecemasan
FROM katalog_[nim].kesehatan_mental.genie_mentalhealth_business_view;
```

---

#### 5.3 Konfigurasi Genie Agent Berdasarkan 4 Tab Databricks UI

Buka menu **Genie / AI Agents** di sidebar Databricks -> Klik **New Genie Space** -> Pilih data source `katalog_[nim].kesehatan_mental.genie_mentalhealth_business_view`.

Setelah Space terbuat, klik tombol **Edit Space / Settings** di sudut kanan atas untuk mengonfigurasi Agent melalui **4 Tab Utama Antarmuka Databricks**:

---

##### 📍 Tab 1: "About" (Informasi & Identitas Agent)
* **Fungsi & Kegunaan**: Mendefinisikan nama resmi, tujuan, dan gambaran peran utama dari agen AI agar pengguna memahami kapabilitasnya.
* **Langkah Konfigurasi UI**:
  - **Name**: `GA05_MentalHealth_Business_Analyst`
  - **Description**: *"Agent AI Analisis Kesehatan Mental Remaja DKI Jakarta yang bertugas menganalisis tren depresi, durasi layar harian, faktor stres dominan, dan tingkat rujukan medis ke Puskesmas."*

---

##### 📍 Tab 2: "Sources" (Sumber Data & Kamus Sinonim Kolom)
* **Fungsi & Kegunaan**: Menghubungkan *Business View* dan mengajari AI tentang **kamus kata kunci sehari-hari (Sinonim)**. Tanpa sinonim, AI tidak akan paham jika pengguna bertanya menggunakan istilah gaul/lokal seperti *"gadget"* atau *"pasien"*.
* **Langkah Konfigurasi UI**:
  1. Pastikan Data Source utama menunjuk ke: `katalog_[nim].kesehatan_mental.genie_mentalhealth_business_view`.
  2. Di bawah daftar kolom, klik masing-masing nama kolom untuk memasukkan deskripsi & kata sinonim:

| Nama Kolom Original | Deskripsi & Kata Sinonim untuk AI |
| :--- | :--- |
| `user_id_masked` | ID Remaja terenkripsi; sinonim: *Pengguna, Pasien, Remaja*. |
| `wilayah_jakarta` | Wilayah adm. DKI Jakarta (*Jakarta Selatan, Timur, Pusat, Barat, Utara*). |
| `durasi_layar_jam` | Screen time harian (jam); sinonim: *Penggunaan Gadget, Durasi Layar, Screen Time*. |
| `skor_phq9` | Skor depresi kuesioner PHQ-9 (skala 0–27). |
| `skor_gad7` | Skor kecemasan kuesioner GAD-7 (skala 0–21). |
| `total_skor_kombinasi` | Penjumlahan skor PHQ-9 + GAD-7 (skala 0–48); sinonim: *Skor Krisis*. |
| `high_crisis_flag` | Indikator krisis tinggi (1 jika total skor >= 22, else 0); sinonim: *Kasus Berat*. |
| `butuh_rujukan_medis` | Indikator rujukan medis (1 jika rujukan ke Puskesmas/RSJ); sinonim: *Rujukan Medis*. |

---

##### 📍 Tab 3: "Instructions" (Petunjuk Umum & Aturan Main AI)
* **Fungsi & Kegunaan**: Memberikan batasan etika, bahasa, dan aturan perhitungan resmi. Aturan ini memastikan AI selalu menjawab dalam Bahasa Indonesia yang formal dan tidak salah memasukkan rumus perhitungan matematika.
* **Langkah Konfigurasi UI**:
  Isikan teks petunjuk berikut pada kotak dialog **Instructions**:

  - *Selalu berikan jawaban dalam Bahasa Indonesia yang formal dan profesional.*
  - *Satu baris data mewakili satu catatan interaksi remaja.*
  - *Hitung Total Remaja Terdaftar menggunakan `COUNT(DISTINCT user_id_masked)`.*
  - *Hitung Total Kasus Rujukan Medis menggunakan `COUNT(DISTINCT CASE WHEN butuh_rujukan_medis = 1 THEN user_id_masked END)`.*
  - *Hitung Total Kasus Krisis Tinggi menggunakan `COUNT(DISTINCT CASE WHEN high_crisis_flag = 1 THEN user_id_masked END)`.*
  - *Jika pengguna bertanya tentang 'wilayah terparah', tampilkan wilayah dengan rata-rata skor depresi PHQ-9 tertinggi.*
  - *Jika pengguna bertanya tentang 'faktor stres dominan', hitung `COUNT(faktor_stres_utama)` yang terbanyak.*

---

##### 📍 Tab 4: "Examples" (Contoh Kueri SQL & Trusted Queries)
* **Fungsi & Kegunaan**: Seperti murid sekolah yang belajar dari contoh soal, AI akan menyusun kueri SQL dengan jauh lebih akurat jika kita memberinya contoh kueri kurasi (*Curated Examples*) dan kueri terpercaya terparameter (*Trusted Queries*) buatan Data Engineer.
* **Langkah Konfigurasi UI**:
  Pada tab **Examples**, klik tombol **`+ Add`** untuk menambahkan 2 contoh kueri berikut:

  **A. Example Query (Contoh Pola SQL Perbandingan Wilayah)**:

  - **Question**: *"Tampilkan perbandingan rata-rata depresi dan total rujukan medis per wilayah Jakarta."*
  - **SQL Query**:
    ```sql
    SELECT 
        wilayah_jakarta,
        COUNT(DISTINCT user_id_masked) AS total_remaja,
        ROUND(AVG(skor_phq9), 2) AS avg_skor_depresi,
        COUNT(DISTINCT CASE WHEN butuh_rujukan_medis = 1 THEN user_id_masked END) AS total_rujukan_medis
    FROM katalog_[nim].kesehatan_mental.genie_mentalhealth_business_view
    GROUP BY wilayah_jakarta
    ORDER BY avg_skor_depresi DESC;
    ```

  **B. Parameterized Trusted Query (Kueri Terpercaya Berparameter Dinamis)**:

  - **Question**: *"Tampilkan analisis faktor stres dan durasi layar untuk wilayah tertentu."*
  - **SQL Query**:
    ```sql
    SELECT 
        wilayah_jakarta,
        faktor_stres_utama,
        COUNT(*) AS total_kasus,
        ROUND(AVG(durasi_layar_jam), 1) AS avg_durasi_layar,
        COUNT(DISTINCT CASE WHEN butuh_rujukan_medis = 1 THEN user_id_masked END) AS total_rujukan
    FROM katalog_[nim].kesehatan_mental.genie_mentalhealth_business_view
    WHERE wilayah_jakarta = :wilayah_target
    GROUP BY wilayah_jakarta, faktor_stres_utama
    ORDER BY total_kasus DESC;
    ```

---

#### 5.4 Evaluasi & Benchmark Suite (`BM05_MentalHealth_Core_Questions`)

Jalankan pengujian obrolan pada Genie Space menggunakan 8 pertanyaan benchmark berikut dan catat hasil yang diberikan oleh Genie:

| No | Pertanyaan Bahasa Alami (*Natural Language*) | Nilai Hasil Kueri | Status Evaluasi |
| :--- | :--- | :--- | :--- |
| **1** | *"Berapa total remaja terdaftar di sistem?"* | *23.562* | ✅ PASS |
| **2** | *"Berapa total kasus konseling yang membutuhkan rujukan medis?"* | *5.853* | ✅ PASS |
| **3** | *"Wilayah manakah dengan tingkat depresi PHQ-9 tertinggi?"* | *Jakarta Selatan* | ✅ PASS |
| **4** | *"Apa faktor stres utama yang paling dominan di Jakarta?"* | *Akademik & Ujian Sekolah* | ✅ PASS |
| **5** | *"Berapa rata-rata durasi layar harian remaja di Jakarta Selatan?"* | *9,79 jam/hari* | ✅ PASS |
| **6** | *"Berapa persentase kasus rujukan medis dari total log interaksi?"* | *24,98%* | ✅ PASS |
| **7** | *"Kelompok usia mana yang paling banyak mengalami krisis tinggi?"* | *usia 15-17 tahun* | ✅ PASS |
| **8** | *"Bagaimana korelasi antara durasi layar dengan rujukan medis?"* | *Semakin tinggi durasi layar harian, semakin tinggi persentase remaja yang membutuhkan rujukan medis ke fasilitas kesehatan mental* | ✅ PASS |

---

### 6. Troubleshooting (Penanganan Masalah Umum)

| Masalah / Kendala | Penyebab | Solusi / Cara Mengatasi |
| :--- | :--- | :--- |
| **Genie Menjawab *I don't know*** | AI tidak mengenali istilah lokal (misal: "gadget" atau "pasien"). | Tambahkan sinonim kata tersebut di tab **Sources** pada Genie Space. |
| **Generated SQL Menggunakan Kolom yang Salah** | Skema Business View belum ter-refresh di Genie Space. | Klik tombol **Refresh Schema** pada tab **Sources** di konfigurasi Data Source. |
| **Hasil Kueri Beda dengan Rekonsiliasi** | AI melakukan agregasi tanpa `DISTINCT` pada `user_id_masked`. | Tambahkan petunjuk eksplisit di tab **Instructions**: *"Gunakan COUNT(DISTINCT user_id_masked) untuk menghitung jumlah remaja."* |

---

### 7. Output Pertemuan 5
1. Business View untuk NLP: `katalog_[nim].kesehatan_mental.genie_mentalhealth_business_view`
2. Agent Genie Space: `GA05_MentalHealth_Business_Analyst`
3. Benchmark Evaluation Suite: `BM05_MentalHealth_Core_Questions`
4. Hasil Obrolan Analytics: Chat Room NLP Genie Space & Verified SQL Queries
