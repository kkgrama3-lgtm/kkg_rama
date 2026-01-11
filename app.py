import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import time

# --- PENGATURAN IDENTITAS PEMBUAT ---
APP_NAME = "KKG RAMA"
CREATOR_NAME = "masdintop"   # <--- Ganti Nama Anda
CREATOR_CONTACT = "sdn 4 kaliaman"   # <--- Ganti No WA
CREATOR_MESSAGE = "SEMOGA BERMANFAAT"

# --- KONFIGURASI GOOGLE DRIVE ---
try:
    PARENT_FOLDER_ID = st.secrets["gdrive"]["folder_id"]
    if "?" in PARENT_FOLDER_ID:
        PARENT_FOLDER_ID = PARENT_FOLDER_ID.split("?")[0]
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
st.set_page_config(page_title=APP_NAME, page_icon="🏫", layout="wide")

# Koneksi ke Drive
try:
    drive_service = authenticate()
except Exception as e:
    st.error(f"Gagal koneksi: {e}")
    st.stop()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("Navigasi")
# Menambahkan menu "Keluar Aplikasi"
menu = st.sidebar.radio("Pilih Mode:", ["🏠 Beranda & Pencarian", "🔐 Area Admin (Upload)", "🚪 Keluar Aplikasi"])

st.sidebar.markdown("---")
st.sidebar.caption(f"Dev: {CREATOR_NAME}")
st.sidebar.caption("v3.1 (With Exit)")

# =========================================
# HALAMAN 1: BERANDA & PENCARIAN
# =========================================
if menu == "🏠 Beranda & Pencarian":
    st.title(f"🏫 Portal {APP_NAME}")
    st.markdown("Cari dan download materi KKG dengan mudah.")
    st.markdown("---")

    # Info Pengembang
    with st.expander("ℹ️ Info Pengembang & Status Aplikasi", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**Pembuat:** {CREATOR_NAME}")
            st.caption(f"asal: {CREATOR_CONTACT}")
        with c2:
            st.metric("Status Database", "Online 🟢")
    
    st.write("") 

    # Fitur Pencarian
    st.subheader("🔍 Cari Dokumen")
    search_text = st.text_input("Ketik kata kunci dokumen...", placeholder="Contoh: Modul Ajar Kelas 1")

    try:
        with st.spinner("Mencari di arsip..."):
            if search_text:
                query = f"name contains '{search_text}' and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
                pesan_hasil = f"Hasil pencarian untuk: **'{search_text}'**"
            else:
                query = f"'{PARENT_FOLDER_ID}' in parents and trashed=false"
                pesan_hasil = "📂 **Dokumen Terbaru di Folder Utama:**"
            
            results = drive_service.files().list(q=query, fields="files(id, name, webViewLink, iconLink)").execute()
            items = results.get('files', [])

            st.markdown("---")
            st.markdown(pesan_hasil)

            if items:
                for item in items:
                    with st.container():
                        col_a, col_b = st.columns([5, 1])
                        with col_a:
                            st.markdown(f"📄 **{item['name']}**")
                        with col_b:
                            st.link_button("⬇️ Download", item['webViewLink'], use_container_width=True)
                        st.divider()
            else:
                if search_text:
                    st.warning("Tidak ditemukan dokumen.")
                else:
                    st.info("Folder utama kosong atau file ada di sub-folder.")
    except Exception as e:
        st.error("Terjadi gangguan koneksi.")

# =========================================
# HALAMAN 2: AREA ADMIN (UPLOAD)
# =========================================
elif menu == "🔐 Area Admin (Upload)":
    st.title("🔐 Area Khusus Admin")
    st.markdown("---")
    
    col_pass, col_dummy = st.columns([1, 2])
    with col_pass:
        password = st.text_input("Masukkan Password:", type="password")
    
    if password == "gugusr4m4":
        st.success(f"Login Admin Diterima.")
        
        try:
            folder_query = f"'{PARENT_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            folder_results = drive_service.files().list(q=folder_query, fields="files(id, name)").execute()
            folders = folder_results.get('files', [])
            
            if folders:
                folder_names = [f['name'] for f in folders]
                pilihan_folder = st.selectbox("📂 Pilih Folder Penyimpanan:", folder_names)
                target_folder_id = next(item['id'] for item in folders if item["name"] == pilihan_folder)
            else:
                st.warning("⚠️ Tidak ada sub-folder. File akan masuk ke Folder Utama.")
                target_folder_id = PARENT_FOLDER_ID
            
            st.markdown("### Upload File Baru")
            uploaded_file = st.file_uploader("Pilih file:", type=['pdf', 'docx', 'xlsx', 'pptx', 'jpg', 'jpeg', 'png'])
            
            if st.button("🚀 Upload Sekarang", type="primary"):
                if uploaded_file:
                    with st.spinner("Mengunggah..."):
                        try:
                            timestamp = datetime.now().strftime("%Y-%m-%d")
                            file_metadata = {'name': f"{timestamp} - {uploaded_file.name}", 'parents': [target_folder_id]}
                            media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type, resumable=True)
                            drive_service.files().create(body=file_metadata, media_body=media).execute()
                            st.balloons()
                            st.success("✅ Berhasil Upload!")
                        except Exception as e:
                            st.error(f"Gagal: {e}")
                else:
                    st.toast("Pilih file dulu!")
        except Exception as e:
            st.error(f"Error: {e}")
    elif password != "":
        st.error("Password salah.")

# =========================================
# HALAMAN 3: KELUAR APLIKASI
# =========================================
elif menu == "🚪 Keluar Aplikasi":
    st.header("Sampai Jumpa! 👋")
    st.success("Terima kasih telah menggunakan aplikasi KKG Rama.")
    
    st.markdown("""
    <div style="background-color:#f0f2f6; padding:20px; border-radius:10px;">
        <p>Anda telah mengakhiri sesi penggunaan aplikasi.</p>
        <p><strong>Untuk keamanan data, silakan tutup Tab Browser atau Aplikasi ini sekarang.</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    
    # Tombol Refresh jika user berubah pikiran
    if st.button("🔄 Buka Aplikasi Kembali"):
        st.rerun()
