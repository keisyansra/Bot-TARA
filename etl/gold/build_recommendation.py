"""
Bangun gold.prospect_recommendation versi awal -- fuzzy-match-only.
Kolom terkait ODP (nearest_odp_*, odp_distance_m, odp_available_port,
badge_status) sengaja dikosongin dulu, nanti diisi belakangan pas
spatial matching selesai. Struktur tabelnya udah final sekarang, jadi
kode yang query ke tabel ini (FastAPI/bot) udah bisa mulai dibangun
paralel walau ODP-nya belum kesambung.

Prospek yang DIKELUARIN dari daftar (dianggap udah pelanggan):
- customer_match_status IN ('MATCH_CONFIDENT', 'MATCH_POSSIBLE')
- is_telkom_entity = true

Sisanya (termasuk *_SINGLE_TOKEN, MATCH_REJECTED_LENGTH, NO_MATCH,
SKIPPED_SHORT_NAME) dianggap masih BELUM BERLANGGANAN -- default aman,
karena salah exclude prospek asli lebih mahal (kehilangan peluang)
daripada salah include orang yang udah jadi pelanggan (cuma rugi
waktu verifikasi pas sales kontak).

Usage:
    python -m etl.gold.build_recommendation
"""
import uuid
import pandas as pd
from sqlalchemy import text

from etl.common.db import get_engine

STAGING_TABLE = "_stg_prospect_recommendation"

EXCLUDED_MATCH_STATUS = ("MATCH_CONFIDENT", "MATCH_POSSIBLE")


def load_candidates(engine) -> pd.DataFrame:
    placeholders = ", ".join(f"'{s}'" for s in EXCLUDED_MATCH_STATUS)
    query = f"""
        SELECT
            p.prospect_id, p.nama, p.alamat, p.latitude, p.longitude,
            p.url_gmaps, p.wilayah,
            m.match_status AS customer_match_status,
            m.match_score AS customer_match_score
        FROM silver.prospect_clean p
        LEFT JOIN silver.prospect_customer_match m ON m.prospect_id = p.prospect_id
        WHERE p.is_telkom_entity = false
          AND (m.match_status IS NULL OR m.match_status NOT IN ({placeholders}))
    """
    return pd.read_sql(query, engine)


def upsert_gold(df: pd.DataFrame, engine, batch_id: str):
    df = df.copy()
    df["batch_id"] = batch_id

    df.to_sql(STAGING_TABLE, engine, schema="gold", if_exists="replace", index=False)

    with engine.begin() as conn:
        conn.execute(text(f"""
            INSERT INTO gold.prospect_recommendation (
                prospect_id, nama, alamat, latitude, longitude, geom,
                wilayah, url_gmaps, customer_match_status, customer_match_score,
                batch_id
            )
            SELECT
                prospect_id, nama, alamat, latitude, longitude,
                ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                wilayah, url_gmaps, customer_match_status, customer_match_score,
                batch_id
            FROM gold.{STAGING_TABLE}
            ON CONFLICT (prospect_id) DO UPDATE SET
                nama = EXCLUDED.nama,
                alamat = EXCLUDED.alamat,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                geom = EXCLUDED.geom,
                wilayah = EXCLUDED.wilayah,
                url_gmaps = EXCLUDED.url_gmaps,
                customer_match_status = EXCLUDED.customer_match_status,
                customer_match_score = EXCLUDED.customer_match_score,
                batch_id = EXCLUDED.batch_id,
                calculated_at = now();
        """))

        # buang baris gold yang prospect_id-nya udah nggak ada lagi di
        # daftar kandidat batch ini (misal abis fuzzy matching di-rerun
        # dan sekarang statusnya dianggap udah pelanggan)
        conn.execute(text(f"""
            DELETE FROM gold.prospect_recommendation
            WHERE prospect_id NOT IN (SELECT prospect_id FROM gold.{STAGING_TABLE});
        """))

        conn.execute(text(f"DROP TABLE IF EXISTS gold.{STAGING_TABLE};"))


def main():
    engine = get_engine()
    df = load_candidates(engine)

    print(f"Kandidat prospek (belum berlangganan): {len(df)}")

    if df.empty:
        print("Nggak ada kandidat, cek lagi query filter-nya.")
        return

    batch_id = f"gold-{uuid.uuid4().hex[:8]}"
    upsert_gold(df, engine, batch_id)
    print(f"Selesai. batch_id: {batch_id}")


if __name__ == "__main__":
    main()