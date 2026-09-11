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

    match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if match:
        return match.group(1), match.group(2)

    match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    if match:
        return match.group(1), match.group(2)

    return None, None


def cocok_kategori(nama, kategori):
    """
    Cek apakah nama tempat beneran mengandung salah satu kata kunci
    badan usaha (PT/CV/UD) sebagai kata utuh -- nyaring hasil yang
    Maps balikin pas search "PT di Malang" tapi ternyata bukan PT
    beneran (nama_normalized-nya cuma numpang lolos di full-text Maps).
    Dipinjam dari pendekatan temen, diadaptasi buat feed-scroll (bukan
    click-detail).
    """
    if not nama:
        return False
    kategori_upper = kategori.upper()

    #PT/CV/UD tetap menggunakan filter nama
    if kategori_upper in ("PT", "CV", "UD"):
        pattern = r"\b(" + re.escape(kategori_upper) + r")\b"
        return bool(re.search(pattern, nama, re.IGNORECASE))

    #kategori usaha umum tidak perlu mengandung keyword di nama 
    return True
    # pattern = r"\b(" + "|".join(re.escape(k) for k in kategori_list) + r")\b"
    # return bool(re.search(pattern, nama, re.IGNORECASE))


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
            pass
        elif url_gmaps:
            url_gmaps = "https://www.google.com" + url_gmaps
        else:
            return None

        # Nama biasanya ada di aria-label dari link utama
        nama = (link_el.get_attribute("aria-label") or "").strip()

        # FILTER: skip di sini juga kalau namanya gak beneran PT/CV/UD --
        # sebelum buang waktu regex rating/telepon/alamat yang gak perlu.
        if not cocok_kategori(nama, kategori): 
            return None

        inner_text = element_handle.inner_text()

        rating_match = re.search(r"(\d[.,]\d)\s*(?:\(|bintang)", inner_text, re.IGNORECASE)
        rating = rating_match.group(1).replace(",", ".") if rating_match else None

        phone_match = re.search(r"\b((?:\+62|0\d{2,3})[-\s]?\d{4,5}[-\s]?\d{3,5})\b", inner_text)
        telepon = phone_match.group(1).strip() if phone_match else None

        lines = [line.strip() for line in inner_text.split('\n') if line.strip()]

        kategori_maps = kategori

        for line in lines: 
            line_clean = line.strip().lower()

            #Cari baris yang mengandung separator Google Maps 
            if '·' in line_clean:
                parts = [part.strip() for part in line_clean.split('·') if part.strip()]

                if len(parts) >= 2:
                    kandidat_kategori = parts[0]

                    # Jangan ambil rating sebagai kategori
                    if re.match(r"^\d[.,]\d", kandidat_kategori):
                        continue

                    # Jangan ambil nama bisnis
                    if kandidat_kategori.lower() == nama.lower():
                        continue

                    kategori_maps = kandidat_kategori
                    break

        alamat = None
        for i, line in enumerate(lines):
            if '·' in line:
                parts = line.split('·')
                line = parts[-1].strip()

            line_lower = line.lower()
            if len(line) > 10 and any(keyword in line_lower for keyword in ["jl.", "jalan", "raya", "kec", "kab", "kota", ","]):
                if not re.match(r"^[0-9\s+-,.]+$", line):
                    alamat = line
                    break

        lat, lon = parse_coordinate_from_url(url_gmaps)

        return {
            "nama": nama,
            "kategori": kategori_maps,
            "alamat": alamat,
            "telepon": telepon,
            "rating": rating,
            "latitude": lat,
            "longitude": lon,
            "url_gmaps": url_gmaps
        }
    except Exception as e:
        return None


if __name__ == "__main__":
    lat, lon = parse_coordinate_from_url("https://www.google.com/maps/place/test/@-7.96662,112.632632,15z/")
    print(f"Test 1 - lat: {lat}, lon: {lon}")

    lat, lon = parse_coordinate_from_url("https://www.google.com/maps/data=!3d-7.96662!4d112.632632")
    print(f"Test 2 - lat: {lat}, lon: {lon}")

    # Test filter kategori
    print(cocok_kategori("PT Maju Jaya Sentosa", "PT"))   # True
    print(cocok_kategori("Warung Bu Siti", "restoran"))   # True