# Gold Layer Documentation

> Dokumentasi ini menjelaskan seluruh proses di layer Gold: pembentukan data rekomendasi, kebijakan customer matching, dan spatial enrichment ODP.
> Berdasarkan inspeksi kode aktual di `etl/gold/`.

---

## Gambaran Umum Gold

Gold adalah layer **business-ready data** yang menjadi sumber utama untuk API dan Telegram Bot. Data di layer ini:

- Hanya berisi prospect yang **belum menjadi pelanggan Telkom**
- Dilengkapi informasi ODP terdekat yang memiliki port tersedia
- Menggunakan snapshot model (di-upsert tiap batch, bukan accumulate history)
- Siap di-query secara realtime

Layer Gold terdiri dari **dua proses terpisah** yang dijalankan secara berurutan:

| Proses | File | Fungsi |
|---|---|---|
| Build Recommendation | `build_recommendation.py` | Filter prospect bukan customer → masukkan ke Gold |
| Enrich Nearest ODP | `enrich_nearest_odp.py` | Tambahkan info ODP terdekat via PostGIS |

---

## A. Build Recommendation

**File**: [`etl/gold/build_recommendation.py`](../etl/gold/build_recommendation.py)

### A.1. Tujuan

Membentuk tabel `gold.prospect_recommendation` yang berisi prospect yang **dianggap belum menjadi pelanggan Telkom**, berdasarkan:
1. Hasil fuzzy matching dari `silver.prospect_customer_match`
2. Flag `is_telkom_entity` dari `silver.prospect_clean`

### A.2. Proses

Fungsi utama: `load_candidates(engine)` dan `upsert_gold(df, engine, batch_id)`

**Query filter kandidat:**

```sql
SELECT
    p.prospect_id, p.nama, p.alamat, p.latitude, p.longitude,
    p.url_gmaps, p.wilayah,
    m.match_status AS customer_match_status,
    m.match_score  AS customer_match_score
FROM silver.prospect_clean p
LEFT JOIN silver.prospect_customer_match m ON m.prospect_id = p.prospect_id
WHERE p.is_telkom_entity = false
  AND (m.match_status IS NULL OR m.match_status NOT IN ('MATCH_CONFIDENT', 'MATCH_POSSIBLE'))
```

**Prospect yang DIKELUARKAN dari Gold:**
- `is_telkom_entity = true` — entitas Telkom sendiri (contoh: "PT Telkom Indonesia", "Telkom Kandatel")
- `match_status = 'MATCH_CONFIDENT'` — dianggap pasti sudah menjadi customer
- `match_status = 'MATCH_POSSIBLE'` — dianggap kemungkinan besar sudah customer

**Prospect yang MASUK ke Gold** (semua selain yang dikeluarkan di atas):
- `match_status IS NULL` — belum pernah di-match
- `MATCH_CONFIDENT_SINGLE_TOKEN` — match satu kata, perlu verifikasi
- `MATCH_POSSIBLE_SINGLE_TOKEN` — match lemah
- `MATCH_REJECTED_LENGTH` — match ditolak karena panjang nama
- `NO_MATCH` — tidak ada kemiripan
- `SKIPPED_SHORT_NAME` — terlalu pendek untuk di-match

### A.3. Strategi Upsert

Script menggunakan staging table `gold._stg_prospect_recommendation` untuk performa bulk insert, diikuti `INSERT ... ON CONFLICT (prospect_id) DO UPDATE`. Tabel Gold juga **membersihkan baris lama** yang tidak ada di batch saat ini:

```sql
DELETE FROM gold.prospect_recommendation
WHERE prospect_id NOT IN (SELECT prospect_id FROM gold._stg_prospect_recommendation);
```

Ini memastikan jika status matching berubah (misal prospect yang sebelumnya `NO_MATCH` sekarang menjadi `MATCH_CONFIDENT` setelah re-run), prospect tersebut otomatis dikeluarkan dari Gold.

