---
tags: [metodologi-riset-ml]
---

# 05. Fase 2: Analitik Diagnostik (Contextual Pattern Extraction)

Dokumen ini mendokumentasikan metodologi dan kerangka kerja analitik Tahap 2 (Diagnostik) yang menjawab **Rumusan Masalah 2 (RM2)**: *"Faktor kontekstual apa (mis. sesi perdagangan, volatilitas, arah tren, geometri level, dinamika pendekatan) yang secara statistik membedakan sweep dari breakout, dan seberapa besar pengaruhnya?"*.

---

## 1. Matriks Objektif Fase 2 (G1 – G6)

```text
Fase 1: "Seberapa sering?"  -->  Base Rate 51,58%
Fase 2: "Dalam kondisi apa?" -->  Feature Library (5 Famili) & Information Value (IV)
Fase 3: "Berapa probabilitasnya sekarang?" --> Model ML Terkalibrasi
```

| Kode | Objektif Diagnostik | Output Konkret | Pemanfaatan di Fase 3 |
| :---: | :--- | :--- | :--- |
| **G1** | **Pustaka Fitur Kandidat** | Kamus fitur: nama, formula matematis, famili, *point-in-time certification*. | Input matriks kovariat ($X$) untuk model. |
| **G2** | **Uji Asosiasi Univariat** | Peringkat fitur berdasarkan *Information Value* (IV), *Weight of Evidence* (WOE), dan *Effect Size*. | Pemilihan 5–15 fitur paling prediktif untuk model baseline B2. |
| **G3** | **Tabel Probabilitas Kondisional** | Estimasi $P(Y \mid X_i)$, *Lift* terhadap *Base Rate*, dan selang kepercayaan. | Pembentukan aturan keputusan tunggal (*Rule Baseline B1*). |
| **G4** | **Pangkas Redundansi & Multikolinieritas** | Matriks korelasi Pearson/Spearman & *Variance Inflation Factor* (VIF). | Mencegah instabilitas koefisien dan *overfitting*. |
| **G5** | **Penambangan Interaksi (*Rule Mining*)** | *Decision Tree* dangkal (kedalaman 2–3) untuk mengekstrak aturan gabungan multi-kondisi. | Ekstraksi fitur interaksi non-linier untuk model pohon. |
| **G6** | **Audit Kebocoran & Stabilitas Fitur** | Sertifikasi ketiadaan *lookahead* pada $T_0$ dan evaluasi stabilitas PSI lintas era. | Menjamin model tidak mengandalkan fitur yang rapuh di masa depan. |

---

## 2. Disiplin Metodologis Ketat Fase 2

> [!CAUTION]
> **Dua Aturan Disiplin yang Tidak Boleh Dilanggar:**
> 1. **Eksklusivitas Train Set:** Seluruh analisis diagnostik, pengujian hipotesis, dan seleksi fitur **hanya boleh dijalankan pada TRAIN SET (2016–2023)**. Memeriksa data validasi atau OOS untuk memilih fitur adalah bentuk kebocoran data (*data leakage*) halus yang fatal.
> 2. **Koreksi Pengujian Jamak (*Multiple Testing Correction*):** Menguji ~40 fitur kandidat secara simultan berisiko menghasilkan temuan signifikan semu akibat kebetulan (*false discovery*). Analisis wajib menerapkan **Benjamini-Hochberg False Discovery Rate (FDR)** dan selalu melaporkan **ukuran efek (*effect size*)**, bukan sekadar nilai $p$.

---

## 3. G1 — Pustaka Fitur Kandidat (*Feature Candidate Library*)

Seluruh fitur diturunkan **murni dari data OHLCV XAUUSD** dan tersertifikasi dihitung hanya menggunakan informasi yang tersedia tepat pada saat $T_0$ (*Point-in-Time*).

### 3.1 Famili A — Temporal & Sesi
Menangkap pola musiman waktu dan siklus likuiditas intraday/pekanan:

| Nama Fitur | Definisi & Formula Teknis | Hipotesis Finansial |
| :--- | :--- | :--- |
| `hour_of_day` | Jam candle saat sentuhan pertama $T_0$ (0–23 UTC). | Jam tertentu memiliki tingkat likuiditas dan pelaku pasar berbeda. |
| `session` | Kategori sesi: `ASIA`, `LONDON`, `NY`, `OFF_SESSION`. | Sesi Asia cenderung *ranging* ($\rightarrow$ lebih banyak *Sweep*); Sesi London/NY lebih *trending* ($\rightarrow$ lebih banyak *Breakout*). |
| `day_of_week` | Hari dalam sepekan (Senin s/d Jumat). | Hari Senin membentuk batas rentang mingguan; Jumat cenderung aksi ambil untung (*profit taking*). |
| `is_session_open_hour` | Indikator biner (1 jika $T_0$ terjadi pada jam pertama pembukaan sesi). | Pembukaan sesi sering menghasilkan dorongan penembusan semu (*fakeout*). |
| `hours_to_weekly_close` | Selisih jam menuju penutupan pasar Jumat 17:00 NY. | Penutupan posisi institusional menjelang akhir pekan mengubah perilaku likuiditas. |

---

### 3.2 Famili B — Rezim Volatilitas
Menangkap kondisi ekspansi vs kompresi volatilitas pasar:

