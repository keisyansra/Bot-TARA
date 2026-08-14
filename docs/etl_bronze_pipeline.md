# Bronze Layer Documentation

> Dokumentasi ini menjelaskan proses **raw ingestion** di layer Bronze.
> Berdasarkan inspeksi kode aktual di `etl/bronze/`.

---

## 1. Tujuan Bronze

Bronze adalah lapisan penyimpanan data **mentah apa adanya** dari sumber, dengan perubahan sesedikit mungkin.

Prinsip desain yang diterapkan di repository ini:

- **Semua kolom disimpan sebagai `TEXT`** — sehingga proses ingestion tidak pernah gagal karena ketidakkonsistenan format sumber (contoh: koma sebagai pemisah desimal, newline di tengah nilai, angka dalam format saintifik).
- **Tidak ada cleaning, validasi tipe, atau transformasi logika bisnis** di layer ini.
- **Data mentah dipertahankan** untuk keperluan audit dan reprocessing jika logika Silver berubah.
- **Duplikasi diperbolehkan** — Bronze menggunakan `if_exists="append"`, sehingga setiap kali loader dijalankan ulang, data ditambahkan (bukan menimpa).
- Setiap baris dilabeli dengan metadata ingestion: `_batch_id`, `_loaded_at`, `_source_file`, dan `_wilayah_file` (jika relevan).

---

## 2. Tabel Bronze

### 2.1. `bronze.odp_raw`

| Atribut | Detail |
|---|---|
| **Sumber data** | File CSV atau Excel ODP per wilayah |
| **File ETL** | [`etl/bronze/load_odp.py`](../etl/bronze/load_odp.py) |
| **Fungsi utama** | `load_odp_file(file_path, wilayah, batch_id, source_file, sheet_name)` |
| **Primary key** | `id` (BIGSERIAL, auto-generated) |
| **Conflict policy** | `if_exists="append"` — tidak ada upsert, setiap run menambah data |

**Kolom penting:**

| Kolom Bronze | Kolom Sumber Asli | Deskripsi |
|---|---|---|
| `id_odp` | `ID ODP` | ID ODP dari sistem Telkom (TEXT di bronze) |
| `odp_name` | `ODP NAME` | Nama ODP |
| `latitude` | `LATITUDE` | Koordinat lintang (TEXT di bronze) |
| `longitude` | `LONGITUDE` | Koordinat bujur (TEXT di bronze) |
| `avai` | `AVAI` | Port tersedia (TEXT di bronze) |
| `used` | `USED` | Port terpakai |
| `rsv` | `RSV` | Port reserved |
| `rsk` | `RSK` | Port rusak |
| `is_total` | `IS TOTAL` | Total port |
| `occ_1` | `OCC 1` | Occupancy status 1 |
| `occ_2` | `OCC 2` | Occupancy status 2 |
| `telkom_witel` | `Telkom Witel` | Wilayah Telkom |
| `kabupaten_kota` | `KABUPATEN KOTA` | Lokasi administratif |
| `telda` | `Telda` | Telkom Daerah (digunakan Silver untuk kolom `wilayah_file`) |
| `tgl_golive` | `TGL GOLIVE` | Tanggal go-live ODP |
| `update_date` | `UPDATE DATE` | Tanggal update data |
| `_wilayah_file` | *(dari argumen CLI `--wilayah`)* | Label wilayah saat ingestion |
| `_source_file` | *(dari nama file)* | Nama file sumber |
| `_batch_id` | *(dari argumen CLI `--batch-id`)* | ID batch ingestion |
| `_loaded_at` | *(auto)* | Timestamp ingestion |

**Cara menjalankan:**
```bash
# Format CSV
python -m etl.bronze.load_odp --file "data/odp_batu.csv" --wilayah BATU

# Format Excel, pilih sheet tertentu
python -m etl.bronze.load_odp --file "data/odp_master.xlsx" --wilayah JATIM_BARAT --sheet "Sheet3"
```

---

### 2.2. `bronze.prospect_raw`

