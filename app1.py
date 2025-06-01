# ======================
# IMPORT LIBRARY
# ======================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
import time
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from fpdf import FPDF
import base64

# ======================
# KONFIGURASI APLIKASI
# ======================
APP_CONFIG = {
    "page_title": "Analisis Kelengkapan Dokumen Santri",
    "page_icon": "📚",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# ======================
# KONSTANTA
# ======================
DOCUMENT_MAPPING = {
    "is_nisn": ["NISN", "nisn"],
    "is_no_induk_santri": ["No. Induk Santri"],
    "is_nspp": ["NSPP"],
    "is_npsn": ["NPSN"],
    "is_sk_ijop_terakhir": ["SK Ijop Terakhir"],
    "is_kip": ["No. KIP", "KIP"],
    "is_pkm": ["No. PKM", "PKM"],
    "is_skrtm": ["No. SKRTM", "SKRTM"],
    "is_sktm": ["No. SKTM", "SKTM"]
}

COLOR_MAP = {
    "Lolos": "#2ecc71",
    "Lolos Bersyarat": "#f39c12",
    "Tidak Lolos": "#e74c3c"
}

MAX_MISSING_DOCS_CONDITIONAL = 2

# ======================
# FUNGSI UTILITAS
# ======================
def animate_progress() -> None:
    """Menampilkan animasi loading selama pemrosesan data"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(101):
        progress_bar.progress(i)
        status_text.text(f"Memproses data... {i}%")
        time.sleep(0.02)
    
    status_text.text("Analisis selesai!")
    time.sleep(0.5)
    status_text.empty()

def preprocess_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """
    Membersihkan dan mempersiapkan data input
    
    1. Standarisasi nama kolom
    2. Konversi data dokumen ke binary (1=lengkap, 0=tidak lengkap)
    3. Identifikasi kolom dokumen
    
    Returns:
        Tuple (DataFrame yang sudah diproses, list kolom dokumen)
    """
    processed_df = df.copy()
    processed_df.columns = processed_df.columns.str.lower().str.replace(' ', '_')
    
    doc_columns = []
    
    for doc_type, possible_names in DOCUMENT_MAPPING.items():
        for col in processed_df.columns:
            if any(name.lower() in col.lower() for name in possible_names):
                processed_df[doc_type] = (~processed_df[col].isna() & (processed_df[col] != '')).astype(int)
                doc_columns.append(doc_type)
                break
    
    return processed_df, doc_columns

def determine_status(row: pd.Series, doc_cols: list) -> str:
    """Menentukan status kelulusan berdasarkan dokumen yang lengkap"""
    missing_count = sum(1 for col in doc_cols if row[col] == 0)
    
    if missing_count == 0:
        return "Lolos"
    elif missing_count <= MAX_MISSING_DOCS_CONDITIONAL:
        return "Lolos Bersyarat"
    else:
        return "Tidak Lolos"

def get_missing_documents(row: pd.Series, doc_cols: list) -> str:
    """Mendapatkan daftar dokumen yang kurang"""
    missing_docs = [doc_type for doc_type in doc_cols if row[doc_type] == 0]
    return ", ".join(missing_docs) if missing_docs else "Tidak ada"

# ======================
# FUNGSI EKSPOR FILE (FIXED UTF-8)
# ======================
class PDF(FPDF):
    """PDF generator dengan fallback font yang aman"""
    
    def __init__(self):
        super().__init__()
        # Gunakan font bawaan FPDF yang tersedia di semua sistem
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(left=15, top=15, right=15)
        
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'Laporan Kelengkapan Dokumen Santri', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')

def create_pdf(df: pd.DataFrame, title: str) -> bytes:
    """
    Membuat PDF modern dengan font bawaan yang tersedia di semua sistem
    
    Args:
        df: DataFrame berisi data santri
        title: Judul laporan
    
    Returns:
        PDF dalam format bytes
    """
    try:
        pdf = PDF()
        pdf.add_page()
        
        # Halaman judul
        pdf.set_font('helvetica', 'B', 18)
        pdf.cell(0, 40, '', 0, 1)
        pdf.cell(0, 15, title, 0, 1, 'C')
        pdf.set_font('helvetica', '', 12)
        pdf.cell(0, 10, f"Tanggal: {datetime.now().strftime('%d %B %Y')}", 0, 1, 'C')
        pdf.add_page()
        
        # Statistik utama
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(0, 10, 'Statistik Kelulusan', 0, 1)
        pdf.ln(5)
        
        total = len(df)
        stats = [
            ('Total Santri', str(total)),
            ('Lolos', f"{(df['status'] == 'Lolos').sum()} ({(df['status'] == 'Lolos').mean():.1%})"),
            ('Lolos Bersyarat', f"{(df['status'] == 'Lolos Bersyarat').sum()} ({(df['status'] == 'Lolos Bersyarat').mean():.1%})"),
            ('Tidak Lolos', f"{(df['status'] == 'Tidak Lolos').sum()} ({(df['status'] == 'Tidak Lolos').mean():.1%})")
        ]
        
        pdf.set_font('helvetica', '', 12)
        for label, value in stats:
            pdf.cell(90, 10, f"{label}:", 0, 0)
            pdf.cell(0, 10, value, 0, 1)
            pdf.ln(3)
        
        pdf.ln(10)
        
        # Daftar santri per kategori
        status_colors = {
            'Lolos': (46, 204, 113),
            'Lolos Bersyarat': (241, 196, 15),
            'Tidak Lolos': (231, 76, 60)
        }
        
        for status, color in status_colors.items():
            pdf.set_font('helvetica', 'B', 12)
            pdf.set_text_color(*color)
            pdf.cell(0, 10, f"Daftar Santri - {status}", 0, 1)
            pdf.set_text_color(0, 0, 0)
            
            filtered_df = df[df['status'] == status].reset_index(drop=True)
            
            if not filtered_df.empty:
                # Header tabel
                pdf.set_fill_color(200, 200, 200)
                pdf.set_font('helvetica', 'B', 10)
                pdf.cell(12, 8, 'No.', 1, 0, 'C', 1)
                pdf.cell(60, 8, 'Nama Santri', 1, 0, 'C', 1)
                pdf.cell(35, 8, 'Status', 1, 0, 'C', 1)
                pdf.cell(0, 8, 'Dokumen Kurang', 1, 1, 'C', 1)
                # Fungsi untuk menulis header tabel (agar bisa dipanggil ulang)
                def write_table_header():
                    pdf.set_fill_color(200, 200, 200)
                    pdf.set_font('helvetica', 'B', 10)
                    pdf.cell(12, 8, 'No.', 1, 0, 'C', 1)
                    pdf.cell(60, 8, 'Nama Santri', 1, 0, 'C', 1)
                    pdf.cell(35, 8, 'Status', 1, 0, 'C', 1)
                    pdf.cell(0, 8, 'Dokumen Kurang', 1, 1, 'C', 1)
                    pdf.set_font('helvetica', '', 9)

                # Isi tabel
                pdf.set_font('helvetica', '', 9)
                line_height = 8
                for idx, (_, row) in enumerate(filtered_df.iterrows(), 1):
                    # Cek apakah perlu ganti halaman dan tulis header tabel jika perlu
                    if pdf.get_y() + line_height > pdf.page_break_trigger:
                        pdf.add_page()
                        write_table_header()
                    # Handle karakter khusus dengan replace
                    nama = str(row['nama_santri']).encode('latin-1', 'replace').decode('latin-1')
                    dokumen = str(row['dokumen_kurang']).encode('latin-1', 'replace').decode('latin-1')
                    status_val = str(row['status']).encode('latin-1', 'replace').decode('latin-1')

                    # Kolom selain status: fill putih, status: warna sesuai
                    pdf.set_fill_color(255, 255, 255)
                    pdf.cell(12, 8, str(idx), 1, 0, 'C', 1)
                    pdf.cell(60, 8, nama, 1, 0, 'L', 1)
                    # Status: warna sesuai
                    if row['status'] == 'Lolos':
                        pdf.set_fill_color(46, 204, 113)  # Hijau
                    elif row['status'] == 'Lolos Bersyarat':
                        pdf.set_fill_color(241, 196, 15)  # Kuning
                    else:
                        pdf.set_fill_color(231, 76, 60)   # Merah
                    pdf.cell(35, 8, status_val, 1, 0, 'C', 1)
                    # Kembalikan fill ke putih untuk kolom berikutnya
                    pdf.set_fill_color(255, 255, 255)
                    pdf.cell(0, 8, dokumen, 1, 1, 'L', 1)
            else:
                pdf.set_font('helvetica', 'I', 10)
                pdf.cell(0, 8, f"Tidak ada santri dengan status {status}", 0, 1)

            pdf.ln(8)

        return pdf.output(dest='S').encode('latin-1')

    except Exception as e:
        raise Exception(f"Gagal membuat PDF: {str(e)}")


# ======================
# FUNGSI CLUSTERING
# ======================
def apply_kmeans_clustering(df: pd.DataFrame, features: list[str], n_clusters: int = 3) -> tuple[pd.DataFrame, dict]:
    """Menerapkan algoritma K-Means clustering pada data"""
    try:
        # 1. Standarisasi fitur
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[features])
        
        # 2. Latih model K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        df['cluster'] = clusters
        
        # 3. Hitung metrik evaluasi
        silhouette_avg = silhouette_score(X_scaled, clusters)
        
        # 4. Reduksi dimensi untuk visualisasi
        pca = PCA(n_components=2)
        principal_components = pca.fit_transform(X_scaled)
        df['PC1'] = principal_components[:, 0]
        df['PC2'] = principal_components[:, 1]
        
        # 5. Hasilkan plot dengan pengecekan kolom hover
        hover_data = {
            'Nama Santri': df['nama_santri'],
            'Status': df['status'],
            'Dokumen Kurang': df['dokumen_kurang']
        }
        
        cluster_plot = px.scatter(
            df,
            x='PC1',
            y='PC2',
            color='cluster',
            title='Visualisasi Cluster (PCA)',
            hover_data=hover_data,
            color_continuous_scale=px.colors.qualitative.Plotly
        )
        
        # 6. Analisis karakteristik cluster
        cluster_stats = df.groupby('cluster')[features].mean().T
        
        return df, {
            'plot': cluster_plot,
            'silhouette_score': silhouette_avg,
            'cluster_stats': cluster_stats,
            'pca': pca,
            'kmeans': kmeans
        }
        
    except Exception as e:
        st.error(f"Error dalam clustering: {str(e)}")
        return df, {}

# ======================
# FUNGSI TAMPILAN
# ======================
def show_analysis_results(df: pd.DataFrame) -> None:
    """Menampilkan hasil analisis utama"""
    st.markdown("---")
    st.markdown("## 📊 Hasil Analisis")
    
    total = len(df)
    lolos = (df['status'] == 'Lolos').sum()
    bersyarat = (df['status'] == 'Lolos Bersyarat').sum()
    tidak_lolos = (df['status'] == 'Tidak Lolos').sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Santri", total)
    with col2:
        st.metric("Lolos", f"{lolos} ({lolos/total:.1%})")
    with col3:
        st.metric("Lolos Bersyarat", f"{bersyarat} ({bersyarat/total:.1%})")
    with col4:
        st.metric("Tidak Lolos", f"{tidak_lolos} ({tidak_lolos/total:.1%})")
    
    st.markdown("### 📈 Distribusi Status")
    status_counts = df['status'].value_counts().reset_index()
    fig = px.pie(status_counts, values='count', names='status', 
                 color='status', color_discrete_map=COLOR_MAP)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 📋 Detail Kelengkapan Dokumen")
    
    # Buat accordion untuk setiap kategori status
    with st.expander("✅ Lolos (Dokumen Lengkap)", expanded=True):
        lolos_df = df[df['status'] == 'Lolos']
        if not lolos_df.empty:
            display_cols = ['nama_santri', 'dokumen_kurang'] + [col for col in df.columns if col.startswith('is_')]
            display_cols = [col for col in display_cols if col in lolos_df.columns]
            st.dataframe(lolos_df[display_cols], use_container_width=True)
        else:
            st.info("Tidak ada santri yang lolos dengan dokumen lengkap")
    
    with st.expander("⚠️ Lolos Bersyarat (Maksimal 2 Dokumen Kurang)"):
        bersyarat_df = df[df['status'] == 'Lolos Bersyarat']
        if not bersyarat_df.empty:
            display_cols = ['nama_santri', 'dokumen_kurang'] + [col for col in df.columns if col.startswith('is_')]
            display_cols = [col for col in display_cols if col in bersyarat_df.columns]
            st.dataframe(bersyarat_df[display_cols], use_container_width=True)
        else:
            st.info("Tidak ada santri yang lolos bersyarat")
    
    with st.expander("❌ Tidak Lolos (Lebih dari 2 Dokumen Kurang)"):
        tidak_lolos_df = df[df['status'] == 'Tidak Lolos']
        if not tidak_lolos_df.empty:
            display_cols = ['nama_santri', 'dokumen_kurang'] + [col for col in df.columns if col.startswith('is_')]
            display_cols = [col for col in display_cols if col in tidak_lolos_df.columns]
            st.dataframe(tidak_lolos_df[display_cols], use_container_width=True)
        else:
            st.info("Tidak ada santri yang tidak lolos")
    
    st.markdown("### 💾 Unduh Hasil")
    col1, col2 = st.columns(2)
    
    with col1:
        # Ekspor CSV
        csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            "Unduh sebagai CSV (UTF-8)",
            data=csv,
            file_name=f"hasil_analisis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Ekspor PDF
        pdf_title = f"Analisis Kelengkapan Dokumen Santri - {datetime.now().strftime('%d/%m/%Y')}"
        try:
            pdf_data = create_pdf(df, pdf_title)
            st.download_button(
                "Unduh sebagai PDF",
                data=pdf_data,
                file_name=f"hasil_analisis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Gagal membuat PDF: {str(e)}")
            st.warning("Pastikan data tidak mengandung karakter khusus yang tidak didukung")

def show_clustering_results(df: pd.DataFrame, clustering_results: dict) -> None:
    """Menampilkan hasil clustering"""
    st.markdown("---")
    st.markdown("## 🧮 Hasil Clustering")
    
    st.plotly_chart(clustering_results['plot'], use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Silhouette Score", f"{clustering_results['silhouette_score']:.2f}",
                 help="Skor antara -1 sampai 1, semakin mendekati 1 semakin baik")
    
    st.markdown("### 📊 Karakteristik Cluster")
    st.dataframe(clustering_results['cluster_stats'], use_container_width=True)
    
    st.markdown("### 📌 Distribusi Status per Cluster")
    cluster_status = pd.crosstab(df['cluster'], df['status'])
    st.bar_chart(cluster_status)

# ======================
# FUNGSI UTAMA
# ======================
def main():
    st.set_page_config(**APP_CONFIG)
    st.title("📚 Analisis Kelengkapan Dokumen Santri")
    
    with st.sidebar:
        st.markdown("### 📂 Upload Data")
        uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
        
        st.markdown("---")
        st.markdown("### ⚙️ Pengaturan Analisis")
        show_animation = st.checkbox("Animasi", value=True)
        use_clustering = st.checkbox("Analisis Clustering", value=False)
        
        if use_clustering:
            n_clusters = st.slider("Jumlah Cluster", 2, 5, 3)
        
        st.markdown("---")
        st.markdown("**Kriteria Kelulusan:**")
        st.markdown(f"- ✅ **Lolos**: Semua dokumen lengkap")
        st.markdown(f"- ⚠️ **Lolos Bersyarat**: Maksimal {MAX_MISSING_DOCS_CONDITIONAL} dokumen kurang")
        st.markdown("- ❌ **Tidak Lolos**: Lebih dari 2 dokumen kurang")

    if not uploaded_file:
        st.info("Silakan upload file CSV untuk memulai analisis")
        return

    try:
        if show_animation:
            animate_progress()
            
        # Baca file CSV dengan encoding UTF-8
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        df, doc_cols = preprocess_data(df)
        
        if df is None:
            return
            
        # Tentukan status terlebih dahulu sebelum clustering
        df["status"] = df.apply(lambda row: determine_status(row, doc_cols), axis=1)
        df["dokumen_kurang"] = df.apply(lambda row: get_missing_documents(row, doc_cols), axis=1)
            
        clustering_results = {}
        if use_clustering:
            df, clustering_results = apply_kmeans_clustering(df, doc_cols, n_clusters)
        
        st.success("✅ Analisis berhasil!")
        show_analysis_results(df)
        
        if use_clustering and clustering_results:
            show_clustering_results(df, clustering_results)
            
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
        st.warning("Pastikan file CSV menggunakan encoding UTF-8 dan format yang benar")

if __name__ == "__main__":
    main()