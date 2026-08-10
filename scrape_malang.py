import asyncio
from playwright.sync_api import sync_playwright
import pandas as pd
import re

def extract_phone(text):
    """Mengambil hanya digit nomor telepon murni"""
    if not text:
        return ""
    match = re.search(r'(\+?62[\s-]?\d+|\(0\d+\)[\s-]?\d+|08\d+[\s-]?\d+[\s-]?\d+)', text)
    if match:
        return match.group(0).strip()
    return ""

def extract_kategori_and_alamat(lines, nama_usaha):
    """
    Ekstraksi Kategori & Alamat Presisi:
    - Mendukung Kategori Bahasa Indonesia & Inggris (misal: 'Telecommunications service provider')
    - Memotong prefix kategori & pemisah (·) agar Alamat murni dimulai dari 'Jl. ...'
    """
    known_categories = [
        # Kategori Bahasa Inggris
        "Telecommunications service provider", "Corporate office", "Manufacturer", 
        "Building materials supplier", "Travel agency", "Construction company", 
        "Wholesaler", "Real estate developer", "Warehouse", "Supplier", "Distributor",
        
        # Kategori Bahasa Indonesia
        "Penyedia Layanan Telekomunikasi", "Kantor Perusahaan", "Produsen", 
        "Pemasok Bahan Bangunan", "Biro Perjalanan dan Wisata", "Perusahaan Pertambangan", 
        "Peternakan", "Gudang", "Pengembang Realestat", "Grosir", "Bank", 
        "Terapis Pijat Olahraga", "Vila", "Perusahaan Konstruksi", "Kantor Pemerintah", 
        "Perhentian bus", "Biro Wisata", "Toko Ban", "Toko Herbal", 
        "Perusahaan investasi properti", "Pemasok tembakau", "Jasa Konstruksi dan Bangunan", 
        "Pengolahan Buah dan Sayuran", "Minimarket", "Museum", "Pemasok peralatan keselamatan", 
        "Perusahaan", "Toko Kerajinan Tangan", "Kontraktor", "Toko Alat Pancing", 
        "Distributor", "Pabrik", "Agen Tenaga Kerja", "Agen", "Toko"
    ]
    
    kategori = "Kantor Perusahaan" # Fallback default
    alamat = "Kota Malang, Jawa Timur"
    
    # 1. CARI KATEGORI
    for line in lines:
        clean_line = line.split("·")[0].strip() if "·" in line else line.strip()
        
        for cat in known_categories:
            if cat.lower() in clean_line.lower() and clean_line.lower() != nama_usaha.strip().lower():
                kategori = cat
                break
        if kategori != "Kantor Perusahaan":
            break

    # 2. CARI DAN BERSIHKAN ALAMAT MURNI
    for line in lines:
        is_address_pattern = any(kw in line for kw in ["Jl.", "Jalan", "Kec.", "Kel.", "Gg.", "No.", "Malang", "Jawa Timur"])
        is_not_rating = not re.match(r'^\d[.,]\d$', line)
        is_not_status = not any(st in line.lower() for st in ["buka", "tutup", "pukul", "operasional", "confirmed"])
        is_not_nama = line.strip().lower() != nama_usaha.strip().lower()
        
        if is_address_pattern and is_not_rating and is_not_status and is_not_nama:
            raw_alamat = line.strip()
            
            # Jika alamat tercampur dengan kategori atau simbol titik tengah (·)
            if "·" in raw_alamat:
                parts = raw_alamat.split("·")
                for part in parts:
                    clean_part = re.sub(r'^[^\w]+', '', part).strip()
                    if any(kw in clean_part for kw in ["Jl.", "Jalan", "Kec.", "Kel.", "Gg.", "No.", "Malang"]):
                        alamat = clean_part
                        break
            else:
                alamat = re.sub(r'^[^\w]+', '', raw_alamat).strip()
                
            break
            
    return kategori, alamat

def scrape_gmaps_malang(search_queries, max_results_per_query=30):
    all_results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        for query in search_queries:
            print(f"🔎 Sedang scraping kata kunci: '{query}'...")
            url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            page.goto(url)
            page.wait_for_timeout(4000)
            
            # Scroll panel kiri Google Maps
            try:
                scrollable_div = page.locator('div[role="feed"]')
                for _ in range(6):
                    scrollable_div.evaluate('el => el.scrollBy(0, 1000)')
                    page.wait_for_timeout(1500)
            except Exception:
                pass
                
            listings = page.locator('div[role="article"]').all()
            
            for item in listings[:max_results_per_query]:
                try:
                    # 1. Klik Item untuk Membuka Detail & Mendapatkan Koordinat Presisi
                    item.click()
                    page.wait_for_timeout(2000)
                    
                    current_url = page.url
                    lat, lon = None, None
                    
                    match_coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
                    if match_coords:
                        lat = float(match_coords.group(1))
                        lon = float(match_coords.group(2))
                    
                    # 2. Nama Usaha
                    nama = item.locator('div.fontHeadlineSmall').inner_text() if item.locator('div.fontHeadlineSmall').count() > 0 else ""
                    if not nama:
                        continue

                    # 3. Text Info Gabungan
                    full_text = item.inner_text()
                    lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                    
                    # Rating
                    rating = None
                    for line in lines:
                        if re.match(r'^\d[.,]\d$', line):
                            rating = line
                            break
                            
                    # Telepon
                    telepon_clean = extract_phone(full_text)
                    
                    # Kategori & Alamat
                    kategori_clean, alamat_clean = extract_kategori_and_alamat(lines, nama)
                    
                    all_results.append({
                        'nama': nama,
                        'kategori': kategori_clean,  # Terpisah murni (Indo/Inggris)
                        'alamat': alamat_clean,      # Murni dimulai dari "Jl. ..."
                        'telepon': telepon_clean,    # Murni angka
                        'rating': rating,
                        'latitude': lat,
                        'longitude': lon,
                        'url_gmaps': current_url
                    })
                except Exception:
                    continue
                    
        browser.close()
        
    return pd.DataFrame(all_results)

if __name__ == "__main__":
    queries_se_malang = [
        "PT di Kota Malang",
        "CV di Kota Malang",
        "Pabrik di Kota Malang",
        "Perusahaan B2B Kota Malang"
    ]

    print("🚀 Memulai proses scraping presisi Kota Malang...")
    df_malang = scrape_gmaps_malang(queries_se_malang, max_results_per_query=30)
    df_malang.drop_duplicates(subset=['nama'], inplace=True)

    output_file = 'scraping_gmaps_ptcv_Kota_Malang_revisi_v4.xlsx'
    df_malang.to_excel(output_file, index=False)

    print(f"✅ SELESAI! File tersimpan rapi sebagai '{output_file}'.")