| Atribut | Detail |
|---|---|
| **Sumber data** | File Excel hasil scraping Google Maps, satu file per wilayah |
| **File ETL** | [`etl/bronze/load_prospect.py`](../etl/bronze/load_prospect.py) |
| **Fungsi utama** | `load_prospect_file(file_path, wilayah, batch_id, source_file)` |
| **Primary key** | `id` (BIGSERIAL, auto-generated) |
| **Conflict policy** | `if_exists="append"` — tidak ada upsert |

**Kolom penting:**

| Kolom Bronze | Kolom Sumber Asli | Deskripsi |
|---|---|---|
| `nama` | `nama` | Nama bisnis/tempat dari Google Maps |
| `kategori` | `kategori` | Kategori tempat |
| `alamat` | `alamat` | Alamat lengkap |
| `telepon` | `telepon` | Nomor telepon |
| `rating` | `rating` | Rating Google Maps (TEXT di bronze) |
| `latitude` | `latitude` | Koordinat lintang (TEXT di bronze) |
| `longitude` | `longitude` | Koordinat bujur (TEXT di bronze) |
| `url_gmaps` | `url_gmaps` | URL Google Maps |
| `_wilayah_file` | *(dari argumen CLI `--wilayah`)* | Label wilayah, digunakan Silver untuk kolom `wilayah` |
| `_source_file` | *(dari nama file)* | Nama file sumber |
| `_batch_id` | *(dari argumen CLI `--batch-id`)* | ID batch ingestion |
| `_loaded_at` | *(auto)* | Timestamp ingestion |

**Cara menjalankan:**
```bash
python -m etl.bronze.load_prospect --file "data/scraping_batu.xlsx" --wilayah BATU
```

---

### 2.3. `bronze.cbase_raw`

| Atribut | Detail |
|---|---|
| **Sumber data** | File Excel export CBASE (Customer Base) dari sistem internal Telkom, satu file nasional/regional |
| **File ETL** | [`etl/bronze/load_cbase.py`](../etl/bronze/load_cbase.py) |
| **Fungsi utama** | `load_cbase_file(file_path, batch_id, source_file)` |
| **Primary key** | `id` (BIGSERIAL, auto-generated) |
| **Conflict policy** | `if_exists="append"` — tidak ada upsert |

**Catatan khusus CBASE**: Loader CBASE memiliki logika tambahan karena format Excel-nya tidak konsisten:
1. **Auto-detect baris header** — Loader mencari baris pertama yang mengandung kolom wajib `NIPNAS`, `WITEL_HO`, dan `STANDARD_NAME`. Baris di atas header tersebut diabaikan.
2. **Dynamic column mapping** — Dua kolom memiliki nama yang berubah setiap bulan (`CEK CBASE [tanggal]` dan `MAPPING [BULAN]_NIK/NAMA`). Loader menggunakan regex pattern matching di [`etl/bronze/column_maps.py`](../etl/bronze/column_maps.py) agar tetap berfungsi meskipun nama kolom berubah.

**Kolom penting:**

| Kolom Bronze | Kolom Sumber Asli | Deskripsi |
|---|---|---|
| `nipnas` | `NIPNAS` | ID unik customer (TEXT di bronze) |
| `witel_ho` | `WITEL_HO` | Wilayah Telkom customer |
| `standard_name` | `STANDARD_NAME` | Nama standar customer |
| `alur` | `ALUR` | Kode alur |
| `regional_ho` | `REGIONAL_HO` | Regional Telkom |
| `rev_witel_bill_sama` | `REV WITEL BILL SAMA ...` | Revenue witel sama |
| `total_sustain` | `TOTAL_SUSTAIN` | Total sustain revenue |
| `revenue_ge_75jt` | `REVENUE >= ... JUTA` | Flag revenue ≥ 75 juta (nama kolom dinamis) |
| `cek_cbase_tanggal` | `CEK CBASE [tanggal]` | Status cek CBASE (nama kolom dinamis, tanggal berubah) |
| `mapping_bulan_nik` | `MAPPING [BULAN]_NIK` | Mapping NIK per bulan (nama kolom dinamis) |
| `mapping_bulan_nama` | `MAPPING [BULAN]_NAMA` | Mapping Nama per bulan (nama kolom dinamis) |
| `eksisting_nik_mapping` | `EKSISTING NIK MAPPING` | NIK mapping eksisting |
| `eksisting_nama_mapping` | `EKSISTING NAMA MAPPING` | Nama mapping eksisting |
| `_source_file` | *(dari nama file)* | Nama file sumber |
| `_batch_id` | *(dari argumen CLI `--batch-id`)* | ID batch ingestion |
| `_loaded_at` | *(auto)* | Timestamp ingestion |