### A.4. Kolom yang Diisi oleh `build_recommendation.py`

| Kolom | Tipe | Deskripsi |
|---|---|---|
| `prospect_id` | `BIGINT` PRIMARY KEY | FK ke `silver.prospect_clean` |
| `nama` | `TEXT` NOT NULL | Nama bisnis prospect |
| `alamat` | `TEXT` | Alamat prospect |
| `latitude` | `NUMERIC` NOT NULL | Koordinat lintang |
| `longitude` | `NUMERIC` NOT NULL | Koordinat bujur |
| `geom` | `GEOGRAPHY(POINT,4326)` NOT NULL | Geometri PostGIS (dibuat via `ST_SetSRID`) |
| `wilayah` | `TEXT` NOT NULL | Wilayah prospect |
| `url_gmaps` | `TEXT` | URL Google Maps |
| `customer_match_status` | `TEXT` | Status matching dari Silver |
| `customer_match_score` | `NUMERIC` | Skor matching dari Silver |
| `batch_id` | `TEXT` NOT NULL | ID batch Gold |
| `calculated_at` | `TIMESTAMPTZ` | Timestamp build (auto-update tiap upsert) |

**Kolom yang belum diisi oleh step ini** (diisi oleh `enrich_nearest_odp.py`):

| Kolom | Tipe | Deskripsi |
|---|---|---|
| `nearest_odp_id` | `BIGINT` | FK ke `silver.odp_clean(id_odp)` |
| `nearest_odp_name` | `TEXT` | Nama ODP terdekat |
| `odp_distance_m` | `NUMERIC` | Jarak ke ODP terdekat (meter) |
| `odp_available_port` | `INTEGER` | Port tersedia di ODP tersebut |
| `badge_status` | `TEXT` | Status rekomendasi |

### A.5. Format Batch ID

```
gold-{8 karakter hex acak}
```
Contoh: `gold-a1b2c3d4`

### A.6. Cara Menjalankan

```bash
python -m etl.gold.build_recommendation
```

### A.7. Verification Query

```sql
-- Total prospect di Gold
SELECT COUNT(*) FROM gold.prospect_recommendation;

-- Pastikan tidak ada entitas Telkom di Gold
SELECT COUNT(*) FROM gold.prospect_recommendation gr
JOIN silver.prospect_clean sc ON sc.prospect_id = gr.prospect_id
WHERE sc.is_telkom_entity = true;
-- Hasil HARUS 0

-- Pastikan tidak ada MATCH_CONFIDENT/POSSIBLE di Gold
SELECT COUNT(*) FROM gold.prospect_recommendation
WHERE customer_match_status IN ('MATCH_CONFIDENT', 'MATCH_POSSIBLE');
-- Hasil HARUS 0

-- Distribusi customer_match_status yang ada di Gold
SELECT customer_match_status, COUNT(*)
FROM gold.prospect_recommendation
GROUP BY customer_match_status
ORDER BY customer_match_status;
```

---

## B. Kebijakan Customer Matching di Gold

Tabel lengkap keputusan per status:

| Match Status | Masuk Gold? | Alasan |
|---|---|---|
| `MATCH_CONFIDENT` | ❌ Tidak | Dianggap sudah customer — dikeluarkan dari prospecting |
| `MATCH_POSSIBLE` | ❌ Tidak | Kemungkinan besar sudah customer |
| `MATCH_CONFIDENT_SINGLE_TOKEN` | ✅ Ya | Skor tinggi tapi match hanya 1 kata, perlu verifikasi manual lapangan |
| `MATCH_POSSIBLE_SINGLE_TOKEN` | ✅ Ya | Match lemah, potensi false positive tinggi |
| `MATCH_REJECTED_LENGTH` | ✅ Ya | Match ditolak oleh guard panjang nama, dianggap belum berlangganan |
| `NO_MATCH` | ✅ Ya | Tidak ditemukan kemiripan cukup dengan customer manapun |
| `SKIPPED_SHORT_NAME` | ✅ Ya | Nama terlalu pendek untuk di-match, tidak ada data cukup |
| `NULL` (belum di-match) | ✅ Ya | Matching belum pernah dijalankan untuk prospect ini |

