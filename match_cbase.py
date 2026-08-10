import pandas as pd
from rapidfuzz import process, fuzz

def match_with_cbase():
    file_scraping = "MASTER_SCRAPING_GMAPS_JATIM_BARAT_CLEAN.xlsx"
    file_cbase = "cbase_jatim_barat_clean.csv" 

    print("📖 Membaca file hasil scraping & database CBASE CSV...")
    try:
        df_scraping = pd.read_excel(file_scraping)
        
        # PERBAIKAN: Gunakan sep=None dan engine='python' atau fallback on_bad_lines
        try:
            # Otomatis deteksi pemisah (koma atau titik koma)
            df_cbase = pd.read_csv(file_cbase, sep=None, engine='python', on_bad_lines='skip')
        except Exception:
            # Fallback jika CSV menggunakan delimiter titik koma (;) standar Excel Indonesia
            df_cbase = pd.read_csv(file_cbase, sep=';', on_bad_lines='skip')

    except FileNotFoundError as e:
        print(f"⚠️ File tidak ditemukan: {e}")
        print("Pastikan file 'cbase_jatim_barat_clean.csv' sudah berada di folder proyek!")
        return

    print(f"📊 Total Data Scraping : {len(df_scraping)} baris")
    print(f"📊 Total Data CBASE    : {len(df_cbase)} baris")

    # Menggunakan kolom 'nama_normalized' atau 'nama_usaha'
    cbase_col_nama = 'nama_normalized' if 'nama_normalized' in df_cbase.columns else 'nama_usaha'
    
    if cbase_col_nama not in df_cbase.columns:
        print(f"\n⚠️ Kolom '{cbase_col_nama}' tidak ditemukan di {file_cbase}!")
        print(f"   Daftar kolom yang terdeteksi: {list(df_cbase.columns)}")
        return

    print(f"🔗 Menggunakan kolom '{cbase_col_nama}' dari file CBASE untuk pencocokan.")

    # Ambil daftar nama perusahaan CBASE sebagai referensi
    cbase_names = df_cbase[cbase_col_nama].dropna().astype(str).tolist()

    print("\n🔍 Memulai proses matching nama perusahaan (Fuzzy Matching via RapidFuzz)...")

    matched_names = []
    similarity_scores = []
    status_list = []

    # Threshold kemiripan (80% ke atas dianggap perusahaan yang sama)
    THRESHOLD = 95.0

    for idx, nama_scrap in enumerate(df_scraping['nama']):
        if pd.isna(nama_scrap):
            matched_names.append(None)
            similarity_scores.append(0)
            status_list.append("NEW LEADS (Belum Ada di CBASE)")
            continue

        nama_scrap_clean = str(nama_scrap).lower().strip()

        # Cari nama terbaik yang mirip di CBASE
        match = process.extractOne(nama_scrap_clean, cbase_names, scorer=fuzz.WRatio)

        if match and match[1] >= THRESHOLD:
            matched_names.append(match[0])
            similarity_scores.append(round(match[1], 1))
            status_list.append("MATCH (Sudah Ada di CBASE)")
        else:
            matched_names.append(match[0] if match else None)
            similarity_scores.append(round(match[1], 1) if match else 0)
            status_list.append("NEW LEADS (Belum Ada di CBASE)")

        if (idx + 1) % 100 == 0 or (idx + 1) == len(df_scraping):
            print(f"   ⏳ Processed {idx + 1}/{len(df_scraping)} data...")

    # Simpan hasil ke DataFrame
    df_scraping['cbase_matched_name'] = matched_names
    df_scraping['match_score'] = similarity_scores
    df_scraping['lead_status'] = status_list

    # Statistik Hasil Matching
    new_leads_count = (df_scraping['lead_status'] == "NEW LEADS (Belum Ada di CBASE)").sum()
    already_in_cbase = (df_scraping['lead_status'] == "MATCH (Sudah Ada di CBASE)").sum()

    print("\n🎯 HASIL DATA MATCHING:")
    print(f"   • Existing di CBASE  : {already_in_cbase} perusahaan")
    print(f"   • NEW LEADS POTENSIAL : {new_leads_count} perusahaan ⭐")

    # Simpan ke File Excel Hasil
    output_file = "HASIL_MATCHING_LEADS_TARA.xlsx"
    df_scraping.to_excel(output_file, index=False)
    print(f"\n✅ Selesai! File penemuan leads tersimpan sebagai '{output_file}'.")

if __name__ == "__main__":
    match_with_cbase()