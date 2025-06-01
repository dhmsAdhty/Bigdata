

## 📚 Analisis Kelengkapan Dokumen Santri

Aplikasi berbasis **Streamlit** untuk menganalisis kelengkapan dokumen santri dan menghasilkan laporan statistik beserta file PDF rekap data.

### 🚀 Fitur Utama

* Deteksi otomatis kelengkapan dokumen berdasarkan file Excel yang diunggah
* Visualisasi data kelulusan (Lolos, Lolos Bersyarat, Tidak Lolos)
* Ekspor laporan rekap dalam format PDF
* Progress bar interaktif saat analisis berjalan

---

### 📂 Struktur Dokumen yang Didukung

| Nama Dokumen (Alias) | Kolom yang Dicari di Excel |
| -------------------- | -------------------------- |
| NISN                 | `NISN`, `nisn`             |
| No. Induk Santri     | `No. Induk Santri`         |
| NSPP                 | `NSPP`                     |
| NPSN                 | `NPSN`                     |
| SK Ijop Terakhir     | `SK Ijop Terakhir`         |
| KIP                  | `No. KIP`, `KIP`           |
| PKM                  | `No. PKM`, `PKM`           |
| SKRTM                | `No. SKRTM`, `SKRTM`       |
| SKTM                 | `No. SKTM`, `SKTM`         |

---

### 🛠️ Cara Instalasi

1. **Clone repositori ini**

   ```bash
   git clone https://github.com/dhmsAdhty/Bigdata.git
   cd Bigdata
   ```

2. **Buat virtual environment (opsional tapi disarankan)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**

    Kamu bisa install semua dependensi dengan perintah berikut (misal dalam virtual environment atau sebelum deploy):

```bash
pip install streamlit pandas plotly numpy scikit-learn fpdf
```
---

### ▶️ Cara Menjalankan Aplikasi

1. Pastikan Anda berada di direktori proyek, lalu jalankan:

   ```bash
   streamlit run app1.py
   ```

2. Aplikasi akan terbuka di browser (biasanya `http://localhost:8501`)

---

### 📥 Contoh Input Excel

Pastikan file Excel Anda memiliki kolom:

* `Nama Santri`
* Serta dokumen-dokumen seperti `NISN`, `No. Induk Santri`, dll.

Contoh struktur Excel:

| Nama Santri | NISN     | No. Induk Santri | NSPP  | SK Ijop Terakhir | ... |
| ----------- | -------- | ---------------- | ----- | ---------------- | --- |
| Ahmad       | 12345678 | 001              | 88888 | Ada              |     |
| Fatimah     |          | 002              |       | Ada              |     |

---

### 🖨️ Fitur Ekspor PDF

* PDF akan berisi statistik dan daftar santri beserta dokumen yang kurang
* Font menggunakan `helvetica` agar universal di semua sistem

---

### 📦 Requirements

* Python ≥ 3.8
* Streamlit
* Pandas
* Plotly
* Scikit-learn
* FPDF

