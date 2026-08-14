# Silver Layer Documentation

> Dokumentasi ini menjelaskan seluruh proses di layer Silver: cleaning, normalisasi, validasi, dan matching.
> Berdasarkan inspeksi kode aktual di `etl/silver/` dan `etl/common/`.

---

## Gambaran Umum Silver

Silver adalah layer **cleaning dan standardization**. Data dari Bronze diproses menjadi:
- Tipe data yang benar (NUMERIC, BOOLEAN, TIMESTAMPTZ, dll.)
- Nilai yang tervalidasi (koordinat dalam batas Jawa Timur)
- Geometri PostGIS yang dapat digunakan untuk spatial query
- Nama yang dinormalisasi untuk kebutuhan fuzzy matching
- Duplikasi yang sudah dihapus

Semua tabel Silver menggunakan strategi **UPSERT** (`ON CONFLICT DO UPDATE`) sehingga `id` / primary key stabil antar-batch — penting karena Gold memiliki foreign key ke Silver.

---

## 1. `silver.odp_clean`

### 1.1. Input

Tabel sumber: `bronze.odp_raw`

File ETL: [`etl/silver/clean_odp.py`](../etl/silver/clean_odp.py)

### 1.2. Transformasi

Fungsi utama: `clean_odp(df)`

| Langkah | Detail |
|---|---|
| **Type casting koordinat** | `latitude`, `longitude` → `NUMERIC` via `pd.to_numeric(errors='coerce')` |
| **Type casting port** | `avai`, `used`, `rsv`, `rsk`, `is_total` → `NUMERIC` via `pd.to_numeric(errors='coerce')` |
| **Type casting ID** | `id_odp` → `NUMERIC` via `pd.to_numeric(errors='coerce')` |
| **Drop baris kritis** | Baris di-drop jika `id_odp`, `latitude`, `longitude`, atau `avai` gagal di-parse (NULL setelah coerce) |
| **Validasi koordinat** | Koordinat harus dalam batas wajar Jawa Timur: lat ∈ [-9.5, -6.5], lon ∈ [110.5, 114.5] |
| **Penentuan wilayah** | Kolom `wilayah_file` diambil dari kolom `telda` per baris. Baris tanpa nilai `telda` diberi label `"TIDAK_DIKETAHUI"` |
| **Deduplication** | Duplikat `id_odp` dihapus; baris dengan `_loaded_at` paling baru dipertahankan |
| **Rename kolom** | `avai` → `available_port`, `used` → `used_port`, `rsv` → `rsv_port`, `rsk` → `rsk_port`, `is_total` → `total_port`, `occ_2` → `occupancy_status`, `telkom_witel` → `witel` |
| **Geometri PostGIS** | Kolom `geom` dibentuk di SQL via `ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography` saat upsert |

> **Catatan**: Penggunaan `telda` (bukan `_wilayah_file`) untuk kolom `wilayah_file` di Silver disengaja. Komentar di kode menjelaskan bahwa `_wilayah_file` adalah label lineage yang bisa bersifat blanket jika file di-load sebagai satu gabungan, sedangkan `telda` mencerminkan wilayah sebenarnya per baris.

### 1.3. Output — `silver.odp_clean`

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id_odp` | `BIGINT` PRIMARY KEY | ID ODP dari sistem Telkom |
| `odp_name` | `TEXT` NOT NULL | Nama ODP |
| `latitude` | `NUMERIC` NOT NULL | Koordinat lintang |
| `longitude` | `NUMERIC` NOT NULL | Koordinat bujur |
| `geom` | `GEOGRAPHY(POINT,4326)` NOT NULL | Geometri PostGIS |
| `available_port` | `INTEGER` NOT NULL | Jumlah port tersedia |
| `used_port` | `INTEGER` | Jumlah port terpakai |
| `rsv_port` | `INTEGER` | Port reserved |
| `rsk_port` | `INTEGER` | Port rusak |
| `total_port` | `INTEGER` | Total port |
| `occupancy_status` | `TEXT` | Status occupancy (dari `OCC 2`) |
| `witel` | `TEXT` | Wilayah Telkom |
| `kabupaten_kota` | `TEXT` | Lokasi administratif |
| `provinsi` | `TEXT` | Provinsi |
| `wilayah_file` | `TEXT` NOT NULL | Wilayah per baris (dari kolom `telda`) |
| `tgl_golive` | `DATE` | Tanggal go-live ODP |
| `update_date` | `TIMESTAMPTZ` | Tanggal update data |
| `batch_id` | `TEXT` NOT NULL | ID batch ETL |
| `cleaned_at` | `TIMESTAMPTZ` NOT NULL | Timestamp cleaning |

**Index yang ada:**
- `idx_odp_clean_geom` — GIST index pada kolom `geom` (untuk spatial query)
- `idx_odp_clean_available` — Partial index `WHERE available_port > 0` (untuk filter port tersedia)

### 1.4. Cara Menjalankan

```bash
python -m etl.silver.clean_odp
```

### 1.5. Verification Query

```sql
-- Jumlah total ODP clean
SELECT COUNT(*) FROM silver.odp_clean;

