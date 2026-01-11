import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime

# --- KONFIGURASI ---
try:
    # Mengambil ID Folder Utama
    PARENT_FOLDER_ID = st.secrets["gdrive"]["folder_id"]
    # Membersihkan ID jika ada sisa URL (Jaga-jaga jika user lupa hapus tanda tanya)
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
st.set_page_config(page_title="KKG Rama", page_icon="🏫", layout="wide")

st.title("🏫 Portal KKG Rama")
st.markdown("Aplikasi Penyimpanan & Berbagi Materi Kegiatan KKG")
st.markdown("---")

# Menu Sidebar
menu = st.sidebar.selectbox("Menu Utama", ["Beranda", "Upload Materi", "Cari & Download"])
st.sidebar.markdown("---")
st.sidebar.info("Versi Web App 2.0 (Dynamic Folders)")

# Koneksi ke Drive
try:
    drive_service = authenticate()
except Exception as e:
    st.error(f"Gagal koneksi: {e}")
    st.stop()

if menu == "Beranda":
    st.header("Selamat Datang Bapak/Ibu Guru")
    st.success("Aplikasi ini tersinkronisasi otomatis dengan Google Drive.")
    
    try:
        # Hitung jumlah file di folder utama dan subfolder
        # (Query sederhana untuk cek koneksi)
        query = f"'{PARENT_FOLDER_ID}' in parents and trashed=false"
        results = drive_service.files().list(q=query).execute()
        files = results.get('files', [])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Koneksi Database", "Terhubung 🟢")
        with col2:
            st.metric("Folder Utama", "Siap Akses ✅")
            
        st.markdown("### 📢 Petunjuk Singkat")
        st.markdown("""
        1. **Beranda:** Cek status aplikasi.
        2. **Upload Materi:** (Khusus Admin) Upload file langsung ke folder pilihan.
        3. **Cari & Download:** Cari materi dari seluruh arsip KKG.
        """)
    except:
        st.warning("Sedang menghubungkan ke Google Drive...")

elif menu == "Upload Materi":
    st.header("📤 Area Khusus Editor")
    st.info("Kategori di bawah ini otomatis membaca Folder di Google Drive.")
    
    # --- PASSWORD PROTECTION ---
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "admin123": # <--- Ganti Password disini jika mau
        st.success("Akses Diterima! Silakan upload.")
        st.divider()

        # --- FITUR BARU: BACA FOLDER OTOMATIS ---
        try:
            # Cari semua folder yang ada di dalam Folder Utama
            folder_query = f"'{PARENT_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            folder_results = drive_service.files().list(q=folder_query, fields="files(id, name)").execute()
            folders = folder_results.get('files', [])
            
            # Jika ada folder, buat daftarnya
            if folders:
                folder_names = [f['name'] for f in folders]
                # Pilihan folder
                pilihan_folder = st.selectbox("Simpan ke Folder mana?", folder_names)
                
                # Cari ID dari nama folder yang dipilih
                target_folder_id = next(item['id'] for item in folders if item["name"] == pilihan_folder)
            else:
                # Jika tidak ada folder sama sekali, pakai folder utama
                st.warning("Tidak ditemukan sub-folder. File akan disimpan di Folder Utama.")
                target_folder_id = PARENT_FOLDER_ID
                
            uploaded_file = st.file_uploader("Pilih file (PDF, Word, Excel, Gambar)", type=['pdf', 'docx', 'xlsx', 'pptx', 'jpg', 'jpeg', 'png'])
            
            if st.button("Simpan ke Cloud"):
                if uploaded_file:
                    with st.spinner(f"Mengupload ke folder '{pilihan_folder if folders else 'Utama'}'..."):
                        try:
                            timestamp = datetime.now().strftime("%Y-%m-%d")
                            # Nama file asli, tanpa label manual karena sudah masuk folder
                            file_metadata = {
                                'name': f"{timestamp} - {uploaded_file.name}",
                                'parents': [target_folder_id] # <--- Simpan ke ID folder yang dipilih
                            }
                            media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type, resumable=True)
                            drive_service.files().create(body=file_metadata, media_body=media).execute()
                            
                            st.balloons()
                            st.success(f"Sukses! File tersimpan di folder: {pilihan_folder if folders else 'Utama'}")
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
        # LOGIKA PENCARIAN (RECURSIVE)
        if search_text:
            # Cari file di mana saja (di semua folder) yang namanya cocok
            query = f"name contains '{search_text}' and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
        else:
            # Jika kosong, tampilkan file di folder utama saja agar rapi
            query = f"'{PARENT_FOLDER_ID}' in parents and trashed=false"
        
        results = drive_service.files().list(
            q=query, 
            fields="files(id, name, webViewLink, parents)" 
        ).execute()
        
        items = results.get('files', [])

        if items:
            st.markdown(f"*Ditemukan {len(items)} dokumen:*")
            for item in items:
                with st.container():
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"📄 **{item['name']}**")
                    with c2:
                        st.link_button("Download", item['webViewLink'])
                    st.divider()
        else:
            if search_text:
                st.info("Tidak ada dokumen ditemukan dengan kata kunci tersebut.")
            else:
                st.info("Folder utama kosong. Coba gunakan fitur pencarian untuk melihat isi sub-folder.")
            
    except Exception as e:
        st.error("Terjadi Masalah saat mengambil data.")
        st.warning(f"Detail Error: {e}")
