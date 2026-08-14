"""
Spatial enrichment: isi nearest ODP untuk setiap prospect
di gold.prospect_recommendation menggunakan PostGIS.

Aturan bisnis:
    - Radius maksimum = 250 meter (ditetapkan mentor).
    - Hanya ODP dengan available_port > 0 yang boleh dipilih.
    - Prioritas: ODP terdekat dalam radius → siap_pasang
    - Fallback: ODP terdekat di luar radius → di_luar_radius
    - Tidak ada ODP available → odp_tidak_ditemukan

Usage:
    python -m etl.gold.enrich_nearest_odp
"""

import uuid
from sqlalchemy import text

from etl.common.db import get_engine

MAX_RADIUS_M = 250


def enrich(engine, batch_id: str):
    """
    Satu transaksi SQL, tiga langkah UPDATE:
      1) siap_pasang
      2) di_luar_radius
      3) odp_tidak_ditemukan
    """
    with engine.begin() as conn:

        # ── Reset hasil spatial sebelumnya ───────────────────────────
        # Penting supaya setiap kali ETL dijalankan ulang,
        # hasil lama tidak mempengaruhi perhitungan baru.
        conn.execute(text("""
            UPDATE gold.prospect_recommendation
            SET
                nearest_odp_id = NULL,
                nearest_odp_name = NULL,
                nearest_odp_latitude = NULL,
                nearest_odp_longitude = NULL,
                odp_distance_m = NULL,
                odp_available_port = NULL,
                badge_status = NULL;
        """))

        # ── Langkah 1: siap_pasang ───────────────────────────────────
        conn.execute(text("""
            UPDATE gold.prospect_recommendation AS p
            SET
                nearest_odp_id     = sub.id_odp,
                nearest_odp_name   = sub.odp_name,
                nearest_odp_latitude = sub.latitude,
                nearest_odp_longitude = sub.longitude,
                odp_distance_m     = sub.distance_m,
                odp_available_port = sub.available_port,
                badge_status       = 'siap_pasang',
                batch_id           = :batch_id,
                calculated_at      = now()
            FROM (
                SELECT DISTINCT ON (pr.prospect_id)
                    pr.prospect_id,
                    o.id_odp,
                    o.odp_name,
                    o.latitude,
                    o.longitude,
                    o.available_port,
                    ST_Distance(pr.geom, o.geom) AS distance_m
                FROM gold.prospect_recommendation pr
                CROSS JOIN LATERAL (
                    SELECT
                        oc.id_odp,
                        oc.odp_name,
                        oc.latitude,
                        oc.longitude,
                        oc.available_port,
                        oc.geom
                    FROM silver.odp_clean oc
                    WHERE oc.available_port > 0
                      AND ST_DWithin(pr.geom, oc.geom, :radius)
                    ORDER BY pr.geom <-> oc.geom
                    LIMIT 1
                ) o
            ) sub
            WHERE p.prospect_id = sub.prospect_id;
        """), {"batch_id": batch_id, "radius": MAX_RADIUS_M})

        # ── Langkah 2: di_luar_radius ────────────────────────────────
        # Untuk prospect yang belum dapat ODP di langkah 1,
        # cari ODP terdekat available_port>0 TANPA batas radius.
        conn.execute(text("""
            UPDATE gold.prospect_recommendation AS p
            SET
                nearest_odp_id     = sub.id_odp,
                nearest_odp_name   = sub.odp_name,
                nearest_odp_latitude = sub.latitude,
                nearest_odp_longitude = sub.longitude,
                odp_distance_m     = sub.distance_m,
                odp_available_port = sub.available_port,
                badge_status       = 'di_luar_radius',
                batch_id           = :batch_id,
                calculated_at      = now()
            FROM (
                SELECT DISTINCT ON (pr.prospect_id)
                    pr.prospect_id,
                    o.id_odp,
                    o.odp_name,
                    o.latitude,
                    o.longitude,
                    o.available_port,
                    ST_Distance(pr.geom, o.geom) AS distance_m
                FROM gold.prospect_recommendation pr
                CROSS JOIN LATERAL (
                    SELECT
                        oc.id_odp,
                        oc.odp_name,
                        oc.latitude,
                        oc.longitude,
                        oc.available_port,
                        oc.geom
                    FROM silver.odp_clean oc
                    WHERE oc.available_port > 0
                    ORDER BY pr.geom <-> oc.geom
                    LIMIT 1
                ) o
                WHERE pr.badge_status IS NULL
                   OR pr.badge_status NOT IN ('siap_pasang')
            ) sub
            WHERE p.prospect_id = sub.prospect_id;
        """), {"batch_id": batch_id})

        # ── Langkah 3: odp_tidak_ditemukan ───────────────────────────
        # Prospect yang masih belum punya badge setelah langkah 1 & 2.
        conn.execute(text("""
            UPDATE gold.prospect_recommendation
            SET
                nearest_odp_id     = NULL,
                nearest_odp_name   = NULL,
                nearest_odp_latitude = NULL,
                nearest_odp_longitude = NULL,
                odp_distance_m     = NULL,
                odp_available_port = NULL,
                badge_status       = 'odp_tidak_ditemukan',
                batch_id           = :batch_id,
                calculated_at      = now()
            WHERE badge_status IS NULL
               OR badge_status NOT IN ('siap_pasang', 'di_luar_radius');
        """), {"batch_id": batch_id})


def print_stats(engine):
    with engine.connect() as conn:
        total = conn.execute(text(
            "SELECT COUNT(*) FROM gold.prospect_recommendation"
        )).scalar()

        rows = conn.execute(text("""
            SELECT badge_status, COUNT(*) AS cnt
            FROM gold.prospect_recommendation
            GROUP BY badge_status
            ORDER BY badge_status
        """)).fetchall()

    stats = {r[0]: r[1] for r in rows}

    print(f"Total prospect diproses: {total}")
    print(f"  - siap_pasang: {stats.get('siap_pasang', 0)}")
    print(f"  - di_luar_radius: {stats.get('di_luar_radius', 0)}")
    print(f"  - odp_tidak_ditemukan: {stats.get('odp_tidak_ditemukan', 0)}")


def main():
    engine = get_engine()

    batch_id = f"gold-odp-{uuid.uuid4().hex[:8]}"
    enrich(engine, batch_id)
    print_stats(engine)

    print(f"\nSelesai.\nbatch_id: {batch_id}")


if __name__ == "__main__":
    main()
