"""
Fuzzy matching antara prospect dan customer (CBASE) menggunakan RapidFuzz.
Mencari kandidat terbaik untuk setiap prospect berdasarkan nama_normalized.

Usage:
    python -m etl.silver.match_prospect_customer
"""

import uuid
import pandas as pd
from sqlalchemy import text
from rapidfuzz import process, fuzz

from etl.common.db import get_engine

STAGING_TABLE = "_stg_prospect_customer_match"

# Kalau nama lebih pendek dari ini dibanding pasangannya (rasio panjang),
# match ditolak apapun skornya -- nangkep kasus nama CBASE super pendek
# ("REJEKI") yang kebetulan jadi substring nama prospek yang panjang.
MIN_LENGTH_RATIO = 0.5


def load_data(engine):
    df_prospect = pd.read_sql(
        "SELECT prospect_id, nama as prospect_name, nama_normalized as prospect_name_normalized, "
        "wilayah as prospect_wilayah FROM silver.prospect_clean",
        engine
    )
    df_cbase = pd.read_sql(
        "SELECT nipnas as matched_nipnas, standard_name as matched_standard_name, "
        "nama_normalized as matched_name_normalized FROM silver.cbase_clean",
        engine
    )
    return df_prospect, df_cbase


def match_prospects(df_prospect: pd.DataFrame, df_cbase: pd.DataFrame) -> pd.DataFrame:
    df_cbase = df_cbase[
        (df_cbase["matched_name_normalized"].notna()) &
        (df_cbase["matched_name_normalized"] != "")
    ].copy()

    cbase_names = df_cbase["matched_name_normalized"].tolist()
    cbase_indices = df_cbase.index.tolist()

    results = []

    for _, prospect in df_prospect.iterrows():
        p_name = str(prospect["prospect_name_normalized"]).strip()

        res = {
            "prospect_id": prospect["prospect_id"],
            "prospect_name": prospect["prospect_name"],
            "prospect_name_normalized": p_name,
            "prospect_wilayah": prospect["prospect_wilayah"],
            "matched_nipnas": None,
            "matched_standard_name": None,
            "matched_name_normalized": None,
            "match_score": None,
            "match_status": None,
        }

        if not p_name or p_name.lower() in ['nan', 'none']:
            res["match_status"] = "NO_MATCH"
            res["match_score"] = 0.0
            results.append(res)
            continue

        if len(p_name) < 4:
            res["match_status"] = "SKIPPED_SHORT_NAME"
            res["match_score"] = 0.0
            results.append(res)
            continue

        # PENTING: token_sort_ratio, BUKAN token_set_ratio.
        # token_set_ratio bisa ngasih skor 100 kalau salah satu nama
        # cuma subset kata dari nama lainnya -- bikin nama pendek
        # generik (mis. "REJEKI") ke-match 100% ke nama panjang yang
        # kebetulan ngandung kata itu ("PELITA REJEKI FARMA"), padahal
        # jelas beda entitas. token_sort_ratio bandingin string penuh
        # (abis kata-katanya diurutin), jadi selisih panjang tetep
        # kena penalti wajar.
        match = process.extractOne(
            p_name,
            cbase_names,
            scorer=fuzz.token_sort_ratio
        )

        if match:
            best_match_name, best_score, best_idx_in_list = match
            best_real_idx = cbase_indices[best_idx_in_list]
            cbase_row = df_cbase.loc[best_real_idx]

            res["matched_nipnas"] = cbase_row["matched_nipnas"]
            res["matched_standard_name"] = cbase_row["matched_standard_name"]
            res["matched_name_normalized"] = cbase_row["matched_name_normalized"]
            res["match_score"] = round(best_score, 2)

            len_a, len_b = len(p_name), len(best_match_name)
            length_ratio = min(len_a, len_b) / max(len_a, len_b) if max(len_a, len_b) > 0 else 0

            # nama 1 kata doang di DUA sisi (gak ada kata lain yang
            # bisa mastiin itu entitas yang sama) -- dipisah kategorinya,
            # BUKAN dibuang, biar tetep keliatan pas audit tapi nggak
            # otomatis dianggap "pasti pelanggan yang sama" kayak match
            # multi-kata yang lebih meyakinkan.
            is_single_token = (" " not in p_name) and (" " not in best_match_name)

            if length_ratio < MIN_LENGTH_RATIO:
                res["match_status"] = "MATCH_REJECTED_LENGTH"
            elif best_score >= 95.0:
                res["match_status"] = "MATCH_CONFIDENT_SINGLE_TOKEN" if is_single_token else "MATCH_CONFIDENT"
            elif best_score >= 85.0:
                res["match_status"] = "MATCH_POSSIBLE_SINGLE_TOKEN" if is_single_token else "MATCH_POSSIBLE"
            else:
                res["match_status"] = "NO_MATCH"
        else:
            res["match_status"] = "NO_MATCH"
            res["match_score"] = 0.0

        results.append(res)

    return pd.DataFrame(results)