-- Distribusi per wilayah
SELECT wilayah_file, COUNT(*) FROM silver.odp_clean GROUP BY wilayah_file ORDER BY wilayah_file;

-- ODP dengan port tersedia
SELECT COUNT(*) FROM silver.odp_clean WHERE available_port > 0;

-- Cek ada tidak koordinat di luar Jatim (seharusnya 0)
SELECT COUNT(*) FROM silver.odp_clean
WHERE latitude NOT BETWEEN -9.5 AND -6.5
   OR longitude NOT BETWEEN 110.5 AND 114.5;
```

---

## 2. `silver.prospect_clean`

### 2.1. Input

Tabel sumber: `bronze.prospect_raw`

File ETL: [`etl/silver/clean_prospect.py`](../etl/silver/clean_prospect.py)

### 2.2. Transformasi

Fungsi utama: `clean_prospect(df)`

| Langkah | Detail |
|---|---|
| **Normalisasi nama** | Kolom `nama_normalized` dibuat menggunakan fungsi `normalize_name()` dari `etl.common.text` |
| **Cleaning alamat/telepon** | Strip karakter newline (`\r\n`) dan spasi leading/trailing |
| **Parsing rating** | Koma desimal diganti titik (`3,4` → `3.4`), lalu cast ke NUMERIC |
| **Parsing koordinat** | `latitude`, `longitude` → NUMERIC via `pd.to_numeric(errors='coerce')` |
| **Drop baris kritis** | Baris di-drop jika `latitude` atau `longitude` NULL setelah parsing, atau `nama_normalized` kosong |
| **Validasi koordinat** | Koordinat harus dalam batas Jawa Timur: lat ∈ [-9.5, -6.5], lon ∈ [110.5, 114.5] |
| **Penentuan wilayah** | Kolom `wilayah` diambil dari `_wilayah_file` (label dari CLI saat Bronze load) |
| **Flag entitas Telkom** | `is_telkom_entity = true` jika nama mengandung kata "telkom" (case-insensitive) **atau** kategori mengandung "telekomunikasi" |
| **Deduplication** | Duplikat kombinasi `(nama_normalized, wilayah)` dihapus; baris dengan `_loaded_at` paling baru dipertahankan |
| **Geometri PostGIS** | Kolom `geom` dibentuk di SQL via `ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography` |

### 2.3. Output — `silver.prospect_clean`

| Kolom | Tipe | Keterangan |
|---|---|---|
| `prospect_id` | `BIGINT` PRIMARY KEY | Auto-generated (BIGSERIAL) |
| `nama` | `TEXT` NOT NULL | Nama asli dari scraping |
| `nama_normalized` | `TEXT` NOT NULL | Nama setelah normalisasi (untuk fuzzy matching) |
| `kategori` | `TEXT` | Kategori Google Maps |
| `alamat` | `TEXT` | Alamat |
| `telepon` | `TEXT` | Nomor telepon |
| `rating` | `NUMERIC` | Rating Google Maps |
| `latitude` | `NUMERIC` NOT NULL | Koordinat lintang |
| `longitude` | `NUMERIC` NOT NULL | Koordinat bujur |
| `geom` | `GEOGRAPHY(POINT,4326)` NOT NULL | Geometri PostGIS |
| `url_gmaps` | `TEXT` | URL Google Maps |
| `wilayah` | `TEXT` NOT NULL | Wilayah (dari `_wilayah_file` Bronze) |
| `is_telkom_entity` | `BOOLEAN` NOT NULL | Flag entitas Telkom sendiri |
| `batch_id` | `TEXT` NOT NULL | ID batch ETL |
| `cleaned_at` | `TIMESTAMPTZ` NOT NULL | Timestamp cleaning |

**Unique constraint**: `(nama_normalized, wilayah)` — digunakan sebagai natural key untuk UPSERT.

**Index yang ada:**
- `prospect_clean_pkey` — PRIMARY KEY pada `prospect_id`
- `idx_prospect_clean_geom` — GIST index pada `geom`
- `idx_prospect_clean_name_norm` — B-tree index pada `nama_normalized`

### 2.4. Cara Menjalankan

```bash
python -m etl.silver.clean_prospect
```

### 2.5. Verification Query

```sql
-- Total prospect
SELECT COUNT(*) FROM silver.prospect_clean;

