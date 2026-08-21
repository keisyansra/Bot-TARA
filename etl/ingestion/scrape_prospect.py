import argparse
import datetime
import uuid
import sys
from etl.ingestion.browser import scrape_google_maps
from etl.ingestion.storage import save_to_bronze

REGIONS = [
    "Batu",
    "Blitar",
    "Bojonegoro",
    "Kediri",
    "Madiun",
    "Malang",
    "Nganjuk",
    "Ngawi",
    "Ponorogo",
    "Tuban",
    "Tulungagung",
]

CATEGORIES = [
    "PT",
    "CV",
    "UD",
]

def main():
    parser = argparse.ArgumentParser(description="Google Maps Prospect Scraper")
    parser.add_argument("--wilayah", type=str, help="Filter pencarian untuk satu wilayah saja")
    parser.add_argument("--kategori", type=str, help="Filter pencarian untuk satu kategori saja")
    args = parser.parse_args()

    # Tentukan target yang akan discrape
    target_regions = [args.wilayah] if args.wilayah else REGIONS
    target_categories = [args.kategori] if args.kategori else CATEGORIES

    # Buat Batch ID unik untuk satu kali execution
    # Format: scrape-YYYYMMDD-xxxx
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")
    hex_str = uuid.uuid4().hex[:4]
    batch_id = f"scrape-{date_str}-{hex_str}"

    print("========================================")
    print("[START] Google Maps Prospect Scraper")
    print(f"[START] Batch ID: {batch_id}")
    print("========================================")

    summary = {r: 0 for r in target_regions}
    total_records = 0

    for region in target_regions:
        for cat in target_categories:
            print(f"[START] {region} - {cat}")
            try:
                # 1. Scrape data dari Google Maps
                records = scrape_google_maps(region, cat)
                
                # 2. Save ke Bronze
                if records:
                    saved_count = save_to_bronze(records, region, batch_id)
                    print(f"[OK] {region} - {cat} - {saved_count} records")
                    summary[region] += saved_count
                    total_records += saved_count
                else:
                    print(f"[OK] {region} - {cat} - 0 records (Tidak ada hasil atau timeout)")
                    
            except Exception as e:
                print(f"[ERROR] {region} - {cat} - Error: {str(e)}")
                # Tetap lanjut ke kombinasi berikutnya jika error

    # Print Summary
    print("========================================")
    print("SCRAPING SUMMARY")
    print("========================================")
    print(f"Batch ID      : {batch_id}")
    print(f"Total region  : {len(target_regions)}")
    print(f"Total category: {len(target_categories)}")
    print(f"Total records : {total_records}")
    print("")
    for region, count in summary.items():
        print(f"{region.ljust(15)}: {count}")
    print("========================================")

if __name__ == "__main__":
    main()
