# 04. Fase 1: Analitik Deskriptif (Data Engineering & Analytics)

Dokumen ini menyajikan hasil lengkap analisis Tahap 1 (Deskriptif) yang menjawab **Rumusan Masalah 1 (RM1)**: *"Berapa proporsi pasti kejadian liquidity sweep dibandingkan breakout pada level likuiditas XAUUSD, dan apakah proporsi tersebut berbeda antara level harian (PDH/PDL) dan mingguan (PWH/PWL)?"*.

---

## 1. Matriks Objektif Fase 1 (D1 – D7)

Setiap objektif deskriptif dirancang untuk menyuplai fondasi empiris bagi pemodelan prediktif di Fase 3:

| Kode | Objektif Analitik | Output Konkret | Pemanfaatan di Fase 3 (ML & DSS) |
| :---: | :--- | :--- | :--- |
| **D1** | **Kunci Definisi Label** | Skema target 4 kelas saling lepas (`outcome`) dan target biner (`is_sweep`). | Mendefinisikan variabel dependen ($Y$) model. *(Blocker utama)*. |
| **D2** | **Inventarisasi & Kualitas Event** | Tabel event per `level_type` per tahun dan audit data hilang. | Menentukan kelayakan ukuran sampel ($N$) dan batas kompleksitas model. |
| **D3** | **Estimasi *Base Rate*** | Tabel proporsi *Sweep* vs *Breakout* + Selang Kepercayaan 95% Wilson. | **Garis Dasar Wajib (Baseline B0).** Model ML harus mengungguli angka ini. |
| **D4** | **Distribusi Tersegmentasi** | Rasio dipecah per level, sesi, hari, dan tahun. | Mengidentifikasi fitur-fitur kandidat primer untuk Fase 2. |
| **D5** | **Frekuensi Skenario Pasar** | Proporsi 4 kelas outcome (termasuk *Failed Sweep*). | Menilai kelayakan pemodelan kelas minoritas (`DELAYED_SWEEP`). |
| **D6** | **Deskriptif Magnitudo** | Distribusi penetrasi & pembalikan dalam satuan ATR. | Parameter penentuan lebar batas *stop-loss* dan *take-profit*. |
| **D7** | **Stabilitas Antar-Periode** | Rasio kelas pada split *Train*, *Validation*, dan *OOS*. | Mengonfirmasi ketiadaan *regime shift* & memandu *class weighting*. |

---

## 2. D2 — Inventarisasi Dataset Event (2016 – Juli 2026)

Dari seluruh perlintasan harga, diperoleh total **3.148 event *first-touch***:
- **Event Harian (Daily):** **2.619 event** (1.399 PDH dan 1.220 PDL).
- **Event Mingguan (Weekly):** **529 event** (303 PWH dan 226 PWL).

### Tabel Sebaran Event per Tahun:
| Tahun | PDH | PDL | PWH | PWL | Total Harian | Total Gabungan |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2016** | 119 | 121 | 26 | 21 | 240 | 287 |
| **2017** | 136 | 118 | 32 | 21 | 254 | 307 |
| **2018** | 118 | 126 | 23 | 26 | 244 | 293 |
| **2019** | 134 | 106 | 28 | 20 | 240 | 288 |
| **2020** | 145 | 108 | 30 | 18 | 253 | 301 |
| **2021** | 133 | 118 | 27 | 24 | 251 | 302 |
| **2022** | 126 | 126 | 26 | 26 | 252 | 304 |
| **2023** | 125 | 126 | 27 | 24 | 251 | 302 |
| **2024** | 140 | 106 | 29 | 20 | 246 | 295 |
| **2025** | 151 | 94 | 40 | 12 | 245 | 297 |
| **2026 (s/d Jul)** | 72 | 71 | 15 | 14 | 143 | 172 |
| **TOTAL** | **1.399** | **1.220** | **303** | **226** | **2.619** | **3.148** |

> **Implikasi Desain Pemodelan:**
> Ukuran sampel harian ($N = 2.619$) sangat memadai untuk algoritma pohon teratur (*Gradient Boosted Trees / LightGBM*) dan Regresi Logistik, namun tidak memadai untuk *Deep Learning*. Sementara itu, sampel mingguan ($N = 529$) berstatus **deskriptif saja** dan sinyalnya diinjeksikan ke model harian lewat fitur konfluensi geometri level.

---

## 3. D3 — Estimasi *Base Rate* & Asimetri PDH vs PDL

