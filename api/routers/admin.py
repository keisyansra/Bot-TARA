"""
Endpoint admin: upload file ODP/CBASE baru, otomatis load ke bronze,
lanjut trigger ulang pipeline Silver+Gold. Pengganti alur manual
"jalanin load_odp.py/load_cbase.py dari terminal, terus run_pipeline.py".
"""
import os
import io
import shutil
import uuid
import pandas as pd
from telegram import Bot
from pathlib import Path
from typing import Optional
from bot.services.user_service import (
    get_all_users,
    get_user_role,
    update_user_role_and_notify,
    delete_user as delete_bot_user,
)

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    HTTPException,
)

from pydantic import BaseModel
from sqlalchemy import text
from etl.common.db import get_engine

from etl.bronze.load_odp import load_odp_file
from etl.bronze.load_cbase import load_cbase_file
from etl.run_pipeline import main as run_pipeline

router = APIRouter()
engine = get_engine()
BOT_TOKEN = os.getenv("BOT_TOKEN")

ODP_UPLOAD_DIR = Path("data/incoming/odp")
CBASE_UPLOAD_DIR = Path("data/incoming/cbase")

# ODP sekarang selalu dikirim 1 file utuh buat seluruh Jatim Barat
# (bukan per-region lagi), jadi wilayah gak perlu ditanya user tiap
# upload -- cukup konstanta di sini.
ODP_WILAYAH_DEFAULT = "JATIM_BARAT"
UPLOAD_STATUS = {}


def _process_odp_upload(
    file_path: str,
    batch_id: str,
    sheet_name: Optional[str],
):
    print(
        f"[ADMIN] Mulai proses upload ODP, "
        f"batch {batch_id}"
    )

    UPLOAD_STATUS[batch_id] = {
        "batch_id": batch_id,
        "source": "odp",
        "status": "running",
        "row_count": None,
        "notes": "Data ODP sedang diproses server.",
    }

    try:
        load_odp_file(
            file_path=file_path,
            wilayah=ODP_WILAYAH_DEFAULT,
            batch_id=batch_id,
            sheet_name=sheet_name,
        )

        run_pipeline()

        with engine.connect() as conn:
            row_count = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM silver.odp_clean
                    """
                )
            ).scalar() or 0

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "odp",
            "status": "success",
            "row_count": int(row_count),
            "notes": (
                "Upload dan pemrosesan data ODP "
                "berhasil diselesaikan."
            ),
        }

        try:
            log_admin_activity(
                action="Memperbarui Data ODP",
                admin_name="Administrator",
                target_type="odp",
                target_id=batch_id,
                detail=(
                    f"Upload ODP berhasil diproses. "
                    f"Total data ODP: {int(row_count):,}."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Upload ODP: {log_exc}"
            )

        print(
            f"[ADMIN] Selesai proses upload ODP, "
            f"batch {batch_id}"
        )

    except Exception as exc:

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "odp",
            "status": "failed",
            "row_count": None,
            "notes": str(exc),
        }

        try:
            log_admin_activity(
                action="Memperbarui Data ODP",
                admin_name="Administrator",
                target_type="odp",
                target_id=batch_id,
                detail=(
                    f"Upload ODP gagal: {str(exc)}"
                ),
                status="failed",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Upload ODP gagal: {log_exc}"
            )

        print(
            f"[ADMIN] Gagal proses upload ODP, "
            f"batch {batch_id}: {exc}"
        )


def _process_cbase_upload(
    file_path: str,
    batch_id: str,
):
    print(f"[ADMIN] Mulai proses upload CBASE, batch {batch_id}")

    UPLOAD_STATUS[batch_id] = {
        "batch_id": batch_id,
        "source": "cbase",
        "status": "running",
        "row_count": None,
        "notes": None,
    }

    try:
        load_cbase_file(
            file_path=file_path,
            batch_id=batch_id,
        )

        run_pipeline()

        # Hitung total CBASE setelah pipeline selesai
        with engine.connect() as conn:
            row_count = conn.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM silver.cbase_clean"
                )
            ).scalar() or 0

        # Tandai proses upload berhasil
        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase",
            "status": "success",
            "row_count": int(row_count),
            "notes": "Upload dan pipeline CBASE berhasil diselesaikan.",
        }

        # Catat ke Riwayat Aktivitas.
        # Kalau log gagal, upload CBASE tetap dianggap berhasil.
        try:
            log_admin_activity(
                action="Memperbarui Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=batch_id,
                detail=(
                    f"Upload CBASE berhasil diproses. "
                    f"Total data pelanggan: {int(row_count):,}."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"untuk batch {batch_id}: {log_exc}"
            )

        print(
            f"[ADMIN] Selesai proses upload CBASE, "
            f"batch {batch_id}"
        )

    except Exception as exc:
        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase",
            "status": "failed",
            "row_count": None,
            "notes": str(exc),
        }

        # Catat kegagalan ke Riwayat Aktivitas.
        try:
            log_admin_activity(
                action="Memperbarui Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=batch_id,
                detail=f"Upload CBASE gagal: {str(exc)}",
                status="failed",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log gagal "
                f"untuk batch {batch_id}: {log_exc}"
            )

        print(
            f"[ADMIN] Gagal proses upload CBASE, "
            f"batch {batch_id}: {exc}"
        )

        raise

def _process_manual_cbase_create(
    batch_id: str,
    nipnas: str,
):
    print(
        f"[ADMIN] Mulai proses tambah CBASE manual, "
        f"batch {batch_id}, NIPNAS {nipnas}"
    )

    UPLOAD_STATUS[batch_id] = {
        "batch_id": batch_id,
        "source": "cbase_manual_create",
        "status": "running",
        "row_count": None,
        "notes": None,
    }

    try:
        # Tetap menggunakan pipeline resmi tim:
        # Bronze → Silver → Gold
        run_pipeline()

        # Pastikan data benar-benar lolos sampai Silver
        with engine.connect() as conn:
            created_row = conn.execute(
                text(
                    """
                    SELECT
                        nipnas,
                        standard_name,
                        witel_ho
                    FROM silver.cbase_clean
                    WHERE nipnas = :nipnas
                    LIMIT 1
                    """
                ),
                {
                    "nipnas": nipnas,
                },
            ).mappings().first()

        if created_row is None:
            raise RuntimeError(
                "Data sudah masuk Bronze, tetapi tidak ditemukan "
                "di Silver setelah pipeline selesai."
            )

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_create",
            "status": "success",
            "row_count": 1,
            "notes": (
                f"Data pelanggan NIPNAS {nipnas} "
                f"berhasil ditambahkan."
            ),
        }

        try:
            log_admin_activity(
                action="Menambah Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Menambahkan pelanggan "
                    f"{created_row.get('standard_name', '-')} "
                    f"dengan NIPNAS {nipnas}."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Create CBASE: {log_exc}"
            )

        print(
            f"[ADMIN] Selesai tambah CBASE manual, "
            f"batch {batch_id}"
        )

    except Exception as exc:
        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_create",
            "status": "failed",
            "row_count": None,
            "notes": str(exc),
        }

        try:
            log_admin_activity(
                action="Menambah Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Gagal menambahkan pelanggan "
                    f"NIPNAS {nipnas}: {str(exc)}"
                ),
                status="failed",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Create CBASE gagal: {log_exc}"
            )

        print(
            f"[ADMIN] Gagal tambah CBASE manual, "
            f"batch {batch_id}: {exc}"
        )

def _process_manual_cbase_update(
    batch_id: str,
    nipnas: str,
):
    print(
        f"[ADMIN] Mulai proses edit CBASE manual, "
        f"batch {batch_id}, NIPNAS {nipnas}"
    )

    UPLOAD_STATUS[batch_id] = {
        "batch_id": batch_id,
        "source": "cbase_manual_update",
        "status": "running",
        "row_count": None,
        "notes": None,
    }

    try:
        # Tetap memakai pipeline resmi tim
        run_pipeline()

        with engine.connect() as conn:
            updated_row = conn.execute(
                text(
                    """
                    SELECT
                        nipnas,
                        standard_name,
                        witel_ho
                    FROM silver.cbase_clean
                    WHERE nipnas = :nipnas
                    LIMIT 1
                    """
                ),
                {
                    "nipnas": nipnas,
                },
            ).mappings().first()

        if updated_row is None:
            raise RuntimeError(
                "Data update sudah masuk Bronze, tetapi "
                "tidak ditemukan di Silver setelah pipeline."
            )

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_update",
            "status": "success",
            "row_count": 1,
            "notes": (
                f"Data pelanggan NIPNAS {nipnas} "
                f"berhasil diperbarui."
            ),
        }

        try:
            log_admin_activity(
                action="Memperbarui Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Memperbarui pelanggan "
                    f"{updated_row.get('standard_name', '-')} "
                    f"dengan NIPNAS {nipnas}."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Update CBASE: {log_exc}"
            )

        print(
            f"[ADMIN] Selesai edit CBASE manual, "
            f"batch {batch_id}"
        )

    except Exception as exc:
        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_update",
            "status": "failed",
            "row_count": None,
            "notes": str(exc),
        }

        try:
            log_admin_activity(
                action="Memperbarui Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Gagal memperbarui pelanggan "
                    f"NIPNAS {nipnas}: {str(exc)}"
                ),
                status="failed",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Update CBASE gagal: {log_exc}"
            )

        print(
            f"[ADMIN] Gagal edit CBASE manual, "
            f"batch {batch_id}: {exc}"
        )

@router.post("/upload/odp")
async def upload_odp(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    sheet: Optional[str] = Form(None, description="Nama sheet Excel, opsional -- kosongin kalau file cuma 1 sheet"),
):
    ODP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = ODP_UPLOAD_DIR / file.filename

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    batch_id = f"web-{uuid.uuid4().hex[:8]}"

    UPLOAD_STATUS[batch_id] = {
        "batch_id": batch_id,
        "source": "odp",
        "status": "queued",
        "row_count": None,
        "notes": "File diterima dan menunggu diproses.",
    }

    background_tasks.add_task(
        _process_odp_upload,
        file_path=str(dest),
        batch_id=batch_id,
        sheet_name=sheet,
    )

    return {
        "status": "uploaded_and_queued",
        "source": "odp",
        "filename": file.filename,
        "wilayah": ODP_WILAYAH_DEFAULT,
        "batch_id": batch_id,
    }

@router.post("/upload/cbase")
async def upload_cbase(
    background_tasks: BackgroundTasks,
    file: UploadFile,
):
    CBASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = CBASE_UPLOAD_DIR / file.filename

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    batch_id = f"web-{uuid.uuid4().hex[:8]}"

    UPLOAD_STATUS[batch_id] = {
    "batch_id": batch_id,
    "source": "cbase",
    "status": "queued",
    "row_count": None,
    "notes": "File diterima dan menunggu diproses.",
}
    
    background_tasks.add_task(
        _process_cbase_upload,
        file_path=str(dest),
        batch_id=batch_id,
    )

    return {
        "status": "uploaded_and_queued",
        "source": "cbase",
        "filename": file.filename,
        "batch_id": batch_id,
    }

@router.get("/upload/status/{batch_id}")
def get_upload_status(batch_id: str):

    data = UPLOAD_STATUS.get(batch_id)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Status proses upload tidak ditemukan."
        )

    return {
        "status": "success",
        "data": data,
    }

@router.get("/stats")
def get_stats():
    with engine.connect() as conn:
        total_cbase = conn.execute(
            text("SELECT COUNT(*) FROM silver.cbase_clean")
        ).scalar() or 0

        total_odp = conn.execute(
            text("SELECT COUNT(*) FROM silver.odp_clean")
        ).scalar() or 0

        total_prospects = conn.execute(
            text("SELECT COUNT(*) FROM silver.prospect_clean")
        ).scalar() or 0

        last_cbase_update = conn.execute(
            text("SELECT MAX(cleaned_at) FROM silver.cbase_clean")
        ).scalar()

        last_odp_update = conn.execute(
            text("SELECT MAX(cleaned_at) FROM silver.odp_clean")
        ).scalar()

    updates = [
        x for x in [
            last_cbase_update,
            last_odp_update,
        ]
        if x is not None
    ]

    last_update = max(updates) if updates else None

    return {
        "status": "success",
        "data": {
            "total_cbase": total_cbase,
            "total_odp": total_odp,
            "total_prospects": total_prospects,

            "cbase_count": total_cbase,
            "odp_count": total_odp,
            "prospect_count": total_prospects,

            "last_cbase_update": (
                last_cbase_update.isoformat()
                if last_cbase_update
                else None
            ),

            "last_odp_update": (
                last_odp_update.isoformat()
                if last_odp_update
                else None
            ),

            "last_update": (
                last_update.isoformat()
                if last_update
                else None
            ),
        }
    }

def init_cbase_exclusion_table():
    """Menyimpan NIPNAS CBASE yang dinonaktifkan dari dashboard."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS admin_cbase_exclusions (
                    nipnas TEXT PRIMARY KEY,
                    excluded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

