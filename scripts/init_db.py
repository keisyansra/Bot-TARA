"""
Jalanin DDL db/schema_bronze_silver_gold.sql ke database yang udah
di-spin-up lewat docker-compose. Jalanin sekali di awal, atau tiap
kali ada perubahan schema.

Usage:
    python scripts/init_db.py
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "schema_bronze_silver_gold.sql")


def main():
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        ddl = f.read()

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(ddl)
        print("Schema berhasil dijalankan: bronze, silver, gold ke-create.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()