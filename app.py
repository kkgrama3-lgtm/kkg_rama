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

# --- PENGATURAN ID FOLDER ---
INFO_FOLDER_ID = "153jOCfhplc22HZsZTNCypqxOjF1p_25m" 

# --- KONFIGURASI GOOGLE DRIVE ---
try:
    # Mengambil konfigurasi dari Secrets
    if "gdrive" in st.secrets:
        PARENT_FOLDER_ID = st.secrets["gdrive"]["folder_id"]
    else:
        st.error("Secrets 'gdrive' tidak ditemukan.")
        st.stop()
        
    if "?" in PARENT_FOLDER_ID:
        PARENT_FOLDER_ID = PARENT_FOLDER_ID.split("?")[0]
        
    if "MASUKKAN_ID" in INFO_FOLDER_ID:
        INFO_FOLDER_ID = PARENT_FOLDER_ID
        
    SCOPES = ['https://www.googleapis.com/auth/drive']
except Exception as e:
    st.error(f"Error Konfigurasi Secrets: {e}")
    st.stop()

def authenticate():
    if "gdrive_creds" not in st.secrets:
        st.error("Secrets 'gdrive_creds' tidak ditemukan.")
        st.stop()
    creds_dict = st.secrets["gdrive_creds"]
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def get_drive_service():
    try:
        return authenticate()
    except Exception as e:
        st.error(f"Gagal koneksi ke Google Drive: {e}")
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
        query = f"'{folder_id_khusus}' in parents and mimeType = 'text/plain' and trashed=false"
        results = service.files().list(
            q=query, fields="files(id, name, createdTime)", orderBy="createdTime desc",
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        announcements = []
        for file in files:
            request = service.files().get_media(fileId=file['id'])
            downloader = request.execute()
            content = downloader.decode('utf-8')
            announcements.append({"title": file['name'], "content": content, "id": file['id']})
        return announcements
    except:
        return []

# --- CSS KHUSUS (MOBILE OPTIMIZED & CLEAN LAYOUT) ---
def local_css():
    st.markdown("""
    <style>
        /* Sembunyikan Footer */
        footer {visibility: hidden;}
        
        /* Gambar Header */
        img { border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        
        /* Judul */
        .main-title { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0; }
        .sub-title { font-size: 1rem; color: #555; margin-top: -5px; }
        
        /* Info Box */
        .info-box { background-color: #f0f9ff; border-left: 5px solid #0ea5e9; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
        
        /* TOMBOL APUNG (Settingan V5.5 yang Bapak suka) */
        .floating-top-btn {
            position: fixed;
            bottom: 70px; 
            right: 25px;
            z-index: 999; 
            background-color: #1E3A8A;
            color: white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            text-align: center;
            line-height: 50px;
            font-size: 24px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.3); 
            text-decoration: none;
            transition: all 0.3s ease;
            opacity: 0.9;
        }
        .floating-top-btn:hover { 
            background-color: #0ea5e9; 
            color: white; 
            transform: translateY(-3px);
            opacity: 1;
        }
        
        /* TOMBOL BUKA CUSTOM (Style V5.5) */
        .custom-link-btn {
            display: inline-block;
            background-color: #ffffff;
            color: #1E3A8A;
            padding: 5px 15px;
            border-radius: 8px;
            border: 1px solid #1E3A8A;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            text-align: center;
        }
        .custom-link-btn:hover {
            background-color: #1E3A8A;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Anchor Top
    st.markdown('<div id="top-page"></div>', unsafe_allow_html=True)
    # Tombol Floating
    st.markdown('<a href="#top-page" class="floating-top-btn">⬆️</a>', unsafe_allow_html=True)

# --- FUNGSI TAMPILAN ITEM ---
def render_file_item(name, link, mime_type):
    if mime_type == 'application/vnd.google-apps.folder':
        icon = "📁"
        bg_color = "#fffbf0"
    elif "pdf" in mime_type:
        icon = "📕"
        bg_color = "white"
    elif "word" in mime_type or "document" in mime_type:
        icon = "📘"
        bg_color = "white"
    elif "sheet" in mime_type or "excel" in mime_type:
        icon = "📗"
        bg_color = "white"
    else:
        icon = "📄"
        bg_color = "white"

    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 10px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
        <div style="flex-grow: 1; padding-right: 10px;">
            <span style="font-size: 1.2rem;">{icon}</span> 
            <span style="font-weight: 500; color: #333;">{name}</span>
        </div>
        <div>
            <a href="{link}" target="_blank" class="custom-link-btn">Buka</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- INIT ---
st.set_page_config(page_title=APP_NAME, page_icon="🏫", layout="wide")
local_css()
drive_service = get_drive_service()

# --- SIDEBAR NAVIGASI (KEMBALI KE VERSI STABIL/SIMPLE) ---
st.sidebar.title("Navigasi")
main_menus = ["Beranda"]
st.sidebar.markdown("**📂 Daftar Isi:**")

folders = get_folders(drive_service, PARENT_FOLDER_ID)
folder_map = {f['name']: f['id'] for f in folders}
folder_names = list(folder_map.keys())

footer_menus = ["🔐 Area Admin (Upload Info)", "🚪 Keluar Aplikasi"]
all_menus = main_menus + folder_names + footer_menus

# Gunakan radio button biasa (Tanpa Session State yang rumit agar anti-error)
selected_menu = st.sidebar.radio("Pilih Halaman:", all_menus)

st.sidebar.markdown("---")
st.sidebar.caption("v5.7 (Versi Stabil)")

# =========================================
# HALAMAN 1: BERANDA
# =========================================
if selected_menu == "Beranda":
    
    # Header
    c1, c2 = st.columns([1, 6])
    with c1:
        try: st.image(LOGO_IMAGE_FILE, width=90)
        except: st.warning("Logo?")
    with c2:
        st.markdown(f'<h1 class="main-title"> {APP_NAME}</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-title"> Berbagi Materi & Informasi </p>', unsafe_allow_html=True)

    st.markdown("---")

    # Split Layout
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("🔍 Cari Dokumen")
        search_text = st.text_input("Ketik kata kunci...", placeholder="Contoh: Modul, Undangan, RPP", label_visibility="collapsed")
        
        if search_text:
            with st.spinner("Mencari di seluruh folder..."):
                try:
                    query = f"name contains '{search_text}' and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
                    results = drive_service.files().list(
                        q=query, fields="files(id, name, webViewLink, mimeType)",
                        supportsAllDrives=True, includeItemsFromAllDrives=True,
                        pageSize=20
                    ).execute()
                    items = results.get('files', [])
                    
                    if items:
                        st.success(f"Ditemukan {len(items)} hasil:")
                        for item in items:
                            render_file_item(item['name'], item['webViewLink'], item['mimeType'])
                    else:
                        st.warning("Tidak ditemukan. Coba kata kunci lain.")
                except Exception as e:
                    st.error(f"Error pencarian: {e}")
        
        # --- INFO TERBARU ---
        st.write("") 
        st.subheader("📢 Informasi Terbaru")
        infos = get_announcements(drive_service, INFO_FOLDER_ID)
        
        with st.container(height=300, border=True):
            if infos:
                for info in infos:
                    judul_bersih = info['title'].replace(".txt", "").replace("[INFO] ", "")
                    st.markdown(f"""<div class="info-box"><strong>🗓️ {judul_bersih}</strong><br>{info['content']}</div>""", unsafe_allow_html=True)
            else:
                st.caption("Belum ada info terbaru.")

    with col_right:
        try: st.image(HEADER_IMAGE_FILE, use_column_width=True, caption="Keluarga Besar KKG Rama")
        except: pass
        
        with st.expander("ℹ️ Tentang Aplikasi"):
            st.caption(f"Dikelola oleh **{CREATOR_NAME}**, didukung sepenuhnya oleh Pengurus KKG Rama 2026-2030.")

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
                render_file_item(item['name'], item['webViewLink'], item['mimeType'])
        else:
            st.info("Folder ini kosong.")
    except:
        st.error("Gagal memuat folder.")

# =========================================
# HALAMAN 3: AREA ADMIN
# =========================================
elif selected_menu == "🔐 Area Admin (Upload Info)":
    st.title("🔐 Area Admin")
    st.info("Fitur Upload Cerdas: Jika robot penuh, tombol manual akan muncul otomatis.")
    
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "admin123":
        st.success("Login Berhasil.")
        tab1, tab2 = st.tabs(["📤 Upload Materi", "📢 Tulis Info Beranda"])
        
        # --- TAB 1: UPLOAD ---
        with tab1:
            st.subheader("Upload Dokumen")
            if folder_names:
                pilihan_folder = st.selectbox("Pilih Folder Tujuan:", folder_names)
                target_folder_id = folder_map[pilihan_folder]
            else:
                target_folder_id = PARENT_FOLDER_ID
            
            uploaded_file = st.file_uploader("Pilih file:")
            if st.button("🚀 Upload Dokumen"):
                if uploaded_file:
                    with st.spinner("Mengupload..."):
                        try:
                            file_metadata = {'name': uploaded_file.name, 'parents': [target_folder_id]}
                            media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type, resumable=True)
                            drive_service.files().create(body=file_metadata, media_body=media, supportsAllDrives=True).execute()
                            st.success("✅ Berhasil!")
                        except Exception as e:
                            if "storageQuotaExceeded" in str(e):
                                st.error("⚠️ Kuota Robot Penuh.")
                                link_manual = f"https://drive.google.com/drive/u/0/folders/{target_folder_id}"
                                st.link_button(f"📂 Upload ke {pilihan_folder} (Manual)", link_manual)
                            else:
                                st.error(f"Error: {e}")

        # --- TAB 2: INFO ---
        with tab2:
            st.subheader("Tulis Info Baru")
            judul_info = st.text_input("Judul Singkat:")
            isi_info = st.text_area("Isi Pengumuman:", height=100)
            
            if st.button("💾 Terbitkan Info"):
                if judul_info and isi_info:
                    with st.spinner("Menerbitkan..."):
                        try:
                            tanggal = datetime.now().strftime("%d-%m-%Y")
                            file_metadata = {'name': f"[INFO] {tanggal} - {judul_info}.txt", 'parents': [INFO_FOLDER_ID], 'mimeType': 'text/plain'}
                            media = MediaIoBaseUpload(io.BytesIO(isi_info.encode('utf-8')), mimetype='text/plain', resumable=True)
                            drive_service.files().create(body=file_metadata, media_body=media, supportsAllDrives=True).execute()
                            st.success("✅ Berhasil!")
                        except Exception as e:
                            if "storageQuotaExceeded" in str(e):
                                st.error("⚠️ Kuota Robot Penuh.")
                                link_info = f"https://drive.google.com/drive/u/0/folders/{INFO_FOLDER_ID}"
                                st.link_button("📂 Buka Folder Info (Manual)", link_info)
                            else:
                                st.error(f"Error: {e}")
    elif password != "":
        st.error("Password salah.")

# =========================================
# HALAMAN 4: KELUAR
# =========================================
elif selected_menu == "🚪 Keluar Aplikasi":
    st.markdown("### 👋 Anda telah keluar.")
    st.markdown("Terima kasih telah menggunakan aplikasi ini.")
    st.divider()
    
    st.info("Untuk masuk kembali, silakan **klik 'Beranda'** pada menu di sebelah kiri.")
    
    if st.button("🔄 Segarkan Aplikasi"):
        st.rerun()
