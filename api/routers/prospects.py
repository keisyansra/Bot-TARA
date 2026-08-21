"""
Endpoint terkait prospek. Query langsung ke gold.prospect_recommendation
-- tabel ini udah lengkap (fuzzy match customer + nearest ODP), jadi
endpoint di sini sengaja SIMPEL, cuma 1 query per request, nggak ada
logic tambahan/join lagi di sisi API.
"""
from fastapi import APIRouter, Query
from sqlalchemy import text

from etl.common.db import get_engine

router = APIRouter()
engine = get_engine()


@router.get("/nearby")
def get_nearby_prospects(
    lat: float = Query(..., description="Latitude lokasi sales"),
    lon: float = Query(..., description="Longitude lokasi sales"),
    limit: int = Query(5, ge=1, le=20),
):
    """
    Endpoint utama Fitur 2: sales share lokasi -> daftar prospek
    terdekat, udah lengkap sama info ODP terdekatnya (precomputed di
    ETL, bukan dihitung ulang di sini -- makanya cuma 1 query).
    """
    query = text("""
        SELECT
            prospect_id, nama, alamat, wilayah, url_gmaps, latitude, longitude,
            customer_match_status, customer_match_score,
            nearest_odp_id, nearest_odp_name, nearest_odp_latitude, nearest_odp_longitude,
            odp_distance_m, odp_available_port, badge_status,
            ROUND(ST_Distance(
                geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            )::numeric, 1) AS distance_from_sales_m
        FROM gold.prospect_recommendation
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
        LIMIT :limit;
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"lat": lat, "lon": lon, "limit": limit}).mappings().all()

    formatted_data = []
    for r in rows:
        formatted_data.append({
            "prospect": {
                "id": r["prospect_id"],
                "name": r["nama"],
                "alamat": r["alamat"],
                "wilayah": r["wilayah"],
                "url_gmaps": r["url_gmaps"],
                "latitude": float(r["latitude"]) if r["latitude"] is not None else None,
                "longitude": float(r["longitude"]) if r["longitude"] is not None else None,
                "distance_from_sales_m": float(r["distance_from_sales_m"]) if r["distance_from_sales_m"] is not None else None,
                "customer_match_status": r["customer_match_status"],
                "customer_match_score": float(r["customer_match_score"]) if r["customer_match_score"] is not None else None,
            },
            "nearest_odp": {
                "id": r["nearest_odp_id"],
                "name": r["nearest_odp_name"],
                "latitude": float(r["nearest_odp_latitude"]) if r["nearest_odp_latitude"] is not None else None,
                "longitude": float(r["nearest_odp_longitude"]) if r["nearest_odp_longitude"] is not None else None,
                "distance_m": float(r["odp_distance_m"]) if r["odp_distance_m"] is not None else None,
                "available_port": r["odp_available_port"],
                "status": r["badge_status"]
            } if r["badge_status"] != "odp_tidak_ditemukan" else None
        })

    return {"status": "success", "data": formatted_data}


@router.get("/search")
def search_prospects(
    query: str = Query(..., min_length=2, description="Kata kunci nama prospek"),
    limit: int = Query(5, ge=1, le=20),
):
    """
    Pencarian prospek by nama (buat kasus sales ketik nama PT, bukan
    share lokasi). ILIKE dulu buat MVP -- bisa di-upgrade ke pg_trgm
    similarity nanti kalau butuh toleransi typo yang lebih baik.
    """
    sql = text("""
        SELECT
            prospect_id, nama, alamat, wilayah, url_gmaps, latitude, longitude,
            customer_match_status, customer_match_score,
            nearest_odp_id, nearest_odp_name, nearest_odp_latitude, nearest_odp_longitude,
            odp_distance_m, odp_available_port, badge_status
        FROM gold.prospect_recommendation
        WHERE nama ILIKE :pattern
        ORDER BY nama
        LIMIT :limit;
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, {"pattern": f"%{query}%", "limit": limit}).mappings().all()

    formatted_data = []
    for r in rows:
        formatted_data.append({
            "prospect": {
                "id": r["prospect_id"],
                "name": r["nama"],
                "alamat": r["alamat"],
                "wilayah": r["wilayah"],
                "url_gmaps": r["url_gmaps"],
                "latitude": float(r["latitude"]) if r["latitude"] is not None else None,
                "longitude": float(r["longitude"]) if r["longitude"] is not None else None,
                "customer_match_status": r["customer_match_status"],
                "customer_match_score": float(r["customer_match_score"]) if r["customer_match_score"] is not None else None,
            },
            "nearest_odp": {
                "id": r["nearest_odp_id"],
                "name": r["nearest_odp_name"],
                "latitude": float(r["nearest_odp_latitude"]) if r["nearest_odp_latitude"] is not None else None,
                "longitude": float(r["nearest_odp_longitude"]) if r["nearest_odp_longitude"] is not None else None,
                "distance_m": float(r["odp_distance_m"]) if r["odp_distance_m"] is not None else None,
                "available_port": r["odp_available_port"],
                "status": r["badge_status"]
            } if r["badge_status"] != "odp_tidak_ditemukan" else None
        })

    return {"status": "success", "data": formatted_data}