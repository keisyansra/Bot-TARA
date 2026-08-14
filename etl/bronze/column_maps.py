"""
Mapping nama kolom asli (dari file Excel sumber) ke nama kolom
snake_case di tabel bronze. Taruh di sini biar kalau ada perubahan
header dari sumber, tinggal update di satu tempat.
"""
import re

ODP_COLUMN_MAP = {
    "DEVICE ID": "device_id",
    "ODP INDEX": "odp_index",
    "ODP NAME": "odp_name",
    "LATITUDE": "latitude",
    "LONGITUDE": "longitude",
    "CLUSNAME": "clusname",
    "CLUSTERSATATUS": "cluster_status",
    "AVAI": "avai",
    "USED": "used",
    "RSV": "rsv",
    "RSK": "rsk",
    "IS TOTAL": "is_total",
    "Telkom Regional": "telkom_regional",
    "Telkom Witel": "telkom_witel",
    "Telkom Datel": "telkom_datel",
    "Telkom STO": "telkom_sto",
    "Telkom STO Deskripsi": "telkom_sto_deskripsi",
    "ODP INFO": "odp_info",
    "UPDATE DATE": "update_date",
    "TGL GOLIVE": "tgl_golive",
    "TAHUN ODP": "tahun_odp",
    "BULAN ODP": "bulan_odp",
    "KATEGORI": "kategori",
    "NAMA PROYEK": "nama_proyek",
    "KABUPATEN KOTA": "kabupaten_kota",
    "PROVINSI": "provinsi",
    "OCC 1": "occ_1",
    "OCC 2": "occ_2",
    "ID ODP": "id_odp",
    "Telkomsel Area": "telkomsel_area",
    "Telkomsel Regional": "telkomsel_regional",
    "Telkomsel Branch": "telkomsel_branch",
    "Telkomsel Cluster": "telkomsel_cluster",
    "Validasi STO": "validasi_sto",
    "Validasi ODC": "validasi_odc",
    "Jarak ODP ke ODC (Meter)": "jarak_odp_odc_m",
    "Jarak ODC ke STO (Meter)": "jarak_odc_sto_m",
    "Jarak ODP ke STO (Meter)": "jarak_odp_sto_m",
    "Validasi Provinsi": "validasi_provinsi",
    "Validasi Kabupaten Kota": "validasi_kabupaten_kota",
    "Validasi Kecamatan": "validasi_kecamatan",
    "Validasi Kelurahan": "validasi_kelurahan",
    "Telda": "telda",
}

PROSPECT_COLUMN_MAP = {
    "nama": "nama",
    "kategori": "kategori",
    "alamat": "alamat",
    "telepon": "telepon",
    "rating": "rating",
    "latitude": "latitude",
    "longitude": "longitude",
    "url_gmaps": "url_gmaps",
}

# CBASE punya 2 kolom yang nama aslinya BERUBAH tiap bulan:
#   "CEK CBASE 17042026"      -> tanggal beda tiap refresh
#   "MAPPING APRIL_NIK/NAMA"  -> nama bulan beda tiap refresh
# Dua ini di-match pakai pola regex, bukan nama persis, biar loader
# nggak rusak begitu bulan/tanggalnya berubah di file berikutnya.
CBASE_STATIC_MAP = {
    "NIPNAS": "nipnas",
    "WITEL_HO": "witel_ho",
    "ALUR": "alur",
    "REGIONAL_HO": "regional_ho",
    "STANDARD_NAME": "standard_name",
    "REV WITEL BILL SAMA DENGAN WITEL HO": "rev_witel_bill_sama",
    "REV WITEL BILL BERBEDA DENGAN WITEL HO": "rev_witel_bill_beda",
    "REV_POTS": "rev_pots",
    "REV_NONPOTS": "rev_nonpots",
    "TOTAL_SUSTAIN": "total_sustain",
    "EKSISTING NIK MAPPING": "eksisting_nik_mapping",
    "EKSISTING NAMA MAPPING": "eksisting_nama_mapping",
    "USULAN NIK MAPPING": "usulan_nik_mapping",
    "USULAN NAMA MAPPING": "usulan_nama_mapping",
}

CBASE_PATTERN_MAP = [
    (re.compile(r"^REVENUE\s*>=.*JUTA.*", re.IGNORECASE), "revenue_ge_75jt"),
    (re.compile(r"^CEK CBASE\s*\d+", re.IGNORECASE), "cek_cbase_tanggal"),
    (re.compile(r"^MAPPING\s+\w+_NIK$", re.IGNORECASE), "mapping_bulan_nik"),
    (re.compile(r"^MAPPING\s+\w+_NAMA$", re.IGNORECASE), "mapping_bulan_nama"),
]


def map_cbase_columns(columns):
    """Petain kolom CBASE asli ke nama snake_case bronze, termasuk
    yang nama aslinya berubah-ubah tiap bulan (tanggal/nama bulan).
    Kolom yang nggak dikenali dipetakan ke None dan di-skip pas load."""
    result = {}
    for col in columns:
        col_stripped = str(col).strip()
        if col_stripped in CBASE_STATIC_MAP:
            result[col] = CBASE_STATIC_MAP[col_stripped]
            continue
        matched = None
        for pattern, target in CBASE_PATTERN_MAP:
            if pattern.match(col_stripped):
                matched = target
                break
        result[col] = matched
    return result