> **Filosofi yang tertulis di kode**: "Salah exclude prospek asli (kehilangan peluang sales) lebih mahal daripada salah include orang yang sudah jadi pelanggan (cuma rugi waktu verifikasi pas sales kontak)."

---

## C. Nearest ODP Enrichment

**File**: [`etl/gold/enrich_nearest_odp.py`](../etl/gold/enrich_nearest_odp.py)

### C.1. Tujuan

Mengisi kolom ODP pada `gold.prospect_recommendation` untuk setiap prospect menggunakan **spatial query PostGIS**. Tujuannya adalah memberikan informasi apakah prospect dapat dipasang layanan Telkom berdasarkan ketersediaan ODP terdekat.

### C.2. Aturan Bisnis

```python
MAX_RADIUS_M = 250  # ditetapkan oleh mentor, TIDAK boleh diubah
```

- Hanya ODP dengan `available_port > 0` yang boleh dipilih sebagai nearest ODP.
- ODP dengan `available_port = 0` **diabaikan** meskipun lebih dekat.

### C.3. Proses Enrichment

Fungsi utama: `enrich(engine, batch_id)`

Script menjalankan **empat UPDATE** dalam satu transaksi atomik:

#### Step 0 — Reset

Sebelum memulai perhitungan baru, seluruh kolom ODP di-reset ke NULL agar hasil lama tidak mempengaruhi perhitungan:

```sql
UPDATE gold.prospect_recommendation
SET nearest_odp_id = NULL, nearest_odp_name = NULL,
    odp_distance_m = NULL, odp_available_port = NULL, badge_status = NULL;
```

#### Step 1 — `siap_pasang`

Mencari ODP dengan `available_port > 0` dalam radius 250 meter, menggunakan `ST_DWithin` dan `CROSS JOIN LATERAL` dengan `ORDER BY pr.geom <-> oc.geom LIMIT 1` (nearest-neighbor search yang memanfaatkan GIST index):

```sql
UPDATE gold.prospect_recommendation AS p
SET ... badge_status = 'siap_pasang', ...
FROM (
    SELECT DISTINCT ON (pr.prospect_id)
        pr.prospect_id, o.id_odp, o.odp_name, o.available_port,
        ST_Distance(pr.geom, o.geom) AS distance_m
    FROM gold.prospect_recommendation pr
    CROSS JOIN LATERAL (
        SELECT oc.id_odp, oc.odp_name, oc.available_port, oc.geom
        FROM silver.odp_clean oc
        WHERE oc.available_port > 0
          AND ST_DWithin(pr.geom, oc.geom, 250)
        ORDER BY pr.geom <-> oc.geom
        LIMIT 1
    ) o
) sub
WHERE p.prospect_id = sub.prospect_id;
```

#### Step 2 — `di_luar_radius`

Untuk prospect yang **belum mendapat badge** setelah Step 1, cari ODP terdekat dengan `available_port > 0` tanpa batas radius (gunakan pola yang sama tanpa `ST_DWithin`):

```sql
-- Sama seperti Step 1 tapi tanpa WHERE ST_DWithin(...)
-- dan hanya untuk prospect dengan badge_status IS NULL atau != 'siap_pasang'
badge_status = 'di_luar_radius'
```

#### Step 3 — `odp_tidak_ditemukan`

Prospect yang masih belum punya badge setelah Step 1 dan 2 (tidak ada ODP `available_port > 0` sama sekali):

```sql
UPDATE gold.prospect_recommendation
SET nearest_odp_id = NULL, nearest_odp_name = NULL, ...
    badge_status = 'odp_tidak_ditemukan'
WHERE badge_status IS NULL
   OR badge_status NOT IN ('siap_pasang', 'di_luar_radius');
```

