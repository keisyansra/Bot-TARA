"""HTTP client untuk komunikasi Streamlit dengan FastAPI TARA.

Streamlit tidak pernah membuka koneksi PostgreSQL secara langsung. Seluruh
akses data harus melalui FastAPI agar aturan validasi, ETL, dan keamanan tetap
berada di backend.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)

# URL ini hanya fallback. Untuk penggunaan harian, tulis URL backend pada
# TARA_API_BASE_URL di file .env agar tunnel dapat diganti tanpa mengubah kode.
DEFAULT_BASE_URL = "https://kinetic-untried-whoops.ngrok-free.dev"
BASE_URL = os.getenv("TARA_API_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60
UPLOAD_READ_TIMEOUT = 180

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "ngrok-skip-browser-warning": "true",
}


def _friendly_server_error(status_code: int) -> str:
    if status_code == 502:
        return "Backend TARA sedang tidak aktif atau tunnel ngrok sedang offline."
    if status_code == 503:
        return "Layanan TARA sedang tidak tersedia. Silakan coba lagi beberapa saat."
    if status_code == 504:
        return "Backend TARA terlalu lama memproses permintaan. Silakan coba lagi."
    return "Server mengalami kendala saat memproses permintaan. Hubungi administrator jika masalah berulang."


def _extract_safe_detail(response: requests.Response) -> str | None:
    """Ambil pesan validasi yang aman tanpa menampilkan traceback/SQL mentah."""
    try:
        payload = response.json()
    except ValueError:
        return None

    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, list):
        messages = []
        for item in detail:
            if isinstance(item, dict) and item.get("msg"):
                messages.append(str(item["msg"]))
        return "; ".join(messages) if messages else None

    if not isinstance(detail, str):
        return None

    lowered = detail.lower()
    unsafe_markers = (
        "traceback",
        "sqlalchemy",
        "psycopg",
        "select ",
        "insert ",
        "update ",
        "delete from",
        "relation ",
        "connection to server",
    )
    if any(marker in lowered for marker in unsafe_markers):
        return None
    return detail.strip()[:500]


def _request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    if not path.startswith("/"):
        path = f"/{path}"

    headers = {**DEFAULT_HEADERS, **kwargs.pop("headers", {})}
    timeout = kwargs.pop("timeout", (CONNECT_TIMEOUT, READ_TIMEOUT))

    try:
        response = requests.request(
            method=method,
            url=f"{BASE_URL}{path}",
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
    except requests.exceptions.ConnectionError:
        return {
            "ok": False,
            "kind": "offline",
            "error": (
                "Backend TARA tidak dapat dihubungi. Pastikan FastAPI aktif dan "
                "alamat TARA_API_BASE_URL masih berlaku."
            ),
        }
    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "kind": "timeout",
            "error": "Server terlalu lama merespons. Silakan coba lagi.",
        }
    except requests.exceptions.RequestException:
        return {
            "ok": False,
            "kind": "network_error",
            "error": "Terjadi gangguan komunikasi dengan backend TARA.",
        }

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if response.status_code == 404:
        return {
            "ok": False,
            "kind": "not_deployed",
            "error": "Fitur ini belum tersedia pada versi backend yang sedang aktif.",
            "status_code": 404,
        }

    if response.status_code >= 500:
        return {
            "ok": False,
            "kind": "server_error",
            "error": _friendly_server_error(response.status_code),
            "status_code": response.status_code,
        }

    if response.status_code >= 400:
        detail = _extract_safe_detail(response)
        return {
            "ok": False,
            "kind": "invalid_input",
            "error": detail or "Data yang dikirim belum sesuai. Periksa kembali file atau formulir.",
            "status_code": response.status_code,
        }

    if payload is None:
        return {
            "ok": False,
            "kind": "invalid_response",
            "error": "Respons server tidak dapat dibaca. Hubungi administrator.",
            "status_code": response.status_code,
        }

    return {"ok": True, "data": payload, "status_code": response.status_code}


def api_get(path: str, params: dict | None = None) -> dict[str, Any]:
    return _request("GET", path, params=params)


def api_post(path: str, json: dict | None = None) -> dict[str, Any]:
    return _request("POST", path, json=json)


def api_put(path: str, json: dict | None = None) -> dict[str, Any]:
    return _request("PUT", path, json=json)


def api_delete(path: str) -> dict[str, Any]:
    return _request("DELETE", path)


LEGACY_UPLOAD_PATHS = {
    "/api/admin/upload/cbase": "/api/admin/upload_cbase",
    "/api/admin/upload/odp": "/api/admin/upload_odp",
}


def api_upload(
    path: str,
    file_bytes: bytes,
    filename: str,
    extra_data: dict | None = None,
) -> dict[str, Any]:
    files = {"file": (filename, file_bytes)}
    result = _request(
        "POST",
        path,
        files=files,
        data=extra_data or {},
        timeout=(CONNECT_TIMEOUT, UPLOAD_READ_TIMEOUT),
    )

    # Kompatibilitas sementara dengan backend lama milik Bot-TARA-Nada-Local.
    # Setelah backend baru dideploy, fallback ini tidak digunakan lagi.
    legacy_path = LEGACY_UPLOAD_PATHS.get(path)
    if result.get("kind") == "not_deployed" and legacy_path:
        result = _request(
            "POST",
            legacy_path,
            files={"file": (filename, file_bytes)},
            timeout=(CONNECT_TIMEOUT, UPLOAD_READ_TIMEOUT),
        )
        if result.get("ok"):
            result["legacy_endpoint"] = True
    return result


def collection_payload(result: dict[str, Any]) -> tuple[list[dict], int | None]:
    """Baca respons list dari API baru maupun API lama tanpa KeyError."""
    if not result.get("ok") or not isinstance(result.get("data"), dict):
        return [], 0

    body = result["data"]
    raw_data = body.get("data", [])
    total = body.get("total")

    if isinstance(raw_data, dict):
        total = raw_data.get("total", total)
        raw_data = raw_data.get("data", [])

    if not isinstance(raw_data, list):
        return [], 0

    rows = [row for row in raw_data if isinstance(row, dict)]
    return rows, int(total) if isinstance(total, (int, float)) else None


def pagination_params(query: str, page: int, page_size: int) -> dict[str, Any]:
    """Kirim parameter API baru dan lama secara bersamaan."""
    params: dict[str, Any] = {
        "page": page,
        "page_size": page_size,
        "limit": page_size,
        "offset": max(page - 1, 0) * page_size,
    }
    if query:
        params.update({"q": query, "search": query})
    return params


def upload_is_finished(result: dict[str, Any]) -> bool:
    """True bila backend lama sudah menyelesaikan upload secara sinkron."""
    if not result.get("ok") or not isinstance(result.get("data"), dict):
        return False
    return str(result["data"].get("status", "")).lower() == "success"


def upload_row_count(result: dict[str, Any]) -> int | None:
    if not result.get("ok") or not isinstance(result.get("data"), dict):
        return None
    value = result["data"].get("rows_inserted")
    return int(value) if isinstance(value, (int, float)) else None


def poll_upload_status(
    batch_id: str,
    max_wait_seconds: int = 180,
    interval_seconds: int = 2,
) -> dict[str, Any]:
    waited = 0
    last_data = None

    while waited < max_wait_seconds:
        result = api_get(f"/api/admin/upload/status/{batch_id}")
        if result.get("kind") == "not_deployed":
            return {"timed_out": False, "status": "unsupported", "data": None}

        if result.get("ok") and isinstance(result.get("data"), dict):
            last_data = result["data"].get("data", {})
            status = last_data.get("status") if isinstance(last_data, dict) else None
            if status in ("success", "failed"):
                return {"timed_out": False, "status": status, "data": last_data}

        time.sleep(interval_seconds)
        waited += interval_seconds

    return {"timed_out": True, "status": "running", "data": last_data}


def show_error(result: dict[str, Any]) -> None:
    kind = result.get("kind")
    message = result.get("error", "Terjadi kesalahan yang tidak diketahui.")
    if kind == "not_deployed":
        st.warning(f"🛠️ {message}")
    elif kind in ("offline", "timeout", "network_error", "invalid_response"):
        st.error(f"📡 {message}")
    elif kind == "server_error":
        st.error(f"🔴 {message}")
    else:
        st.error(f"⚠️ {message}")


@st.cache_data(ttl=30, show_spinner=False)
def check_capability(path: str) -> bool:
    result = api_get(path)
    return result.get("ok", False) or result.get("kind") != "not_deployed"


@st.cache_data(ttl=60, show_spinner=False)
def _openapi_paths() -> dict | None:
    result = api_get("/openapi.json")
    if not result.get("ok") or not isinstance(result.get("data"), dict):
        return None
    paths = result["data"].get("paths", {})
    return paths if isinstance(paths, dict) else None


def api_supports(method: str, path_template: str) -> bool:
    """Periksa metode/path dari OpenAPI tanpa mengeksekusi operasi CRUD."""
    paths = _openapi_paths()
    if paths is None:
        # Jangan menyembunyikan fitur hanya karena pemeriksaan kontrak sedang
        # gagal. Request sebenarnya tetap akan menampilkan error yang aman.
        return True
    operations = paths.get(path_template, {})
    return method.lower() in operations
