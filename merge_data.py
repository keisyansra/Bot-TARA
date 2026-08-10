import pandas as pd
import glob
import os

# 1. Tentukan folder lokasi file-file Excel
folder_path = "data_scraping"
file_list = glob.glob(os.path.join(folder_path, "*.xlsx"))

print(f"📦 Ditemukan {len(file_list)} file wilayah...")

all_dfs = []

# 2. Baca setiap file dan tambahkan kolom 'wilayah'
for file in file_list:
    filename = os.path.basename(file)
    df = pd.read_excel(file)
    
    # Ambil nama wilayah dari nama file
    wilayah_name = (
        filename.replace("scraping_gmaps_ptcv_", "")
        .replace("Hasil_Scraping_Gmaps_", "")
        .replace(".xlsx", "")
    )
    
    # Isi kolom 'wilayah' berdasarkan nama file
    df['wilayah'] = wilayah_name
    all_dfs.append(df)

if all_dfs:
    # 3. Gabungkan seluruh data
    df_master = pd.concat(all_dfs, ignore_index=True)

    # 4. Hapus duplikat berdasarkan Nama Usaha & Alamat
    total_before = len(df_master)
    df_master.drop_duplicates(subset=['nama', 'alamat'], inplace=True)
    total_after = len(df_master)

    # 5. Simpan ke File Excel Master
    output_file = "MASTER_SCRAPING_GMAPS_JATIM_BARAT.xlsx"
    df_master.to_excel(output_file, index=False)

    print(f"\n✅ PENGGABUNGAN SELESAI!")
    print(f"   • Total Data Awal  : {total_before} baris")
    print(f"   • Duplikat Dibuang : {total_before - total_after} baris")
    print(f"   • Total Data Unik  : {total_after} baris")
    print(f"💾 File tersimpan sebagai '{output_file}' di folder utama.")
else:
    print("⚠️ Tidak ada file .xlsx yang ditemukan di dalam folder 'data_scraping'.")