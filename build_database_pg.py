import psycopg2
import pandas as pd
import os

# --- KONFIGURASI KONEKSI POSTGRESQL ---
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "tara_bot"  # <--- Sesuai dengan nama database kamu
DB_USER = "postgres"
DB_PASS = "admin123"  # <--- GANTI SESUAI PASSWORD POSTGRESQL LAPTOPMU!

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def init_postgresql_database():
    print("🚀 [STEP 1] Menghubungkan ke PostgreSQL ('tara_bot') & Membuat Tabel...")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Tabel Master ODP (odp_master)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odp_master (
                odp_id SERIAL PRIMARY KEY,
                odp_name VARCHAR(255),
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                total_port INT,
                used_port INT,
                available_port INT,
                occupancy_status VARCHAR(50)
            );
        ''')

        # 2. Tabel Terintegrasi (lead_candidates)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_candidates (
                lead_id SERIAL PRIMARY KEY,
                nama VARCHAR(255),
                nama_normalized VARCHAR(255),
                kategori VARCHAR(100),
                alamat TEXT,
                telepon VARCHAR(50),
                wilayah VARCHAR(100),
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                status_existing BOOLEAN, -- TRUE: CBASE (Eksis), FALSE: New Leads
                priority_source VARCHAR(50), -- 'SCRAPING' / 'VISIT_OLD'
                usage_score INT DEFAULT 0,
                is_ready_tara BOOLEAN DEFAULT TRUE
            );
        ''')

        conn.commit()
        print("✅ Tabel 'odp_master' dan 'lead_candidates' sukses dibuat di PostgreSQL 'tara_bot'!")

        # --- [STEP 2] IMPORT DATA HASIL MATCHING KEMARIN ---
        file_matching = "HASIL_MATCHING_LEADS_TARA.xlsx"
        if os.path.exists(file_matching):
            print(f"\n📥 [STEP 2] Mengimpor data dari '{file_matching}' ke database 'tara_bot'...")
            df = pd.read_excel(file_matching)

            cursor.execute("TRUNCATE TABLE lead_candidates RESTART IDENTITY;") # Reset data lama jika ada

            insert_query = '''
                INSERT INTO lead_candidates (
                    nama, nama_normalized, kategori, alamat, telepon, wilayah,
                    latitude, longitude, status_existing, priority_source, usage_score, is_ready_tara
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            '''

            records = []
            for _, row in df.iterrows():
                is_existing = True if "MATCH" in str(row.get('lead_status', '')) else False
                records.append((
                    row.get('nama'),
                    str(row.get('nama', '')).lower().strip(),
                    row.get('kategori'),
                    row.get('alamat'),
                    row.get('telepon_clean'),
                    row.get('wilayah'),
                    row.get('latitude'),
                    row.get('longitude'),
                    is_existing,
                    'SCRAPING',
                    0,
                    bool(row.get('is_ready_tara', True))
                ))

            cursor.executemany(insert_query, records)
            conn.commit()
            print(f"✅ Berhasil mengimpor {len(records)} baris data ke tabel 'lead_candidates' di PostgreSQL!")
        else:
            print(f"⚠️ File '{file_matching}' tidak ditemukan di folder proyek!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error Koneksi/Database: {e}")

if __name__ == "__main__":
    init_postgresql_database()