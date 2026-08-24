# 07. Catatan Review Kritis & Audit Perbaikan Desain [V1]

Dokumen ini memuat catatan telaah kritis terhadap rancangan riset awal, pembuktian matematis atas kelemahan logika formula lama, dan rincian penyempurnaan desain (*Design Refinement*) yang diwujudkan dalam arsitektur v2.0.

---

## 1. Ringkasan Eksekutif Temuan Audit Desain (T1 – T14)

| ID Temuan | Tingkat Keparahan | Ringkasan Masalah | Dampak pada Desain Awal | Status Resolusi |
| :---: | :---: | :--- | :--- | :---: |
| **T1** | 🔴 **Kritis** | `target_structural_sweep` secara matematis identik dengan `NOT target_breakout`. | Membawa redundansi informasi pada **3.177 dari 3.177 event**. Skenario *Delayed Sweep* tidak terdeteksi. | ✅ **Tuntas (v2.0)**<br>Diganti kolom `outcome` 4 kelas saling lepas. |
| **T2** | 🔴 **Kritis** | Event di ujung akhir dataset dilabeli `0` secara diam-diam akibat urutan filter yang salah. | Label salah tanpa pesan error (*silent failure*). | ✅ **Tuntas**<br>Filter `close_lead_6 IS NOT NULL` dieksekusi setelah *exhaustion*. |
| **T3** | 🔴 **Kritis** | Jendela observasi 6 candle menembus libur akhir pekan (Jumat ke Senin). | Mendistorsi 12% event Weekly dan 1,5% event Daily. | ✅ **Tuntas**<br>Penanda boolean `window_is_continuous`. |
| **T13** | 🔴 **Kritis** | Kunci pekan `F.year() + F.weekofyear()` mencampur tahun kalender dengan ISO-8601. | **Level PWH/PWL bocor dari masa depan** pada minggu pergantian tahun. | ✅ **Tuntas**<br>Kunci pekan seragam: `date_trunc("week", session_date)`. |
| **T13b**| 🔴 **Kritis** | Candle pembukaan Minggu (~2 jam) diperlakukan sebagai 1 hari perdagangan penuh. | **27,9% event tercemar** level PDH/PDL cacat. | ✅ **Tuntas**<br>Batas hari berbasis sesi **17:00 New York**. |
| **T4** | 🟠 **Serius** | Zona waktu broker diasumsikan statis GMT+2/+3 tanpa penanganan DST. | Label sesi salah selama ±3 minggu tiap pergantian musim. | ✅ **Tuntas**<br>Sumber terverifikasi **UTC**, konversi via `from_utc_timestamp`. |
| **T14** | 🟠 **Serius** | Jendela observasi 6 candle melintasi batas hari sesi (level baru lahir di tengah jendela). | Terjadi pada **8,90% event Daily** (233 dari 2.619 event). | ✅ **Tuntas**<br>Ditandai pada kolom `crosses_session_boundary`. |
| **T5** | 🟠 **Serius** | Kebocoran data antar-split pada validation set tunggal 2024. | Sampel kelas `DELAYED_SWEEP` hanya 15 event (sangat rapuh). | ✅ **Tuntas**<br>Diadopsi *Purged Expanding Walk-Forward CV*. |
| **T6** | 🟠 **Serius** | Penggunaan `INNER JOIN` membuang baris H1 tanpa pasangan level secara diam-diam. | Data hilang tanpa tercatat di log audit. | ✅ **Tuntas**<br>Diubah menjadi `LEFT JOIN` + pencatatan di *DQ Funnel*. |
| **T7** | 🟡 **Limitasi** | Lonjakan harga saat pembukaan pasar (*gap open*) terhitung sebagai sentuhan level biasa. | Mencampur dua fenomena mikrostruktur berbeda. | ✅ **Tuntas**<br>Penambahan kolom penanda `is_gap_event`. |
| **T8** | 🟡 **Limitasi** | Volume pasar forex ritel adalah *tick volume*, bukan volume transaksi riil. | Pembatasan interpretasi pada fitur volume. | ✅ **Tuntas**<br>Dinyatakan eksplisit sebagai limitasi riset. |

---

## 2. Pembuktian Matematis Temuan Kritis T1 (Redundansi Formula Boolean)

### 2.1 Formula Lama pada Script Awal
Pada implementasi awal untuk level PDH (High), kolom `target_structural_sweep` didefinisikan sebagai berikut:

```python
# Formula Lama yang Cacat:
.withColumn("target_structural_sweep", 
    F.when(
        (F.col("close_lead_6") <= F.col("PDH")) &          # <-- Syarat A
        (
            (F.col("close_lead_3") <= F.col("PDH")) | 
            (F.col("close_lead_4") <= F.col("PDH")) | 
            (F.col("close_lead_5") <= F.col("PDH")) | 
            (F.col("close_lead_6") <= F.col("PDH"))        # <-- Syarat A Muncul Kembali
        ), 
    1).otherwise(0))
```

