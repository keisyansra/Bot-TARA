# TARA Admin Dashboard (Streamlit)

Dashboard admin buat CRUD data ODP, Pelanggan (CBASE), Prospek, dan approval
user bot Telegram. Terhubung ke backend FastAPI Bot TARA lewat REST API.

## Menjalankan

```bash
cd dashboard
pip install -r requirements.txt
streamlit run Home.py
```

Default-nya dashboard connect ke:

```
https://kinetic-untried-whoops.ngrok-free.dev
```

Kalau backend pindah host (misal deploy permanen, ganti tunnel ngrok, atau
testing ke localhost), override lewat environment variable sebelum
`streamlit run`:

```bash
export TARA_API_BASE_URL="http://localhost:8000"
streamlit run Home.py
```

## Struktur halaman

- `Home.py` — Dashboard ringkasan (jumlah data, status sistem, aktivitas terbaru)
- `pages/1_Data_Pelanggan_CBASE.py` — CRUD pelanggan + upload file CBASE
- `pages/2_Data_ODP.py` — CRUD ODP + upload file ODP
- `pages/3_Data_Prospek.py` — Lihat/edit/hapus data prospek hasil pipeline
- `pages/4_Riwayat_Aktivitas.py` — Log upload & perubahan manual
- `pages/5_User_Approval.py` — Approve/tolak/hapus user bot Telegram

## Endpoint backend yang dipakai

Semua di-prefix `/api/admin` di FastAPI (lihat `api/routers/admin.py`):

| Fitur | Endpoint |
|---|---|
| Upload ODP | `POST /api/admin/upload/odp` (file, sheet opsional) |
| Upload CBASE | `POST /api/admin/upload/cbase` (file) |
| CRUD ODP | `GET/POST /api/admin/odp`, `GET/PUT/DELETE /api/admin/odp/{id_odp}` |
| CRUD CBASE | `GET/POST /api/admin/cbase`, `GET/PUT/DELETE /api/admin/cbase/{nipnas}` |
| CRUD Prospek | `GET /api/admin/prospects`, `GET/PUT/DELETE /api/admin/prospects/{id}` |
| User bot | `GET /api/admin/users`, `PUT/DELETE /api/admin/users/{user_id}` |
| Statistik dashboard | `GET /api/admin/stats`, `GET /api/admin/activity` |

## Catatan penting

- Endpoint upload otomatis menjalankan ulang tahap silver + gold yang
  relevan (jadi hasilnya langsung kepakai bot & dashboard, tanpa perlu
  jalanin `python -m etl.run_pipeline` manual). Untuk data yang besar ini
  bisa makan waktu beberapa detik–menit; tunggu sampai spinner selesai.
- Tambah/edit/hapus manual langsung mengubah tabel `silver.*` (bukan
  `bronze.*`). Kalau nanti ada upload file baru yang membawa baris dengan
  ID yang sama, data upload akan menimpa hasil edit manual tersebut.
- `ngrok-skip-browser-warning: true` sudah otomatis dikirim di setiap
  request supaya tidak kena halaman interstitial ngrok free tier.
