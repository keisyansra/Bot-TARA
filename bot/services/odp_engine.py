import math
import pandas as pd
from services.db_service import get_prospect_data, get_odp_data

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Menghitung jarak antara 2 titik koordinat (dalam meter)"""
    R = 6371000  
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)


def find_nearest_prospects_by_location(sales_lat, sales_long, limit=5):
    """Mencari 5 PT/CV belum berlangganan terdekat dari lokasi Sales"""
    df_scraping = get_prospect_data()
    if df_scraping.empty:
        return []

    prospect_list = []
    for _, row in df_scraping.iterrows():
        try:
            p_lat = float(row.get('latitude', 0))
            p_long = float(row.get('longitude', 0))
            
            if p_lat == 0 or p_long == 0:
                continue

            distance = calculate_haversine_distance(sales_lat, sales_long, p_lat, p_long)

            prospect_list.append({
                "nama": row.get('nama_perusahaan', 'PT/CV Tanpa Nama'),
                "alamat": row.get('alamat', 'Alamat tidak tersedia'),
                "lat": p_lat,
                "long": p_long,
                "distance_m": distance
            })
        except Exception:
            continue

   
    prospect_list.sort(key=lambda x: x['distance_m'])
    return prospect_list[:limit]


def find_nearby_odps(lat, long, max_distance=250):
    df_odp = get_odp_data()
    if df_odp.empty:
        return []

    nearby_odps = []
    for _, row in df_odp.iterrows():
        try:
            odp_lat = float(row.get('latitude', 0))
            odp_long = float(row.get('longitude', 0))

            if odp_lat == 0 or odp_long == 0:
                continue

            distance = calculate_haversine_distance(lat, long, odp_lat, odp_long)

            if distance <= max_distance:
                total_cap = int(row.get('kapasitas_total', 8))
                avail_port = int(row.get('port_tersedia', 0))
                status_color = "HIJAU" if avail_port > 0 else "MERAH"

                nearby_odps.append({
                    "nama_odp": str(row.get('nama_odp', 'ODP-UNKNOWN')),
                    "jarak": distance,
                    "port_tersedia": avail_port,
                    "kapasitas": total_cap,
                    "status": status_color,
                    "latitude": odp_lat,     
                    "longitude": odp_long    
                })
        except Exception:
            continue

    nearby_odps.sort(key=lambda x: x['jarak'])
    return nearby_odps