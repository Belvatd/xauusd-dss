---
tags: [dokumen-formal]
---

# 02. Decision Log: Catatan Keputusan Metodologis & Validasi Empiris

Dokumen ini mencatat keputusan-keputusan metodologis krusial yang diambil selama perancangan riset, termasuk hasil uji pra-registrasi penentuan periode data, bukti ketahanan fitur berbasis ATR (Population Stability Index), dan justifikasi transisi skema validasi model.

---

## 1. Decision Log — Pemilihan Periode Data (2016-01-01 s/d 2026-07-31)

> **Keputusan Resmi:** **Periode Data: 1 Januari 2016 s/d 31 Juli 2026.**  
> Diambil pada 2 Agustus 2026 berdasarkan protokol uji empiris pra-registrasi, menggantikan opsi awal periode 2018+.

### 1.1 Aturan Keputusan Pra-Registrasi
Untuk menghindari bias seleksi (*cherry-picking*) dan *p-hacking*, kriteria keputusan ditetapkan **sebelum melihat hasil**:

| Kode Uji | Metrik yang Diukur | Kriteria Kelulusan |
| :--- | :--- | :--- |
| **U1** | Beda proporsi *sweep* antar-era | Chi-square $p > 0,05$ **atau** selisih proporsi $< 3$ poin persentase (pp). |
| **U2** | Tren proporsi *sweep* per tahun | *Slope* regresi linier tidak signifikan ($p > 0,05$). |
| **U3** | Stabilitas distribusi fitur (*Population Stability Index* - PSI) | $\ge 80\%$ fitur kandidat memiliki nilai $\text{PSI} < 0,10$ (stabil). |

**Aturan Pemetaan Keputusan:**
- **3 dari 3 Lulus:** Gunakan seluruh data dari tahun 2010+.
- **2 dari 3 Lulus:** Gunakan data dari tahun **2016+**.
- **0–1 Lulus:** Potong di tahun 2018 dengan justifikasi perubahan rezim.

---

### 1.2 Hasil Pengujian Empiris (2 dari 3 Lulus)

| Uji | Hasil Empiris | Status | Catatan & Analisis |
| :--- | :--- | :---: | :--- |
| **U1** | 2010–2017: **47,51%** · 2018–2026: **51,01%**<br>$p = 0,0277$ · Selisih: **3,50 pp** | **GAGAL** | Selisih melebihi ambang batas 3,0 pp. |
| **U2** | *Slope* tren: **+0,18 pp/tahun** ($p = 0,381$) | **LULUS** | Tidak ada tren jangka panjang; tren tahunan praktis datar (nol). |
| **U3** | **5 dari 6 fitur** memiliki $\text{PSI} < 0,10$ | **LULUS** | Distribusi fitur ternormalisasi ATR sangat stabil melintasi dekade. |

---

### 1.3 Analisis Mendalam: Mengapa Kegagalan U1 Bukan Perubahan Rezim Struktural?

Perubahan rezim pasar sejati memiliki titik mula yang tegas dan bertahan seterusnya (*persistent*). Data menunjukkan fenomena yang berbeda:

```text
Proporsi Sweep Lintas Era:
2010–2013: 47,89% [CI 95%: 44,73% – 51,07%]
2014–2017: 47,13% [CI 95%: 43,96% – 50,33%]
2018–2021: 52,85% [CI 95%: 49,70% – 55,98%]  <-- Anomali Lokal
2022–2026: 49,41% [CI 95%: 46,47% – 52,36%]  <-- Kembali Normal
```

| Titik Potong Era (*Cutoff*) | Nilai $p$ (Chi-square) | Selisih Proporsi | Keterangan |
| :---: | :---: | :---: | :--- |
| **2014** | $p = 0,3048$ | 1,91 pp | Tidak signifikan |
| **2016** | $p = 0,0556$ | 3,18 pp | Tidak signifikan secara statistik ($p > 0,05$) |
| **2018** | **$p = 0,0277$** | **3,50 pp** | Tampak signifikan sebelum koreksi jamak |
| **2020** | $p = 0,0924$ | 2,73 pp | Tidak signifikan |
| **2022** | $p = 0,9568$ | 0,10 pp | Sangat identik |

> [!NOTE]
> **Temuan Artefak Statistik:**
> "Patahan" hanya muncul secara tunggal di titik potong 2018 dan menghilang di seluruh titik potong lainnya. Setelah dilakukan **koreksi pengujian jamak Benjamini-Hochberg**, nilai $p=0,0277$ pada tahun 2018 **tidak lolos signifikansi**. Ini membuktikan lonjakan 2018–2021 adalah variasi acak (*random noise*), bukan perubahan rezim permanen.

---

### 1.4 Temuan U3: Bukti Ketahanan Satuan ATR (*Average True Range*)