def _process_manual_cbase_delete(
    batch_id: str,
    nipnas: str,
    standard_name: str,
):
    print(
        f"[ADMIN] Mulai proses hapus CBASE manual, "
        f"batch {batch_id}, NIPNAS {nipnas}"
    )

    UPLOAD_STATUS[batch_id] = {
        "batch_id": batch_id,
        "source": "cbase_manual_delete",
        "status": "running",
        "row_count": None,
        "notes": None,
    }

    silver_deleted = False

    try:
        init_cbase_exclusion_table()

        # Tandai NIPNAS sebagai tidak aktif.
        # Bronze tetap disimpan sebagai histori.
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO admin_cbase_exclusions (
                        nipnas
                    )
                    VALUES (
                        :nipnas
                    )
                    ON CONFLICT (nipnas) DO NOTHING
                    """
                ),
                {
                    "nipnas": nipnas,
                },
            )

        # Jalankan pipeline resmi tim.
        # Matcher sudah diatur agar tidak menggunakan
        # NIPNAS yang masuk exclusion.
        run_pipeline()

        # Pastikan tidak ada lagi referensi matching
        # yang masih menunjuk ke NIPNAS tersebut.
        # Setelah itu baru hapus dari Silver aktif.
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE silver.prospect_customer_match
                    SET
                        matched_nipnas = NULL,
                        matched_standard_name = NULL,
                        matched_name_normalized = NULL,
                        match_score = 0,
                        match_status = 'NO_MATCH',
                        matched_at = now()
                    WHERE matched_nipnas = :nipnas
                    """
                ),
                {
                    "nipnas": nipnas,
                },
            )

            conn.execute(
                text(
                    """
                    DELETE FROM silver.cbase_clean
                    WHERE nipnas = :nipnas
                    """
                ),
                {
                    "nipnas": nipnas,
                },
            )

        silver_deleted = True

        # Verifikasi data sudah tidak ada di Silver aktif.
        with engine.connect() as conn:
            remaining = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM silver.cbase_clean
                    WHERE nipnas = :nipnas
                    """
                ),
                {
                    "nipnas": nipnas,
                },
            ).scalar() or 0

        if int(remaining) > 0:
            raise RuntimeError(
                "Data pelanggan masih ditemukan di Silver "
                "setelah proses penghapusan."
            )

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_delete",
            "status": "success",
            "row_count": 1,
            "notes": (
                f"Data pelanggan NIPNAS {nipnas} "
                f"berhasil dihapus dari data aktif."
            ),
        }

        try:
            log_admin_activity(
                action="Menghapus Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Menghapus pelanggan "
                    f"{standard_name} "
                    f"dengan NIPNAS {nipnas} "
                    f"dari data aktif."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Delete CBASE: {log_exc}"
            )

        print(
            f"[ADMIN] Selesai hapus CBASE manual, "
            f"batch {batch_id}"
        )

    except Exception as exc:
        # Kalau data Silver belum terhapus,
        # batalkan exclusion agar data tetap aktif.
        if not silver_deleted:
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            """
                            DELETE FROM admin_cbase_exclusions
                            WHERE nipnas = :nipnas
                            """
                        ),
                        {
                            "nipnas": nipnas,
                        },
                    )
            except Exception as rollback_exc:
                print(
                    f"[ADMIN] Gagal membatalkan exclusion "
                    f"NIPNAS {nipnas}: {rollback_exc}"
                )

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_delete",
            "status": "failed",
            "row_count": None,
            "notes": str(exc),
        }

        try:
            log_admin_activity(
                action="Menghapus Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Gagal menghapus pelanggan "
                    f"NIPNAS {nipnas}: {str(exc)}"
                ),
                status="failed",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Delete CBASE gagal: {log_exc}"
            )

        print(
            f"[ADMIN] Gagal hapus CBASE manual, "
            f"batch {batch_id}: {exc}"
        )

class CBaseCreate(BaseModel):
    nipnas: str
    standard_name: str
    witel_ho: str = "TELKOM JATIM BARAT"


@router.post("/cbase", status_code=201)
def create_cbase(
    payload: CBaseCreate,
):
    from etl.common.text import normalize_name

    nipnas = payload.nipnas.strip()
    standard_name = payload.standard_name.strip()
    witel_ho = payload.witel_ho.strip().upper()

    # --------------------------------------------------------
    # VALIDASI
    # --------------------------------------------------------

    if not nipnas:
        raise HTTPException(
            status_code=422,
            detail="NIPNAS wajib diisi.",
        )

    if not standard_name:
        raise HTTPException(
            status_code=422,
            detail="Nama pelanggan wajib diisi.",
        )

    if witel_ho != "TELKOM JATIM BARAT":
        raise HTTPException(
            status_code=422,
            detail="Witel harus TELKOM JATIM BARAT.",
        )

    init_cbase_exclusion_table()

    # --------------------------------------------------------
    # CEK DATA AKTIF
    # --------------------------------------------------------

    with engine.connect() as conn:
        existing = conn.execute(
            text(
                """
                SELECT nipnas
                FROM silver.cbase_clean
                WHERE nipnas = :nipnas
                LIMIT 1
                """
            ),
            {"nipnas": nipnas},
        ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"NIPNAS {nipnas} sudah tersedia. "
                "Gunakan fitur Edit untuk memperbarui data."
            ),
        )

    batch_id = (
        f"manual-cbase-{uuid.uuid4().hex[:8]}"
    )

    nama_normalized = normalize_name(standard_name)

    try:
        with engine.begin() as conn:

            # Jika NIPNAS pernah dihapus, aktifkan kembali
            # ketika dibuat ulang oleh admin.
            conn.execute(
                text(
                    """
                    DELETE FROM admin_cbase_exclusions
                    WHERE nipnas = :nipnas
                    """
                ),
                {"nipnas": nipnas},
            )

            # Simpan histori ke Bronze
            conn.execute(
                text(
                    """
                    INSERT INTO bronze.cbase_raw (
                        nipnas,
                        witel_ho,
                        standard_name,
                        _source_file,
                        _batch_id
                    )
                    VALUES (
                        :nipnas,
                        :witel_ho,
                        :standard_name,
                        :source_file,
                        :batch_id
                    )
                    """
                ),
                {
                    "nipnas": nipnas,
                    "witel_ho": "TELKOM JATIM BARAT",
                    "standard_name": standard_name,
                    "source_file": "dashboard_manual_create",
                    "batch_id": batch_id,
                },
            )

            # Masukkan langsung SATU pelanggan ke Silver.
            conn.execute(
                text(
                    """
                    INSERT INTO silver.cbase_clean (
                        nipnas,
                        witel_ho,
                        standard_name,
                        nama_normalized,
                        batch_id,
                        cleaned_at
                    )
                    VALUES (
                        :nipnas,
                        :witel_ho,
                        :standard_name,
                        :nama_normalized,
                        :batch_id,
                        NOW()
                    )
                    ON CONFLICT (nipnas)
                    DO UPDATE SET
                        witel_ho = EXCLUDED.witel_ho,
                        standard_name = EXCLUDED.standard_name,
                        nama_normalized = EXCLUDED.nama_normalized,
                        batch_id = EXCLUDED.batch_id,
                        cleaned_at = NOW()
                    """
                ),
                {
                    "nipnas": nipnas,
                    "witel_ho": "TELKOM JATIM BARAT",
                    "standard_name": standard_name,
                    "nama_normalized": nama_normalized,
                    "batch_id": batch_id,
                },
            )

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_create",
            "status": "success",
            "row_count": 1,
            "notes": (
                f"Data pelanggan NIPNAS {nipnas} "
                f"berhasil ditambahkan."
            ),
        }

        try:
            log_admin_activity(
                action="Menambah Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Menambahkan pelanggan "
                    f"{standard_name} "
                    f"dengan NIPNAS {nipnas}."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Create CBASE: {log_exc}"
            )

        print(
            f"[ADMIN] Tambah CBASE cepat selesai, "
            f"batch {batch_id}, NIPNAS {nipnas}"
        )

        return {
            "status": "success",
            "message": "Data pelanggan berhasil ditambahkan.",
            "batch_id": batch_id,
            "nipnas": nipnas,
            "standard_name": standard_name,
        }

    except Exception as exc:

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_create",
            "status": "failed",
            "row_count": None,
            "notes": str(exc),
        }

        try:
            log_admin_activity(
                action="Menambah Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Gagal menambahkan pelanggan "
                    f"NIPNAS {nipnas}: {str(exc)}"
                ),
                status="failed",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Create CBASE gagal: {log_exc}"
            )

        print(
            f"[ADMIN] Gagal tambah CBASE cepat "
            f"NIPNAS {nipnas}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Gagal menambahkan data pelanggan.",
        )

class CBaseUpdate(BaseModel):
    standard_name: str
    witel_ho: str = "TELKOM JATIM BARAT"


@router.put("/cbase/{nipnas}", status_code=200)
def update_cbase(
    nipnas: str,
    payload: CBaseUpdate,
):
    from etl.common.text import normalize_name

    nipnas = nipnas.strip()
    standard_name = payload.standard_name.strip()
    witel_ho = payload.witel_ho.strip().upper()

    # --------------------------------------------------------
    # VALIDASI
    # --------------------------------------------------------

    if not nipnas:
        raise HTTPException(
            status_code=422,
            detail="NIPNAS wajib diisi.",
        )

    if not standard_name:
        raise HTTPException(
            status_code=422,
            detail="Nama pelanggan wajib diisi.",
        )

    if witel_ho != "TELKOM JATIM BARAT":
        raise HTTPException(
            status_code=422,
            detail="Witel harus TELKOM JATIM BARAT.",
        )

    # --------------------------------------------------------
    # CEK DATA EXISTING
    # --------------------------------------------------------

    with engine.connect() as conn:
        existing = conn.execute(
            text(
                """
                SELECT
                    nipnas,
                    standard_name,
                    witel_ho
                FROM silver.cbase_clean
                WHERE nipnas = :nipnas
                LIMIT 1
                """
            ),
            {"nipnas": nipnas},
        ).mappings().first()

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Data pelanggan dengan NIPNAS "
                f"{nipnas} tidak ditemukan."
            ),
        )

    # --------------------------------------------------------
    # CEK APAKAH ADA PERUBAHAN
    # --------------------------------------------------------

    if (
        str(existing.get("standard_name", "")).strip()
        == standard_name
        and
        str(existing.get("witel_ho", "")).strip().upper()
        == witel_ho
    ):
        raise HTTPException(
            status_code=409,
            detail="Tidak ada perubahan data yang perlu disimpan.",
        )

    batch_id = (
        f"manual-cbase-update-{uuid.uuid4().hex[:8]}"
    )

    nama_normalized = normalize_name(standard_name)

    # --------------------------------------------------------
    # SIMPAN BRONZE + UPDATE 1 DATA SILVER
    # --------------------------------------------------------

    try:
        with engine.begin() as conn:

            # Simpan riwayat perubahan ke Bronze
            conn.execute(
                text(
                    """
                    INSERT INTO bronze.cbase_raw (
                        nipnas,
                        witel_ho,
                        standard_name,
                        _source_file,
                        _batch_id
                    )
                    VALUES (
                        :nipnas,
                        :witel_ho,
                        :standard_name,
                        :source_file,
                        :batch_id
                    )
                    """
                ),
                {
                    "nipnas": nipnas,
                    "witel_ho": "TELKOM JATIM BARAT",
                    "standard_name": standard_name,
                    "source_file": "dashboard_manual_update",
                    "batch_id": batch_id,
                },
            )

            # Update langsung SATU pelanggan di Silver
            conn.execute(
                text(
                    """
                    UPDATE silver.cbase_clean
                    SET
                        standard_name = :standard_name,
                        nama_normalized = :nama_normalized,
                        witel_ho = :witel_ho,
                        batch_id = :batch_id,
                        cleaned_at = NOW()
                    WHERE nipnas = :nipnas
                    """
                ),
                {
                    "nipnas": nipnas,
                    "standard_name": standard_name,
                    "nama_normalized": nama_normalized,
                    "witel_ho": "TELKOM JATIM BARAT",
                    "batch_id": batch_id,
                },
            )

            # Sinkronkan nama pada hasil matching yang
            # memang sudah menunjuk NIPNAS ini.
            conn.execute(
                text(
                    """
                    UPDATE silver.prospect_customer_match
                    SET
                        matched_standard_name = :standard_name,
                        matched_name_normalized = :nama_normalized
                    WHERE matched_nipnas = :nipnas
                    """
                ),
                {
                    "nipnas": nipnas,
                    "standard_name": standard_name,
                    "nama_normalized": nama_normalized,
                },
            )

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_update",
            "status": "success",
            "row_count": 1,
            "notes": (
                f"Data pelanggan NIPNAS {nipnas} "
                f"berhasil diperbarui."
            ),
        }

        try:
            log_admin_activity(
                action="Memperbarui Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Memperbarui pelanggan "
                    f"{standard_name} "
                    f"dengan NIPNAS {nipnas}."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Update CBASE: {log_exc}"
            )

        print(
            f"[ADMIN] Edit CBASE cepat selesai, "
            f"batch {batch_id}, NIPNAS {nipnas}"
        )

        return {
            "status": "success",
            "message": "Data pelanggan berhasil diperbarui.",
            "batch_id": batch_id,
            "nipnas": nipnas,
            "standard_name": standard_name,
        }

    except Exception as exc:
        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_update",
            "status": "failed",
            "row_count": None,
            "notes": str(exc),
        }

        try:
            log_admin_activity(
                action="Memperbarui Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Gagal memperbarui pelanggan "
                    f"NIPNAS {nipnas}: {str(exc)}"
                ),
                status="failed",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Update CBASE gagal: {log_exc}"
            )

        print(
            f"[ADMIN] Gagal edit CBASE cepat "
            f"NIPNAS {nipnas}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Gagal memperbarui data pelanggan.",
        )

@router.delete("/cbase/{nipnas}", status_code=200)
def delete_cbase(
    nipnas: str,
):
    nipnas = nipnas.strip()

    if not nipnas:
        raise HTTPException(
            status_code=422,
            detail="NIPNAS wajib diisi.",
        )

    init_cbase_exclusion_table()

    # --------------------------------------------------------
    # CEK DATA
    # --------------------------------------------------------

    with engine.connect() as conn:

        existing = conn.execute(
            text(
                """
                SELECT
                    nipnas,
                    standard_name,
                    witel_ho
                FROM silver.cbase_clean
                WHERE nipnas = :nipnas
                LIMIT 1
                """
            ),
            {
                "nipnas": nipnas,
            },
        ).mappings().first()

        excluded = conn.execute(
            text(
                """
                SELECT nipnas
                FROM admin_cbase_exclusions
                WHERE nipnas = :nipnas
                LIMIT 1
                """
            ),
            {
                "nipnas": nipnas,
            },
        ).first()

    if existing is None:

        if excluded:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Data pelanggan dengan NIPNAS "
                    f"{nipnas} sudah tidak aktif."
                ),
            )

        raise HTTPException(
            status_code=404,
            detail=(
                f"Data pelanggan dengan NIPNAS "
                f"{nipnas} tidak ditemukan."
            ),
        )

    standard_name = (
        existing.get("standard_name")
        or "-"
    )

    batch_id = (
        f"manual-cbase-delete-{uuid.uuid4().hex[:8]}"
    )

    try:

        # Semua dalam satu transaction.
        # Kalau salah satu gagal, semuanya rollback.
        with engine.begin() as conn:

            # Simpan exclusion agar data lama di Bronze
            # tidak muncul kembali saat pipeline berikutnya.
            conn.execute(
                text(
                    """
                    INSERT INTO admin_cbase_exclusions (
                        nipnas
                    )
                    VALUES (
                        :nipnas
                    )
                    ON CONFLICT (nipnas) DO NOTHING
                    """
                ),
                {
                    "nipnas": nipnas,
                },
            )

            # Putuskan referensi matching terlebih dahulu
            # agar tidak melanggar foreign key.
            conn.execute(
                text(
                    """
                    UPDATE silver.prospect_customer_match
                    SET
                        matched_nipnas = NULL,
                        matched_standard_name = NULL,
                        matched_name_normalized = NULL,
                        match_score = 0,
                        match_status = 'NO_MATCH',
                        matched_at = NOW()
                    WHERE matched_nipnas = :nipnas
                    """
                ),
                {
                    "nipnas": nipnas,
                },
            )

            # Hapus dari daftar CBASE aktif.
            conn.execute(
                text(
                    """
                    DELETE FROM silver.cbase_clean
                    WHERE nipnas = :nipnas
                    """
                ),
                {
                    "nipnas": nipnas,
                },
            )

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_delete",
            "status": "success",
            "row_count": 1,
            "notes": (
                f"Data pelanggan NIPNAS {nipnas} "
                f"berhasil dihapus dari data aktif."
            ),
        }

        try:
            log_admin_activity(
                action="Menghapus Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Menghapus pelanggan "
                    f"{standard_name} "
                    f"dengan NIPNAS {nipnas} "
                    f"dari data aktif."
                ),
                status="success",
            )

        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Delete CBASE: {log_exc}"
            )

        print(
            f"[ADMIN] Hapus CBASE cepat selesai, "
            f"batch {batch_id}, NIPNAS {nipnas}"
        )

        return {
            "status": "success",
            "message": (
                "Data pelanggan berhasil dihapus "
                "dari data aktif."
            ),
            "batch_id": batch_id,
            "nipnas": nipnas,
        }

    except Exception as exc:

        UPLOAD_STATUS[batch_id] = {
            "batch_id": batch_id,
            "source": "cbase_manual_delete",
            "status": "failed",
            "row_count": None,
            "notes": str(exc),
        }

        try:
            log_admin_activity(
                action="Menghapus Data CBASE",
                admin_name="Administrator",
                target_type="cbase",
                target_id=nipnas,
                detail=(
                    f"Gagal menghapus pelanggan "
                    f"NIPNAS {nipnas}: {str(exc)}"
                ),
                status="failed",
            )

        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity log "
                f"Delete CBASE gagal: {log_exc}"
            )

        print(
            f"[ADMIN] Gagal hapus CBASE cepat "
            f"NIPNAS {nipnas}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Gagal menghapus data pelanggan.",
        )

# ============================================================
# CRUD MANUAL: DATA ODP
# ============================================================

class ODPUpdate(BaseModel):
    odp_name: str
    latitude: float
    longitude: float
    available_port: int = 0
    used_port: int = 0
    total_port: int = 0
    occupancy_status: Optional[str] = None
    witel: Optional[str] = None


class ODPCreate(ODPUpdate):
    id_odp: int


def init_odp_exclusion_table():
    """
    Menyimpan ID ODP yang dinonaktifkan dari dashboard
    supaya tidak muncul kembali saat pipeline dijalankan.
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS admin_odp_exclusions (
                    id_odp BIGINT PRIMARY KEY,
                    excluded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )


