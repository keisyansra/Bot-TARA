from rapidfuzz import process, fuzz
from services.db_service import get_prospect_data, get_cbase_data

def search_unsubscribed_prospects(query_name, limit=5):
    """
    1. Mengambil data Scraping & CBASE.
    2. Melakukan filter/matching agar hanya menampilkan prospek BELUM BERLANGGANAN.
    3. Mengembalikan Top-N hasil pencarian menggunakan RapidFuzz.
    """
    df_scraping = get_prospect_data()
    df_cbase = get_cbase_data()

    if df_scraping.empty:
        return []

    # Ambil list pelanggan eksis CBASE untuk pemfilteran
    cbase_names = []
    if not df_cbase.empty and 'nama_perusahaan' in df_cbase.columns:
        cbase_names = df_cbase['nama_perusahaan'].dropna().astype(str).tolist()

    # Ekstrak daftar nama dari scraping
    choices = df_scraping['nama_perusahaan'].dropna().astype(str).tolist()

    # Matching kemiripan nama
    results = process.extract(query_name, choices, scorer=fuzz.WRatio, limit=limit * 2)

    matched_list = []
    for match_name, score, index in results:
        if score >= 50:  # Threshold kemiripan min 50%
            row = df_scraping.iloc[index]

            # Cek apakah nama ini ada di CBASE (Eksis)
            is_eksis = False
            if cbase_names:
                cbase_match = process.extractOne(match_name, cbase_names, scorer=fuzz.WRatio)
                if cbase_match and cbase_match[1] >= 85:  # Jika kemiripan > 85% dengan CBASE, dianggap sudah berlangganan
                    is_eksis = True

            # Hanya ambil yang BELUM BERLANGGANAN
            if not is_eksis:
                matched_list.append({
                    "nama": row.get('nama_perusahaan', match_name),
                    "alamat": row.get('alamat', 'Alamat tidak tersedia'),
                    "lat": float(row.get('latitude', 0)),
                    "long": float(row.get('longitude', 0)),
                    "score": round(score, 1)
                })

            if len(matched_list) >= limit:
                break

    return matched_list