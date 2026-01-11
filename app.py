import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime

# --- KONFIGURASI ---
# Mengambil rahasia dari Streamlit Cloud
try:
    PARENT_FOLDER_ID = st.secrets["gdrive"]["folder_id"]
    SCOPES = ['https://www.googleapis.com/auth/drive']
except:
    st.error("Konfigurasi Secrets belum diatur dengan benar.")
    st.stop()

def authenticate():
    creds_dict = st.secrets["gdrive_creds"]
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

# --- TAMPILAN APLIKASI ---
st.set_page_config(page_title="KKG Rama", page_icon="🏫", layout="wide")

st.title("🏫 Portal KKG Rama")
st.markdown("Aplikasi Penyimpanan & Berbagi Materi Kegiatan KKG")
st.markdown("---")

# Menu Sidebar
menu = st.sidebar.selectbox("Menu Utama", ["Beranda", "Upload Materi", "Cari & Download"])
st.sidebar.markdown("---")
st.sidebar.info("Versi Web App 1.0")

# Koneksi ke Drive
try:
    drive_service = authenticate()
except Exception as e:
    st.error(f"Gagal koneksi: {e}")
    st.stop()

if menu == "Beranda":
    st.header("Selamat Datang Bapak/Ibu Guru")
    st.success("Aplikasi ini terhubung langsung ke Penyimpanan Cloud.")
    
    # Cek jumlah file
    try:
        query = f"'{PARENT_FOLDER_ID}' in parents and trashed=false"
        results = drive_service.files().list(q=query).execute()
        files = results.get('files', [])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Dokumen Tersimpan", len(files))
        with col2:
            st.metric("Status Server", "Online ✅")
    except:
        st.warning("Belum bisa membaca folder. Cek izin Share di Google Drive.")

elif menu == "Upload Materi":
    st.header("📤 Upload File Baru")
    
    uploaded_file = st.file_uploader("Pilih file (PDF, Word, Excel, Gambar)", type=['pdf', 'docx', 'xlsx', 'pptx', 'jpg', 'jpeg', 'png'])
    kategori = st.selectbox("Jenis Dokumen", ["Administrasi KKG", "Perangkat Ajar (RPP/Modul)", "Undangan & Surat", "Dokumentasi Foto", "Lainnya"])
    
    if st.button("Simpan ke Cloud"):
        if uploaded_file:
            with st.spinner("Sedang mengirim data..."):
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d")
                    file_metadata = {
                        'name': f"[{kategori}] {timestamp} - {uploaded_file.name}",
                        'parents': [PARENT_FOLDER_ID]
                    }
                    media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type, resumable=True)
                    drive_service.files().create(body=file_metadata, media_body=media).execute()
                    
                    st.balloons()
                    st.success("Alhamdulillah! File berhasil disimpan.")
                except Exception as e:
                    st.error(f"Gagal upload: {e}")
        else:
            st.warning("Mohon pilih file terlebih dahulu.")

elif menu == "Cari & Download":
    st.header("📂 Cari Arsip")
    
    search_text = st.text_input("Ketik kata kunci (misal: RPP, Undangan)...")
    
    # Tampilkan file
    query = f"'{PARENT_FOLDER_ID}' in parents and trashed=false"
    if search_text:
        query += f" and name contains '{search_text}'"
        
    results = drive_service.files().list(q=query, fields="files(id, name, webViewLink, iconLink)").execute()
    items = results.get('files', [])

    if items:
        for item in items:
            with st.container():
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{item['name']}**")
                with c2:
                    st.link_button("Buka/Download", item['webViewLink'])
                st.divider()
    else:
        st.info("Tidak ada dokumen ditemukan.")