def _validate_odp_payload(payload):
    odp_name = payload.odp_name.strip()

    if not odp_name:
        raise HTTPException(
            status_code=422,
            detail="Kode / Nama ODP wajib diisi.",
        )

    latitude = float(payload.latitude)
    longitude = float(payload.longitude)

    # Batas wajar data Jawa Timur
    if not (-9.5 <= latitude <= -6.5):
        raise HTTPException(
            status_code=422,
            detail="Latitude berada di luar jangkauan Jawa Timur.",
        )

    if not (110.5 <= longitude <= 114.5):
        raise HTTPException(
            status_code=422,
            detail="Longitude berada di luar jangkauan Jawa Timur.",
        )

    available_port = int(payload.available_port)
    used_port = int(payload.used_port)
    total_port = int(payload.total_port)

    if (
        available_port < 0
        or used_port < 0
        or total_port < 0
    ):
        raise HTTPException(
            status_code=422,
            detail="Jumlah port tidak boleh bernilai negatif.",
        )

    if used_port > total_port:
        raise HTTPException(
            status_code=422,
            detail="Port terpakai tidak boleh melebihi kapasitas total.",
        )

    occupancy_status = (
        payload.occupancy_status.strip().upper()
        if payload.occupancy_status
        else None
    )

    witel = (
        payload.witel.strip()
        if payload.witel
        else None
    )

    return {
        "odp_name": odp_name,
        "latitude": latitude,
        "longitude": longitude,
        "available_port": available_port,
        "used_port": used_port,
        "total_port": total_port,
        "occupancy_status": occupancy_status,
        "witel": witel,
    }


