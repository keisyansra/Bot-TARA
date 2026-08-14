"""
Load file ODP ke bronze.odp_raw.

Bisa membaca:
- File CSV
- File Excel (.xlsx / .xls)
- Sheet tertentu pada file Excel

Usage:
    # CSV
    python -m etl.bronze.load_odp --file "data/odp_batu.csv" --wilayah BATU

    # Excel + pilih sheet
    python -m etl.bronze.load_odp --file "data/odp_master.xlsx" --wilayah JATIM_BARAT --sheet "Sheet3"
"""

import argparse
import os
import uuid
import pandas as pd

from etl.common.db import get_engine
from etl.common.io import read_table
from etl.bronze.column_maps import ODP_COLUMN_MAP


def load_odp_file(
    file_path: str,
    wilayah: str,
    batch_id: str,
    source_file: str = None,
    sheet_name: str = None,
):
    """
    Load file ODP ke bronze.odp_raw.

    Jika file Excel, sheet tertentu bisa dipilih menggunakan sheet_name.
    Jika file CSV, sheet_name akan diabaikan.
    """

    # Baca file berdasarkan format
    if file_path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name if sheet_name is not None else 0,
            dtype=str
        )
    else:
        df = read_table(file_path)

    # Bersihkan nama kolom dari kemungkinan spasi
    df.columns = [str(c).strip() for c in df.columns]

    # Mapping nama kolom sumber -> nama kolom bronze
    df = df.rename(columns=ODP_COLUMN_MAP)

    # Ambil hanya kolom yang dikenal
    known_cols = list(ODP_COLUMN_MAP.values())
    df = df[[c for c in known_cols if c in df.columns]]

    # Metadata ingestion
    df["_wilayah_file"] = wilayah
    df["_source_file"] = source_file or os.path.basename(file_path)
    df["_batch_id"] = batch_id

    # Simpan ke PostgreSQL
    engine = get_engine()

    df.to_sql(
        "odp_raw",
        engine,
        schema="bronze",
        if_exists="append",
        index=False
    )

    print(
        f"{len(df)} baris ODP wilayah {wilayah} "
        f"masuk ke bronze.odp_raw "
        f"(batch: {batch_id})"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--file",
        required=True,
        help="Path file CSV/XLSX ODP"
    )

    parser.add_argument(
        "--wilayah",
        required=True,
        help="Wilayah sumber file, contoh: BATU atau JATIM_BARAT"
    )

    parser.add_argument(
        "--sheet",
        default=None,
        help="Nama sheet Excel yang ingin dibaca, contoh: Sheet3"
    )

    parser.add_argument(
        "--batch-id",
        default=None
    )

    args = parser.parse_args()

    batch_id = args.batch_id or f"manual-{uuid.uuid4().hex[:8]}"

    load_odp_file(
        file_path=args.file,
        wilayah=args.wilayah.upper(),
        batch_id=batch_id,
        sheet_name=args.sheet
    )