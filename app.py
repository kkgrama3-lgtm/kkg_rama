import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

# --- PENGATURAN IDENTITAS PEMBUAT ---
APP_NAME = "KKG Rama"
CREATOR_NAME = "masdintop (sdn4kaliaman)"
CREATOR_CONTACT = "Pengurus KKG Rama 2026-2030"

# --- PENGATURAN GAMBAR ---
HEADER_IMAGE_FILE = "Foto Bareng KKG.jpg" 
LOGO_IMAGE_FILE = "Logo KKG Rama.png"

# --- PENGATURAN ID FOLDER (PENTING!) ---
# 1. PARENT_FOLDER_ID: Diambil dari secrets (Folder Utama Dokumen)
# 2. INFO_FOLDER_ID: Masukkan ID Folder Khusus Info di bawah ini (Manual)
INFO_FOLDER_ID = "153jOCfhplc22HZsZTNCypqxOjF1p_25m" 
# Contoh: INFO_FOLDER_ID = "1KIqyTb7_xxxxxxxxx_yyyyyyyy"

# --- KONFIGURASI GOOGLE DRIVE ---
try:
    PARENT_FOLDER_ID = st.secrets["gdrive"]["folder_id"]
    if "?" in PARENT_FOLDER_ID:
        PARENT_FOLDER_ID = PARENT_FOLDER_ID.split("?")[0]
        
    # Jika INFO_FOLDER_ID belum diisi user, gunakan Folder Utama sebagai cadangan
    if "MASUKKAN_ID" in INFO_FOLDER_ID:
        INFO_FOLDER_ID = PARENT_FOLDER_ID
        
    SCOPES = ['https://www.googleapis.com/auth/drive']
except:
    st.error("Konfigurasi Secrets belum diatur dengan benar.")
    st.stop()

def authenticate():
    creds_dict = st.secrets["gdrive_creds"]
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

# --- FUNGSI BANTUAN ---
def get_drive_service():
    try:
        return authenticate()
    except Exception as e:
        st.error(f"Gagal koneksi: {e}")
        st.stop()

def get_folders(service, parent_id):
    try:
        query = f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query, fields="files(id, name)", orderBy="name",
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        return results.get('files', [])
    except:
        return []