Uji PSI membuktikan bahwa meskipun harga emas XAUUSD bergerak naik hampir 4 kali lipat (dari ±$1.100 pada 2016 ke ±$4.100 pada 2026), fitur yang dinormalisasi dengan satuan ATR **tetap memiliki distribusi yang identik**:

| Nama Fitur | Nilai PSI | Status Distribusi |
| :--- | :---: | :--- |
| `penetration_atr` | **0,0079** | Sangat Stabil ($\text{PSI} < 0,10$) |
| `close_pos_in_range` | **0,0082** | Sangat Stabil |
| `candle_range_atr` | **0,0193** | Sangat Stabil |
| `jam` (hour of day) | **0,0226** | Sangat Stabil |
| `body_ratio` | **0,0227** | Sangat Stabil |
| `atr_pct_of_price` | **0,2158** | **Bergeser Signifikan ($\text{PSI} > 0,20$)** |

> **Keputusan Eliminasi Fitur:**
> Fitur `atr_pct_of_price` dibuang dari pemodelan karena sebagai rasio terhadap harga absolut, ia menyelundupkan informasi level harga nominal yang merusak performa *Out-of-Sample* (OOS). Digantikan dengan **`atr_ratio_vs_median60`** (volatilitas saat ini relatif terhadap median 60 candle terakhir) yang bersifat nir-dimensi (*dimensionless*) dan kebal perubahan rezim harga.

---

### 1.5 Justifikasi Final Periode 2016–2026
1. Memenuhi aturan pra-registrasi (2 dari 3 lulus).
2. Menghasilkan **+24% ukuran sampel data** (2.560 event vs 2.072 event Daily).
3. Titik potong 2016 menghasilkan $p = 0,0556$ (konsisten homogen).
4. Menghilangkan seluruh era *bear market* emas 2011–2015 dan *crash* April 2013.
5. **Justifikasi Akademik untuk Proposal:** *"Periode penelitian dimulai Januari 2016, setelah dasar siklus bear market emas pada Desember 2015."*
6. **Data 2010–2015 dijadikan *Historical Robustness Set*** untuk membuktikan apakah model yang dilatih pada era 2016+ tetap tangguh saat diuji mundur pada era pasar sebelumnya.

---

## 2. Decision Log — Evolusi Skema Validasi Model

> **Keputusan Resmi:** **Mengadopsi *Purged Expanding Walk-Forward Cross-Validation* dengan *Embargo* 6 Candle**, menggantikan skema *single validation set* tahun 2024.

### 2.1 Masalah pada Skema Validation Tunggal 2024
Ketika distribusi dataset dipecah menurut 4 kelas target `outcome`:

| Split Dataset | IMMEDIATE | DELAYED | FAILED | PURE | Total Event |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Train (2016–2023)** | 840 | **190** | 348 | 608 | 1.986 |
| **Validation (2024)** | 114 | **15** | 44 | 73 | 246 |
| **OOS Test (2025–Jul 2026)** | 162 | **30** | 67 | 129 | 387 |

> [!WARNING]
> **Kerapuhan Sampel Kritis:**
> Pada *validation set* 2024 tunggal, kelas **`DELAYED_SWEEP` hanya memiliki 15 sampel**. Satu kesalahan prediksi kelas ini akan mengubah metrik *recall* sebesar **6,67%**. Akibatnya, seluruh proses pemilihan model dan *hyperparameter tuning* akan dipandu oleh noise statistik. Selain itu, proporsi split menjadi sangat timpang (76% / 9% / 15%).

---

### 2.2 Solusi: Purged Expanding Walk-Forward CV

Dengan menerapkan 6 fold validasi bergulir kronologis (*walk-forward*):

```text
Fold 1: Train 2016–2018 -> Val 2019   [DELAYED: 20 event]
Fold 2: Train 2016–2019 -> Val 2020   [DELAYED: 24 event]
Fold 3: Train 2016–2020 -> Val 2021   [DELAYED: 21 event]
Fold 4: Train 2016–2021 -> Val 2022   [DELAYED: 26 event]
Fold 5: Train 2016–2022 -> Val 2023   [DELAYED: 18 event]
Fold 6: Train 2016–2023 -> Val 2024   [DELAYED: 15 event]
---------------------------------------------------------
TOTAL AKUMULASI EVALUASI:             [DELAYED: 124 event]
```

**Keuntungan Metodologis:**
1. Meningkatkan ketersediaan sampel kelas langka untuk tuning sebesar **8,3 kali lipat (dari 15 menjadi 124 event)** tanpa menambah data baru.
2. Mematuhi kaidah temporal deret waktu (*time-series*): data latih selalu mendahului data uji secara kronologis.
3. *Purging* dan *Embargo* 6 candle diaplikasikan di setiap batas antar-fold untuk mencegah kebocoran informasi (*information leakage*).