| Nama Fitur | Definisi & Formula Teknis | Hipotesis Finansial |
| :--- | :--- | :--- |
| `atr_14` | *Average True Range* periode 14 candle H1. | Mengukur volatilitas absolut saat ini. |
| `atr_ratio_vs_median60` | $\text{ATR}_{14} / \text{Median}(\text{ATR}_{14}, 60\text{ candle})$. | **Kandidat Kuat.** Mengukur rezim volatilitas saat ini relatif terhadap kondisi normalnya (nir-dimensi). |
| `adr_used_pct` | $(\text{High}_{\text{today}} - \text{Low}_{\text{today}}) / \text{ADR}_{20}$. | **Kandidat Sangat Kuat.** Jika 90%+ rentang harian rata-rata sudah terpakai sebelum menyentuh level, "bahan bakar" breakout habis $\rightarrow$ *Sweep* lebih dominan. |
| `bb_width` | $(BB_{\text{upper}} - BB_{\text{lower}}) / BB_{\text{middle}}$. | Kondisi *squeeze* volatilitas mendahului ekspansi *breakout*. |

---

### 3.3 Famili C — Tren & Struktur Pasar
Menangkap keselarasan arah penembusan terhadap tren *higher timeframe* (HTF):

| Nama Fitur | Definisi & Formula Teknis | Hipotesis Finansial |
| :--- | :--- | :--- |
| `htf_trend_direction` | Kemiringan EMA-50 dan EMA-200 pada timeframe H4/D1. | **Kandidat Kuat.** Menembus PDH saat tren besar naik adalah *continuation breakout*, sedangkan menembus PDH saat tren besar turun cenderung *sweep*. |
| `price_vs_ema_atr` | $(\text{Price} - \text{EMA}_{50}) / \text{ATR}_{14}$. | Jarak harga terhadap garis rata-rata dalam satuan ATR (deteksi kondisi *overextended*). |
| `adx_14` | *Average Directional Index* periode 14. | ADX rendah ($<20$) menandakan pasar *ranging* ($\rightarrow$ *sweep* tinggi); ADX tinggi ($>30$) menandakan pasar *trending*. |
| `consecutive_d1_direction` | Jumlah candle harian berturut-turut yang ditutup searah. | Mengukur tingkat kejenuhan momentum harian. |

---

### 3.4 Famili D — Geometri Level & Sinyal Mingguan
Menangkap konfigurasi teknikal di sekitar level acuan:

| Nama Fitur | Definisi & Formula Teknis | Hipotesis Finansial |
| :--- | :--- | :--- |
| `prev_range_width_atr` | $(\text{PDH} - \text{PDL}) / \text{ATR}_{D1}$. | Rentang hari kemarin yang sempit lebih mudah ditembus secara permanen (*breakout*). |
| `level_confluence_flag` | Biner: 1 jika $|\text{PDH} - \text{PWH}| \le 0,3 \times \text{ATR}$. | **Injeksi Sinyal Mingguan Utama.** Ketika level harian berimpit dengan level mingguan, likuiditas berlipat ganda $\rightarrow$ target *sweep* bernilai tinggi. |
| `level_age_hours` | Waktu (jam) sejak level terbentuk hingga disentuh $T_0$. | Level yang lebih segar (*fresh*) memiliki reaksi penolakan lebih kuat daripada level usang. |
| `distance_to_next_level_atr` | Jarak ke level kunci berikutnya dalam satuan ATR. | Menilai "ruang kosong" (*vacuum space*) di depan harga untuk melanjutkan penembusan. |

---

### 3.5 Famili E — Dinamika Pendekatan (*Approach Dynamics*)
Menangkap profil momentum saat harga bergerak mendekati level likuiditas:

| Nama Fitur | Definisi & Formula Teknis | Hipotesis Finansial |
| :--- | :--- | :--- |
| `travel_from_day_open_atr` | $|\text{Level} - \text{Open}_{\text{day}}| / \text{ATR}_{14}$. | Jarak tempuh dari pembukaan hari ke level. |
| `hours_since_day_open` | Jumlah candle H1 sejak pergantian hari 17:00 NY. | Mengukur fase siklus hari saat sentuhan terjadi. |
| `cum_return_3` | Return kumulatif 3 candle H1 sebelum $T_0$. | Kecepatan momentum menjelang level (*sharp push* vs *gradual climb*). |
| `opposite_level_swept_today` | Biner: 1 jika level sisi berlawanan sudah tersapu hari ini. | **Kandidat Kuat.** Jika PDL sudah disapu hari ini dan harga berbalik menembus PDH, pola *expansion day* lebih mungkin terjadi. |

---

## 4. Evaluasi Redundansi & Aturan Interaksi (G4 & G5)

1. **Uji Multikolinieritas:** Fitur dengan nilai VIF $> 5,0$ atau korelasi antar-fitur ($|r| > 0,70$) dipangkas. Fitur dengan nilai Information Value (IV) lebih tinggi dipertahankan.
2. **Rule Mining (G5):** Menghasilkan pohon keputusan (*decision tree*) dangkal dengan kedalaman $\text{depth} \le 3$ untuk mengekstrak aturan gabungan yang intuitif bagi trader (misal: `IF adr_used_pct > 85% AND session == 'ASIA' THEN P(Sweep) = 74,2%`).

---

## 5. Batasan Eksogenitas

> [!NOTE]
> **Keterbatasan Data Eksogen:**
> Model ini tidak menggunakan data makroekonomi eksternal (indeks Dolar DXY, imbal hasil US10Y, SPX, atau kalender berita ekonomi NFP/CPI/FOMC). Dampak berita ekonomi berdampak tinggi diserap secara tidak langsung melalui lonjakan volatilitas dan penanda jam sesi, yang dicatat secara terbuka sebagai batasan penelitian.