# ============================================================
# CREATE ODP
# ============================================================

@router.post("/odp", status_code=201)
def create_odp(payload: ODPCreate):

    id_odp = int(payload.id_odp)

    if id_odp <= 0:
        raise HTTPException(
            status_code=422,
            detail="ID ODP harus lebih dari 0.",
        )

    values = _validate_odp_payload(payload)

    init_odp_exclusion_table()

    with engine.connect() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id_odp
                FROM silver.odp_clean
                WHERE id_odp = :id_odp
                LIMIT 1
                """
            ),
            {"id_odp": id_odp},
        ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"ODP dengan ID {id_odp} sudah tersedia. "
                "Gunakan fitur Edit untuk memperbarui data."
            ),
        )

    batch_id = (
        f"manual-odp-create-{uuid.uuid4().hex[:8]}"
    )

    try:
        with engine.begin() as conn:

            # Jika sebelumnya pernah dihapus,
            # aktifkan kembali ID ini.
            conn.execute(
                text(
                    """
                    DELETE FROM admin_odp_exclusions
                    WHERE id_odp = :id_odp
                    """
                ),
                {"id_odp": id_odp},
            )

            conn.execute(
                text(
                    """
                    INSERT INTO silver.odp_clean (
                        id_odp,
                        odp_name,
                        latitude,
                        longitude,
                        geom,
                        available_port,
                        used_port,
                        rsv_port,
                        rsk_port,
                        total_port,
                        occupancy_status,
                        witel,
                        kabupaten_kota,
                        provinsi,
                        wilayah_file,
                        batch_id,
                        cleaned_at
                    )
                    VALUES (
                        :id_odp,
                        :odp_name,
                        :latitude,
                        :longitude,
                        ST_SetSRID(
                            ST_MakePoint(
                                :longitude,
                                :latitude
                            ),
                            4326
                        )::geography,
                        :available_port,
                        :used_port,
                        0,
                        0,
                        :total_port,
                        :occupancy_status,
                        :witel,
                        NULL,
                        'JAWA TIMUR',
                        :wilayah_file,
                        :batch_id,
                        NOW()
                    )
                    """
                ),
                {
                    "id_odp": id_odp,
                    **values,
                    "wilayah_file": (
                        values["witel"]
                        or "DASHBOARD_MANUAL"
                    ),
                    "batch_id": batch_id,
                },
            )

        try:
            log_admin_activity(
                action="Menambah Data ODP",
                admin_name="Administrator",
                target_type="odp",
                target_id=str(id_odp),
                detail=(
                    f"Menambahkan ODP "
                    f"{values['odp_name']} "
                    f"dengan ID {id_odp}."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity "
                f"Create ODP: {log_exc}"
            )

        return {
            "status": "success",
            "message": "Data ODP berhasil ditambahkan.",
            "id_odp": id_odp,
            "batch_id": batch_id,
        }

    except Exception as exc:
        print(
            f"[ADMIN] Gagal tambah ODP "
            f"{id_odp}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Gagal menambahkan data ODP: {str(exc)}",
        )


# ============================================================
# UPDATE ODP
# ============================================================

@router.put("/odp/{id_odp}", status_code=200)
def update_odp(
    id_odp: int,
    payload: ODPUpdate,
):

    values = _validate_odp_payload(payload)

    with engine.connect() as conn:
        existing = conn.execute(
            text(
                """
                SELECT
                    id_odp,
                    odp_name
                FROM silver.odp_clean
                WHERE id_odp = :id_odp
                LIMIT 1
                """
            ),
            {"id_odp": id_odp},
        ).mappings().first()

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"ODP dengan ID {id_odp} tidak ditemukan.",
        )

    batch_id = (
        f"manual-odp-update-{uuid.uuid4().hex[:8]}"
    )

    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE silver.odp_clean
                    SET
                        odp_name = :odp_name,
                        latitude = :latitude,
                        longitude = :longitude,

                        geom = ST_SetSRID(
                            ST_MakePoint(
                                :longitude,
                                :latitude
                            ),
                            4326
                        )::geography,

                        available_port = :available_port,
                        used_port = :used_port,
                        total_port = :total_port,
                        occupancy_status = :occupancy_status,
                        witel = :witel,
                        wilayah_file = :wilayah_file,
                        batch_id = :batch_id,
                        cleaned_at = NOW()

                    WHERE id_odp = :id_odp
                    """
                ),
                {
                    "id_odp": id_odp,
                    **values,
                    "wilayah_file": (
                        values["witel"]
                        or "DASHBOARD_MANUAL"
                    ),
                    "batch_id": batch_id,
                },
            )

        try:
            log_admin_activity(
                action="Memperbarui Data ODP",
                admin_name="Administrator",
                target_type="odp",
                target_id=str(id_odp),
                detail=(
                    f"Memperbarui ODP "
                    f"{values['odp_name']} "
                    f"dengan ID {id_odp}."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity "
                f"Update ODP: {log_exc}"
            )

        return {
            "status": "success",
            "message": "Data ODP berhasil diperbarui.",
            "id_odp": id_odp,
            "batch_id": batch_id,
        }

    except Exception as exc:
        print(
            f"[ADMIN] Gagal update ODP "
            f"{id_odp}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Gagal memperbarui data ODP: {str(exc)}",
        )


# ============================================================
# DELETE ODP
# ============================================================

@router.delete("/odp/{id_odp}", status_code=200)
def delete_odp(id_odp: int):

    init_odp_exclusion_table()

    with engine.connect() as conn:

        existing = conn.execute(
            text(
                """
                SELECT
                    id_odp,
                    odp_name
                FROM silver.odp_clean
                WHERE id_odp = :id_odp
                LIMIT 1
                """
            ),
            {"id_odp": id_odp},
        ).mappings().first()

        excluded = conn.execute(
            text(
                """
                SELECT id_odp
                FROM admin_odp_exclusions
                WHERE id_odp = :id_odp
                LIMIT 1
                """
            ),
            {"id_odp": id_odp},
        ).first()

    if existing is None:

        if excluded:
            raise HTTPException(
                status_code=409,
                detail="Data ODP sudah tidak aktif.",
            )

        raise HTTPException(
            status_code=404,
            detail=f"ODP dengan ID {id_odp} tidak ditemukan.",
        )

    odp_name = existing.get("odp_name") or "-"

    batch_id = (
        f"manual-odp-delete-{uuid.uuid4().hex[:8]}"
    )

    try:
        with engine.begin() as conn:

            # Tandai agar tidak muncul lagi setelah pipeline.
            conn.execute(
                text(
                    """
                    INSERT INTO admin_odp_exclusions (
                        id_odp
                    )
                    VALUES (
                        :id_odp
                    )
                    ON CONFLICT (id_odp) DO NOTHING
                    """
                ),
                {"id_odp": id_odp},
            )

            conn.execute(
                text(
                    """
                    DELETE FROM silver.odp_clean
                    WHERE id_odp = :id_odp
                    """
                ),
                {"id_odp": id_odp},
            )

        try:
            log_admin_activity(
                action="Menghapus Data ODP",
                admin_name="Administrator",
                target_type="odp",
                target_id=str(id_odp),
                detail=(
                    f"Menghapus ODP "
                    f"{odp_name} "
                    f"dengan ID {id_odp} "
                    f"dari data aktif."
                ),
                status="success",
            )
        except Exception as log_exc:
            print(
                f"[ADMIN] Gagal mencatat activity "
                f"Delete ODP: {log_exc}"
            )

        return {
            "status": "success",
            "message": "Data ODP berhasil dihapus.",
            "id_odp": id_odp,
            "batch_id": batch_id,
        }

    except Exception as exc:
        print(
            f"[ADMIN] Gagal hapus ODP "
            f"{id_odp}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Gagal menghapus data ODP: {str(exc)}",
        )

# ============================================================
# READ-ONLY: DATA PELANGGAN / CBASE
# ============================================================

@router.get("/cbase")
def list_cbase(
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
):
    init_cbase_exclusion_table()

    page = max(page, 1)
    page_size = max(1, min(page_size, 100))

    where = [
        """
        NOT EXISTS (
            SELECT 1
            FROM admin_cbase_exclusions e
            WHERE e.nipnas = silver.cbase_clean.nipnas
        )
        """
    ]
    params = {}

    if q:
        where.append(
            "(nipnas ILIKE :q OR standard_name ILIKE :q)"
        )
        params["q"] = f"%{q}%"

    where_clause = " AND ".join(where)

    with engine.connect() as conn:
        total = conn.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM silver.cbase_clean
                WHERE {where_clause}
                """
            ),
            params,
        ).scalar() or 0

        params_page = {
            **params,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }

        rows = conn.execute(
            text(
                f"""
                SELECT
                    nipnas,
                    witel_ho,
                    standard_name,
                    total_sustain,
                    revenue_ge_75jt,
                    eksisting_nik_mapping,
                    eksisting_nama_mapping,
                    cleaned_at
                FROM silver.cbase_clean
                WHERE {where_clause}
                ORDER BY cleaned_at DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            params_page,
        ).mappings().all()

    return {
        "status": "success",
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [dict(row) for row in rows],
    }


