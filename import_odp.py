import os
import glob
import pandas as pd
import psycopg2

# --- KONFIGURASI KONEKSI POSTGRESQL ---
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "tara_bot"
DB_USER = "postgres"
DB_PASS = "admin123"  # <--- Ganti sesuai password PostgreSQL laptopmu

# --- PATH FOLDER DATA ODP ---
ROOT_FOLDER_ODP = "data_odp"

def get_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )

def import_all_odp_to_postgres():
    print("🚀 [STEP 1] Memaknai & memindai seluruh file ODP dari folder 'data_odp'...")

    if not os.path.exists(ROOT_FOLDER_ODP):
        print(f"⚠️ Folder '{ROOT_FOLDER_ODP}' tidak ditemukan!")
        print("Pastikan kamu sudah merename folder ODP utama menjadi 'data_odp' di folder proyek!")
        return

    # Ambil semua file .csv dan .xlsx di semua sub-folder
    csv_files = glob.glob(os.path.join(ROOT_FOLDER_ODP, "**", "*.csv"), recursive=True)
    excel_files = glob.glob(os.path.join(ROOT_FOLDER_ODP, "**", "*.xlsx"), recursive=True)
    all_files = csv_files + excel_files

    print(f"📦 Ditemukan {len(all_files)} file pecahan ODP.")

    all_odp_records = []

    for idx, file_path in enumerate(all_files):
        try:
            if file_path.endswith('.csv'):
                try:
                    df = pd.read_csv(file_path, on_bad_lines='skip', low_memory=False)
                except Exception:
                    df = pd.read_csv(file_path, sep=';', on_bad_lines='skip', low_memory=False)
            else:
                df = pd.read_excel(file_path)

            # Rapikan nama kolom agar tidak sensitif spasi
            df.columns = df.columns.str.strip()

            for _, row in df.iterrows():
                try:
                    odp_name = str(row.get('ODP NAME', '')).strip()
                    lat = float(row.get('LATITUDE'))
                    lon = float(row.get('LONGITUDE'))

                    # Ambil port berdasarkan header CSV kamu (AVAI, USED, IS TOTAL)
                    avail_p = int(row.get('AVAI', 0)) if pd.notna(row.get('AVAI')) else 0
                    used_p = int(row.get('USED', 0)) if pd.notna(row.get('USED')) else 0
                    total_p = int(row.get('IS TOTAL', 8)) if pd.notna(row.get('IS TOTAL')) else (avail_p + used_p)

                    # Tentukan occupancy status sesuai Atribut Data ODP
                    if avail_p <= 0:
                        status = "MERAH (FULL)"
                    elif avail_p <= 2:
                        status = "ORANGE (HAMPIR FULL)"
                    else:
                        status = "HIJAU (AVAILABLE)"

                    if pd.notna(lat) and pd.notna(lon) and odp_name:
                        all_odp_records.append((odp_name, lat, lon, total_p, used_p, avail_p, status))

                except Exception:
                    continue  # Lewati baris yang corrup / koordinat kosong

        except Exception as e:
            print(f"⚠️ Gagal membaca {file_path}: {e}")

        if (idx + 1) % 10 == 0 or (idx + 1) == len(all_files):
            print(f"   ⏳ Berhasil memproses {idx + 1}/{len(all_files)} file...")

    print(f"\n📊 Total Baris ODP Valid Siap Impor: {len(all_odp_records)} baris.")

    # --- MASUKKAN BULK DATA KE POSTGRESQL ---
    try:
        conn = get_connection()
        cursor = conn.cursor()

        print("💾 Memasukkan data ke tabel 'odp_master' di database 'tara_bot'...")
        cursor.execute("TRUNCATE TABLE odp_master RESTART IDENTITY;")

        insert_query = '''
            INSERT INTO odp_master (
                odp_name, latitude, longitude, total_port, used_port, available_port, occupancy_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        '''

        cursor.executemany(insert_query, all_odp_records)
        conn.commit()

        # Buat Spatial Indexing agar Query Jarak Spasial (<250m) super cepat (<5ms)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_odp_coords ON odp_master(latitude, longitude);")
        conn.commit()

        print(f"\n✅ SUKSES BESAR! Total {len(all_odp_records)} data ODP dari seluruh sub-folder berhasil masuk ke PostgreSQL!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error simpan ke PostgreSQL: {e}")

if __name__ == "__main__":
    import_all_odp_to_postgres()