def get_announcements(service, folder_id_khusus):
    try:
        # Sekarang mencari di folder_id_khusus, bukan parent utama
        query = f"'{folder_id_khusus}' in parents and mimeType = 'text/plain' and trashed=false"
        results = service.files().list(
            q=query, fields="files(id, name, createdTime)", orderBy="createdTime desc",
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        announcements = []
        for file in files:
            # Baca isi file teks
            request = service.files().get_media(fileId=file['id'])
            fh = io.BytesIO()
            downloader = request.execute()
            content = downloader.decode('utf-8')
            announcements.append({"title": file['name'], "content": content, "id": file['id']})
        return announcements
    except:
        return []

# --- CSS KHUSUS AGAR TAMPILAN ELEGAN ---
def local_css():
    st.markdown("""
    <style>
        img { border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .main-title { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0; }
        .sub-title { font-size: 1.2rem; color: #555; margin-top: -10px; }
        .info-box { background-color: #f0f9ff; border-left: 5px solid #0ea5e9; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- TAMPILAN APLIKASI ---
st.set_page_config(page_title=APP_NAME, page_icon="🏫", layout="wide")
local_css()
drive_service = get_drive_service()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("Navigasi")
main_menus = ["Beranda"]
st.sidebar.markdown("**📂 Daftar Isi:**")

folders = get_folders(drive_service, PARENT_FOLDER_ID)
folder_map = {f['name']: f['id'] for f in folders}
folder_names = list(folder_map.keys())

footer_menus = ["🔐 Area Admin (Upload Info)", "🚪 Keluar Aplikasi"]
all_menus = main_menus + folder_names + footer_menus
selected_menu = st.sidebar.radio("Pilih Halaman:", all_menus)

st.sidebar.markdown("---")
st.sidebar.caption(f"Dev: {CREATOR_NAME}")
st.sidebar.caption("v5.2 (Custom Info Folder)")

# =========================================
# HALAMAN 1: BERANDA
# =========================================
if selected_menu == "Beranda":
    
    # Header
    col_header_1, col_header_2 = st.columns([1, 6])
    with col_header_1:
        try: st.image(LOGO_IMAGE_FILE, width=100)
        except: st.warning("Logo hilang")
    with col_header_2:
        st.markdown(f'<h1 class="main-title"> {APP_NAME}</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-title"> Berbagi Materi & Informasi </p>', unsafe_allow_html=True)

    st.markdown("---")

    # Split Layout
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("🔍 Cari Dokumen")
        search_text = st.text_input("Ketik kata kunci...", placeholder="Contoh: Modul Ajar, Undangan", label_visibility="collapsed")
        
        if search_text:
            with st.spinner("Mencari..."):
                try:
                    # Mencari di folder utama (Parent)
                    query = f"'{PARENT_FOLDER_ID}' in parents and name contains '{search_text}' and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
                    results = drive_service.files().list(
                        q=query, fields="files(id, name, webViewLink)",
                        supportsAllDrives=True, includeItemsFromAllDrives=True
                    ).execute()
                    items = results.get('files', [])
                    if items:
                        st.success(f"Ditemukan {len(items)} hasil:")
                        for item in items:
                            c_a, c_b = st.columns([5, 2])
                            c_a.markdown(f"📄 **{item['name']}**")
                            c_b.link_button("⬇️ Unduh", item['webViewLink'])
                            st.divider()
                    else:
                        st.warning("Tidak ditemukan (Pastikan file ada di Folder Utama, bukan Sub-folder).")
                except:
                    st.error("Terjadi kesalahan pencarian.")
        
        # --- LOGIKA INFO TERBARU (Mengambil dari Folder Khusus) ---
        st.write("") 
        st.subheader("📢 Informasi Terbaru")
        
        # Ambil info dari folder khusus INFO_FOLDER_ID
        infos = get_announcements(drive_service, INFO_FOLDER_ID)
        
        with st.container(height=300, border=True):
            if infos:
                for info in infos:
                    judul_bersih = info['title'].replace(".txt", "").replace("[INFO] ", "")
                    st.markdown(f"""
                    <div class="info-box">
                        <strong>🗓️ {judul_bersih}</strong><br>
                        {info['content']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                if "MASUKKAN_ID" in INFO_FOLDER_ID:
                    st.warning("⚠️ ID Folder Info belum disetting di script (Baris 17).")
                else:
                    st.caption(f"Belum ada info di folder khusus ini.")

    with col_right:
        try: st.image(HEADER_IMAGE_FILE, use_column_width=True, caption="Keluarga Besar KKG Rama")
        except: st.info("Foto header belum diupload.")
        
        with st.expander("ℹ️ Tentang Aplikasi", expanded=True):
            st.caption(f"Aplikasi ini dikelola oleh **{CREATOR_NAME}**, disupport oleh **{CREATOR_CONTACT}.")

# =========================================
# HALAMAN 2: KATEGORI FOLDER
# =========================================
elif selected_menu in folder_names:
    current_folder_id = folder_map[selected_menu]
    st.title(f"📂 {selected_menu}")
    st.markdown("---")
    try:
        query = f"'{current_folder_id}' in parents and trashed=false"
        results = drive_service.files().list(
            q=query, fields="files(id, name, webViewLink, mimeType)",
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        items = results.get('files', [])
        
        if items:
            for item in items:
                with st.container():
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        icon = "📁" if item['mimeType'] == 'application/vnd.google-apps.folder' else "📄"
                        st.markdown(f"{icon} **{item['name']}**")
                    with c2: st.link_button("Buka", item['webViewLink'])
                    st.divider()
        else:
            st.info("Folder ini kosong.")
    except:
        st.error("Gagal memuat folder.")

# =========================================
# HALAMAN 3: AREA ADMIN
# =========================================
elif selected_menu == "🔐 Area Admin (Upload Info)":
    st.title("🔐 Area Admin")
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "admin123":
        st.success("Login Berhasil.")
        tab1, tab2 = st.tabs(["📤 Upload Materi", "📢 Tulis Info Beranda"])
        
        # --- TAB 1: UPLOAD DOKUMEN (Masuk ke Folder Pilihan / Utama) ---
        with tab1:
            st.subheader("Upload Dokumen")
            if folder_names:
                pilihan_folder = st.selectbox("Pilih Folder Tujuan:", folder_names)
                target_folder_id = folder_map[pilihan_folder]
            else:
                target_folder_id = PARENT_FOLDER_ID
                
            uploaded_file = st.file_uploader("Pilih file (PDF/Word/Excel):")
            
            if st.button("🚀 Upload Dokumen"):
                if uploaded_file:
                    with st.spinner("Mengupload..."):
                        try:
                            file_metadata = {'name': uploaded_file.name, 'parents': [target_folder_id]}
                            media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type, resumable=True)
                            drive_service.files().create(body=file_metadata, media_body=media, supportsAllDrives=True).execute()
                            st.success("✅ Dokumen berhasil diupload!")
                        except Exception as e:
                            st.error(f"Gagal: {e}")

        # --- TAB 2: TULIS INFO (Masuk ke Folder KHUSUS INFO) ---
        with tab2:
            st.subheader("Tulis Info Baru")
            st.markdown(f"Info ini akan disimpan otomatis ke folder khusus (ID: `{INFO_FOLDER_ID[:5]}...`).")
            
            judul_info = st.text_input("Judul Singkat:")
            isi_info = st.text_area("Isi Pengumuman:", height=100)
            
            if st.button("💾 Terbitkan Info"):
                if judul_info and isi_info:
                    with st.spinner("Menerbitkan..."):
                        try:
                            tanggal = datetime.now().strftime("%d-%m-%Y")
                            # Simpan ke INFO_FOLDER_ID, bukan Parent Utama
                            file_metadata = {
                                'name': f"[INFO] {tanggal} - {judul_info}.txt", 
                                'parents': [INFO_FOLDER_ID], 
                                'mimeType': 'text/plain'
                            }
                            media = MediaIoBaseUpload(io.BytesIO(isi_info.encode('utf-8')), mimetype='text/plain', resumable=True)
                            drive_service.files().create(body=file_metadata, media_body=media, supportsAllDrives=True).execute()
                            st.success("✅ Info berhasil tampil di Beranda!")
                        except Exception as e:
                            st.error(f"Gagal: {e}")
    elif password != "":
        st.error("Password salah.")

# =========================================
# HALAMAN 4: KELUAR
# =========================================
elif selected_menu == "🚪 Keluar Aplikasi":
    st.markdown("### Anda telah keluar.")
    if st.button("Masuk Kembali"):
        st.rerun()