# ============================================================
# READ-ONLY: DATA ODP
# ============================================================

@router.get("/odp")
def list_odp(
    q: Optional[str] = None,
    witel: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
):
    page = max(page, 1)
    page_size = max(1, min(page_size, 100))

    where = ["1=1"]
    params = {}

    if q:
        where.append(
            "(CAST(id_odp AS TEXT) ILIKE :q OR odp_name ILIKE :q)"
        )
        params["q"] = f"%{q}%"

    if witel:
        where.append("witel = :witel")
        params["witel"] = witel

    if status:
        where.append("occupancy_status = :status")
        params["status"] = status

    where_clause = " AND ".join(where)

    with engine.connect() as conn:
        total = conn.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM silver.odp_clean
                WHERE {where_clause}
                """
            ),
            params,
        ).scalar() or 0

        params_page = {
            **params,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }

        rows = conn.execute(
            text(
                f"""
                SELECT
                    id_odp,
                    odp_name,
                    latitude,
                    longitude,
                    available_port,
                    used_port,
                    rsv_port,
                    rsk_port,
                    total_port,
                    occupancy_status,
                    witel,
                    kabupaten_kota,
                    provinsi,
                    cleaned_at
                FROM silver.odp_clean
                WHERE {where_clause}
                ORDER BY cleaned_at DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            params_page,
        ).mappings().all()

    return {
        "status": "success",
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [dict(row) for row in rows],
    }


