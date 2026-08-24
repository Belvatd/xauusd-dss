# 14. Kamus Data Gold (Data Dictionary)

Dokumen ini menjelaskan secara rinci seluruh `52` kolom yang ada di dalam *dataset* final pengujian model Machine Learning kita, yakni `gold-data.csv` (tabel *Gold* pada arsitektur Medallion).

Dataset ini disusun sedemikian rupa sehingga 1 baris (row) mewakili **1 Event Crossover** (kejadian di mana harga menyentuh/menembus suatu level likuiditas penting).

---

## 1. Identitas Waktu & Pemrosesan (*Temporal Identifiers*)
Kolom-kolom ini bertugas menjaga urutan kronologis data agar tidak terjadi kebocoran waktu (*Data Leakage*) saat proses *Cross-Validation*.
* `week_start`: Tanggal patokan awal minggu (hari Senin) dari event tersebut. Berguna sebagai poros perhitungan level mingguan.
* `session_date`: Tanggal "Sesi Trading" secara logis (biasanya mengacu pada batas pergantian hari di bursa New York jam 17:00 EST).
* `timestamp`: Waktu aktual absolut (dalam UTC) saat *candle* penembus (*crossover*) itu terbentuk.
* `ingested_at`: Stempel waktu otomatis (*timestamp*) kapan *pipeline Data Engineering* memproses baris ini masuk ke tabel Gold.

## 2. Aksi Harga Saat Kejadian ($T_0$ *Price Action*)
Ini adalah bentuk fisik dari *candle* H1 yang tepat sedang bersentuhan dengan garis likuiditas.
* `open`, `high`, `low`, `close`: Empat pilar harga pembukaan, tertinggi, terendah, dan penutupan dari *candle* tersebut.
* `Spread`: Rentang/selisih harga jual (*bid*) dan harga beli (*ask*). Bisa menjadi indikator seberapa tipis/tebal likuiditas saat itu.
* `volume`: Jumlah frekuensi transaksi (*tick volume*) selama 1 jam *candle* tersebut terbentuk.

## 3. Konteks Sesi Pasar (*Market Session Context*)
Emas (XAUUSD) bergerak berbeda tergantung bursa mana yang sedang buka. Fitur ini menangkap hal tersebut.
* `hour_ny`: Jam lokal di zona waktu New York (Wall Street).
* `hour_london`: Jam lokal di zona waktu London (Eropa).
* `hour_tokyo`: Jam lokal di zona waktu Tokyo (Asia).
* `session`: Label kategorikal (teks) yang menyimpulkan sesi mana yang sedang paling aktif (contoh: `ASIA`, `LONDON`, `NY`, atau `OFF_SESSION`).

## 4. Referensi Level Likuiditas Utama
Kolom ini mencatat "garis apa" yang sedang ditembus oleh pergerakan harga saat itu.
* `PDH` (*Previous Daily High*): Rekor harga tertinggi di hari sebelumnya.
* `PDL` (*Previous Daily Low*): Rekor harga terendah di hari sebelumnya.
* `PWH` (*Previous Weekly High*): Rekor harga tertinggi di minggu sebelumnya.
* `PWL` (*Previous Weekly Low*): Rekor harga terendah di minggu sebelumnya.
* `prev_high` / `prev_low`: Harga rekor referensi yang aktif digunakan pada baris tersebut.
* `level_type`: Menyebutkan nama level yang ditembus (salah satu dari PDH, PDL, PWH, atau PWL).
* `level_price`: Angka/harga eksak dari garis `level_type` yang sedang diserang.
* `touch_rank`: Urutan sentuhan. Angka `1` berarti ini adalah *First Touch* (sentuhan pertama) terhadap level tersebut, yang mana merupakan likuiditas paling segar dan valid untuk dimodelkan.

## 5. Jendela Observasi Masa Depan ($T_1$ hingga $T_6$)
Mesin *Data Engineering* di Fase Silver melihat ke depan (selama 6 jam) untuk menentukan apa nasib penembusan tersebut. **(Perhatian: Kolom ini DILARANG dimasukkan sebagai fitur model ML karena akan membocorkan masa depan!)**
* `close_lead_1` s/d `close_lead_6`: Harga penutupan 1 jam hingga 6 jam setelah *candle* kejadian.
* `high_lead_1` s/d `high_lead_6`: Harga tertinggi 1 jam hingga 6 jam setelah *candle* kejadian.
* `low_lead_1` s/d `low_lead_6`: Harga terendah 1 jam hingga 6 jam setelah *candle* kejadian.
* `ts_lead_N`: Waktu aktual (UTC) dari *candle* masa depan ke-6.
* `window_hours`: Total durasi nyata dalam satuan jam.
* `window_is_continuous`: Bernilai `1` jika perjalanannya mulus (tidak terpotong libur Sabtu-Minggu). Bernilai `0` jika ada jeda akhir pekan.

## 6. Output & Target Klasifikasi (Label Mesin Pembelajar)
Bagian inilah yang dicari oleh model. Sistem menganalisis pergerakan $T_1$ s/d $T_6$ lalu merangkumnya menjadi stempel klasifikasi ini:
* `returned_early`: (True/False) Apakah harga sempat memutar arah atau menusuk kembali melewati garis *level_price* dalam kurun waktu 6 jam?
* `ended_inside`: (True/False) Apakah saat jam ke-6 ditutup, harganya aman bertengger kembali di zona asal (membuktikan pembalikan tren)?
* **`outcome`**: Ini adalah **Label Utama (Target/Jawaban)** untuk model ML Anda. Isinya 4 tipe pergerakan:
  1. `PURE_BREAKOUT`: Tembus dan bablas terus.
  2. `IMMEDIATE_SWEEP`: Tembus sebentar, lalu langsung berbalik memutar arah dengan cepat.
  3. `DELAYED_SWEEP`: Tembus, tertahan/sideways sejenak, lalu baru memutar arah di ujung waktu.
  4. `FAILED_SWEEP`: Sempat berusaha memutar arah, tapi gagal dan harganya malah lanjut bablas.
* `is_sweep`, `is_immediate_sweep`, `is_delayed_sweep`, `is_failed_sweep`, `is_pure_breakout`: Merupakan *dummy variables*. Ini adalah versi angka (0 dan 1) dari kolom `outcome` agar mudah dibaca oleh algoritma matematika/statistik.
