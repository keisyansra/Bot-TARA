"""
Bronze -> Silver buat prospek (hasil scraping): normalisasi nama,
cleaning alamat/telepon, flag entitas Telkom sendiri, dedup per
(nama_normalized, wilayah), upsert ke silver.prospect_clean.

Beda sama ODP: wilayah di sini diambil dari `_wilayah_file` (bukan
kolom per-baris kayak telda), karena file scraping emang di-load
per wilayah lewat --wilayah CLI dan itu udah tervalidasi bener
(breakdown 11 wilayah jumlahnya pas).

Usage:
    python -m etl.silver.clean_prospect
"""
import uuid
import pandas as pd
from sqlalchemy import text

from etl.common.db import get_engine
from etl.common.text import normalize_name

LAT_MIN, LAT_MAX = -9.5, -6.5
LON_MIN, LON_MAX = 110.5, 114.5

STAGING_TABLE = "_stg_prospect_clean"

def load_bronze_prospect(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM bronze.prospect_raw", engine)


def clean_prospect(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    n_before = len(df)

    df["nama_normalized"] = df["nama"].apply(normalize_name)
    df["alamat"] = df["alamat"].astype(str).str.replace(r"[\r\n]+", " ", regex=True).str.strip()
    df["telepon"] = df["telepon"].astype(str).str.replace(r"[\r\n]+", " ", regex=True).str.strip()

    df["rating"] = df["rating"].astype(str).str.replace(",", ".", regex=False)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    for col in ["latitude", "longitude"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # buang baris yang nama/koordinatnya nggak bisa dipakai sama sekali
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[df["nama_normalized"] != ""]
    n_after_required = len(df)

    valid_coord = df["latitude"].between(LAT_MIN, LAT_MAX) & df["longitude"].between(LON_MIN, LON_MAX)
    n_bad_coord = int((~valid_coord).sum())
    df = df[valid_coord]

    df["wilayah"] = df["_wilayah_file"]

    df["is_telkom_entity"] = (
        df["nama"].str.contains("telkom", case=False, na=False)
        | df["kategori"].astype(str).str.contains("telekomunikasi", case=False, na=False)
    )
    n_telkom = int(df["is_telkom_entity"].sum())

    n_before_dedup = len(df)
    df = df.sort_values("_loaded_at", ascending=False).drop_duplicates(
        subset=["nama_normalized", "wilayah"], keep="first"
    )
    n_duplicates = n_before_dedup - len(df)

    print(f"Bronze: {n_before} baris")
    print(f"  - dibuang (nama/lat/lon kosong atau gagal parse): {n_before - n_after_required}")
    print(f"  - dibuang (koordinat di luar jangkauan wajar Jatim): {n_bad_coord}")
    print(f"  - dibuang (duplikat nama_normalized+wilayah): {n_duplicates}")
    print(f"  - ditandai entitas Telkom sendiri (is_telkom_entity=true): {n_telkom}")
    print(f"Siap di-upsert ke silver: {len(df)} baris")

    return df[[
        "nama", "nama_normalized", "kategori", "alamat", "telepon",
        "rating", "latitude", "longitude", "url_gmaps", "wilayah", "is_telkom_entity",
    ]]


def upsert_silver(df: pd.DataFrame, engine, batch_id: str):
    df = df.copy()
    df["batch_id"] = batch_id

    df.to_sql(STAGING_TABLE, engine, schema="silver", if_exists="replace", index=False)

    with engine.begin() as conn:
        conn.execute(text(f"""
            INSERT INTO silver.prospect_clean (
                nama, nama_normalized, kategori, alamat, telepon, rating,
                latitude, longitude, geom, url_gmaps, wilayah, is_telkom_entity, batch_id
            )
            SELECT
                nama, nama_normalized, kategori, alamat, telepon, rating,
                latitude, longitude,
                ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                url_gmaps, wilayah, is_telkom_entity, batch_id
            FROM silver.{STAGING_TABLE}
            ON CONFLICT (nama_normalized, wilayah) DO UPDATE SET
                nama = EXCLUDED.nama,
                kategori = EXCLUDED.kategori,
                alamat = EXCLUDED.alamat,
                telepon = EXCLUDED.telepon,
                rating = EXCLUDED.rating,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                geom = EXCLUDED.geom,
                url_gmaps = EXCLUDED.url_gmaps,
                is_telkom_entity = EXCLUDED.is_telkom_entity,
                batch_id = EXCLUDED.batch_id,
                cleaned_at = now();
        """))
        conn.execute(text(f"DROP TABLE IF EXISTS silver.{STAGING_TABLE};"))


def main():
    engine = get_engine()
    df = load_bronze_prospect(engine)
    df_clean = clean_prospect(df)

    if df_clean.empty:
        print("Nggak ada baris valid buat di-upsert, cek lagi bronze.prospect_raw.")
        return

    batch_id = f"silver-{uuid.uuid4().hex[:8]}"
    upsert_silver(df_clean, engine, batch_id)
    print(f"Selesai. batch_id: {batch_id}")


if __name__ == "__main__":
    main()