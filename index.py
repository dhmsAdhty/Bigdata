import pandas as pd
import re

# Membaca dataset
file_path = "BIG DATA - EDIT.csv"
df = pd.read_csv(file_path)

# 1. Mengubah semua nama dengan huruf kapital di awal
df['Nama Santri'] = df['Nama Santri'].apply(lambda x: ' '.join(word.capitalize() for word in x.split()))

# 2. Menghapus spasi yang berlebihan
df['Nama Santri'] = df['Nama Santri'].apply(lambda x: re.sub(r'\s+', ' ', x.strip()))

# 3. Menampilkan data duplikat berdasarkan Nama Santri sebelum dihapus
duplikat = df[df.duplicated(subset=['Nama Santri'], keep=False)]
if not duplikat.empty:
    print("Data duplikat berdasarkan kolom 'Nama Santri':")
    print(duplikat)
else:
    print("Tidak ada data duplikat pada kolom 'Nama Santri'.")

# 4. Menghapus data duplikat berdasarkan Nama Santri (jika ada, hanya satu yang dipertahankan)
df = df.drop_duplicates(subset=['Nama Santri'], keep='first')

# 5. Untuk atribut jenjang dan jenis harus huruf kecil semua
df['Jenjang'] = df['Jenjang'].str.lower()
df['Jenis'] = df['Jenis'].str.lower()

# 6. Menyamakan kata 'wustho' menjadi 'wustha'
df['Jenjang'] = df['Jenjang'].apply(lambda x: x.replace('wustho', 'wustha') if isinstance(x, str) else x)

# 7. Mengkategorikan jenjang = ula(1), wustha(2), ulya(3)
jenjang_mapping = {"ula": 1, "wustha": 2, "ulya": 3}
df["Jenjang"] = df["Jenjang"].map(jenjang_mapping)

# 8. Menghapus karakter aneh
kolom_bersih = [
    'Nama Santri', 
    'NISN',
    'No. Induk Santri', 
    'NPSN', 
    'NSPP', 
    'SK Ijop Terakhir', 
    'No. SKRTM', 
    'No. SKTM', 
    'No. KIP', 
    'No. PKM'
]
for kolom in kolom_bersih:
    df[kolom] = df[kolom].astype(str).apply(lambda x: re.sub(r'[^a-zA-Z0-9\s]', '', x))

# 9. Mengisi semua nilai NaN dengan 0
pd.set_option('future.no_silent_downcasting', True)  # Menghindari FutureWarning
df.replace('nan', pd.NA, inplace=True)               # Ubah 'nan' kecil jadi NaN pandas
df.fillna(0, inplace=True)                           # Isi semua NaN dengan 0
df = df.infer_objects(copy=False)                    # Memastikan tipe data sesuai

# Menyimpan hasil preprocessing
df.to_csv('dataset_preprocessed5.csv', index=False)
print("Preprocessing selesai. Data disimpan dalam 'dataset_preprocessed5.csv'")