**Cara menjalankan:**
```bash
python -m etl.bronze.load_cbase --file "data/cbase.xlsx"
```

---

## 3. Column Mapping — `etl/bronze/column_maps.py`

File [`column_maps.py`](../etl/bronze/column_maps.py) berisi tiga komponen:

| Komponen | Kegunaan |
|---|---|
| `ODP_COLUMN_MAP` | Dict statis: nama kolom Excel ODP → nama kolom Bronze |
| `PROSPECT_COLUMN_MAP` | Dict statis: nama kolom Excel Prospect → nama kolom Bronze |
| `CBASE_STATIC_MAP` | Dict statis untuk kolom CBASE yang namanya tidak berubah |
| `CBASE_PATTERN_MAP` | List regex pattern untuk kolom CBASE yang namanya berubah tiap bulan |
| `map_cbase_columns(columns)` | Fungsi yang menggabungkan STATIC + PATTERN mapping untuk setiap batch CBASE |

---

## 4. Karakteristik Bronze

| Karakteristik | ODP | Prospect | CBASE |
|---|---|---|---|
| Semua kolom TEXT | ✅ | ✅ | ✅ |
| Data belum di-clean | ✅ | ✅ | ✅ |
| Belum dilakukan typing | ✅ | ✅ | ✅ |
| Belum dilakukan validasi koordinat | ✅ | ✅ | N/A |
| Belum dilakukan deduplication | ✅ | ✅ | ✅ |
| Duplikasi antar-run dimungkinkan | ✅ | ✅ | ✅ |
| Memiliki metadata ingestion | ✅ | ✅ | ✅ |
| Filter wilayah | Tidak | Tidak | Tidak |

---

## 5. Data Flow Diagram

```
CSV / Excel (ODP per wilayah)
          │
          │  python -m etl.bronze.load_odp --file ... --wilayah ...
          ▼
    bronze.odp_raw
    (append only, semua TEXT)

Excel (Prospect per wilayah dari scraping Google Maps)
          │
          │  python -m etl.bronze.load_prospect --file ... --wilayah ...
          ▼
    bronze.prospect_raw
    (append only, semua TEXT)

Excel (CBASE — 1 file utuh, header auto-detect, kolom dinamis)
          │
          │  python -m etl.bronze.load_cbase --file ...
          ▼
    bronze.cbase_raw
    (append only, semua TEXT)
```

---

## 6. Verification Query

Cek total baris per tabel Bronze:

```sql
-- Jumlah baris ODP raw
SELECT COUNT(*) FROM bronze.odp_raw;

-- Jumlah baris per batch ODP
SELECT _batch_id, _wilayah_file, COUNT(*)
FROM bronze.odp_raw
GROUP BY _batch_id, _wilayah_file
ORDER BY MIN(_loaded_at) DESC;

-- Jumlah baris Prospect raw
SELECT COUNT(*) FROM bronze.prospect_raw;

-- Jumlah baris per wilayah Prospect
SELECT _wilayah_file, COUNT(*)
FROM bronze.prospect_raw
GROUP BY _wilayah_file
ORDER BY _wilayah_file;

-- Jumlah baris CBASE raw
SELECT COUNT(*) FROM bronze.cbase_raw;

-- Cek distribusi witel_ho di CBASE
SELECT witel_ho, COUNT(*)
FROM bronze.cbase_raw
GROUP BY witel_ho
ORDER BY COUNT(*) DESC
LIMIT 20;
```

---

*Dokumen ini dibuat berdasarkan kode aktual di repository. Angka data bersifat indikatif dan akan berubah sesuai data terkini.*
