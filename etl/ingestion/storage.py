import os
import pandas as pd
from etl.common.db import get_engine

def deduplicate_records(records):
    """
    Deduplikasi ringan intra-batch HANYA untuk hasil dari scraping saat ini.
    Prioritas identifier:
    1. url_gmaps
    2. kombinasi: nama + alamat + latitude + longitude
    """
    seen = set()
    deduped = []
    
    for r in records:
        url = r.get("url_gmaps")
        if url and url.strip():
            identifier = url.strip()
        else:
            # Fallback ke kombinasi teks
            nama = str(r.get("nama") or "").strip().lower()
            alamat = str(r.get("alamat") or "").strip().lower()
            lat = str(r.get("latitude") or "").strip()
            lon = str(r.get("longitude") or "").strip()
            identifier = f"{nama}|{alamat}|{lat}|{lon}"
            
        if identifier not in seen:
            seen.add(identifier)
            deduped.append(r)
            
    return deduped

def save_to_bronze(records, wilayah, batch_id):
    """
    Simpan list of dict ke bronze.prospect_raw.
    Hanya metadata ingestion yang ditambahkan, data bisnis tidak diubah.
    """
    if not records:
        return 0
        
    records = deduplicate_records(records)
    
    df = pd.DataFrame(records)
    
    # Tambahkan kolom metadata ingestion (mengikuti schema Bronze existing)
    df["_wilayah_file"] = wilayah
    df["_source_file"] = "google_maps_scraper"
    df["_batch_id"] = batch_id
    
    # Ambil engine DB
    engine = get_engine()
    
    # Pastikan tipe datanya string semua untuk Bronze (kecuali null)
    for col in df.columns:
        # Convert non-null to string
        df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else None)
        # Ensure strings like "nan" or "None" are converted to actual None
        df[col] = df[col].replace(["nan", "None", "", "<NA>"], None)
        
    # Masukkan ke Bronze secara append
    df.to_sql("prospect_raw", engine, schema="bronze", if_exists="append", index=False)
    
    return len(df)