# ============================================================
# READ-ONLY: DAFTAR WITEL ODP
# ============================================================

@router.get("/odp/witel-list")
def list_odp_witel():
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT DISTINCT witel
                FROM silver.odp_clean
                WHERE witel IS NOT NULL
                  AND TRIM(witel) <> ''
                ORDER BY witel
                """
            )
        ).all()

    return {
        "status": "success",
        "data": [row[0] for row in rows],
    }

# ============================================================
# READ-ONLY: USER BOT TELEGRAM
# ============================================================

@router.get("/users")
def list_users(role: Optional[str] = None):
    return {
        "status": "success",
        "data": get_all_users(role)
    }

class UserRoleUpdate(BaseModel):
    role: str
    admin_id: Optional[str] = None
    admin_name: Optional[str] = "Administrator"


@router.put("/users/{user_id}")
async def set_user_role(
    user_id: int,
    payload: UserRoleUpdate,
):
    allowed_roles = {
        "pending",
        "sales",
        "admin",
        "rejected",
    }

    if payload.role not in allowed_roles:
        raise HTTPException(
            status_code=422,
            detail="Role tidak valid."
        )

    current_role = get_user_role(user_id)

    if current_role is None:
        raise HTTPException(
            status_code=404,
            detail="User tidak ditemukan."
        )

    if not BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN tidak tersedia pada API."
        )

    bot = Bot(token=BOT_TOKEN)

    await update_user_role_and_notify(
        user_id,
        payload.role,
        bot,
    )

    action_map = {
        "sales": "Menyetujui User",
        "admin": "Menjadikan User sebagai Admin",
        "rejected": "Menolak User",
        "pending": "Mengembalikan User ke Pending",
    }

    log_admin_activity(
        admin_id=payload.admin_id,
        admin_name=payload.admin_name or "Administrator",
        action=action_map.get(
            payload.role,
            "Mengubah Role User"
        ),
        target_type="user",
        target_id=str(user_id),
        detail=f"Role diubah dari {current_role} menjadi {payload.role}",
        status="success",
    )

    return {
        "status": "success",
        "message": f"Role user {user_id} berhasil diubah menjadi {payload.role}.",
        "user_id": user_id,
        "role": payload.role,
    }


@router.delete("/users/{user_id}")
def remove_user(user_id: int):
    user = get_user_role(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User tidak ditemukan."
        )

    success = delete_bot_user(user_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="User gagal dihapus."
        )

    return {
        "status": "success",
        "message": "User berhasil dihapus.",
        "user_id": user_id,
    }



# ============================================================
# ADMIN ACTIVITY LOG - TAMBAHAN DASHBOARD
# ============================================================

def init_activity_log_table():
    """Membuat tabel riwayat aktivitas admin jika belum ada."""
    with engine.begin() as conn:
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS admin_activity_logs (
                    id BIGSERIAL PRIMARY KEY,
                    admin_id VARCHAR(100),
                    admin_name VARCHAR(255),
                    action VARCHAR(100) NOT NULL,
                    target_type VARCHAR(100),
                    target_id VARCHAR(100),
                    detail TEXT,
                    status VARCHAR(50) DEFAULT 'success',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )


def log_admin_activity(
    action: str,
    admin_id: str = None,
    admin_name: str = "Administrator",
    target_type: str = None,
    target_id: str = None,
    detail: str = None,
    status: str = "success",
):
    """Menyimpan aktivitas admin ke PostgreSQL."""

    init_activity_log_table()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO admin_activity_logs (
                    admin_id,
                    admin_name,
                    action,
                    target_type,
                    target_id,
                    detail,
                    status
                )
                VALUES (
                    :admin_id,
                    :admin_name,
                    :action,
                    :target_type,
                    :target_id,
                    :detail,
                    :status
                )
            """),
            {
                "admin_id": admin_id,
                "admin_name": admin_name,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "detail": detail,
                "status": status,
            }
        )