*Base rate* dihitung menggunakan estimator proporsi dengan **Selang Kepercayaan 95% Wilson Score Interval**:

$$\text{CI}_{95\%} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$

| Tingkat Level | Kategori Level | Jumlah Event ($N$) | Proporsi *Sweep* (%) | Selang Kepercayaan 95% (Wilson) |
| :--- | :--- | :---: | :---: | :---: |
| **Harian (Daily)** | **Agregat Harian** | **2.619** | **51,58%** | **[49,67% – 53,49%]** |
| | PDH (High Kemarin) | 1.399 | **48,25%** | [45,64% – 50,87%] |
| | PDL (Low Kemarin) | 1.220 | **55,41%** | [52,61% – 58,18%] |
| **Mingguan (Weekly)** | **Agregat Mingguan** | **529** | **53,12%** | **[48,86% – 57,32%]** |
| | PWH (High Pekan Lalu) | 303 | 49,83% | [44,24% – 55,44%] |
| | PWL (Low Pekan Lalu) | 226 | 57,52% | [51,00% – 63,77%] |

```text
Temuan Asimetri Struktural:
PDL Sweep Rate : [52,61% ===================== 58,18%]  (Mean: 55,41%)
PDH Sweep Rate : [45,64% ================= 50,87%]      (Mean: 48,25%)
                       ^ Selang Kepercayaan Terpisah Bersih (Disjoint CI)
```

> [!IMPORTANT]
> **Temuan Kunci Asimetri Pasar:**
> Penembusan PDL memiliki probabilitas *Sweep* (pembalikan arah naik) yang **secara signifikan lebih tinggi (+7,16 pp)** daripada penembusan PDH. Selang kepercayaan 95% keduanya **terpisah bersih tanpa irisan**. Hal ini mencerminkan bias struktural pasar emas jangka panjang (*secular bull market*) di mana penurunan harga ke area likuiditas bawah lebih agresif diserap oleh pembeli institusional (*liquidity hunting / dip buying*).

---

## 4. D5 — Distribusi Frekuensi Matriks Skenario Pasar

| Kelas Target `outcome` | returned_early | ended_inside | Frekuensi Harian ($N$) | Persentase (%) | Makna Praktis bagi Trader |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`IMMEDIATE_SWEEP`** | 1 | 1 | 1.066 | **40,70%** | Penolakan harga instan; konfirmasi pembalikan cepat dalam 2 jam pertama. |
| **`DELAYED_SWEEP`** | 0 | 1 | 285 | **10,88%** | Penembusan lambat; harga sempat melayang di luar sebelum ditarik kembali. |
| **`FAILED_SWEEP`** | 1 | 0 | 458 | **17,49%** | **Reversal Trap (Jebakan Pembalikan).** Sempat memberi sinyal palsu pembalikan pada jam 1–2, namun akhirnya jebol sebagai breakout. |
| **`PURE_BREAKOUT`** | 0 | 0 | 810 | **30,93%** | Penembusan murni berlanjut tanpa perlawanan. |
| **TOTAL** | - | - | **2.619** | **100,00%** | |

> **Signifikansi Kelas `FAILED_SWEEP`:**
> Mencakup **17,49% event** (hampir 1 dari 5 kejadian). Mengidentifikasi kondisi yang membedakan `FAILED_SWEEP` dari `IMMEDIATE_SWEEP` adalah kontribusi paling bernilai dari DSS ini untuk melindungi modal trader dari jebakan pasar.

---

## 5. D7 — Uji Stabilitas Antar-Periode (Ketiadaan *Regime Shift*)

| Split Dataset | Rentang Waktu | Jumlah Event | Proporsi *Sweep* (%) | Selang Kepercayaan 95% |
| :--- | :--- | :---: | :---: | :---: |
| **Train Set** | 2016 – 2023 (8 Tahun) | 1.986 | **51,86%** | [49,66% – 54,06%] |
| **Validation Set** | 2024 (1 Tahun) | 246 | **52,44%** | [46,18% – 58,60%] |
| **OOS Test Set** | 2025 – Juli 2026 (1,5 Thn) | 387 | **50,13%** | [45,18% – 55,08%] |

Semua selang kepercayaan saling beririsan secara konsisten (selisih maksimum antar-split hanya 2,31 pp). Hal ini membuktikan bahwa perilaku dasar *sweep vs breakout* pada level PDH/PDL stabil dan tidak mengalami patahan struktural.