-- Distribusi per wilayah
SELECT wilayah, COUNT(*) FROM silver.prospect_clean GROUP BY wilayah ORDER BY wilayah;

-- Entitas Telkom sendiri
SELECT is_telkom_entity, COUNT(*) FROM silver.prospect_clean GROUP BY is_telkom_entity;

-- Cek ada tidak koordinat di luar Jatim
SELECT COUNT(*) FROM silver.prospect_clean
WHERE latitude NOT BETWEEN -9.5 AND -6.5
   OR longitude NOT BETWEEN 110.5 AND 114.5;
```

---

## 3. `silver.cbase_clean`

### 3.1. Input

Tabel sumber: `bronze.cbase_raw`

File ETL: [`etl/silver/clean_cbase.py`](../etl/silver/clean_cbase.py)

### 3.2. Transformasi

Fungsi utama: `clean_cbase(df)`

| Langkah | Detail |
|---|---|
| **Filter wilayah** | Hanya baris dengan `witel_ho` = `"TELKOM JATIM BARAT"` yang diproses (perbandingan case-insensitive setelah strip) |
| **Cleaning nipnas** | Strip whitespace; float/scientific notation dikonversi ke integer string (misal: `3001000563.0` → `"3001000563"`) |
| **Cleaning standard_name** | Strip whitespace; nilai `"nan"`, `"none"`, atau string kosong dianggap NULL |
| **Drop nipnas kosong** | Baris dengan `nipnas` kosong/null dihapus |
| **Drop standard_name kosong** | Baris dengan `standard_name` kosong/null dihapus |
| **Normalisasi nama** | `nama_normalized` dibuat menggunakan `normalize_name()` dari `etl.common.text` |
| **Deduplication** | Duplikat `nipnas` dihapus; baris dengan `_loaded_at` paling baru dipertahankan (jika kolom tersedia) |

> **Penting**: Filter `witel_ho = "Telkom JATIM BARAT"` adalah keputusan bisnis yang diterapkan di layer Silver. Data Bronze tetap berisi seluruh wilayah nasional/regional.

### 3.3. Output — `silver.cbase_clean`

| Kolom | Tipe | Keterangan |
|---|---|---|
| `nipnas` | `TEXT` PRIMARY KEY | ID unik customer |
| `witel_ho` | `TEXT` | Wilayah Telkom customer |
| `standard_name` | `TEXT` NOT NULL | Nama standar customer (original) |
| `nama_normalized` | `TEXT` | Nama setelah normalisasi (untuk fuzzy matching) |
| `batch_id` | `TEXT` NOT NULL | ID batch ETL |
| `cleaned_at` | `TIMESTAMPTZ` NOT NULL | Timestamp cleaning |

> **Catatan skema**: Tabel `silver.cbase_clean` di DDL (`db/schema_bronze_silver_gold.sql`) memiliki kolom tambahan yang belum diisi oleh `clean_cbase.py` versi saat ini: `standard_name_normalized`, `total_sustain`, `revenue_ge_75jt`, `eksisting_nik_mapping`, `eksisting_nama_mapping`. Kolom `nama_normalized` ditambahkan via `ALTER TABLE` pada implementasi aktual. Kolom tersebut **ada di tabel** tetapi tidak semua diisi oleh ETL saat ini.

### 3.4. Cara Menjalankan

```bash
python -m etl.silver.clean_cbase
```

### 3.5. Verification Query

```sql
-- Total customer CBASE (Jatim Barat saja)
SELECT COUNT(*) FROM silver.cbase_clean;

