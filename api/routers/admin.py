"""
Endpoint admin: upload file ODP/CBASE baru, otomatis load ke bronze,
lanjut trigger ulang pipeline Silver+Gold. Pengganti alur manual
"jalanin load_odp.py/load_cbase.py dari terminal, terus run_pipeline.py".
"""
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, Form, BackgroundTasks

from etl.bronze.load_odp import load_odp_file
from etl.bronze.load_cbase import load_cbase_file
from etl.run_pipeline import main as run_pipeline

router = APIRouter()

ODP_UPLOAD_DIR = Path("data/incoming/odp")
CBASE_UPLOAD_DIR = Path("data/incoming/cbase")

# ODP sekarang selalu dikirim 1 file utuh buat seluruh Jatim Barat
# (bukan per-region lagi), jadi wilayah gak perlu ditanya user tiap
# upload -- cukup konstanta di sini.
ODP_WILAYAH_DEFAULT = "JATIM_BARAT"


def _process_odp_upload(file_path: str, batch_id: str, sheet_name: Optional[str]):
    print(f"[ADMIN] Mulai proses upload ODP, batch {batch_id}")
    load_odp_file(
        file_path=file_path,
        wilayah=ODP_WILAYAH_DEFAULT,
        batch_id=batch_id,
        sheet_name=sheet_name,
    )
    run_pipeline()
    print(f"[ADMIN] Selesai proses upload ODP, batch {batch_id}")


def _process_cbase_upload(file_path: str, batch_id: str):
    print(f"[ADMIN] Mulai proses upload CBASE, batch {batch_id}")
    load_cbase_file(file_path=file_path, batch_id=batch_id)
    run_pipeline()
    print(f"[ADMIN] Selesai proses upload CBASE, batch {batch_id}")


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