@router.get("/activity")
def get_admin_activity(
    page: int = 1,
    page_size: int = 20,
    admin_id: Optional[str] = None,
):
    init_activity_log_table()

    page = max(page, 1)
    page_size = max(1, min(page_size, 100))

    where = ["1=1"]
    params = {}

    if admin_id:
        where.append("admin_id = :admin_id")
        params["admin_id"] = admin_id

    where_clause = " AND ".join(where)

    with engine.connect() as conn:
        total = conn.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM admin_activity_logs
                WHERE {where_clause}
                """
            ),
            params,
        ).scalar() or 0

        query_params = {
            **params,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }

        rows = conn.execute(
            text(
                f"""
                SELECT
                    id,
                    admin_id,
                    admin_name,
                    action,
                    target_type,
                    target_id,
                    detail,
                    status,
                    created_at
                FROM admin_activity_logs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            query_params,
        ).mappings().all()

    return {
        "status": "success",
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [dict(row) for row in rows],
    }

# ============================================================
# READ-ONLY: RIWAYAT AKTIVITAS ADMIN
# ============================================================

@router.get("/activity")
def get_activity(limit: int = 100):
    init_activity_log_table()

    limit = max(1, min(limit, 200))

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT
                    id,
                    admin_id,
                    admin_name,
                    action,
                    target_type,
                    target_id,
                    detail,
                    status,
                    created_at
                FROM admin_activity_logs
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {
                "limit": limit,
            },
        ).mappings().all()

    return {
        "status": "success",
        "data": [dict(row) for row in rows],
    }

# ============================================================
# PREVIEW CBASE - DASHBOARD ADMIN
# ============================================================

@router.post("/preview/cbase")
async def preview_cbase(
    file: UploadFile = File(...)
):
    """
    Memeriksa struktur file CBASE sebelum diproses.
    Endpoint ini hanya membaca file dan TIDAK mengubah database.
    """

    filename = file.filename or ""

    # Sesuai loader CBASE backend saat ini
    if not filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="File CBASE harus berformat XLSX atau XLS."
        )

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="File CBASE kosong."
            )

        excel_buffer = io.BytesIO(contents)

        # ----------------------------------------------------
        # 1. Baca tanpa header
        #    Sama dengan cara kerja load_cbase_file()
        # ----------------------------------------------------
        raw = pd.read_excel(
            excel_buffer,
            header=None,
            dtype=str,
        )

        required_headers = {
            "NIPNAS",
            "WITEL_HO",
            "STANDARD_NAME",
        }

        header_row = None

        # ----------------------------------------------------
        # 2. Cari baris header otomatis
        # ----------------------------------------------------
        for i, row in raw.iterrows():

            values = {
                str(value).strip().upper()
                for value in row.tolist()
                if pd.notna(value)
            }

            if required_headers.issubset(values):
                header_row = i
                break

        if header_row is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Header CBASE tidak ditemukan. "
                    "File harus memiliki kolom NIPNAS, "
                    "WITEL_HO, dan STANDARD_NAME."
                ),
            )

        # ----------------------------------------------------
        # 3. Baca ulang menggunakan header yang ditemukan
        # ----------------------------------------------------
        excel_buffer.seek(0)

        df = pd.read_excel(
            excel_buffer,
            header=header_row,
            dtype=str,
        )

        df.columns = [
            str(column).strip()
            for column in df.columns
        ]

        # Hapus baris yang seluruh kolomnya kosong
        df = df.dropna(how="all")

        # ----------------------------------------------------
        # 4. Buat preview maksimal 10 baris
        # ----------------------------------------------------
        preview_df = (
            df.head(10)
            .fillna("")
        )

        return {
            "status": "success",
            "data": {
                "filename": filename,
                "row_count": int(len(df)),
                "header_row": int(header_row + 1),
                "sheet": "Sheet pertama",
                "columns": [
                    str(column)
                    for column in df.columns
                ],
                "preview": preview_df.to_dict(
                    orient="records"
                ),
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Gagal membaca file CBASE: "
                f"{str(exc)}"
            ),
        )

