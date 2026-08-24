# 09. Implementasi Script PySpark (Medallion Architecture)

Dokumen ini menjelaskan implementasi teknis dan alur transformasi dari tiga tahapan skrip PySpark (Bronze, Silver, dan Gold) yang berjalan di ekosistem Databricks menggunakan Unity Catalog.

Skrip ini mengadopsi prinsip *Medallion Architecture* untuk memecah *lineage* komputasi DAG (Directed Acyclic Graph) Spark demi stabilitas performa, kemudahan pengujian, dan transparansi aliran data (Data Quality Funnel).

---

## 1. Bronze Layer (`01_bronze.ipynb`)
**Fokus Utama:** *Ingestion* data mentah, normalisasi tipe data, dan standarisasi zona waktu.

* **Input:** File CSV mentah di Unity Catalog Volume (`/Volumes/smt7_research/xauusd/raw_data/XAUUSD_H1.csv`).
* **Output:** Delta Table `smt7_research.xauusd.xauusd_liquidity_bronze`.

### Rincian Tahapan:
1. **Schema Definition & Ingestion:**
   Membaca file TSV/CSV yang dipisahkan tab secara eksplisit dengan struktur kolom konstan (Time, Open, High, Low, Close, Spread, Volume). 
2. **Determinisme dan Filtering (T1):**
   Membuang data duplikat pada kolom waktu (timestamp) untuk memastikan fungsi analitik *window/lead* di masa mendatang bersifat deterministik. Data difilter mulai 1 Januari 2016.
3. **Konversi Zona Waktu & Batas Hari Sesi (T4, T13):**
   - Batas akhir hari *trading* (Daily Session) tidak mengikuti pergantian tanggal tengah malam UTC, melainkan mengikuti **17:00 waktu New York (ET)**.
   - Script menghitung ini dengan menggeser 7 jam (`+ INTERVAL 7 HOURS`) dari zona waktu New York setelah otomatis menyesuaikan perubahan batas waktu (DST) menggunakan fungsi bawaan `from_utc_timestamp`. Hasilnya dimasukkan ke kolom `session_date`.
4. **Agregasi Kunci Pekan (T12):**
   Menambahkan `week_start` berbasis hari Senin dengan fungsi `date_trunc("week")` dari tanggal `session_date`. Hal ini menjamin pembukaan pasar di hari Minggu (UTC) tercatat masuk pada pekan (sesi) yang benar.

---

## 2. Silver Layer (`02_silver.ipynb`)
**Fokus Utama:** Perhitungan *window functions* agregasi H-1/W-1 dan operasi penarikan data prediksi (Lead).

* **Input:** Delta Table `smt7_research.xauusd.xauusd_liquidity_bronze`.
* **Output:** Delta Table `smt7_research.xauusd.xauusd_liquidity_silver`.

### Rincian Tahapan:
1. **Pembuatan Window Global & Look-Ahead Leads (T1):**
   - Skrip membuat urutan global *window* (`Window.orderBy("timestamp")`) yang akan menembus semua sesi.
   - Fungsi perulangan *for-loop* secara dinamis menghasilkan kolom `close_lead_1` hingga `close_lead_6` (sama juga untuk harga tertinggi dan terendah) tanpa harus menulis SQL yang repetitif. 
   - Kolom-kolom ini diperlukan di tahap Gold untuk melihat harga 1-6 jam pasca sebuah sentuhan pada zona *crossover*.
2. **Agregasi Level Harian (PDH, PDL):**
   Menggunakan pengelompokan `session_date`, program mencari titik High tertinggi dan Low terendah hari berjalan. Kemudian dengan fungsi `lag(1)`, program mengambil harga kemarin untuk dicatat sebagai Previous Daily High (PDH) dan Previous Daily Low (PDL).
3. **Agregasi Level Mingguan (PWH, PWL):**
   Melakukan agregasi yang identik, namun dikelompokkan pada tingkat `week_start`. Hasilnya dimasukkan pada kolom Previous Weekly High (PWH) dan Previous Weekly Low (PWL).
4. **Transparent Join (T6):**
   Tingkat harian dan mingguan ini kemudian digabungkan ke set data utama H1 melalui **LEFT JOIN**. Baris yang belum memiliki level referensi (misalnya data di hari pertama) diizinkan lewat sebagai `NULL` (*orphan*) agar sistem tetap transparan merekam data perantara, sebelum difilter dengan sadar di tahap berikutnya.

---

## 3. Gold Layer (`03_gold.ipynb`)
**Fokus Utama:** Pelabelan data set (4 kategori) berdasarkan perilaku penembusan harga (*Liquidity Sweep* atau *Pure Breakout*) dan pemberlakuan filter kejenuhan level (Exhaustion).

* **Input:** Delta Table `smt7_research.xauusd.xauusd_liquidity_silver`.
* **Output:** 
  1. Tabel Dataset Utama: `smt7_research.xauusd.xauusd_liquidity_gold`.
  2. Tabel Funnel Data: `smt7_research.xauusd.xauusd_liquidity_dq_funnel`.

### Rincian Tahapan:
Tahap ini paling krusial karena mendefinisikan variabel target (*class labels*) bagi permodelan ML yang akan datang:

1. **Deteksi Crossover (Penembusan Level):**
   Terdapat perhitungan ketat untuk mengetahui validitas sebuah perlintasan.
   - *High-side* (PDH, PWH): Harga tinggi (`high`) candle saat ini menembus garis batas ke atas, padahal candle sebelumnya (`prev_high`) masih berada tepat pada/di bawah batas tersebut.
2. **First-Touch Exhaustion:**
   Karena harga bisa melintasi sebuah zona berkali-kali dalam satu sesi (fenomena *chop*), permodelan kita membatasi dengan fitur `touch_rank`. Hanya sentuhan **pertama** (Rank 1) pada rentang harian atau mingguan yang dipakai; sentuhan lanjutan dianggap tidak valid.
3. **Formulasi 4 Target Eksklusif:**
   Menggunakan pengecekan bersyarat Boolean pada kolom observasi $t+6$:
   - **`IMMEDIATE_SWEEP`:** Harga kembali cepat pada jam-1/jam-2 (`returned_early`), lalu pada jam ke-6 ternyata harga masih bertahan di rentang penolakan (`ended_inside`).
   - **`DELAYED_SWEEP`:** Harga kembali melambat (`~returned_early`), namun pada jam ke-6 terkonfirmasi mengalami tolakan kembali ke bawah levelnya (`ended_inside`).
   - **`FAILED_SWEEP`:** Harga awalnya terlempar ke bawah dengan cepat (`returned_early`), tetapi di jam ke-6 sukses merangkak naik mematahkan zona perlawanan (`~ended_inside`).
   - **`PURE_BREAKOUT`:** Harga langsung terus meroket naik, tak pernah kembali dari sejak jam ke-1 hingga jam ke-6 (`~returned_early` & `~ended_inside`).
4. **Data Quality Funnel (DQ Funnel):**
   Script ini terus mengumpulkan jumlah baris yang gugur atau berhasil masuk di setiap tahap logikanya (mirip *funnel marketing*) sehingga dapat ditelusuri jika ada anomali dalam penyusutan volume data.

*Catatan: Fungsi `.cache()` pada tahap ini dinonaktifkan (`[NOT_SUPPORTED_WITH_SERVERLESS]`), karena lingkungan Databricks Serverless secara otomatis menangani optimasi *caching* internal dengan mesin disk NVMe (Photon).*
