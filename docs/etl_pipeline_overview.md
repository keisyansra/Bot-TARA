# ETL Data Pipeline Overview

> Dokumen ini menjelaskan arsitektur, alur data, dan cara menjalankan seluruh ETL Pipeline pada project Bot TARA.
> Dokumentasi dibuat berdasarkan inspeksi kode aktual di repository.

---

## 1. Tujuan Pipeline

Pipeline ini mengolah tiga sumber data utama:

| Data | Deskripsi |
|---|---|
| **Prospect** | Data hasil scraping Google Maps per wilayah. Berisi nama bisnis, koordinat, alamat, telepon, dan rating. |
| **CBASE / Customer** | Data customer eksisting Telkom dari sistem internal. Berisi nipnas, nama perusahaan, dan witel. |
| **ODP** | Data Optical Distribution Point (ODP) jaringan fiber Telkom per wilayah. Berisi nama ODP, koordinat, dan jumlah port tersedia. |

Hasil akhir pipeline adalah tabel `gold.prospect_recommendation`: daftar prospek yang **belum menjadi pelanggan Telkom**, dilengkapi informasi ODP terdekat yang tersedia, siap dikonsumsi oleh API/Telegram Bot untuk kebutuhan prospecting lapangan.

---

## 2. Arsitektur Medallion

Pipeline menggunakan arsitektur **Medallion (Bronze → Silver → Gold)**:

```
Sumber Data (CSV / Excel)
          │
          ▼
┌─────────────────────┐
│       BRONZE        │
│  Raw Ingestion      │
│  Semua kolom TEXT   │
│  Tidak ada cleaning │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│       SILVER        │
│  Cleaning & Typing  │
│  Normalisasi Nama   │
│  Fuzzy Matching     │
│  Spatial Geometry   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│        GOLD         │
│  Business Logic     │
│  Recommendation     │
│  Spatial Enrichment │
└──────────┬──────────┘
           │
           ▼
    API / Telegram Bot
```

### Filosofi setiap layer

- **Bronze**: Menyimpan data mentah apa adanya. Semua kolom bertipe `TEXT` agar load tidak pernah gagal karena ketidakkonsistenan format sumber (koma sebagai desimal, newline, dll). Tidak ada transformasi apapun.
- **Silver**: Melakukan cleaning, typing, normalisasi, deduplication, validasi koordinat, pembuatan geometri PostGIS, dan fuzzy matching antara prospect dengan customer.
- **Gold**: Menerapkan kebijakan bisnis. Memfilter prospect yang sudah menjadi customer, menambahkan informasi ODP terdekat menggunakan spatial query PostGIS, dan menghasilkan snapshot terkini yang siap di-query realtime.

---

## 3. Data Sources dan Lineage

| Data Source | Sumber File | Bronze | Silver | Gold |
|---|---|---|---|---|
| **Prospect** | Excel hasil scraping Google Maps per wilayah | `bronze.prospect_raw` | `silver.prospect_clean` | `gold.prospect_recommendation` |
| **CBASE** | Excel export sistem internal Telkom (Jatim Barat) | `bronze.cbase_raw` | `silver.cbase_clean` | Tidak langsung masuk Gold (digunakan sebagai referensi matching) |
| **ODP** | CSV/Excel data ODP per wilayah | `bronze.odp_raw` | `silver.odp_clean` | Direferensikan dari `gold.prospect_recommendation` via `nearest_odp_id` |

### Detail data lineage

```
Prospect Excel per wilayah
    └─► bronze.prospect_raw
            └─► silver.prospect_clean
                    ├─► silver.prospect_customer_match  (hasil fuzzy matching vs CBASE)
                    └─► gold.prospect_recommendation    (hanya prospect bukan customer)

CBASE Excel (satu file utuh Jatim Barat)
    └─► bronze.cbase_raw
            └─► silver.cbase_clean
                    └─► silver.prospect_customer_match  (sebagai referensi customer)

ODP CSV/Excel per wilayah
    └─► bronze.odp_raw
            └─► silver.odp_clean
                    └─► gold.prospect_recommendation    (via nearest ODP spatial query)
```

---

## 4. Struktur Folder ETL