-- Distribusi witel
SELECT witel_ho, COUNT(*) FROM silver.cbase_clean GROUP BY witel_ho;

-- Cek ada tidak nipnas duplikat
SELECT nipnas, COUNT(*) FROM silver.cbase_clean GROUP BY nipnas HAVING COUNT(*) > 1;

-- Sample data
SELECT nipnas, standard_name, nama_normalized FROM silver.cbase_clean LIMIT 10;
```

---

## 4. Fungsi Normalisasi Nama — `etl/common/text.py`

Fungsi `normalize_name()` dari [`etl/common/text.py`](../etl/common/text.py) digunakan oleh **`clean_prospect.py`** dan **`clean_cbase.py`** untuk menghasilkan `nama_normalized` yang konsisten dan dapat dibandingkan.

### Aturan normalisasi:

| Langkah | Aturan | Contoh |
|---|---|---|
| 1 | Guard: nilai kosong atau bukan string → return `""` | `None` → `""` |
| 2 | Ubah ke lowercase | `"PT. Maju Jaya"` → `"pt. maju jaya"` |
| 3 | Titik (`.`) dan koma (`,`) → spasi | `"pt. maju jaya"` → `"pt  maju jaya"` |
| 4 | Hapus kata noise sebagai kata utuh (regex word boundary): `PT`, `CV`, `UD`, `TB`, `TBK` | `"pt  maju jaya"` → `"  maju jaya"` |
| 5 | Multiple spasi → satu spasi; trim awal/akhir | `"  maju jaya"` → `"maju jaya"` |

**Contoh hasil:**

| Input | Output |
|---|---|
| `"PT. LKM BKD Tulungagung"` | `"lkm bkd tulungagung"` |
| `"Timbul Jaya. CV"` | `"timbul jaya"` |
| `"PT. Pelita Rejeki Farma"` | `"pelita rejeki farma"` |
| `"CV. Maju Bersama"` | `"maju bersama"` |
| `"MTSN GRESIK"` | `"mtsn gresik"` |
| `""` atau `None` | `""` |

---

## 5. Prospect-Customer Matching — `silver.prospect_customer_match`

### 5.1. Tujuan

Mencocokkan setiap prospect dari `silver.prospect_clean` dengan customer yang ada di `silver.cbase_clean` menggunakan **fuzzy string matching** pada kolom `nama_normalized`.

Tujuannya adalah untuk mengidentifikasi apakah sebuah prospect **sudah menjadi pelanggan Telkom**.

File ETL: [`etl/silver/match_prospect_customer.py`](../etl/silver/match_prospect_customer.py)

### 5.2. Library dan Scorer

- **Library**: [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) — implementasi Levenshtein/fuzzy matching yang sangat cepat
- **Scorer**: `fuzz.token_sort_ratio`
- **Versi matcher** (tersimpan di DB): `"rapidfuzz-token_sort_ratio-v2-lenguard"`

**Mengapa `token_sort_ratio` dan bukan `token_set_ratio`?**

Komentar di kode menjelaskan alasannya secara eksplisit:

> *"token_set_ratio bisa ngasih skor 100 kalau salah satu nama cuma subset kata dari nama lainnya — bikin nama pendek generik (mis. 'REJEKI') ke-match 100% ke nama panjang yang kebetulan ngandung kata itu ('PELITA REJEKI FARMA'), padahal jelas beda entitas. token_sort_ratio bandingin string penuh (abis kata-katanya diurutin), jadi selisih panjang tetep kena penalti wajar."*

`token_sort_ratio` mengurutkan kata-kata dalam string sebelum membandingkan, sehingga urutan kata tidak berpengaruh, tetapi **perbedaan jumlah kata tetap menghasilkan penalti skor** yang wajar.

### 5.3. Mekanisme Matching

Untuk setiap prospect, `process.extractOne()` dijalankan terhadap seluruh daftar `nama_normalized` di CBASE — menghasilkan satu kandidat terbaik beserta skor-nya.

**Pre-filtering sebelum matching:**
1. CBASE dengan `nama_normalized` kosong atau NULL **dikeluarkan** dari pool kandidat.
2. Prospect dengan `nama_normalized` kosong atau `"nan"/"none"` → langsung `NO_MATCH`.
3. Prospect dengan panjang nama < 4 karakter → langsung `SKIPPED_SHORT_NAME` (tidak di-match sama sekali).

**Guard panjang nama** (`MIN_LENGTH_RATIO = 0.5`):

Setelah mendapat kandidat terbaik, dihitung rasio panjang:
```
length_ratio = min(len_a, len_b) / max(len_a, len_b)
```
Jika `length_ratio < 0.5` → status `MATCH_REJECTED_LENGTH`, berapapun skornya.

Contoh: prospect `"pelita rejeki farma"` (19 char) vs CBASE `"rejeki"` (6 char) → ratio = 6/19 ≈ 0.32 < 0.5 → **ditolak**.

**Deteksi single token:**

Match antara dua nama yang masing-masing hanya terdiri dari **satu kata** diklasifikasikan secara terpisah (suffix `_SINGLE_TOKEN`) karena konfirmasi entitas yang sama lebih lemah tanpa kata konteks tambahan.

### 5.4. Threshold dan Status Matching

| Match Status | Kondisi | Deskripsi |
|---|---|---|
| `MATCH_CONFIDENT` | Skor ≥ 95, length_ratio ≥ 0.5, nama multi-kata | Sangat yakin sama entitas |
| `MATCH_CONFIDENT_SINGLE_TOKEN` | Skor ≥ 95, length_ratio ≥ 0.5, kedua nama 1 kata | Skor tinggi tapi perlu verifikasi manual |
| `MATCH_POSSIBLE` | Skor 85–94.99, length_ratio ≥ 0.5, nama multi-kata | Kemungkinan sama entitas |
| `MATCH_POSSIBLE_SINGLE_TOKEN` | Skor 85–94.99, length_ratio ≥ 0.5, kedua nama 1 kata | Potensi match tapi lemah |
| `MATCH_REJECTED_LENGTH` | length_ratio < 0.5 (apapun skornya) | Salah satu nama terlalu pendek/generik |
| `NO_MATCH` | Skor < 85, atau nama kosong | Tidak ditemukan kemiripan cukup |
| `SKIPPED_SHORT_NAME` | Panjang nama prospect < 4 karakter | Terlalu pendek untuk di-match |

### 5.5. Perlakuan di Gold

Gold menentukan kebijakan bisnis terhadap setiap status matching:

| Match Status | Masuk Gold? | Alasan |
|---|---|---|
| `MATCH_CONFIDENT` | **Tidak** | Dianggap sudah menjadi customer — dikeluarkan dari daftar prospek |
| `MATCH_POSSIBLE` | **Tidak** | Kemungkinan besar sudah customer — dikeluarkan dari daftar prospek |
| `MATCH_CONFIDENT_SINGLE_TOKEN` | **Ya** | Match satu kata, perlu verifikasi manual — tetap masuk sebagai prospek |
| `MATCH_POSSIBLE_SINGLE_TOKEN` | **Ya** | Match lemah, potensi false positive tinggi — tetap masuk |
| `MATCH_REJECTED_LENGTH` | **Ya** | Match ditolak karena panjang — dianggap belum berlangganan |
| `NO_MATCH` | **Ya** | Tidak ada kemiripan cukup — dianggap belum berlangganan |
| `SKIPPED_SHORT_NAME` | **Ya** | Tidak ada data cukup untuk matching — dianggap belum berlangganan |

> **Filosofi**: "Salah exclude prospek asli (kehilangan peluang sales) lebih mahal daripada salah include orang yang sudah jadi pelanggan (cuma rugi waktu verifikasi pas sales kontak)."

### 5.6. Poin Penting

- Hasil matching **tidak menghapus data** dari `silver.prospect_clean` atau `silver.cbase_clean`.
- Seluruh hasil — termasuk `NO_MATCH` dan `SKIPPED_SHORT_NAME` — disimpan di `silver.prospect_customer_match` **untuk keperluan audit**.
- Setiap prospect hanya memiliki satu hasil matching (one-to-one) — yaitu kandidat CBASE **terbaik** yang ditemukan.
- UPSERT menggunakan `ON CONFLICT (prospect_id)` sehingga safe untuk dijalankan berulang.

### 5.7. Output — `silver.prospect_customer_match`

> **Catatan**: Skema DDL di `db/schema_bronze_silver_gold.sql` berbeda dengan implementasi aktual. DDL memiliki kolom `status` dengan constraint `CHECK IN ('EKSIS', 'BELUM_BERLANGGANAN')` dan primary key `match_id`, namun implementasi aktual menggunakan `prospect_id` sebagai primary key dan `match_status` sebagai nama kolom. Tabel aktual dibuat oleh script ETL, bukan dari DDL file tersebut.

| Kolom | Tipe | Keterangan |
|---|---|---|
| `prospect_id` | `BIGINT` PRIMARY KEY | FK ke `silver.prospect_clean` |
| `prospect_name` | `TEXT` NOT NULL | Nama asli prospect |
| `prospect_name_normalized` | `TEXT` NOT NULL | Nama normalized prospect |
| `prospect_wilayah` | `TEXT` | Wilayah prospect |
| `matched_nipnas` | `VARCHAR(50)` | nipnas CBASE yang cocok (NULL jika tidak match) |
| `matched_standard_name` | `TEXT` | Nama CBASE yang cocok |
| `matched_name_normalized` | `TEXT` | Nama normalized CBASE yang cocok |
| `match_score` | `NUMERIC(5,2)` | Skor fuzzy matching (0–100) |
| `match_status` | `VARCHAR(30)` NOT NULL | Salah satu dari 7 status di atas |
| `matcher_version` | `VARCHAR(50)` | Versi algoritma matching |
| `batch_id` | `VARCHAR(50)` | ID batch matching |
| `matched_at` | `TIMESTAMPTZ` | Timestamp matching |

### 5.8. Cara Menjalankan

```bash
python -m etl.silver.match_prospect_customer
```

### 5.9. Verification Query

```sql
-- Total hasil matching
SELECT COUNT(*) FROM silver.prospect_customer_match;

