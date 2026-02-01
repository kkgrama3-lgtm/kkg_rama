import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

# --- PENGATURAN IDENTITAS PEMBUAT ---
APP_NAME = "KKG Rama"
CREATOR_NAME = "masdintop (sdn4kaliaman)"   # <--- Ganti Nama Anda
CREATOR_CONTACT = "support by Pengurus KKG Rama 2026-2030"   # <--- Ganti No WA
CREATOR_MESSAGE = "Hubungi saya jika ada kendala akses."

# --- URL FOTO HEADER ---
HEADER_IMAGE_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEiPq6jM3uGz9ZZ4Q7f5X5x8Y8Y8Y8Y8Y8Y8Y8Y8Y8/s1600/guru-belajar.jpg" 

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
        results = service.files().list(q=query, fields="files(id, name)", orderBy="name").execute()
        return results.get('files', [])
    except:
        return []

def get_announcements(service, parent_id):
    try:
        query = f"'{parent_id}' in parents and name contains '[INFO]' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name, createdTime)", orderBy="createdTime desc").execute()
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

# --- SIDEBAR NAVIGASI (URUTAN BARU) ---
st.sidebar.title("Navigasi")

# 1. Menu Tetap Atas (Hanya Beranda)
main_menus = ["Beranda"]

# 2. Menu Dinamis (Folder Drive)
st.sidebar.markdown("**📂 Kategori Materi:**")
folders = get_folders(drive_service, PARENT_FOLDER_ID)
folder_map = {f['name']: f['id'] for f in folders}
folder_names = list(folder_map.keys())

# 3. Menu Bawah (Admin & Keluar)
# Perubahan: Area Admin dipindah ke sini agar ada di bawah
footer_menus = ["🔐 Area Admin (Upload & Info)", "🚪 Keluar Aplikasi"]

# Gabungkan Semua Menu: Beranda -> Folder -> Admin -> Keluar
all_menus = main_menus + folder_names + footer_menus
selected_menu = st.sidebar.radio("Pilih Halaman:", all_menus)

st.sidebar.markdown("---")
st.sidebar.caption(f"Dev: {CREATOR_NAME}")
st.sidebar.caption("v4.1 (Reordered Menu)")

# =========================================
# HALAMAN 1: BERANDA
# =========================================
if selected_menu == "Beranda":
    st.image(HEADER_IMAGE_URL, use_column_width=True)
    st.title(f"🏫 Portal {APP_NAME}")
    
    with st.expander("ℹ️ Info Pengembang & Status Aplikasi", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**Pengelola:** {CREATOR_NAME}")
            st.caption(f"Kontak: {CREATOR_CONTACT}")
        with c2:
            st.metric("Status Database", "Online 🟢")
            
    st.markdown("---")

    st.subheader("🔍 Cari Dokumen")
    search_text = st.text_input("Ketik kata kunci dokumen...", placeholder="Contoh: RPP Kelas 1")
    
    if search_text:
        with st.spinner("Mencari..."):
            try:
                query = f"name contains '{search_text}' and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
                results = drive_service.files().list(q=query, fields="files(id, name, webViewLink)").execute()
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
    st.title(f"📂 Kategori: {selected_menu}")
    st.markdown(f"Daftar dokumen dalam folder **{selected_menu}**")
    st.markdown("---")
    
    try:
        query = f"'{current_folder_id}' in parents and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name, webViewLink, mimeType)").execute()
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
                            drive_service.files().create(body=file_metadata, media_body=media).execute()
                            st.success("Berhasil Upload!")
                        except Exception as e:
                            st.error(f"Gagal: {e}")

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
                            drive_service.files().create(body=file_metadata, media_body=media).execute()
                            st.success("Info berhasil diterbitkan!")
                        except Exception as e:
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