### C.4. Tiga Badge Status

```
Untuk setiap prospect di Gold:
         │
         ▼
Cari ODP dengan available_port > 0
         │
         ├── Ada dalam jarak ≤ 250 m
         │            │
         │            ▼
         │        siap_pasang
         │        (ODP tersedia, bisa langsung pasang)
         │
         ├── Ada, tapi jarak > 250 m
         │            │
         │            ▼
         │        di_luar_radius
         │        (ODP tersedia, tapi terlalu jauh untuk pasang langsung)
         │
         └── Tidak ada ODP dengan port > 0 sama sekali
                      │
                      ▼
               odp_tidak_ditemukan
               (nearest_odp_id = NULL)
```

**Deskripsi detail setiap badge:**

| Badge | `nearest_odp_id` | `odp_distance_m` | `available_port` | Interpretasi |
|---|---|---|---|---|
| `siap_pasang` | Diisi | ≤ 250.0 | > 0 | Prospect dapat langsung direkomendasikan, ODP dalam jangkauan |
| `di_luar_radius` | Diisi | > 250.0 | > 0 | ODP terdekat ada tapi terlalu jauh; informasi tetap ditampilkan untuk referensi |
| `odp_tidak_ditemukan` | NULL | NULL | NULL | Tidak ada ODP dengan port tersedia di database |

### C.5. Mengapa Spatial Query di SQL, Bukan Python Loop

Dataset: ~2.452 prospect × ~75.034 ODP (dari database aktual saat ini).

Pendekatan loop Python satu per satu akan menghasilkan ~2.452 query SQL terpisah, masing-masing melakukan full scan atau index lookup individual. Pendekatan SQL `CROSS JOIN LATERAL` dengan GIST index menyelesaikan seluruh matching dalam **satu query** yang dieksekusi di sisi database PostgreSQL, memanfaatkan:

- **GIST index** pada `silver.odp_clean(geom)` untuk spatial lookup cepat
- **Partial index** `WHERE available_port > 0` untuk langsung skip ODP penuh
- **Nearest-neighbor operator `<->`** yang memanfaatkan GIST index order
- **`ST_DWithin`** yang sangat dioptimasi untuk filter radius dengan GIST

### C.6. Format Batch ID

```
gold-odp-{8 karakter hex acak}
```
Contoh: `gold-odp-de9bcb3c`

### C.7. Cara Menjalankan

```bash
python -m etl.gold.enrich_nearest_odp
```

### C.8. Verification Query

```sql
-- 1. Breakdown badge_status
SELECT badge_status, COUNT(*)
FROM gold.prospect_recommendation
GROUP BY badge_status
ORDER BY badge_status;

-- 2. Validasi siap_pasang — HARUS 0
SELECT COUNT(*) AS invalid_siap_pasang
FROM gold.prospect_recommendation
WHERE badge_status = 'siap_pasang'
  AND (
      odp_distance_m > 250
      OR odp_available_port <= 0
      OR nearest_odp_id IS NULL
  );

-- 3. Validasi di_luar_radius — HARUS 0
SELECT COUNT(*) AS invalid_di_luar_radius
FROM gold.prospect_recommendation
WHERE badge_status = 'di_luar_radius'
  AND (
      odp_distance_m <= 250
      OR odp_available_port <= 0
      OR nearest_odp_id IS NULL
  );

-- 4. Contoh hasil per badge
SELECT
    nama, wilayah, nearest_odp_name,
    ROUND(odp_distance_m, 2) AS distance_m,
    odp_available_port, badge_status
FROM gold.prospect_recommendation
ORDER BY badge_status, odp_distance_m NULLS LAST
LIMIT 20;
```

**Hasil verifikasi pada snapshot saat dokumentasi dibuat** *(angka dapat berubah ketika source data diperbarui)*:

