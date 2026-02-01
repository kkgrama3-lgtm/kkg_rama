import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

# --- PENGATURAN IDENTITAS PEMBUAT ---
APP_NAME = "KKG Rama"
CREATOR_NAME = "masdintop"   # <--- Ganti Nama Anda
CREATOR_CONTACT = "sdn4kaliaman"   # <--- Ganti No WA
CREATOR_MESSAGE = "support by Pengurus KKG Rama 2026-2030"

# --- URL FOTO HEADER (GANTI DENGAN LINK GAMBAR ANDA) ---
# Tips: Gunakan link gambar yang berakhiran .jpg/.png atau link gambar publik
HEADER_IMAGE_URL = "https://www.facebook.com/photo/?fbid=122120843696087401&set=a.122120843708087401" 
# (Saya pakai gambar ilustrasi guru sementara, nanti Bapak bisa ganti)

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
    """Mendapatkan daftar folder untuk jadi menu navigasi"""
    try:
        query = f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)", orderBy="name").execute()
        return results.get('files', [])
    except:
        return []

def get_announcements(service, parent_id):
    """Membaca file pengumuman (file .txt) dari Drive"""
    try:
        # Kita cari file text yang namanya diawali "[INFO]"
        query = f"'{parent_id}' in parents and name contains '[INFO]' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name, createdTime)", orderBy="createdTime desc").execute()
        files = results.get('files', [])
        
        announcements = []
        for file in files:
            # Download isi file teks
            request = service.files().get_media(fileId=file['id'])
            fh = io.BytesIO()
            downloader = request.execute()
            # Decode isi file
            content = downloader.decode('utf-8')
            # Ambil tanggal dari nama file atau createdTime
            announcements.append({"title": file['name'], "content": content, "id": file['id']})
        return announcements
    except:
        return []

# --- TAMPILAN APLIKASI ---
st.set_page_config(page_title=APP_NAME, page_icon="🏫", layout="wide")
drive_service = get_drive_service()

# --- SIDEBAR NAVIGASI DINAMIS ---
st.sidebar.title("Navigasi")

# 1. Menu Tetap Atas
main_menus = ["🏠 Beranda", "🔐 Area Admin (Upload & Info)"]

# 2. Menu Dinamis (Dari Folder Drive)
st.sidebar.markdown("**📂 Kategori Materi:**")
folders = get_folders(drive_service, PARENT_FOLDER_ID)
folder_map = {f['name']: f['id'] for f in folders} # Simpan ID folder
folder_names = list(folder_map.keys())

# 3. Menu Tetap Bawah
footer_menus = ["🚪 Keluar Aplikasi"]

# Gabungkan Semua Menu
selected_menu = st.sidebar.radio("Pilih Halaman:", main_menus + folder_names + footer_menus)

st.sidebar.markdown("---")
st.sidebar.caption(f"Dev: {CREATOR_NAME}")
st.sidebar.caption("v4.0 (Dynamic Menu)")

# =========================================
# HALAMAN 1: BERANDA
# =========================================
if selected_menu == "🏠 Beranda":
    # A. FOTO HEADER PERMANEN
    st.image(HEADER_IMAGE_URL, use_column_width=True)
    
    st.title(f"🏫 Portal {APP_NAME}")
    
    # B. INFO PENGEMBANG & STATUS
    with st.expander("ℹ️ Info Pengembang & Status Aplikasi", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**Pengelola:** {CREATOR_NAME}")
            st.caption(f"Kontak: {CREATOR_CONTACT}")
        with c2:
            st.metric("Status Database", "Online 🟢")
            
    st.markdown("---")

    # C. PENCARIAN
    st.subheader("🔍 Cari Dokumen")
    search_text = st.text_input("Ketik kata kunci dokumen...", placeholder="Contoh: Modul Ajar Kelas 1")
    
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
    
    # D. PAPAN INFORMASI UPDATE (BERITA TERBARU)
    st.markdown("---")
    st.subheader("📢 Papan Informasi Update")
    
    # Baca file info dari Drive
    infos = get_announcements(drive_service, PARENT_FOLDER_ID)
    
    if infos:
        for info in infos:
            with st.container(border=True):
                # Membersihkan nama file agar tanggal/judul terlihat rapi
                judul_bersih = info['title'].replace(".txt", "").replace("[INFO] ", "")
                st.markdown(f"**🗓️ {judul_bersih}**")
                st.info(info['content'])
    else:
        st.caption("Belum ada informasi terbaru.")

# =========================================
# HALAMAN 2: HALAMAN KATEGORI FOLDER (DINAMIS)
# =========================================
elif selected_menu in folder_names:
    # Ini halaman yang muncul jika user klik nama folder di sidebar
    current_folder_id = folder_map[selected_menu]
    
    st.title(f"📂 Kategori: {selected_menu}")
    st.markdown(f"Daftar dokumen dalam folder **{selected_menu}**")
    st.markdown("---")
    
    try:
        # Tampilkan isi folder tersebut
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
# HALAMAN 3: AREA ADMIN (UPLOAD & TULIS INFO)
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
            # Gunakan folder yang sudah dibaca di awal
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

        # --- TAB 2: TULIS INFO UPDATE ---
        with tab2:
            st.subheader("Buat Pengumuman Baru")
            st.caption("Info ini akan muncul di Halaman Beranda.")
            
            judul_info = st.text_input("Judul Info (Singkat):", placeholder="Contoh: Update Jadwal KKG Maret")
            isi_info = st.text_area("Isi Pengumuman:", height=150)
            
            if st.button("💾 Terbitkan Info"):
                if judul_info and isi_info:
                    with st.spinner("Menerbitkan..."):
                        try:
                            # Simpan sebagai file .txt di Google Drive Folder Utama
                            # Nama file kita beri kode [INFO] agar mudah dicari sistem nanti
                            tanggal = datetime.now().strftime("%d-%m-%Y")
                            nama_file_txt = f"[INFO] {tanggal} - {judul_info}.txt"
                            
                            file_metadata = {
                                'name': nama_file_txt,
                                'parents': [PARENT_FOLDER_ID],
                                'mimeType': 'text/plain'
                            }
                            
                            # Convert string ke file stream
                            media = MediaIoBaseUpload(io.BytesIO(isi_info.encode('utf-8')), mimetype='text/plain', resumable=True)
                            
                            drive_service.files().create(body=file_metadata, media_body=media).execute()
                            st.success("Info berhasil diterbitkan di Beranda!")
                        except Exception as e:
                            st.error(f"Gagal: {e}")
                else:
                    st.warning("Judul dan Isi tidak boleh kosong.")

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
