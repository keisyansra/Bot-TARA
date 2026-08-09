"""
Bronze -> Silver buat ODP: cleaning, typing, validasi koordinat,
dedup per id_odp, upsert ke silver.odp_clean (geography PostGIS).

Wilayah diambil dari kolom `telda` (data asli per baris), BUKAN dari
`_wilayah_file` (itu cuma label lineage, bisa aja blanket kalau
di-load sebagai 1 file gabungan).

Usage:
    python -m etl.silver.clean_odp
"""
import uuid
import pandas as pd
from sqlalchemy import text

from etl.common.db import get_engine

# Kira-kira batas lat/long Jawa Timur, buat nyaring koordinat yang jelas salah
LAT_MIN, LAT_MAX = -9.5, -6.5
LON_MIN, LON_MAX = 110.5, 114.5

STAGING_TABLE = "_stg_odp_clean"


def load_bronze_odp(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM bronze.odp_raw", engine)


def clean_odp(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["latitude", "longitude"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["avai", "used", "rsv", "rsk", "is_total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["id_odp"] = pd.to_numeric(df["id_odp"], errors="coerce")

    n_before = len(df)

    # buang baris yang gagal parse hal krusial (nggak bisa dipakai
    # buat spatial matching atau nentuin sisa port tanpa ini)
    df = df.dropna(subset=["id_odp", "latitude", "longitude", "avai"])
    n_after_required = len(df)

    valid_coord = df["latitude"].between(LAT_MIN, LAT_MAX) & df["longitude"].between(LON_MIN, LON_MAX)
    n_bad_coord = int((~valid_coord).sum())
    df = df[valid_coord]

    n_missing_telda = int(df["telda"].isna().sum() + (df["telda"].astype(str).str.strip() == "").sum())
    df["wilayah_file"] = df["telda"].where(df["telda"].notna() & (df["telda"].astype(str).str.strip() != ""), "TIDAK_DIKETAHUI")

    # dedup id_odp, ambil yang paling baru di-load kalau ada duplikat
    n_before_dedup = len(df)
    df = df.sort_values("_loaded_at", ascending=False).drop_duplicates(subset="id_odp", keep="first")
    n_duplicates = n_before_dedup - len(df)

    print(f"Bronze: {n_before} baris")
    print(f"  - dibuang (id_odp/lat/lon/avai kosong atau gagal parse): {n_before - n_after_required}")
    print(f"  - dibuang (koordinat di luar jangkauan wajar Jatim): {n_bad_coord}")
    print(f"  - dibuang (duplikat id_odp, ambil yang terbaru): {n_duplicates}")
    if n_missing_telda:
        print(f"  - peringatan: {n_missing_telda} baris nggak ada nilai 'telda', ditandai TIDAK_DIKETAHUI")
    print(f"Siap di-upsert ke silver: {len(df)} baris")

    return df[[
        "id_odp", "odp_name", "latitude", "longitude",
        "avai", "used", "rsv", "rsk", "is_total",
        "occ_2", "telkom_witel", "kabupaten_kota", "provinsi", "wilayah_file",
    ]].rename(columns={
        "avai": "available_port",
        "used": "used_port",
        "rsv": "rsv_port",
        "rsk": "rsk_port",
        "is_total": "total_port",
        "occ_2": "occupancy_status",
        "telkom_witel": "witel",
    })


def upsert_silver(df: pd.DataFrame, engine, batch_id: str):
    df = df.copy()
    df["batch_id"] = batch_id

    # staging table dulu (bulk write, cepat), baru INSERT..SELECT ke
    # tabel final dengan ON CONFLICT -- jauh lebih cepat dibanding
    # insert baris-per-baris buat puluhan ribu baris
    df.to_sql(STAGING_TABLE, engine, schema="silver", if_exists="replace", index=False)

    with engine.begin() as conn:
        conn.execute(text(f"""
            INSERT INTO silver.odp_clean (
                id_odp, odp_name, latitude, longitude, geom,
                available_port, used_port, rsv_port, rsk_port, total_port,
                occupancy_status, witel, kabupaten_kota, provinsi,
                wilayah_file, batch_id
            )
            SELECT
                id_odp, odp_name, latitude, longitude,
                ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                available_port, used_port, rsv_port, rsk_port, total_port,
                occupancy_status, witel, kabupaten_kota, provinsi,
                wilayah_file, batch_id
            FROM silver.{STAGING_TABLE}
            ON CONFLICT (id_odp) DO UPDATE SET
                odp_name = EXCLUDED.odp_name,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                geom = EXCLUDED.geom,
                available_port = EXCLUDED.available_port,
                used_port = EXCLUDED.used_port,
                rsv_port = EXCLUDED.rsv_port,
                rsk_port = EXCLUDED.rsk_port,
                total_port = EXCLUDED.total_port,
                occupancy_status = EXCLUDED.occupancy_status,
                witel = EXCLUDED.witel,
                kabupaten_kota = EXCLUDED.kabupaten_kota,
                provinsi = EXCLUDED.provinsi,
                wilayah_file = EXCLUDED.wilayah_file,
                batch_id = EXCLUDED.batch_id,
                cleaned_at = now();
        """))
        conn.execute(text(f"DROP TABLE IF EXISTS silver.{STAGING_TABLE};"))


def main():
    engine = get_engine()
    df = load_bronze_odp(engine)
    df_clean = clean_odp(df)

    if df_clean.empty:
        print("Nggak ada baris valid buat di-upsert, cek lagi bronze.odp_raw.")
        return

    batch_id = f"silver-{uuid.uuid4().hex[:8]}"
    upsert_silver(df_clean, engine, batch_id)
    print(f"Selesai. batch_id: {batch_id}")


if __name__ == "__main__":
    main()