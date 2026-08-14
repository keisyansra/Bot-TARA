import re
from urllib.parse import unquote

def parse_coordinate_from_url(url):
    """
    Ekstrak latitude dan longitude dari URL Google Maps.
    Format URL biasanya: https://www.google.com/maps/place/.../@-7.96662,112.632632,15z/...
    Atau: .../data=!3m1!4b1!4m5!3m4!1s0x...:0x...!8m2!3d-7.96662!4d112.632632
    """
    if not url:
        return None, None
        
    # Coba pattern @lat,long
    match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if match:
        return match.group(1), match.group(2)
        
    # Coba pattern !3dlat!4dlong
    match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    if match:
        return match.group(1), match.group(2)
        
    return None, None

def parse_result_card(element_handle, kategori):
    """
    Ekstrak data dari satu elemen kartu hasil pencarian Google Maps.
    Data raw diekstrak tanpa cleaning bisnis agresif.
    """
    try:
        # Mencari tag <a> yang menuju ke halaman detail tempat
        link_el = element_handle.query_selector('a[href*="/maps/place/"]')
        if not link_el:
            return None
            
        url_gmaps = link_el.get_attribute("href")
        if url_gmaps and url_gmaps.startswith("http"):
            # Clean up the URL slightly
            pass
        elif url_gmaps:
            url_gmaps = "https://www.google.com" + url_gmaps
        else:
            return None
            
        # Nama biasanya ada di aria-label dari link utama
        nama = link_el.get_attribute("aria-label") or ""
        
        # Ekstrak rating
        # Biasanya ada di span dengan aria-label="X bintang" atau text dengan format angka desimal
        # Kita coba ekstrak teks di dalam elemen
        inner_text = element_handle.inner_text()
        
        # Contoh pattern rating: "4,5", "4.5", "5,0" di teks
        rating_match = re.search(r"(\d[.,]\d)\s*(?:\(|bintang)", inner_text, re.IGNORECASE)
        rating = rating_match.group(1).replace(",", ".") if rating_match else None
        
        # Ekstrak telepon dari teks (pattern umum nomor telepon Indonesia)
        # Menghindari koordinat, hanya angka dengan awalan +62 atau 0 (kode area atau HP)
        phone_match = re.search(r"\b((?:\+62|0\d{2,3})[-\s]?\d{4,5}[-\s]?\d{3,5})\b", inner_text)
        telepon = phone_match.group(1).strip() if phone_match else None
        
        # Ekstrak alamat kasar (ambil baris setelah nama/rating/kategori)
        # Ini hanya aproksimasi kasar karena struktur HTML Maps yang kompleks dan dinamis.
        # Biasanya dipisah dengan newline di inner_text
        lines = [line.strip() for line in inner_text.split('\n') if line.strip()]
        alamat = None
        for i, line in enumerate(lines):
            # Pisahkan kategori dari string jika ada pemisah '·'
            if '·' in line:
                parts = line.split('·')
                line = parts[-1].strip() # Ambil bagian terakhir yang biasanya adalah alamat
                
            line_lower = line.lower()
            # Asumsi: baris yang panjang atau mengandung kata "Jl.", "Jalan", "Kec.", "Kab." adalah alamat
            if len(line) > 10 and any(keyword in line_lower for keyword in ["jl.", "jalan", "raya", "kec", "kab", "kota", ","]):
                # Pastikan bukan sekadar nomor telepon atau koordinat
                if not re.match(r"^[0-9\s+-,.]+$", line):
                    alamat = line
                    break
        
        # Parse coordinate from URL
        lat, lon = parse_coordinate_from_url(url_gmaps)
        
        return {
            "nama": nama.strip(),
            "kategori": kategori,
            "alamat": alamat,
            "telepon": telepon,
            "rating": rating,
            "latitude": lat,
            "longitude": lon,
            "url_gmaps": url_gmaps
        }
    except Exception as e:
        # Silently ignore parsing errors for individual cards to not stop the whole scraping
        return None

if __name__ == "__main__":
    # Test cases for coordinates
    lat, lon = parse_coordinate_from_url("https://www.google.com/maps/place/test/@-7.96662,112.632632,15z/")
    print(f"Test 1 - lat: {lat}, lon: {lon}")
    
    lat, lon = parse_coordinate_from_url("https://www.google.com/maps/data=!3d-7.96662!4d112.632632")
    print(f"Test 2 - lat: {lat}, lon: {lon}")