### 2.2 Pembuktian Aljabar Boolean
Misalkan syarat $A \equiv (\text{close\_lead\_6} \le \text{PDH})$ dan syarat $B \equiv (\text{close\_lead\_3} \le \text{PDH} \lor \text{close\_lead\_4} \le \text{PDH} \lor \text{close\_lead\_5} \le \text{PDH})$.

Persamaan di atas dapat dituliskan sebagai:
$$\text{Output} = A \land (B \lor A)$$

Berdasarkan **Hukum Absorpsi Aljabar Boolean**:
$$A \land (B \lor A) \equiv A$$

Karena $A$ bernilai benar, maka $(B \lor A)$ **selalu bernilai benar** secara mutlak. Oleh karena itu, seluruh klausa $B$ tidak memiliki pengaruh komputasi apa pun, sehingga ekspresi menyederhana menjadi:
$$\text{target\_structural\_sweep} \equiv (\text{close\_lead\_6} \le \text{PDH}) \equiv \lnot \text{target\_breakout}$$

### 2.3 Dampak Kegagalan Formula Lama:
1. **Redundansi Informasi:** Kolom ketiga sama sekali tidak membawa informasi baru.
2. **Hilangnya Kelas `DELAYED_SWEEP`:** Skenario harga sempat bermain di luar rentang pada jam 1–2 sebelum berbalik tidak pernah dapat dipisahkan dari *Immediate Sweep*.
3. **Solusi v2.0:** Membangun variabel target `outcome` 4 kelas saling lepas berbasis kombinasi predikat `returned_early` dan `ended_inside`.

---

## 3. Telaah Kritis Temuan T13 & T13b (Batas Hari Finansial & Anomali Candle Minggu)

### 3.1 Masalah Candle Minggu
Broker forex/gold membuka perdagangan pada hari Minggu malam pukul 17:00 waktu New York (pukul 21:00 atau 22:00 UTC). Candle Minggu ini hanya berdurasi 2–3 jam sebelum pergantian hari UTC (00:00).

```text
Pendekatan Lama (Kalender UTC):
[Jumat (24 Jam)] --> [Minggu (2 Jam)] --> [Senin (24 Jam)]
                          ^
              Dianggap sebagai 1 Hari Penuh!
              Level PDH/PDL Senin dihitung HANYA dari 2 jam candle Minggu!
              -> Mengakibatkan 27,9% Level PDH/PDL Rusak/Cacat.
```

### 3.2 Solusi Batas Sesi 17:00 New York (Eastern Time)
Dengan menggeser batas hari ke **17:00 New York**, candle Minggu malam UTC secara otomatis dilebur menjadi jam pembuka bagi sesi hari Senin:

```text
Pendekatan Baru (Session-Date 17:00 NY):
[Sesi Jumat (24 Jam)] ------------------> [Sesi Senin (Minggu 17:00 NY s/d Senin 17:00 NY)]
                                                ^
                                      1 Siklus Sesi Utuh!
```

**Dampak Positif Resolusi T13b:**
Setelah koreksi ini diterapkan pada data, **asimetri PDH vs PDL justru semakin menguat dan selang kepercayaan Wilson 95% terpisah semakin tajam** (PDL Sweep 55,41% vs PDH Sweep 48,25%). Hal ini membuktikan bahwa asimetri tersebut adalah sinyal struktural pasar yang nyata, bukan akibat derau data.

---

## 4. Aspek Desain yang Wajib Dipertahankan

Audit juga mencatat keputusan desain awal yang sudah sangat baik dan wajib dipertahankan:
1. **Pencegahan Lookahead Bias Level:** Penggunaan `F.lag("high", 1)` pada level kemarin menjamin bahwa candle hari ini hanya mengetahui level yang sudah terbentuk sempurna di masa lalu.
2. **Aturan Level Exhaustion (`touch_rank == 1`):** Membatasi satu sentuhan per hari mencegah bias autokorelasi dari sentuhan berulang pada hari *ranging*.
3. **Arsitektur Tiga Tahap (Deskriptif $\rightarrow$ Diagnostik $\rightarrow$ Prediktif):** Memberikan jaminan integritas akademik di mana setiap tahap memiliki luaran independen yang bernilai.
4. **Arsitektur Medallion PySpark:** Memisahkan data mentah (*Bronze*), data teragregasi (*Silver*), dan data siap latih (*Gold*) memudahkan pelacakan silsilah data (*data lineage*).