# ============================================================
# PREVIEW ODP - DASHBOARD ADMIN
# ============================================================

@router.post("/preview/odp")
async def preview_odp(
    file: UploadFile,
    sheet: Optional[str] = Form(None),
):
    """
    Preview file ODP tanpa mengubah database.
    Header dicari otomatis dan lebih fleksibel
    mengikuti variasi file master ODP.
    """

    filename = file.filename or ""

    if not filename.lower().endswith(
        (".xlsx", ".xls", ".csv")
    ):
        raise HTTPException(
            status_code=400,
            detail="File ODP harus berformat XLSX, XLS, atau CSV.",
        )

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="File ODP kosong.",
            )

        # -----------------------------------------------------
        # ALIAS HEADER YANG DITERIMA
        # -----------------------------------------------------

        id_aliases = {
            "ID_ODP",
            "ID ODP",
            "ODP_ID",
            "ODP ID",
            "ODP_INDEX",
            "ODP INDEX",
            "DEVICE_ID",
            "DEVICE ID",
        }

        name_aliases = {
            "ODP_NAME",
            "ODP NAME",
            "NAMA_ODP",
            "NAMA ODP",
            "ODP_INDEX",
            "ODP INDEX",
        }

        lat_aliases = {
            "LATITUDE",
            "LAT",
            "LATITUDE_ODP",
            "LATITUDE ODP",
        }

        lon_aliases = {
            "LONGITUDE",
            "LONG",
            "LON",
            "LONGITUDE_ODP",
            "LONGITUDE ODP",
        }

        selected_sheet = None
        header_row = None
        df = None

        def normalize_header(value):
            return (
                str(value)
                .strip()
                .upper()
                .replace("-", "_")
            )

        def looks_like_odp_header(row):
            values = {
                normalize_header(value)
                for value in row.tolist()
                if pd.notna(value)
            }

            has_lat = bool(
                values.intersection(lat_aliases)
            )

            has_lon = bool(
                values.intersection(lon_aliases)
            )

            has_identifier = bool(
                values.intersection(id_aliases)
                or
                values.intersection(name_aliases)
            )

            return (
                has_lat
                and has_lon
                and has_identifier
            )

        # =====================================================
        # CSV
        # =====================================================

        if filename.lower().endswith(".csv"):

            buffer = io.BytesIO(contents)

            raw = pd.read_csv(
                buffer,
                header=None,
                dtype=str,
                nrows=100,
            )

            for i, row in raw.iterrows():
                if looks_like_odp_header(row):
                    header_row = i
                    break

            if header_row is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Header data ODP belum dapat dikenali. "
                        "Pastikan file memiliki informasi "
                        "ODP serta koordinat latitude dan longitude."
                    ),
                )

            buffer.seek(0)

            df = pd.read_csv(
                buffer,
                header=header_row,
                dtype=str,
            )

            selected_sheet = "CSV"

        # =====================================================
        # EXCEL
        # =====================================================

        else:

            excel_buffer = io.BytesIO(
                contents
            )

            excel_file = pd.ExcelFile(
                excel_buffer
            )

            if sheet:

                if sheet not in excel_file.sheet_names:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Sheet '{sheet}' tidak ditemukan."
                        ),
                    )

                sheets_to_check = [
                    sheet
                ]

            else:

                sheets_to_check = (
                    excel_file.sheet_names
                )

            for sheet_candidate in sheets_to_check:

                raw = pd.read_excel(
                    excel_file,
                    sheet_name=sheet_candidate,
                    header=None,
                    dtype=str,
                    nrows=100,
                )

                for i, row in raw.iterrows():

                    if looks_like_odp_header(row):

                        selected_sheet = (
                            sheet_candidate
                        )

                        header_row = i

                        break

                if header_row is not None:
                    break

            if (
                selected_sheet is None
                or header_row is None
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Header data ODP belum dapat dikenali. "
                        "Pastikan file memiliki informasi "
                        "ODP serta koordinat latitude dan longitude."
                    ),
                )

            excel_buffer.seek(0)

            df = pd.read_excel(
                excel_buffer,
                sheet_name=selected_sheet,
                header=header_row,
                dtype=str,
            )

        # =====================================================
        # PREVIEW
        # =====================================================

        df.columns = [
            str(column).strip()
            for column in df.columns
        ]

        df = df.dropna(
            how="all"
        )

        preview_df = (
            df.head(10)
            .fillna("")
        )

        return {
            "status": "success",
            "data": {
                "filename": filename,
                "row_count": int(
                    len(df)
                ),
                "header_row": int(
                    header_row + 1
                ),
                "sheet": (
                    selected_sheet
                    or "-"
                ),
                "columns": [
                    str(column)
                    for column
                    in df.columns
                ],
                "preview": (
                    preview_df.to_dict(
                        orient="records"
                    )
                ),
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Gagal membaca file ODP: {str(exc)}"
            ),
        )

# ============================================================
# ACTIVITY SUMMARY
# ============================================================

@router.get("/activity-summary")
def get_activity_summary():
    """
    Ringkasan seluruh activity log untuk Dashboard Admin.

    Menghitung seluruh data pada admin_activity_logs,
    bukan hanya data pada halaman pagination aktif.
    """

    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS total_activity,

                        COUNT(*) FILTER (
                            WHERE LOWER(COALESCE(status, ''))
                            IN ('success', 'berhasil')
                        ) AS total_success,

                        COUNT(*) FILTER (
                            WHERE LOWER(COALESCE(status, ''))
                            IN ('failed', 'gagal', 'error')
                        ) AS total_failed

                    FROM admin_activity_logs
                    """
                )
            ).mappings().first()

        total_activity = int(
            row.get("total_activity", 0)
            if row
            else 0
        )

        total_success = int(
            row.get("total_success", 0)
            if row
            else 0
        )

        total_failed = int(
            row.get("total_failed", 0)
            if row
            else 0
        )

        success_rate = (
            round(
                (total_success / total_activity) * 100,
                1,
            )
            if total_activity > 0
            else 0
        )

        return {
            "status": "success",
            "data": {
                "total_activity": total_activity,
                "total_success": total_success,
                "total_failed": total_failed,
                "success_rate": success_rate,
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Gagal mengambil ringkasan "
                f"riwayat aktivitas: {str(exc)}"
            ),
        )