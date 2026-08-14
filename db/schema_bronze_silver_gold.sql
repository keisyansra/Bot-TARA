-- ============================================================
-- SCHEMA: BOT TELKOM PROSPECTING - BRONZE / SILVER / GOLD
-- ============================================================

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- BRONZE — raw, apa adanya. Semua kolom TEXT biar load nggak
-- pernah gagal gara-gara format sumber yang berantakan
-- (koma sebagai desimal, newline nyangkut, dsb).
-- ============================================================

CREATE TABLE IF NOT EXISTS bronze.odp_raw (
    id                      BIGSERIAL PRIMARY KEY,
    device_id               TEXT,
    odp_index                TEXT,
    odp_name                 TEXT,
    latitude                 TEXT,
    longitude                TEXT,
    clusname                 TEXT,
    cluster_status            TEXT,
    avai                     TEXT,
    used                     TEXT,
    rsv                      TEXT,
    rsk                      TEXT,
    is_total                  TEXT,
    telkom_regional            TEXT,
    telkom_witel              TEXT,
    telkom_datel              TEXT,
    telkom_sto                TEXT,
    telkom_sto_deskripsi       TEXT,
    odp_info                  TEXT,
    update_date               TEXT,
    tgl_golive                TEXT,
    tahun_odp                 TEXT,
    bulan_odp                 TEXT,
    kategori                  TEXT,
    nama_proyek                TEXT,
    kabupaten_kota              TEXT,
    provinsi                  TEXT,
    occ_1                     TEXT,
    occ_2                     TEXT,
    id_odp                    TEXT,
    telkomsel_area              TEXT,
    telkomsel_regional          TEXT,
    telkomsel_branch            TEXT,
    telkomsel_cluster           TEXT,
    validasi_sto               TEXT,
    validasi_odc               TEXT,
    jarak_odp_odc_m             TEXT,
    jarak_odc_sto_m             TEXT,
    jarak_odp_sto_m             TEXT,
    validasi_provinsi           TEXT,
    validasi_kabupaten_kota      TEXT,
    validasi_kecamatan          TEXT,
    validasi_kelurahan          TEXT,
    _wilayah_file              TEXT NOT NULL,   -- dari nama folder (BATU, KEDIRI, dst)
    _source_file               TEXT,
    _batch_id                  TEXT NOT NULL,
    _loaded_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE bronze.odp_raw IS 'Raw ODP csv per wilayah, apa adanya';

CREATE TABLE IF NOT EXISTS bronze.cbase_raw (
    id                     BIGSERIAL PRIMARY KEY,
    nipnas                 TEXT,
    witel_ho                TEXT,
    alur                    TEXT,
    regional_ho              TEXT,
    standard_name             TEXT,
    rev_witel_bill_sama        TEXT,
    rev_witel_bill_beda        TEXT,
    rev_pots                 TEXT,
    rev_nonpots               TEXT,
    total_sustain              TEXT,
    revenue_ge_75jt             TEXT,
    cek_cbase_tanggal           TEXT,
    eksisting_nik_mapping        TEXT,
    eksisting_nama_mapping       TEXT,
    usulan_nik_mapping          TEXT,
    usulan_nama_mapping         TEXT,
    mapping_bulan_nik           TEXT,
    mapping_bulan_nama          TEXT,
    _source_file              TEXT,
    _batch_id                 TEXT NOT NULL,
    _loaded_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE bronze.cbase_raw IS 'Raw CBASE export, 1 file utuh jatim barat, apa adanya';

CREATE TABLE IF NOT EXISTS bronze.prospect_raw (
    id             BIGSERIAL PRIMARY KEY,
    nama            TEXT,
    kategori         TEXT,
    alamat           TEXT,
    telepon          TEXT,
    rating           TEXT,
    latitude         TEXT,
    longitude        TEXT,
    url_gmaps        TEXT,
    _wilayah_file      TEXT NOT NULL,
    _source_file       TEXT,
    _batch_id         TEXT NOT NULL,
    _loaded_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE bronze.prospect_raw IS 'Raw hasil scraping google maps per wilayah, apa adanya';

-- ============================================================
-- SILVER — cleaned, typed, normalized, matched.
-- Upsert di sini (bukan truncate+reload) supaya prospect_id /
-- id_odp tetap stabil antar batch, karena gold nge-FK ke sini.
-- ============================================================

CREATE TABLE IF NOT EXISTS silver.cbase_clean (
    nipnas                  TEXT PRIMARY KEY,
    witel_ho                 TEXT,
    standard_name             TEXT NOT NULL,
    standard_name_normalized   TEXT NOT NULL,
    total_sustain             NUMERIC,
    revenue_ge_75jt            BOOLEAN,
    eksisting_nik_mapping      TEXT,
    eksisting_nama_mapping     TEXT,
    batch_id                 TEXT NOT NULL,
    cleaned_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cbase_clean_name_norm ON silver.cbase_clean (standard_name_normalized);

CREATE TABLE IF NOT EXISTS silver.prospect_clean (
    prospect_id       BIGSERIAL PRIMARY KEY,
    nama              TEXT NOT NULL,
    nama_normalized     TEXT NOT NULL,
    kategori           TEXT,
    alamat             TEXT,
    telepon            TEXT,
    rating             NUMERIC,
    latitude           NUMERIC NOT NULL,
    longitude           NUMERIC NOT NULL,
    geom               GEOGRAPHY(POINT, 4326) NOT NULL,
    url_gmaps           TEXT,
    wilayah            TEXT NOT NULL,
    is_telkom_entity      BOOLEAN NOT NULL DEFAULT false,  -- exclude "PT TELKOM ..." dari kandidat
    batch_id           TEXT NOT NULL,
    cleaned_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (nama_normalized, wilayah)   -- natural key buat upsert
);
CREATE INDEX IF NOT EXISTS idx_prospect_clean_geom ON silver.prospect_clean USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_prospect_clean_name_norm ON silver.prospect_clean (nama_normalized);

CREATE TABLE IF NOT EXISTS silver.odp_clean (
    id_odp             BIGINT PRIMARY KEY,
    odp_name            TEXT NOT NULL,
    latitude            NUMERIC NOT NULL,
    longitude           NUMERIC NOT NULL,
    geom               GEOGRAPHY(POINT, 4326) NOT NULL,
    available_port       INTEGER NOT NULL,
    used_port           INTEGER,
    rsv_port            INTEGER,
    rsk_port            INTEGER,
    total_port           INTEGER,
    occupancy_status      TEXT,     -- dari OCC 1 / OCC 2
    witel              TEXT,
    kabupaten_kota         TEXT,
    provinsi            TEXT,
    wilayah_file          TEXT NOT NULL,
    tgl_golive           DATE,
    update_date          TIMESTAMPTZ,
    batch_id            TEXT NOT NULL,
    cleaned_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_odp_clean_geom ON silver.odp_clean USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_odp_clean_available ON silver.odp_clean (available_port) WHERE available_port > 0;

CREATE TABLE IF NOT EXISTS silver.prospect_customer_match (
    match_id      BIGSERIAL PRIMARY KEY,
    prospect_id    BIGINT NOT NULL REFERENCES silver.prospect_clean(prospect_id),
    nipnas         TEXT REFERENCES silver.cbase_clean(nipnas),  -- null = belum berlangganan
    match_score    NUMERIC,                                     -- skor rapidfuzz
    status         TEXT NOT NULL CHECK (status IN ('EKSIS', 'BELUM_BERLANGGANAN')),
    batch_id       TEXT NOT NULL,
    matched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (prospect_id, batch_id)
);
CREATE INDEX IF NOT EXISTS idx_match_status ON silver.prospect_customer_match (status);

-- ============================================================
-- GOLD — snapshot terkini, siap query realtime.
-- Di-upsert tiap batch (bukan accumulate history). Histori
-- batch itu sendiri dicatat di gold.batch_log, terpisah,
-- biar tabel utama tetap kecil & cepat.
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.prospect_recommendation (
    prospect_id        BIGINT PRIMARY KEY REFERENCES silver.prospect_clean(prospect_id),
    nama               TEXT NOT NULL,
    alamat             TEXT,
    latitude            NUMERIC NOT NULL,
    longitude           NUMERIC NOT NULL,
    geom               GEOGRAPHY(POINT, 4326) NOT NULL,
    wilayah             TEXT NOT NULL,
    url_gmaps            TEXT,
    nearest_odp_id        BIGINT REFERENCES silver.odp_clean(id_odp),
    nearest_odp_name      TEXT,
    nearest_odp_latitude  NUMERIC,
    nearest_odp_longitude NUMERIC,
    odp_distance_m        NUMERIC,
    odp_available_port     INTEGER,
    badge_status         TEXT CHECK (badge_status IN ('siap_pasang', 'di_luar_radius', 'odp_tidak_ditemukan')),
    batch_id            TEXT NOT NULL,
    calculated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_gold_prospect_geom ON gold.prospect_recommendation USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_gold_prospect_wilayah ON gold.prospect_recommendation (wilayah);

COMMENT ON TABLE gold.prospect_recommendation IS 'Snapshot terkini per prospek belum berlangganan, diupsert tiap batch. Ini yang langsung diquery FastAPI/bot.';
COMMENT ON COLUMN gold.prospect_recommendation.batch_id IS 'ID batch pipeline yang terakhir menghasilkan baris ini, buat audit/debug';
COMMENT ON COLUMN gold.prospect_recommendation.badge_status IS 'siap_pasang = odp <=250m tersedia; di_luar_radius = odp terdekat >250m; odp_tidak_ditemukan = tidak ada odp available sama sekali dalam jangkauan wajar';

CREATE TABLE IF NOT EXISTS gold.batch_log (
    batch_id       TEXT PRIMARY KEY,
    triggered_by     TEXT NOT NULL,  -- 'odp_upload' | 'cbase_upload' | 'scraping_cron'
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at      TIMESTAMPTZ,
    row_count       INTEGER,
    status          TEXT CHECK (status IN ('running', 'success', 'failed')) DEFAULT 'running',
    notes           TEXT
);
COMMENT ON TABLE gold.batch_log IS 'Riwayat tiap kali pipeline batch jalan, buat audit & debugging tanpa nyimpen history penuh di gold utama';