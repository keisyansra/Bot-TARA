"""
Verifikasi integrasi Postgres + PostGIS:
1. Koneksi berhasil
2. Extension postgis aktif
3. Schema bronze/silver/gold ada
4. Query spatial (ST_Distance) jalan bener

Usage:
    python scripts/test_connection.py
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("1. Koneksi ke Postgres: OK")

    cur.execute("SELECT postgis_full_version();")
    print(f"2. PostGIS aktif: {cur.fetchone()[0][:60]}...")

    cur.execute("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name IN ('bronze', 'silver', 'gold')
        ORDER BY schema_name;
    """)
    schemas = [row[0] for row in cur.fetchall()]
    print(f"3. Schema ditemukan: {schemas}")
    assert schemas == ["bronze", "gold", "silver"], \
        "Ada schema yang belum ke-create, jalanin scripts/init_db.py dulu"

    # dua titik contoh: Malang ke Batu, buat mastiin ST_Distance jalan bener
    cur.execute("""
        SELECT ST_Distance(
            ST_MakePoint(112.6326, -7.9666)::geography,
            ST_MakePoint(112.5238, -7.8713)::geography
        );
    """)
    distance_m = cur.fetchone()[0]
    print(f"4. Spatial query jalan, jarak contoh Malang-Batu: {distance_m:,.0f} meter")

    cur.close()
    conn.close()
    print("\nSemua check lolos, integrasi Postgres+PostGIS siap dipakai.")


if __name__ == "__main__":
    main()