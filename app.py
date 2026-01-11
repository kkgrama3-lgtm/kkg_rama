import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime

# --- PENGATURAN IDENTITAS PEMBUAT (EDIT DISINI) ---
APP_NAME = "KKG Rama"
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

st.title(f"🏫 Portal {APP_NAME}")
st.markdown("Aplikasi Penyimpanan & Berbagi Materi Kegiatan KKG")
st.markdown("---")

# Menu Sidebar
st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Pilih Menu:", ["Beranda", "Upload Materi", "Cari & Download"])

# Footer Sidebar (Identitas Kecil)
st.sidebar.markdown("---")
st.sidebar.caption(f"Dev: {CREATOR_NAME}")
st.sidebar.caption("v2.2 © 2024")

# Koneksi ke Drive
try:
    drive_service = authenticate()
except Exception as e:
    st.error(f"Gagal koneksi: {e}")
    st.stop()

if menu == "Beranda":
    st.header("Selamat Datang Bapak/Ibu Guru")
    st.success("Aplikasi ini tersinkronisasi otomatis dengan Google Drive.")
    
    # Cek Status
    try:
        query = f"'{PARENT_FOLDER_ID}' in parents and trashed=false"
        results = drive_service.files().list(q=query).execute()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Koneksi Database", "Terhubung 🟢")
        with col2:
            st.metric("Status Sistem", "Aktif ✅")
            
    except:
        st.warning("Sedang menghubungkan ke Google Drive...")

    st.markdown("---")
    
    # --- BAGIAN IDENTITAS PEMBUAT (VERSI FONT KECIL & RAPI) ---
    with st.container():
        st.markdown("**👨‍💻 Info Pengembang**") # Judul kecil tebal
        
        # Menggunakan st.info agar ada kotak background, tapi isinya font normal
        st.info(f"""
        Aplikasi ini dibuat oleh:  
        **{CREATOR_NAME}** *(orang baik)*
        
        📧 asal: {CREATOR_CONTACT}  
        _{CREATOR_MESSAGE}_
        """)

elif menu == "Upload Materi":
    st.header("📤 Area Khusus Editor")
    st.caption("Pilih folder tujuan upload di bawah ini.") # Font kecil
    
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "gugusr4m4": # <--- Ganti Password Upload Disini
        st.success(f"Login Berhasil. Silakan upload, Pak {CREATOR_NAME}.")
        st.divider()

        try:
            folder_query = f"'{PARENT_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            folder_results = drive_service.files().list(q=folder_query, fields="files(id, name)").execute()
            folders = folder_results.get('files', [])
            
            if folders:
                folder_names = [f['name'] for f in folders]
                pilihan_folder = st.selectbox("Simpan ke Folder mana?", folder_names)
                target_folder_id = next(item['id'] for item in folders if item["name"] == pilihan_folder)
            else:
                st.warning("Tidak ditemukan sub-folder. File akan disimpan di Folder Utama.")
                target_folder_id = PARENT_FOLDER_ID
                
            uploaded_file = st.file_uploader("Pilih file", type=['pdf', 'docx', 'xlsx', 'pptx', 'jpg', 'jpeg', 'png'])
            
            if st.button("Simpan ke Cloud"):
                if uploaded_file:
                    with st.spinner(f"Mengupload ke folder '{pilihan_folder if folders else 'Utama'}'..."):
                        try:
                            timestamp = datetime.now().strftime("%Y-%m-%d")
                            file_metadata = {
                                'name': f"{timestamp} - {uploaded_file.name}",
                                'parents': [target_folder_id]
                            }
                            media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type, resumable=True)
                            drive_service.files().create(body=file_metadata, media_body=media).execute()
                            st.balloons()
                            st.success("Sukses! File berhasil disimpan.")
                        except Exception as e:
                            st.error(f"Gagal upload: {e}")
                else:
                    st.warning("Mohon pilih file terlebih dahulu.")
        except Exception as e:
            st.error(f"Gagal membaca daftar folder: {e}")
            
    elif password != "":
        st.error("Password salah.")

elif menu == "Cari & Download":
    st.header("📂 Cari Arsip")
    search_text = st.text_input("Ketik kata kunci (Cari di semua folder)...")
    
    try:
        if search_text:
            query = f"name contains '{search_text}' and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
        else:
            query = f"'{PARENT_FOLDER_ID}' in parents and trashed=false"
        
        results = drive_service.files().list(q=query, fields="files(id, name, webViewLink)").execute()
        items = results.get('files', [])

        if items:
            st.caption(f"Menampilkan {len(items)} dokumen terbaru:")
            for item in items:
                with st.container():
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"📄 {item['name']}") # Nama file normal (tidak bold besar)
                    with c2:
                        st.link_button("Unduh", item['webViewLink'])
                    st.divider()
        else:
            st.info("Tidak ada dokumen ditemukan.")
            
    except Exception as e:
        st.error("Terjadi Masalah saat mengambil data.")