| Metrik | Nilai |
|---|---|
| Total Gold prospect | 2.452 |
| `siap_pasang` | 2.266 |
| `di_luar_radius` | 186 |
| `odp_tidak_ditemukan` | 0 |
| Invalid `siap_pasang` (harus 0) | 0 ✅ |
| Invalid `di_luar_radius` (harus 0) | 0 ✅ |

---

## D. PostGIS Performance

### Index yang Digunakan

| Index | Tabel | Kolom | Tipe | Kegunaan |
|---|---|---|---|---|
| `idx_gold_prospect_geom` | `gold.prospect_recommendation` | `geom` | GIST | Spatial query Gold |
| `idx_gold_prospect_wilayah` | `gold.prospect_recommendation` | `wilayah` | B-tree | Filter per wilayah |
| `idx_odp_clean_geom` | `silver.odp_clean` | `geom` | GIST | Spatial lookup ODP |
| `idx_odp_clean_available` | `silver.odp_clean` | `available_port` | Partial (`WHERE > 0`) | Filter ODP dengan port tersedia |

### Tipe Data Geometri

Kedua tabel menggunakan tipe `GEOGRAPHY(POINT, 4326)`:
- **SRID 4326** = WGS84 (koordinat GPS standar)
- **geography vs geometry**: Tipe `geography` menghitung jarak dalam **meter** di permukaan bumi (elipsoid), bukan jarak planar. Ini penting untuk akurasi pencarian ODP dalam radius 250 meter.
- `ST_Distance(geom_a, geom_b)` dengan tipe geography → hasil dalam **meter**
- `ST_DWithin(geom_a, geom_b, 250)` dengan tipe geography → radius dalam **meter**

---

## E. Final Data Flow Diagram

```
Prospect Raw (Excel scraping)
        │
        ▼
bronze.prospect_raw
        │
        ▼
silver.prospect_clean
(nama_normalized, geom, is_telkom_entity)
        │
        ├───────────────────────────────────┐
        │                                   │
        │ match_prospect_customer.py         │
        ▼                                   │
silver.prospect_customer_match              │
(match_status, match_score)                 │
        │                                   ▼
        │                         silver.odp_clean
        │                         (available_port, geom)
        │                                   │
        └──────────────┬────────────────────┘
                       │
                       │ build_recommendation.py
                       ▼
           gold.prospect_recommendation
           (filter bukan customer, bukan Telkom entity)
                       │
                       │ enrich_nearest_odp.py
                       ▼
           gold.prospect_recommendation
           (+ nearest_odp_id, odp_distance_m,
              odp_available_port, badge_status)
                       │
              ┌────────┴─────────┐
              │                  │
              ▼                  ▼
      customer_match_status   badge_status
      customer_match_score    nearest_odp_name
                              odp_distance_m
                              odp_available_port
                              siap_pasang /
                              di_luar_radius /
                              odp_tidak_ditemukan
                       │
                       ▼
              API / Telegram Bot
```

---

## F. Tabel `gold.batch_log` — *(Planned, belum diimplementasikan)*

DDL di `db/schema_bronze_silver_gold.sql` mendefinisikan tabel `gold.batch_log`:

```sql
CREATE TABLE IF NOT EXISTS gold.batch_log (
    batch_id     TEXT PRIMARY KEY,
    triggered_by TEXT NOT NULL,  -- 'odp_upload' | 'cbase_upload' | 'scraping_cron'
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at  TIMESTAMPTZ,
    row_count    INTEGER,
    status       TEXT CHECK (status IN ('running', 'success', 'failed')) DEFAULT 'running',
    notes        TEXT
);
```

**Status**: Tabel ini **belum diisi** oleh script ETL manapun saat ini. Merupakan rencana untuk audit history batch di masa mendatang. Informasi batch saat ini hanya tersimpan di kolom `batch_id` pada masing-masing tabel Gold.

---

*Dokumen ini dibuat berdasarkan kode aktual di repository. Angka data bersifat indikatif dan merupakan snapshot pada saat dokumentasi dibuat — akan berubah ketika source data diperbarui.*
