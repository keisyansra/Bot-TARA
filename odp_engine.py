import psycopg2
from math import radians, cos, sin, asin, sqrt

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "tara_bot"
DB_USER = "postgres"
DB_PASS = "admin123"  # Ganti password sesuai PostgreSQL laptopmu

def get_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )

def haversine(lat1, lon1, lat2, lon2):
    """Menghitung jarak Haversine dalam meter"""
    R = 6371000
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    a = sin(dLat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2)**2
    return R * (2 * asin(sqrt(a)))


# =====================================================================
# STEP 1: CARI DAFTAR PROSPEK (TANPA HITUNG ODP DULU)
# =====================================================================

def get_prospects_by_query(query_type, value, limit=5, sales_lat=None, sales_lon=None):
    """
    Mengambil daftar Top 5 Prospek Baru (Status FALSE di CBASE)
    query_type: 'name', 'wilayah', atau 'liveloc'
    """
    conn = get_connection()
    cursor = conn.cursor()

    if query_type == 'name':
        sql = """
            SELECT lead_id, nama, kategori, alamat, wilayah, latitude, longitude
            FROM lead_candidates
            WHERE status_existing = FALSE AND LOWER(nama) LIKE %s
            LIMIT %s;
        """
        cursor.execute(sql, (f"%{value.lower().strip()}%", limit))
        rows = cursor.fetchall()
        
    elif query_type == 'wilayah':
        sql = """
            SELECT lead_id, nama, kategori, alamat, wilayah, latitude, longitude
            FROM lead_candidates
            WHERE status_existing = FALSE AND LOWER(wilayah) LIKE %s
            LIMIT %s;
        """
        cursor.execute(sql, (f"%{value.lower().strip()}%", limit))
        rows = cursor.fetchall()

    elif query_type == 'liveloc':
        delta = 5.0 / 111.0  # radius 5km
        sql = """
            SELECT lead_id, nama, kategori, alamat, wilayah, latitude, longitude
            FROM lead_candidates
            WHERE status_existing = FALSE
              AND latitude BETWEEN %s AND %s AND longitude BETWEEN %s AND %s;
        """
        cursor.execute(sql, (sales_lat - delta, sales_lat + delta, sales_lon - delta, sales_lon + delta))
        rows = cursor.fetchall()

    conn.close()

    results = []
    for r in rows:
        lead_id, nama, kat, alamat, wil, lat, lon = r
        
        # Hitung jarak ke sales jika via live loc
        dist_sales = round(haversine(sales_lat, sales_lon, lat, lon), 1) if sales_lat else None
        
        results.append({
            'lead_id': lead_id,
            'nama': nama,
            'kategori': kat,
            'alamat': alamat,
            'wilayah': wil,
            'latitude': lat,
            'longitude': lon,
            'dist_to_sales_m': dist_sales
        })

    if query_type == 'liveloc':
        results.sort(key=lambda x: x['dist_to_sales_m'])
        results = results[:limit]

    return results


# =====================================================================
# STEP 2: CEK ODP TERDEKAT (DIPANGGUL SAAT TOMBOL DIKLIK)
# =====================================================================

def check_odp_by_lead_id(lead_id, max_radius_m=250):
    """
    Di-trigger saat sales menekan tombol [📍 Cek ODP & port terdekat]
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Ambil koordinat prospek dari database
    cursor.execute("SELECT nama, alamat, latitude, longitude FROM lead_candidates WHERE lead_id = %s;", (lead_id,))
    lead = cursor.fetchone()

    if not lead or not lead[2] or not lead[3]:
        conn.close()
        return None, "⚠️ Koordinat prospek tidak ditemukan."

    p_nama, p_alamat, p_lat, p_lon = lead

    # 2. Cari ODP di radius 250m
    query_odp = """
        SELECT odp_name, latitude, longitude, total_port, used_port, available_port, occupancy_status
        FROM odp_master
        WHERE latitude BETWEEN %s AND %s AND longitude BETWEEN %s AND %s;
    """
    cursor.execute(query_odp, (p_lat - 0.003, p_lat + 0.003, p_lon - 0.003, p_lon + 0.003))
    odp_rows = cursor.fetchall()
    conn.close()

    if not odp_rows:
        return None, f"⚠️ Tidak ditemukan ODP di radius {max_radius_m}m untuk {p_nama}."

    odp_candidates = []
    for row in odp_rows:
        odp_name, o_lat, o_lon, total_p, used_p, avail_p, status = row
        dist = haversine(p_lat, p_lon, o_lat, o_lon)
        if dist <= max_radius_m:
            odp_candidates.append({
                'odp_name': odp_name, 'latitude': o_lat, 'longitude': o_lon,
                'distance_m': round(dist, 1), 'total_port': total_p,
                'used_port': used_p, 'available_port': avail_p, 'status': status
            })

    odp_candidates.sort(key=lambda x: x['distance_m'])

    # Logika Auto-Redirect ODP Merah
    selected_odp = None
    redirected = False
    for odp in odp_candidates:
        if odp['available_port'] > 0:
            selected_odp = odp
            break
        else:
            redirected = True

    if selected_odp:
        selected_odp['is_redirected'] = redirected
        selected_odp['prospect_nama'] = p_nama
        selected_odp['prospect_lat'] = p_lat
        selected_odp['prospect_lon'] = p_lon
        # Buat Link Rute Google Maps langsung
        selected_odp['gmaps_url'] = f"https://www.google.com/maps/dir/?api=1&destination={selected_odp['latitude']},{selected_odp['longitude']}"
        return selected_odp, "OK"
    
    return None, f"⚠️ Seluruh ODP terdekat di sekitar {p_nama} FULL (Merah)."


# =====================================================================
# SIMULASI ALUR BERTAHAP DI TERMINAL
# =====================================================================
if __name__ == "__main__":
    print("📱 [STEP 1] Sales mencari wilayah 'Kepanjen'...")
    prospek_list = get_prospects_by_query('wilayah', 'Kepanjen', limit=2)
    
    for idx, p in enumerate(prospek_list, 1):
        print(f"\n🏢 [{idx}] {p['nama']}")
        print(f"    Status : BELUM BERLANGGANAN - HIGH PRIORITY")
        print(f"    Alamat : {p['alamat']}")
        print(f"    [BUTTON]: [📍 Cek ODP & port terdekat (ID: {p['lead_id']})]")

    # Simulasi Sales mengeklik tombol pada prospek nomor 1
    selected_id = prospek_list[0]['lead_id']
    print(f"\n👆 Sales mengeklik tombol Cek ODP untuk ID {selected_id}...")
    
    odp_res, msg = check_odp_by_lead_id(selected_id)
    if odp_res:
        print(f"\n✅ OUTPUT RESPONSE ODP:")
        print(f"   🏢 {odp_res['prospect_nama']}")
        print(f"   🔌 {odp_res['odp_name']}")
        print(f"   📏 Jarak {odp_res['distance_m']} meter")
        print(f"   📊 Status: {odp_res['status']} ({odp_res['used_port']}/{odp_res['total_port']} port terisi)")
        print(f"   🟢 LAYAK PASANG")
        print(f"   [BUTTON]: [🗺️ Buka rute Google Maps] ({odp_res['gmaps_url']})")