-- Breakdown per status
SELECT match_status, COUNT(*)
FROM silver.prospect_customer_match
GROUP BY match_status
ORDER BY match_status;

-- Contoh MATCH_CONFIDENT
SELECT prospect_name, matched_standard_name, match_score, match_status
FROM silver.prospect_customer_match
WHERE match_status = 'MATCH_CONFIDENT'
ORDER BY match_score DESC
LIMIT 20;

-- Contoh MATCH_POSSIBLE
SELECT prospect_name, matched_standard_name, match_score, match_status
FROM silver.prospect_customer_match
WHERE match_status = 'MATCH_POSSIBLE'
ORDER BY match_score DESC
LIMIT 20;

-- Contoh yang di-skip
SELECT prospect_name, prospect_name_normalized, match_status
FROM silver.prospect_customer_match
WHERE match_status IN ('SKIPPED_SHORT_NAME', 'MATCH_REJECTED_LENGTH')
LIMIT 20;
```

---

## Diagram Data Flow Silver

```
bronze.odp_raw
      │
      │  python -m etl.silver.clean_odp
      │  (clean_odp.py → staging table → upsert)
      ▼
silver.odp_clean
(75.000+ ODP, PostGIS geometry, partial index available_port > 0)

bronze.prospect_raw
      │
      │  python -m etl.silver.clean_prospect
      │  (clean_prospect.py → staging table → upsert)
      ▼
silver.prospect_clean
(2.747 prospect, PostGIS geometry, flag is_telkom_entity)
      │
      │  python -m etl.silver.match_prospect_customer
      │  (RapidFuzz token_sort_ratio vs silver.cbase_clean)
      ▼
silver.prospect_customer_match
(1 baris per prospect, berisi status dan skor matching)

bronze.cbase_raw
      │
      │  python -m etl.silver.clean_cbase
      │  (filter JATIM BARAT → clean → staging → upsert)
      ▼
silver.cbase_clean
(25.000+ customer Jatim Barat)
```

---

*Dokumen ini dibuat berdasarkan kode aktual di repository. Angka data bersifat indikatif dan akan berubah sesuai data terkini.*