```
etl/
├── __init__.py
├── bronze/
│   ├── __init__.py
│   ├── column_maps.py          # Mapping nama kolom sumber → nama kolom bronze
│   ├── load_odp.py             # Loader ODP: CSV/Excel → bronze.odp_raw
│   ├── load_prospect.py        # Loader Prospect: Excel → bronze.prospect_raw
│   └── load_cbase.py           # Loader CBASE: Excel → bronze.cbase_raw
│
├── silver/
│   ├── __init__.py
│   ├── clean_odp.py            # Bronze → Silver: cleaning & upsert ODP
│   ├── clean_prospect.py       # Bronze → Silver: cleaning & upsert Prospect
│   ├── clean_cbase.py          # Bronze → Silver: filter, cleaning & upsert CBASE
│   └── match_prospect_customer.py  # Fuzzy matching Prospect vs CBASE
│
├── gold/
│   ├── __init__.py
│   ├── build_recommendation.py     # Silver → Gold: bangun tabel rekomendasi
│   └── enrich_nearest_odp.py       # Gold: enrichment ODP terdekat via PostGIS
│
└── common/
    ├── __init__.py
    ├── db.py                   # get_engine() — koneksi ke PostgreSQL
    ├── io.py                   # read_table() — baca CSV/Excel sebagai string
    └── text.py                 # normalize_name() — normalisasi nama bisnis
```

---

## 5. Cara Menjalankan Pipeline

Pipeline harus dijalankan **secara berurutan** karena setiap tahap bergantung pada output tahap sebelumnya.

> **Prasyarat**: Docker container database harus sudah berjalan.
> ```bash
> docker-compose up -d
> ```

### Urutan Eksekusi Lengkap

#### Tahap 1 — Load Bronze (lakukan per wilayah/file)

```bash
# Load data ODP (bisa CSV atau Excel, bisa pilih sheet)
python -m etl.bronze.load_odp --file "data/odp_batu.csv" --wilayah BATU
python -m etl.bronze.load_odp --file "data/odp_master.xlsx" --wilayah JATIM_BARAT --sheet "Sheet3"

# Load data Prospect per wilayah
python -m etl.bronze.load_prospect --file "data/scraping_batu.xlsx" --wilayah BATU

# Load data CBASE (satu file utuh)
python -m etl.bronze.load_cbase --file "data/cbase.xlsx"
```

#### Tahap 2 — Clean Silver

```bash
# Cleaning ODP
python -m etl.silver.clean_odp

# Cleaning Prospect
python -m etl.silver.clean_prospect

# Cleaning CBASE (otomatis filter Telkom JATIM BARAT)
python -m etl.silver.clean_cbase
```

#### Tahap 3 — Fuzzy Matching

```bash
# Match prospect vs customer CBASE
python -m etl.silver.match_prospect_customer
```

#### Tahap 4 — Build Gold

```bash
# Bangun tabel rekomendasi Gold (filter prospect bukan customer)
python -m etl.gold.build_recommendation

# Enrich dengan ODP terdekat menggunakan PostGIS
python -m etl.gold.enrich_nearest_odp
```

---

## 6. Infrastruktur Database

Database menggunakan **PostgreSQL 16 dengan ekstensi PostGIS 3.4**, dijalankan via Docker:

```yaml
# docker-compose.yml
image: postgis/postgis:16-3.4
container_name: bot_telkom_db
```

Koneksi database dikonfigurasi melalui environment variable `DATABASE_URL` di file `.env`.
Helper `get_engine()` tersedia di [etl/common/db.py](../etl/common/db.py).

Schema database (DDL lengkap) tersedia di: [db/schema_bronze_silver_gold.sql](../db/schema_bronze_silver_gold.sql)

---

## 7. Final Output

Tabel Gold utama yang menjadi output pipeline:

**`gold.prospect_recommendation`**

Berisi snapshot terkini setiap prospect yang dianggap **belum menjadi pelanggan Telkom**, dilengkapi:
- Informasi dasar prospect (nama, alamat, koordinat, wilayah)
- Status dan skor customer matching
- ODP terdekat yang memiliki port tersedia
- Badge status rekomendasi (`siap_pasang` / `di_luar_radius` / `odp_tidak_ditemukan`)

Tabel ini yang langsung di-query oleh FastAPI / Telegram Bot.

> Tabel ini **di-upsert** tiap batch, bukan accumulate history. Setiap kali pipeline dijalankan ulang, data diperbarui ke kondisi terkini.

---

## 8. Dependency Python

Dependensi utama yang digunakan oleh ETL Pipeline (lihat `requirements.txt`):

| Library | Kegunaan |
|---|---|
| `pandas` | Transformasi dan pembersihan data |
| `sqlalchemy` | Koneksi dan eksekusi SQL ke PostgreSQL |
| `psycopg2-binary` | Driver PostgreSQL untuk SQLAlchemy |
| `rapidfuzz` | Fuzzy string matching (Prospect vs CBASE) |
| `geoalchemy2` | Integrasi SQLAlchemy dengan tipe data PostGIS |
| `python-dotenv` | Load konfigurasi dari file `.env` |

---

*Dokumen ini dibuat berdasarkan kode aktual di repository pada tanggal pembuatan. Angka-angka data (jumlah baris, dll.) bersifat ilustratif dan akan berubah sesuai data terkini.*
