"""
Load file CBASE (1 file utuh jatim barat) ke bronze.cbase_raw.
Kolom "CEK CBASE [tanggal]" dan "MAPPING [bulan]_NIK/NAMA" dipetakan
pakai pattern matching karena nama aslinya berubah tiap refresh.

Usage:
    python -m etl.bronze.load_cbase --file "db/samples/cbase.xlsx"
"""
import argparse
import os
import uuid
import pandas as pd

from etl.common.db import get_engine
from etl.bronze.column_maps import map_cbase_columns


def load_cbase_file(file_path: str, batch_id: str, source_file: str = None):

    raw = pd.read_excel(file_path, header=None, dtype=str)

    header_row = None

    for i, row in raw.iterrows():
        values = [
            str(value).strip().upper()
            for value in row.tolist()
        ]

        required_headers = {"NIPNAS", "WITEL_HO", "STANDARD_NAME"}

        if required_headers.issubset(set(values)):
            header_row = i
            break

    if header_row is None:
        raise ValueError(
            "Header CBASE tidak ditemukan. Tidak ada baris yang mengandung 'NIPNAS'."
        )

    print(f"Header CBASE ditemukan di baris Excel ke-{header_row + 1}")

    df = pd.read_excel(
        file_path,
        header=header_row,
        dtype=str
    )

    df.columns = [str(c).strip() for c in df.columns]
    col_map = map_cbase_columns(df.columns)

    unrecognized = [c for c, target in col_map.items() if target is None]

    if unrecognized:
        print(
            f"Peringatan: {len(unrecognized)} kolom nggak dikenali, "
            f"di-skip: {unrecognized}"
        )

    recognized = {
        src: tgt
        for src, tgt in col_map.items()
        if tgt is not None
    }

    df = df[list(recognized.keys())].rename(columns=recognized)

    df["_source_file"] = source_file or os.path.basename(file_path)
    df["_batch_id"] = batch_id

    engine = get_engine()

    df.to_sql(
        "cbase_raw",
        engine,
        schema="bronze",
        if_exists="append",
        index=False
    )

    print(
        f"{len(df)} baris CBASE masuk ke bronze.cbase_raw "
        f"(batch: {batch_id})"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--batch-id", default=None)
    args = parser.parse_args()

    batch_id = args.batch_id or f"manual-{uuid.uuid4().hex[:8]}"
    load_cbase_file(args.file, batch_id)