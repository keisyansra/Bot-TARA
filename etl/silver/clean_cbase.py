"""
Bronze -> Silver untuk CBASE.
Filter khusus 'Telkom JATIM BARAT', cleaning nipnas & standard_name,
normalisasi nama, dedup, dan upsert ke silver.cbase_clean.

Usage:
    python -m etl.silver.clean_cbase
"""

import uuid
import pandas as pd
from sqlalchemy import text

from etl.common.db import get_engine
from etl.common.text import normalize_name

STAGING_TABLE = "_stg_cbase_clean"


def load_bronze_cbase(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM bronze.cbase_raw", engine)


def clean_cbase(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    n_before = len(df)

    # 2. Filter hanya Telkom JATIM BARAT
    is_jatim_barat = df["witel_ho"].astype(str).str.strip().str.upper() == "TELKOM JATIM BARAT"
    df = df[is_jatim_barat].copy()
    n_after_filter = len(df)

    # 4. Bersihkan nipnas
    # Hindari float/scientific notation
    def clean_nipnas(x):
        if pd.isna(x):
            return ""
        # Jika bentuk float, jadikan int dulu supaya tidak ada .0
        if isinstance(x, float):
            try:
                x = int(x)
            except (ValueError, OverflowError):
                pass
        s = str(x).strip()
        # Jika string memiliki .0 di akhir, hapus
        if s.endswith(".0"):
            s = s[:-2]
        return s

    df["nipnas"] = df["nipnas"].apply(clean_nipnas)
    
    # 4. Bersihkan standard_name
    df["standard_name"] = df["standard_name"].astype(str).str.strip()
    # Mengganti nilai "nan" atau "None" string bawaan pandas yang terjadi saat cast
    df.loc[df["standard_name"].str.lower().isin(["nan", "none", ""]), "standard_name"] = ""

    # Hapus nipnas kosong
    n_before_drop_nipnas = len(df)
    df = df[df["nipnas"] != ""]
    n_dropped_nipnas = n_before_drop_nipnas - len(df)

    # Hapus standard_name kosong
    n_before_drop_name = len(df)
    df = df[df["standard_name"] != ""]
    n_dropped_name = n_before_drop_name - len(df)

    # 5. Tambahkan nama_normalized
    df["nama_normalized"] = df["standard_name"].apply(normalize_name)
    
    # Jika hasil normalisasi ternyata kosong, drop juga (opsional, tapi disarankan)
    # df = df[df["nama_normalized"] != ""]

    # 6. Dedup berdasarkan nipnas (ambil yang paling baru)
    n_before_dedup = len(df)
    if "_loaded_at" in df.columns:
        df = df.sort_values("_loaded_at", ascending=False)
    
    df = df.drop_duplicates(subset=["nipnas"], keep="first")
    n_duplicates = n_before_dedup - len(df)

    # 8. Print laporan
    print(f"Bronze total: {n_before} baris")
    print(f"Setelah filter Telkom JATIM BARAT: {n_after_filter} baris")
    print(f"Dibuang (nipnas kosong): {n_dropped_nipnas}")
    print(f"Dibuang (standard_name kosong): {n_dropped_name}")
    print(f"Dibuang (duplikat nipnas): {n_duplicates}")
    print(f"Siap di-upsert ke silver: {len(df)} baris")

    # Ambil kolom yang dibutuhkan
    return df[["nipnas", "witel_ho", "standard_name", "nama_normalized"]]


def upsert_silver(df: pd.DataFrame, engine, batch_id: str):
    df = df.copy()
    df["batch_id"] = batch_id

    # Push to staging table
    df.to_sql(STAGING_TABLE, engine, schema="silver", if_exists="replace", index=False)

    # Upsert with ON CONFLICT (nipnas)
    with engine.begin() as conn:
        conn.execute(text(f"""
            INSERT INTO silver.cbase_clean (
                nipnas, witel_ho, standard_name, nama_normalized, batch_id
            )
            SELECT
                nipnas, witel_ho, standard_name, nama_normalized, batch_id
            FROM silver.{STAGING_TABLE}
            ON CONFLICT (nipnas) DO UPDATE SET
                witel_ho = EXCLUDED.witel_ho,
                standard_name = EXCLUDED.standard_name,
                nama_normalized = EXCLUDED.nama_normalized,
                batch_id = EXCLUDED.batch_id,
                cleaned_at = now();
        """))
        conn.execute(text(f"DROP TABLE IF EXISTS silver.{STAGING_TABLE};"))


def main():
    engine = get_engine()
    df = load_bronze_cbase(engine)
    df_clean = clean_cbase(df)

    if df_clean.empty:
        print("Nggak ada data valid buat di-upsert, cek lagi bronze.cbase_raw.")
        return

    batch_id = f"silver-{uuid.uuid4().hex[:8]}"
    upsert_silver(df_clean, engine, batch_id)
    print(f"Selesai. batch_id: {batch_id}")


if __name__ == "__main__":
    main()
