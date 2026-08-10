import pandas as pd
import re

def standardize_phone(phone):
    """Merapikan dan menstandarkan format nomor telepon"""
    if pd.isna(phone) or not str(phone).strip():
        return ""
    
    # Ubah ke string & hapus karakter selain angka dan plus (+)
    phone_str = str(phone).strip()
    phone_clean = re.sub(r'[^0-9+]', '', phone_str)
    
    # Konversi format +62 menjadi 0
    if phone_clean.startswith("+62"):
        phone_clean = "0" + phone_clean[3:]
    elif phone_clean.startswith("62"):
        phone_clean = "0" + phone_clean[2:]
        
    return phone_clean

def clean_master_data():
    file_input = "MASTER_SCRAPING_GMAPS_JATIM_BARAT.xlsx"
    print(f"📖 Membaca file master: '{file_input}'...")
    
    try:
        df = pd.read_excel(file_input)
    except FileNotFoundError:
        print(f"⚠️ File '{file_input}' tidak ditemukan. Pastikan sudah menjalankan merge_data.py!")
        return

    total_rows = len(df)
    print(f"📊 Total data awal: {total_rows} baris")

    # 1. Bersihkan Format Nomor Telepon
    if 'telepon' in df.columns:
        df['telepon_clean'] = df['telepon'].apply(standardize_phone)
    else:
        df['telepon_clean'] = ""

    # 2. Hapus Karakter Aneh / Whitespace Berlebih pada Teks
    for col in ['nama', 'kategori', 'alamat']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(r'^\s*$', pd.NA, regex=True)

    # 3. Penandaan Status Kelengkapan Data (Untuk Bot TARA & Telemarketing)
    # Memiliki Telepon & Koordinat
    df['has_phone'] = df['telepon_clean'].astype(bool)
    df['has_coords'] = df['latitude'].notna() & df['longitude'].notna()
    
    # Data Siap Pakai (Valid untuk Bot TARA: Punya Alamat + Koordinat)
    df['is_ready_tara'] = df['has_coords'] & df['alamat'].notna()

    # 4. Ringkasan Statistik Data
    with_phone_count = df['has_phone'].sum()
    with_coords_count = df['has_coords'].sum()
    ready_tara_count = df['is_ready_tara'].sum()

    print("\n📈 RINGKASAN KUALITAS DATA MASTER:")
    print(f"   • Memiliki Nomor Telepon Valid : {with_phone_count} / {total_rows} ({round(with_phone_count/total_rows*100, 1)}%)")
    print(f"   • Memiliki Koordinat Presisi  : {with_coords_count} / {total_rows} ({round(with_coords_count/total_rows*100, 1)}%)")
    print(f"   • Data Siap Pakai (Bot TARA)   : {ready_tara_count} / {total_rows} ({round(ready_tara_count/total_rows*100, 1)}%)")

    # 5. Simpan Hasil Pembersihan
    output_file = "MASTER_SCRAPING_GMAPS_JATIM_BARAT_CLEAN.xlsx"
    df.to_excel(output_file, index=False)
    print(f"\n✅ Pembersihan selesai! File bersih tersimpan sebagai '{output_file}'.")

if __name__ == "__main__":
    clean_master_data()