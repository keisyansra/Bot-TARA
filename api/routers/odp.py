"""
Endpoint terkait ODP. Query langsung ke silver.odp_clean -- beda
dari prospects.py yang baca gold.prospect_recommendation. Fitur 1 ini
buat sales cek ODP terdekat dari lokasinya langsung, tanpa lewat
prospect matching.
"""
from fastapi import APIRouter, Query
from sqlalchemy import text

from etl.common.db import get_engine

router = APIRouter()
engine = get_engine()


@router.get("/nearby")
def get_nearby_odp(
    lat: float = Query(..., description="Latitude lokasi sales"),
    lon: float = Query(..., description="Longitude lokasi sales"),
    limit: int = Query(5, ge=1, le=20),
    radius: float | None = Query(None, description="Radius pencarian dalam meter, opsional"),
):
    """
    Fitur 1: sales share lokasi -> daftar ODP terdekat yang portnya
    available. Query langsung ke silver.odp_clean (bukan gold), gak
    ada logic prospect matching di sini.
    """
    radius_clause = ""
    params = {"lat": lat, "lon": lon, "limit": limit}
    if radius:
        radius_clause = "AND ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)"
        params["radius"] = radius

    query = text(f"""
        SELECT
            odp_id, nama_odp, alamat, witel, avai,
            latitude, longitude,
            ROUND(ST_Distance(
                geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            )::numeric, 1) AS distance_from_sales_m
        FROM silver.odp_clean
        WHERE avai > 0
        {radius_clause}
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
        LIMIT :limit;
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, params).mappings().all()

    formatted_data = []
    for r in rows:
        formatted_data.append({
            "odp_id": r["odp_id"],
            "name": r["nama_odp"],
            "alamat": r["alamat"],
            "witel": r["witel"],
            "available_port": r["avai"],
            "latitude": float(r["latitude"]) if r["latitude"] is not None else None,
            "longitude": float(r["longitude"]) if r["longitude"] is not None else None,
            "distance_from_sales_m": float(r["distance_from_sales_m"]) if r["distance_from_sales_m"] is not None else None,
        })

    return {"status": "success", "data": formatted_data}