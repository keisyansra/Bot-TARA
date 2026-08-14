"""
Load 1 file Excel hasil scraping Google Maps (per wilayah) ke bronze.prospect_raw.

Usage:
    python -m etl.bronze.load_prospect --file "db/samples/scraping_batu.xlsx" --wilayah BATU
"""
import argparse
import os
import uuid

from etl.common.db import get_engine
from etl.common.io import read_table
from etl.bronze.column_maps import PROSPECT_COLUMN_MAP


def load_prospect_file(file_path: str, wilayah: str, batch_id: str, source_file: str = None):
    df = read_table(file_path)
    df.columns = [str(c).strip().lower() for c in df.columns]  # jaga-jaga spasi/kapital beda
    df = df.rename(columns=PROSPECT_COLUMN_MAP)

    known_cols = list(PROSPECT_COLUMN_MAP.values())
    df = df[[c for c in known_cols if c in df.columns]]

    df["_wilayah_file"] = wilayah
    df["_source_file"] = source_file or os.path.basename(file_path)
    df["_batch_id"] = batch_id

    engine = get_engine()
    df.to_sql("prospect_raw", engine, schema="bronze", if_exists="append", index=False)
    print(f"{len(df)} baris prospek wilayah {wilayah} masuk ke bronze.prospect_raw (batch: {batch_id})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--wilayah", required=True)
    parser.add_argument("--batch-id", default=None)
    args = parser.parse_args()

    batch_id = args.batch_id or f"manual-{uuid.uuid4().hex[:8]}"
    load_prospect_file(args.file, args.wilayah.upper(), batch_id)