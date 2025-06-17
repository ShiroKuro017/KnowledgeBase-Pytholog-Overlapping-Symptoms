import streamlit as st
import pandas as pd
import os

# --- LOGIKA INTI DARI JUPYTER NOTEBOOK ---

def create_symptom_map(df):

    penyakit_symptom_map = {}
    for index, row in df.iterrows():
        # Membersihkan nama penyakit
        penyakit = row['penyakit'].strip().replace(' ', '_')
        
        # Mengambil gejala dari kolom, membersihkan, dan memfilter nilai kosong (NaN)
        gejala = [
            str(g).strip().replace(' ', '_') 
            for g in row[['gejala1', 'gejala2', 'gejala3']] 
            if pd.notna(g)
        ]
        
        # Menambahkan gejala ke map
        if penyakit not in penyakit_symptom_map:
            penyakit_symptom_map[penyakit] = []
        penyakit_symptom_map[penyakit].extend(gejala)
    
    # Memastikan setiap daftar gejala untuk satu penyakit adalah unik
    for penyakit, gejala_list in penyakit_symptom_map.items():
        penyakit_symptom_map[penyakit] = sorted(list(set(gejala_list)))
        
    return penyakit_symptom_map

def analisis_diagnosis(gejala_dialami, penyakit_symptom_map):

    hasil = []
    # Membersihkan input gejala dari pengguna
    gejala_dialami_clean = [g.replace(' ', '_') for g in gejala_dialami]

    for penyakit, gejala_penyakit in penyakit_symptom_map.items():
        # Mencari irisan antara gejala yang dialami dan gejala di database
        gejala_cocok = set(gejala_dialami_clean) & set(gejala_penyakit)
        
        if gejala_cocok:
            # Menghitung persentase kecocokan berdasarkan jumlah gejala di database
            kecocokan = (len(gejala_cocok) / len(gejala_penyakit)) * 100
            
            # Mencari gejala tambahan yang perlu ditanyakan (gejala penyakit - gejala yang dialami)
            saran_gejala = set(gejala_penyakit) - set(gejala_dialami_clean)
            
            hasil.append({
                'penyakit': penyakit,
                'kecocokan': kecocokan,
                'saran_gejala': list(saran_gejala)
            })
    
    # Mengurutkan hasil berdasarkan persentase kecocokan tertinggi
    hasil_sorted = sorted(hasil, key=lambda x: x['kecocokan'], reverse=True)
    
    return hasil_sorted

def get_all_symptoms(df):

    gejala_cols = ['gejala1', 'gejala2', 'gejala3']
    all_symptoms = df[gejala_cols].values.ravel()
    unique_symptoms = pd.unique(all_symptoms)
    
    # Membersihkan daftar dari nilai kosong (NaN) dan spasi ekstra, lalu urutkan
    cleaned_symptoms = [str(s).strip() for s in unique_symptoms if pd.notna(s)]
    return sorted(list(set(cleaned_symptoms)))


# --- ANTARMUKA STREAMLIT ---

st.set_page_config(page_title="Sistem Diagnosis Penyakit", layout="centered")
st.title("🩺 Sistem Diagnosis Penyakit")
st.write("Aplikasi ini membantu mendiagnosis kemungkinan penyakit berdasarkan gejala yang Anda masukkan.")

# --- Bagian 1: Memuat Dataset ---
st.header("1. Muat Dataset Gejala")

# Opsi untuk memuat data
df = None
file_path = 'gejala_penyakit.csv'

# Opsi 1: Deteksi file lokal
if os.path.exists(file_path):
    st.success(f"✔️ Dataset `{file_path}` ditemukan di folder yang sama.")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Gagal memuat file lokal: {e}")
        df = None # Pastikan df None jika gagal

# Opsi 2: Unggah manual jika file lokal tidak ditemukan atau gagal dimuat
if df is None:
    st.info("File `gejala_penyakit.csv` tidak ditemukan. Silakan unggah file secara manual.")
    uploaded_file = st.file_uploader("Pilih file CSV", type="csv")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("✔️ Dataset berhasil diunggah.")
        except Exception as e:
            st.error(f"Gagal memuat file yang diunggah: {e}")

# --- Bagian 2: Input Gejala (hanya jika dataset sudah dimuat) ---
if df is not None:
    # Proses data untuk mendapatkan daftar gejala dan map penyakit
    try:
        all_symptoms = get_all_symptoms(df)
        penyakit_symptom_map = create_symptom_map(df)
        
        # Tambahkan opsi default di awal daftar gejala
        placeholder = ""
        symptom_options = [placeholder] + all_symptoms

        st.header("2. Masukkan Gejala")
        
        # Membuat 3 dropdown untuk input gejala
        gejala1 = st.selectbox("Pilih Gejala 1:", options=symptom_options)
        gejala2 = st.selectbox("Pilih Gejala 2:", options=symptom_options)
        gejala3 = st.selectbox("Pilih Gejala 3:", options=symptom_options)

        # Tombol untuk memulai diagnosis
        if st.button("🚀 Mulai Diagnosis", type="primary"):
            # Kumpulkan gejala yang dipilih pengguna (abaikan placeholder)
            gejala_yang_dialami = [g for g in [gejala1, gejala2, gejala3] if g != placeholder]

            st.header("3. Hasil Diagnosis")
            if not gejala_yang_dialami:
                st.warning("⚠️ Harap pilih minimal satu gejala.")
            else:
                with st.spinner('Menganalisis gejala...'):
                    # Panggil fungsi analisis
                    hasil_diagnosis = analisis_diagnosis(gejala_yang_dialami, penyakit_symptom_map)

                    # Tampilkan hasil
                    if hasil_diagnosis:
                        st.info(f"Diagnosis untuk gejala: **{', '.join(gejala_yang_dialami)}**")
                        for hasil in hasil_diagnosis:
                            nama_penyakit = hasil['penyakit'].replace('_', ' ').title()
                            kecocokan = hasil['kecocokan']
                            saran = hasil['saran_gejala']
                            
                            st.markdown(f"### {nama_penyakit}")
                            st.markdown(f"**Tingkat Kecocokan:** `{kecocokan:.2f}%`")
                            
                            if saran:
                                saran_formatted = ', '.join(s.replace('_', ' ') for s in saran)
                                st.markdown(f"**Saran Gejala Tambahan:** Tanyakan apakah ada gejala berikut: *{saran_formatted}*.")
                            st.divider()
                    else:
                        st.error(">>> Tidak ditemukan diagnosis yang cocok dengan kombinasi gejala yang diberikan. <<<")

    except KeyError as e:
        st.error(f"Terjadi kesalahan: Kolom {e} tidak ditemukan di file CSV. Pastikan file Anda memiliki kolom 'penyakit', 'gejala1', 'gejala2', dan 'gejala3'.")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
else:
    st.warning("Silakan muat dataset terlebih dahulu untuk melanjutkan.")