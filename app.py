import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io
from PIL import Image

# --- PENGATURAN IDENTITAS PEMBUAT ---
APP_NAME = "KKG Rama"
CREATOR_NAME = "masdintop (sdn4kaliaman)"
CREATOR_CONTACT = "Pengurus KKG Rama 2026-2030"

# --- PENGATURAN GAMBAR ---
HEADER_IMAGE_FILE = "Foto Bareng KKG.jpg" 
LOGO_IMAGE_FILE = "Logo KKG Rama.png"

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

def get_announcements(service, parent_id):
    try:
        query = f"'{parent_id}' in parents and name contains '[INFO]' and trashed=false"
        results = service.files().list(
            q=query, fields="files(id, name, createdTime)", orderBy="createdTime desc",
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        announcements = []
        for file in files:
            request = service.files().get_media(fileId=file['id'])
            fh = io.BytesIO()
            downloader = request.execute()
            content = downloader.decode('utf-8')
            announcements.append({"title": file['name'], "content": content, "id": file['id']})
        return announcements
    except:
        return []

# --- TAMPILAN APLIKASI ---
st.set_page_config(page_title=APP_NAME, page_icon="🏫", layout="wide")
drive_service = get_drive_service()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("Navigasi")
main_menus = ["Beranda"]
st.sidebar.markdown("**📂 Daftar Isi:**")
folders = get_folders(drive_service, PARENT_FOLDER_ID)
folder_map = {f['name']: f['id'] for f in folders}
folder_names = list(folder_map.keys())
footer_menus = ["🔐 Area Admin (Upload & Info)", "🚪 Keluar Aplikasi"]
all_menus = main_menus + folder_names + footer_menus
selected_menu = st.sidebar.radio("Pilih Halaman:", all_menus)

st.sidebar.markdown("---")
st.sidebar.caption(f"Dev: {CREATOR_NAME}")
st.sidebar.caption("v4.4 (Smart Error Handling)")

# =========================================
# HALAMAN 1: BERANDA
# =========================================
if selected_menu == "Beranda":
    try:
        st.image(HEADER_IMAGE_FILE, use_column_width=True)
    except:
        st.warning(f"Gambar header '{HEADER_IMAGE_FILE}' belum ditemukan.")

    try:
        col_logo, col_title = st.columns([1, 5])
        with col_logo: st.image(LOGO_IMAGE_FILE, width=120)
        with col_title:
            st.markdown(f"# Portal {APP_NAME}")
            st.markdown("#### Aplikasi Berbagi Materi KKG")
    except:
         st.title(f"🏫 Portal {APP_NAME}")
    
    st.markdown("---")
    with st.expander("ℹ️ Info Pengembang & Status Aplikasi", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**Pengelola:** {CREATOR_NAME}")
            st.caption(f"Support by: {CREATOR_CONTACT}")
        with c2:
            st.metric("Status Database", "Online 🟢")
            
    st.markdown("---")

    st.subheader("🔍 Cari Dokumen")
    search_text = st.text_input("Ketik kata kunci dokumen...", placeholder="Contoh: Modul Ajar Kelas 1")
    
    if search_text:
        with st.spinner("Mencari..."):
            try:
                query = f"name contains '{search_text}' and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
                results = drive_service.files().list(
                    q=query, fields="files(id, name, webViewLink)",
                    supportsAllDrives=True, includeItemsFromAllDrives=True
                ).execute()
                items = results.get('files', [])
                if items:
                    st.success(f"Ditemukan {len(items)} hasil:")
                    for item in items:
                        c_a, c_b = st.columns([5, 1])
                        c_a.markdown(f"📄 {item['name']}")
                        c_b.link_button("Unduh", item['webViewLink'])
                        st.divider()
                else:
                    st.warning("Tidak ditemukan.")
            except:
                st.error("Gagal mencari.")
    
    st.markdown("---")
    st.subheader("📢 Papan Informasi Update")
    infos = get_announcements(drive_service, PARENT_FOLDER_ID)
    if infos:
        for info in infos:
            with st.container(border=True):
                judul_bersih = info['title'].replace(".txt", "").replace("[INFO] ", "")
                st.markdown(f"**🗓️ {judul_bersih}**")
                st.info(info['content'])
    else:
        st.caption("Belum ada informasi terbaru.")

# =========================================
# HALAMAN 2: HALAMAN KATEGORI FOLDER
# =========================================
elif selected_menu in folder_names:
    current_folder_id = folder_map[selected_menu]
    try:
        c_log, c_tit = st.columns([0.5, 5])
        with c_log: st.image(LOGO_IMAGE_FILE, width=60)
        with c_tit: st.title(f"📂 {selected_menu}")
    except:
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
                    with c2:
                        st.link_button("Buka/Unduh", item['webViewLink'])
                    st.divider()
        else:
            st.info("Folder ini masih kosong.")
    except Exception as e:
        st.error("Gagal memuat folder.")

# =========================================
# HALAMAN 3: AREA ADMIN
# =========================================
elif selected_menu == "🔐 Area Admin (Upload & Info)":
    st.title("🔐 Area Khusus Admin")
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "admin123":
        st.success(f"Akses Diterima.")
        tab1, tab2 = st.tabs(["📤 Upload File", "📢 Tulis Info Update"])
        
        # --- TAB 1: UPLOAD FILE ---
        with tab1:
            st.subheader("Upload Dokumen Baru")
            if folder_names:
                pilihan_folder = st.selectbox("Simpan ke Folder:", folder_names)
                target_folder_id = folder_map[pilihan_folder]
            else:
                st.warning("Tidak ada sub-folder. Masuk ke Folder Utama.")
                target_folder_id = PARENT_FOLDER_ID
                
            uploaded_file = st.file_uploader("Pilih file:", type=['pdf', 'docx', 'xlsx', 'pptx', 'jpg', 'png'])
            
            if st.button("🚀 Upload File"):
                if uploaded_file:
                    with st.spinner("Mengunggah..."):
                        try:
                            timestamp = datetime.now().strftime("%Y-%m-%d")
                            file_metadata = {'name': f"{timestamp} - {uploaded_file.name}", 'parents': [target_folder_id]}
                            media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type, resumable=True)
                            
                            drive_service.files().create(
                                body=file_metadata, media_body=media, 
                                supportsAllDrives=True
                            ).execute()
                            
                            st.success("Berhasil Upload!")
                        except Exception as e:
                            # PENANGANAN KHUSUS ERROR KUOTA
                            error_message = str(e)
                            if "storageQuotaExceeded" in error_message or "Service Accounts do not have storage quota" in error_message:
                                st.error("⚠️ Gagal: Kuota Robot Habis/Dibatasi.")
                                st.warning("""
                                **Masalah:** Akun Google Gratis membatasi Robot untuk membuat file baru.
                                **Solusi:** Silakan upload manual lewat link tombol di bawah ini. File akan tetap muncul di aplikasi setelah diupload.
                                """)
                                # Link ke Folder Google Drive yang dituju
                                folder_link = f"https://drive.google.com/drive/u/0/folders/{target_folder_id}"
                                st.link_button(f"📂 Buka Folder '{pilihan_folder}' di Google Drive", folder_link)
                            else:
                                st.error(f"Gagal: {e}")

        # --- TAB 2: TULIS INFO UPDATE ---
        with tab2:
            st.subheader("Buat Pengumuman Baru")
            judul_info = st.text_input("Judul Info:", placeholder="Contoh: Jadwal Maret")
            isi_info = st.text_area("Isi Pengumuman:", height=150)
            
            if st.button("💾 Terbitkan Info"):
                if judul_info and isi_info:
                    with st.spinner("Menerbitkan..."):
                        try:
                            tanggal = datetime.now().strftime("%d-%m-%Y")
                            file_metadata = {'name': f"[INFO] {tanggal} - {judul_info}.txt", 'parents': [PARENT_FOLDER_ID], 'mimeType': 'text/plain'}
                            media = MediaIoBaseUpload(io.BytesIO(isi_info.encode('utf-8')), mimetype='text/plain', resumable=True)
                            
                            drive_service.files().create(
                                body=file_metadata, media_body=media, 
                                supportsAllDrives=True
                            ).execute()
                            
                            st.success("Info berhasil diterbitkan!")
                        except Exception as e:
                            error_message = str(e)
                            if "storageQuotaExceeded" in error_message:
                                st.error("⚠️ Gagal Terbit: Batasan Akun Gratis.")
                                st.info("Tips: Gunakan akun Belajar.id (Shared Drive) agar fitur ini berfungsi.")
                            else:
                                st.error(f"Gagal: {e}")
    elif password != "":
        st.error("Password salah.")

# =========================================
# HALAMAN 4: KELUAR
# =========================================
elif selected_menu == "🚪 Keluar Aplikasi":
    st.header("Sampai Jumpa!")
    st.markdown("Silakan tutup tab browser Anda untuk keamanan data.")
    if st.button("Buka Kembali"):
        st.rerun()