def upsert_match(df: pd.DataFrame, engine, batch_id: str):
    df = df.copy()
    df["batch_id"] = batch_id
    df["matcher_version"] = "rapidfuzz-token_sort_ratio-v2-lenguard"

    df.to_sql(STAGING_TABLE, engine, schema="silver", if_exists="replace", index=False)

    with engine.begin() as conn:
        conn.execute(text(f"""
            INSERT INTO silver.prospect_customer_match (
                prospect_id, prospect_name, prospect_name_normalized, prospect_wilayah,
                matched_nipnas, matched_standard_name, matched_name_normalized,
                match_score, match_status, matcher_version, batch_id
            )
            SELECT
                prospect_id, prospect_name, prospect_name_normalized, prospect_wilayah,
                matched_nipnas, matched_standard_name, matched_name_normalized,
                match_score, match_status, matcher_version, batch_id
            FROM silver.{STAGING_TABLE}
            ON CONFLICT (prospect_id) DO UPDATE SET
                prospect_name = EXCLUDED.prospect_name,
                prospect_name_normalized = EXCLUDED.prospect_name_normalized,
                prospect_wilayah = EXCLUDED.prospect_wilayah,
                matched_nipnas = EXCLUDED.matched_nipnas,
                matched_standard_name = EXCLUDED.matched_standard_name,
                matched_name_normalized = EXCLUDED.matched_name_normalized,
                match_score = EXCLUDED.match_score,
                match_status = EXCLUDED.match_status,
                matcher_version = EXCLUDED.matcher_version,
                batch_id = EXCLUDED.batch_id,
                matched_at = now();
        """))
        conn.execute(text(f"DROP TABLE IF EXISTS silver.{STAGING_TABLE};"))


def main():
    engine = get_engine()
    df_prospect, df_cbase = load_data(engine)

    print(f"Prospect loaded: {len(df_prospect)}")
    print(f"CBASE loaded: {len(df_cbase)}")

    if df_prospect.empty or df_cbase.empty:
        print("Data prospect atau cbase kosong. Membatalkan matching.")
        return

    df_match = match_prospects(df_prospect, df_cbase)

    stats = df_match["match_status"].value_counts()
    print(f"\nMATCH_CONFIDENT: {stats.get('MATCH_CONFIDENT', 0)}")
    print(f"MATCH_CONFIDENT_SINGLE_TOKEN: {stats.get('MATCH_CONFIDENT_SINGLE_TOKEN', 0)}")
    print(f"MATCH_POSSIBLE: {stats.get('MATCH_POSSIBLE', 0)}")
    print(f"MATCH_POSSIBLE_SINGLE_TOKEN: {stats.get('MATCH_POSSIBLE_SINGLE_TOKEN', 0)}")
    print(f"MATCH_REJECTED_LENGTH: {stats.get('MATCH_REJECTED_LENGTH', 0)}")
    print(f"NO_MATCH: {stats.get('NO_MATCH', 0)}")
    print(f"SKIPPED_SHORT_NAME: {stats.get('SKIPPED_SHORT_NAME', 0)}\n")

    batch_id = f"match-{uuid.uuid4().hex[:8]}"
    upsert_match(df_match, engine, batch_id)
    print(f"Selesai. batch_id: {batch_id}")


if __name__ == "__main__":
    main()