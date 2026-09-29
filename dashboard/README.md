# TARA Admin Dashboard (Streamlit)

Frontend administrator untuk **TARA (Telkom Area Recommendation Assistant)**.  
Dashboard ini dibuat dengan **Streamlit** dan terhubung ke backend TARA melalui **REST API (FastAPI)**.

## Fitur Utama

Dashboard menyediakan beberapa fungsi administrasi:

- **Dashboard** — ringkasan status sistem dan data utama.
- **Data Pelanggan (CBASE)** — melihat, menambah, mengubah, menghapus, dan memperbarui data pelanggan.
- **Data ODP** — melihat, menambah, mengubah, menghapus, memfilter, dan memperbarui data ODP.
- **Riwayat Aktivitas** — melihat aktivitas administrator.
- **Data Prospek** — melihat data calon pelanggan/prospek beserta informasi terkait.
- **User & Approval Bot** — mengelola persetujuan dan role pengguna Bot TARA.
- **Login Administrator** — akses dashboard menggunakan akun administrator yang terdaftar.

---

## Struktur Frontend

```text
dashboard/
├── Home.py
├── .streamlit/
│   └── config.toml
├── assets/
│   ├── BG_Login.jpg
│   └── logo_tara.png
├── pages/
│   ├── 0_Login.py
│   ├── 1_Data_Pelanggan_CBASE.py
│   ├── 2_Data_ODP.py
│   ├── 3_Data_Prospek.py
│   ├── 4_Riwayat_Aktivitas.py
│   └── 5_User_Approval.py
├── utils/
│   ├── api_client.py
│   ├── auth.py
│   └── ui.py
├── requirements.txt
└── README.md
```

---

## Arsitektur Singkat

```text
Streamlit Dashboard
        │
        │ REST API
        ▼
FastAPI Backend TARA
        │
        ▼
PostgreSQL / PostGIS
```

Frontend **tidak menyimpan data master secara langsung**. Data CBASE, ODP, prospek, user, dan aktivitas diperoleh melalui API backend TARA.

---

## Persiapan

Pastikan:

1. Python dan `pip` sudah tersedia.
2. Backend TARA sudah berjalan dan dapat diakses dari perangkat yang menjalankan dashboard.
3. Akun administrator dashboard sudah dikonfigurasi secara lokal.
4. Jika backend menggunakan alamat private/LAN, perangkat frontend harus berada pada jaringan yang dapat menjangkau backend tersebut.


## Instalasi Dependency

Masuk ke folder dashboard:

```powershell
cd dashboard
```

Install dependency:

```powershell
pip install -r requirements.txt
```

Jika menggunakan virtual environment, aktifkan virtual environment terlebih dahulu.

---

## Menghubungkan Dashboard ke Backend

Alamat backend diatur melalui environment variable:

```text
TARA_API_BASE_URL
```

Contoh di Windows PowerShell:

```powershell
$env:TARA_API_BASE_URL="http://<HOST-BACKEND>:8000"
```

Ganti `<HOST-BACKEND>` dengan alamat backend yang sedang aktif, misalnya IP server pada jaringan kantor atau domain backend jika sudah dideploy.

Environment variable harus diset pada **terminal yang sama** sebelum menjalankan Streamlit.

> Sebaiknya selalu gunakan `TARA_API_BASE_URL` sesuai environment yang sedang digunakan dan jangan mengandalkan URL tunnel/fallback lama yang mungkin sudah tidak aktif.

---

## Menjalankan Dashboard

Setelah dependency tersedia dan backend sudah ditentukan:

```powershell
python -m streamlit run Home.py --server.maxUploadSize=200 --server.maxMessageSize=200
```

Jika perintah dijalankan dari root repository, gunakan:

```powershell
python -m streamlit run dashboard\Home.py --server.maxUploadSize=200 --server.maxMessageSize=200
```

Streamlit kemudian akan memberikan alamat lokal, biasanya:

```text
http://localhost:8501
```

Buka alamat tersebut melalui browser.

---

## Urutan Menjalankan Sistem

Urutan yang disarankan:

1. Pastikan **database** backend tersedia.
2. Pastikan **FastAPI backend TARA** sudah berjalan.
3. Pastikan perangkat frontend dapat mengakses backend.
4. Set `TARA_API_BASE_URL`.
5. Jalankan Streamlit.
6. Login menggunakan akun administrator yang telah terdaftar.

Jika backend dijalankan menggunakan Docker, Docker dijalankan pada sisi **backend/server**, sedangkan dashboard Streamlit tetap dapat dijalankan secara terpisah selama API backend dapat diakses.

---

## Mengecek Koneksi Backend

Contoh pengecekan dari Windows PowerShell:

```powershell
Test-NetConnection <HOST-BACKEND> -Port 8000
```

Cek endpoint admin:

```powershell
curl.exe http://<HOST-BACKEND>:8000/api/admin/stats
```

Jika koneksi berhasil dan endpoint mengembalikan data, frontend seharusnya dapat terhubung ke backend.

---

## Login Administrator

Dashboard memiliki halaman login administrator.

Credential administrator disimpan melalui konfigurasi lokal Streamlit dan **tidak boleh disimpan di repository publik**.

File seperti berikut harus tetap bersifat lokal:

```text
.streamlit/secrets.toml
.env
```

Jangan memasukkan password atau token asli ke dalam source code.

---

## Jika Dashboard Menampilkan "Sistem Bermasalah"

Periksa hal berikut:

1. Backend FastAPI sedang berjalan.
2. `TARA_API_BASE_URL` sudah diset pada terminal yang menjalankan Streamlit.
3. Host dan port backend dapat dijangkau.
4. Jika menggunakan IP jaringan lokal, frontend dan backend berada pada jaringan yang sesuai.
5. Endpoint `/api/admin/stats` dapat diakses.
6. Setelah mengganti environment variable, restart Streamlit dari terminal yang sama.

---

## Catatan Pengembangan

- Frontend: **Streamlit**
- Backend: **FastAPI / Uvicorn**
- Database: **PostgreSQL / PostGIS**
- Komunikasi frontend-backend: **REST API**
- Data processing: **Pandas / OpenPyXL**
- Konfigurasi alamat backend: **`TARA_API_BASE_URL`**

Jika alamat backend berubah, tidak perlu mengubah seluruh kode frontend. Cukup sesuaikan nilai `TARA_API_BASE_URL` sebelum menjalankan aplikasi.
