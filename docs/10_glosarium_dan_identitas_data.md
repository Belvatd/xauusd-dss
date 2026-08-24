# 10. Glosarium Konsep, Profil Data, dan Logika Aturan (T)

Dokumen ini merangkum identitas data yang digunakan dalam riset, penjelasan konsep dasar *trading* secara sederhana (Likuiditas), logika konversi zona waktu, serta pemahaman tentang aturan pembatas (Tripwires T1-T14) yang diimplementasikan di dalam skrip.

---

## 1. Identitas Data Riset (Data Profile)
Riset ini melatih Sistem Pendukung Keputusan (DSS) berbasis *Machine Learning* menggunakan data terstruktur berikut:

### Spesifikasi Aset & Waktu
* **Instrumen / Aset:** Emas vs Dolar AS (Simbol: `XAUUSD`)
* **Timeframe (Resolusi Data):** H1 (Grafik 1 Jam / 60 menit)
* **Atribut Kolom Harga:** OHLCV (*Open, High, Low, Close, Tick Volume*, ditambah Spread/Interval)
* **Siklus Hari Trading:** Mengikuti zona waktu finansial 17:00 New York (ET).

### Dimensi Data Mentah (*Raw Data*)
* **Sumber File:** `raw-data/XAUUSD_H1.csv`
* **Total Baris (*Raw*):** Tepat 100.000 baris data H1.
* **Rentang Waktu Asli File:** 16 November 2009 – 31 Juli 2026.

### Pemfilteran & Ekstraksi (*Medallion Pipeline*)
* **Batas Waktu Riset:** 1 Januari 2016 – 31 Juli 2026 (menggunakan kondisi `START_DATE = "2016-01-01"` untuk memastikan relevansi dengan pasar ekonomi modern).
* **Total Penembusan Harga (*Raw Crossovers*):** Harga menyentuh/menembus batas harian dan mingguan sebanyak **5.208 kali**.
* **Filter *First-Touch Exhaustion*:** Membuang 2.060 sentuhan berulang agar mesin tidak mempelajari sinyal bising repetitif.

### Hasil Akhir (Dataset untuk ML)
Dari proses *Data Engineering*, dihasilkan total **3.148 observasi (*events*)** bersih yang siap dilatih:
* **2.619 event** dari level harian (PDH/PDL).
* **529 event** dari level mingguan (PWH/PWL).

Tiap observasi telah diklasifikasikan ke dalam salah satu dari empat target (label): `IMMEDIATE_SWEEP`, `DELAYED_SWEEP`, `FAILED_SWEEP`, atau `PURE_BREAKOUT`.

---

## 2. Glosarium Konsep Dasar Trading

### A. Apa itu Likuiditas?
Di dalam pasar finansial (dan *Smart Money Concepts*), **Likuiditas** berarti area di mana terdapat banyak order tertunda (*Pending Orders* dan *Stop Loss*) dari para *trader* ritel di seluruh dunia.
Area favorit tempat berkumpulnya uang ritel ini biasanya terletak tepat di atas **Puncak Harga Kemarin (PDH)** dan tepat di bawah **Jurang Harga Kemarin (PDL)**.

### B. *Liquidity Sweep* vs *Pure Breakout*
Dalam menjawab kejadian penembusan batas harga, DSS mengklasifikasikannya ke dalam dua sifat utama:
1. **Liquidity Sweep (Sapu Likuiditas):** 
   Harga tiba-tiba menembus batas PDH/PDL sehingga memicu seluruh eksekusi *Stop Loss* dan pesanan ritel. Karena hal ini menghasilkan volume "barang" (emas) yang masif, institusi besar memanfaatkannya untuk melempar order sebaliknya. Begitu likuiditas habis tersapu, harga emas segera berbalik arah secara dramatis. (Di dalam skrip dicatat sebagai `IMMEDIATE_SWEEP` dan `DELAYED_SWEEP`).
2. **Pure Breakout (Tembusan Murni):**
   Harga menembus batas PDH/PDL dan terus melanjutkan perjalanannya secara konsisten membentuk tren baru tanpa pernah berbalik arah. Ini menunjukkan penembusan organik tanpa manipulasi mematikan.

---

## 3. Penjelasan Sederhana Konversi Waktu 17:00 NY (T4 & T13)

Bagi masyarakat umum, hari berganti tepat pada pukul 12 malam (00:00). Namun, siklus operasi dunia *trading* menganggap bahwa 1 hari penuh berakhir ketika para pekerja di bursa Wall Street, New York, menyelesaikan sesi kerjanya pada pukul 17:00 sore (Waktu New York).
Artinya, bagi kalender *trading*, **pukul 17:01 New York sudah dihitung sebagai hari esoknya.**

Masalahnya, New York menggunakan sistem *Daylight Saving Time* (DST). Di musim panas jam mereka dimajukan, dan di musim dingin dikembalikan. Ini membuat konversi ke standar waktu universal (UTC) menjadi sangat berantakan jika dikunci pada nilai statis.

**Solusi Skrip (Trik Mesin Waktu 7 Jam):**
- Jarak waktu antara pukul 17:00 sore menuju pukul 24:00 (tengah malam) adalah **7 jam**.
- Skrip *PySpark* mendeteksi jam dinding asli di New York (yang secara otomatis mengakomodasi DST), lalu memaksa jam tersebut **maju 7 jam ke depan**.
- Hasilnya: Saat bursa Wall Street tutup di pukul 17:00, jam di dalam komputer tiba-tiba menunjukkan angka persis **24:00 (00:00)**. 
- Komputer pun secara otomatis memisahkan tanggal (batas kalender harian) secara rapi dan selaras dengan waktu asli tutup bursa di dunia nyata.

---

## 4. Pemahaman Aturan Pembatas (*Tripwires* T1-T14)

Kode T1 hingga T14 pada skrip adalah kependekan dari ***Tripwire*** atau **Aturan Invarian Kualitas Data**. 
Aturan-aturan spesifik ini **didefinisikan sendiri secara internal oleh tim riset**, dan bukan merupakan pedoman baku internasional.

**Mengapa harus dirumuskan sendiri?**
Karakteristik *trading* (seperti keunikan waktu 17:00 NY dan fenomena *crossover* palsu) sangat berbeda dari jenis data tabular biasa. Jika terjadi *off-by-one error* (kesalahan pergeseran 1 baris/jam), model akan mengalami *Data Leakage*—ia mengintip harga masa depan sehingga nampak sukses saat riset tapi gagal total saat diuji di dunia nyata.

**Metodologi Implementasi:**
Tim merangkum logika-logika keharusan ini menjadi aturan T1-T14 dan memasukkannya ke kode menggunakan metode `assert`. Di industri *Data Engineering*, taktik ini dikenal sebagai *Defensive Programming* atau *Circuit Breakers*.
Jika seseorang di masa depan mengubah kode dan tanpa sengaja melanggar salah satu saja dari belasan aturan ini, skrip akan **seketika berhenti beroperasi (*crash* dengan aman)**, mencegah data kotor dan cacat mengalir masuk ke model *Machine Learning*.
