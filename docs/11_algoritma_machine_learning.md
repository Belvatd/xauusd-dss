# 11. Pengenalan Algoritma Machine Learning (XGBoost & LightGBM)

Dalam membangun Sistem Pendukung Keputusan (DSS) pada Fase 3, riset ini menggunakan algoritma klasifikasi tingkat lanjut berbasis pohon keputusan (*Decision Tree*). Dua algoritma kandidat terkuat yang sering digunakan di industri finansial adalah **XGBoost** dan **LightGBM**.

Keduanya berasal dari keluarga algoritma yang sama, yaitu ***Gradient Boosting***. Sebelum membahas bedanya, mari kita pahami dulu apa itu *Gradient Boosting*.

---

## 1. Konsep Dasar *Gradient Boosting* (Analogi Tim Dokter)

Bayangkan Anda memiliki kasus penyakit langka (dalam hal ini: memprediksi pergerakan Emas) dan Anda meminta bantuan sebuah tim dokter (*pohon keputusan*).
1. **Dokter Pertama** membuat diagnosis awal. Tentu saja, diagnosis ini masih kasar dan ada beberapa pasien yang salah didiagnosis (ada *error*).
2. **Dokter Kedua** tidak memeriksa ulang seluruh pasien dari awal. Ia **hanya fokus pada pasien yang salah didiagnosis** oleh Dokter Pertama, lalu berusaha memperbaikinya.
3. **Dokter Ketiga** melakukan hal yang sama: hanya fokus memperbaiki kesalahan spesifik yang dibuat oleh Dokter Kedua.
4. Hal ini diulang sampai ratusan dokter.

Pada akhirnya, keputusan akhir diambil berdasarkan hasil rapat berantai dari ratusan dokter tersebut. Teknik belajar dari kesalahan model sebelumnya secara terus-menerus inilah yang disebut **Gradient Boosting**. Karena prosesnya sangat teliti, akurasinya sangat luar biasa tinggi.

---

## 2. Apa itu XGBoost? (*eXtreme Gradient Boosting*)

XGBoost adalah salah satu algoritma paling terkenal di dunia *Data Science* (sering memenangkan kompetisi AI global).
* **Cara Kerja:** XGBoost menumbuhkan "pohon keputusan" secara horizontal, lapis demi lapis (*level-wise*). Seperti membangun rumah susun, ia harus menyelesaikan lantai 1 secara merata, baru boleh naik ke lantai 2, lalu lantai 3, dan seterusnya.
* **Kelebihan:** Sangat stabil, kokoh, dan hampir tidak pernah gagal memberikan akurasi tinggi pada data terstruktur (seperti data finansial Emas kita).
* **Kekurangan:** Karena ia harus memeriksa dan membangun segala sesuatunya secara merata dan menyeluruh, ia cenderung **sedikit lebih lambat** dan memakan memori komputer yang lebih besar jika datanya jutaan baris.

---

## 3. Apa itu LightGBM? (*Light Gradient Boosting Machine*)

LightGBM adalah algoritma buatan Microsoft yang diciptakan untuk mengatasi masalah kecepatan pada XGBoost. Kata "Light" berarti Ringan/Cepat.
* **Cara Kerja:** Berbeda dengan XGBoost, LightGBM menumbuhkan pohon keputusannya secara vertikal pada daun yang paling bermasalah (*leaf-wise*). Alih-alih membangun rumah susun lapis demi lapis, ia ibarat tukang yang hanya fokus membangun menara tinggi di bagian sudut rumah yang atapnya paling bocor. Ia mengabaikan area yang sudah bagus.
* **Kelebihan:** Sesuai namanya, algoritma ini **sangat cepat**, memakan memori yang jauh lebih kecil, dan sangat jago menangani data berskala masif dengan jutaan baris tanpa membuat komputer *hang*.
* **Kekurangan:** Karena saking fokusnya mengejar area yang "bocor", jika datanya terlalu sedikit (kurang dari 10.000 baris), LightGBM bisa terlalu menghafal data (*overfitting*) sehingga akurasinya memburuk di dunia nyata.

---

## Ringkasan untuk Riset Anda
Karena data *Gold* kita berjumlah **3.148 baris event**, keduanya sangat layak untuk diuji coba. 
* Jika Anda mencari kecepatan saat melakukan iterasi eksperimen fitur-fitur teknikal baru, **LightGBM** akan sangat menghemat waktu Anda. 
* Namun, jika akurasi adalah segalanya dan komputer (Databricks) Anda memiliki spesifikasi memori yang tinggi, **XGBoost** bisa menjadi mesin prediksi *Liquidity Sweep* yang sangat presisi. 

Keduanya adalah pilihan kelas berat *(state-of-the-art)* yang jauh lebih unggul dibandingkan algoritma konvensional (seperti *Logistic Regression* atau *Random Forest* biasa).
