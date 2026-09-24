import hashlib

import streamlit as st

from utils.api_client import (
    api_get,
    api_post,
    api_put,
    api_delete,
    api_upload,
    api_supports,
    collection_payload,
    pagination_params,
    poll_upload_status,
    show_error,
    upload_is_finished,
    upload_row_count,
)
from utils.ui import (
    inject_css,
    render_sidebar,
    render_topbar,
    badge,
    success_screen,
    error_screen,
    pending_screen,
    render_pagination,
)


st.set_page_config(
    page_title="Data Pelanggan (CBASE) - TARA",
    page_icon="👥",
    layout="wide",
)

inject_css()


PAGE_SIZE = 10

ss = st.session_state

ss.setdefault("cbase_view", "list")
ss.setdefault("cbase_page", 1)
ss.setdefault("cbase_edit_row", None)
ss.setdefault("cbase_preview", None)


# ============================================================
# NAVIGATION
# ============================================================

def go(view):
    ss.cbase_view = view


# ============================================================
# DELETE CONFIRMATION
# ============================================================

@st.dialog("Hapus Data CBASE?")
def confirm_delete_dialog(row):

    st.markdown(
        '<div style="text-align:center; font-size:40px;">🗑️</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p style="text-align:center;">'
        'Apakah Anda yakin ingin menghapus data pelanggan ini?'
        '</p>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):

        st.markdown(
            f'<p style="text-align:center; '
            f'color:#9098A3; font-size:0.75rem; '
            f'margin-bottom:0;">NIPNAS</p>'
            f'<p style="text-align:center; '
            f'font-weight:700; font-size:1.1rem;">'
            f'{row.get("nipnas", "-")}</p>'
            f'<p style="text-align:center; '
            f'margin-top:-8px;">'
            f'{row.get("standard_name", "-")}</p>',
            unsafe_allow_html=True,
        )

    st.warning(
        "Data pelanggan akan dihapus dari daftar aktif TARA. "
        "Riwayat data tetap tersimpan untuk kebutuhan administrasi."
    )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "Batal",
            use_container_width=True,
        ):
            st.rerun()

    with c2:

        if st.button(
            "Ya, Hapus Data",
            type="primary",
            use_container_width=True,
        ):

            result = api_delete(
                f"/api/admin/cbase/{row['nipnas']}"
            )

            if result["ok"]:

                ss.cbase_page = 1

                response_data = result.get("data") or {}
                batch_id = response_data.get("batch_id")

                if batch_id:
                    ss.cbase_delete_batch_id = batch_id
                    go("proses_hapus")
                else:
                    go("list")

                st.rerun()

            else:

                show_error(result)


# ============================================================
# TAMBAH / EDIT
# ============================================================

def render_form_view(edit_row=None):
    is_edit = edit_row is not None

    render_topbar(
        [
            "Data Pelanggan",
            "Edit Data" if is_edit else "Tambah Data",
        ]
    )

    st.title(
        "Perbarui Data Pelanggan"
        if is_edit
        else "Tambah Data Pelanggan"
    )

    st.caption(
        "Lengkapi data pelanggan sesuai data CBASE Telkom."
    )

    with st.container(border=True):

        with st.form("form_cbase"):

            fc1, fc2 = st.columns(2)

            with fc1:
                f_nipnas = st.text_input(
                    "NIPNAS *",
                    value=(
                        edit_row.get("nipnas", "")
                        if is_edit
                        else ""
                    ),
                    disabled=is_edit,
                    placeholder="Masukkan NIPNAS",
                )

            with fc2:
                f_nama = st.text_input(
                    "Nama Pelanggan *",
                    value=(
                        edit_row.get(
                            "standard_name",
                            ""
                        )
                        if is_edit
                        else ""
                    ),
                    placeholder="Masukkan nama pelanggan",
                )

            st.text_input(
                "Witel *",
                value="TELKOM JATIM BARAT",
                disabled=True,
                help=(
                    "Data CBASE pada dashboard ini "
                    "khusus TELKOM JATIM BARAT."
                ),
            )

            st.info(
                "Pastikan data pelanggan sudah sesuai sebelum disimpan."
            )

            st.write("")

            bcol1, bcol2, _ = st.columns(
                [1, 1, 3]
            )

            with bcol1:
                cancel = st.form_submit_button(
                    "Batal",
                    use_container_width=True,
                )

            with bcol2:
                submit = st.form_submit_button(
                    "💾 Simpan Data",
                    type="primary",
                    use_container_width=True,
                )

    if cancel:
        go("list")
        st.rerun()

    if not submit:
        return

    nipnas = f_nipnas.strip()
    nama = f_nama.strip()

    if not nipnas or not nama:
        st.warning(
            "NIPNAS dan Nama Pelanggan wajib diisi."
        )
        return

    # ========================================================
    # EDIT DATA
    # ========================================================

    if is_edit:

        with st.spinner(
            "Mengirim perubahan data pelanggan ke server..."
        ):
            result = api_put(
                f"/api/admin/cbase/{nipnas}",
                json={
                    "standard_name": nama,
                    "witel_ho": "TELKOM JATIM BARAT",
                },
            )

        if not result["ok"]:
            show_error(result)
            return

        response_data = (
            result.get("data")
            or {}
        )

        batch_id = response_data.get(
            "batch_id"
        )

        if response_data.get("status") == "success":
            ss.cbase_page = 1
            go("sukses_edit")
            st.rerun()

        if not batch_id:
            st.error(
                "Server menerima perubahan, tetapi tidak "
                "mengembalikan batch_id proses."
            )
            return

        ss.cbase_edit_batch_id = batch_id
        ss.cbase_edit_nipnas = nipnas

        with st.spinner(
            "Perubahan diterima. Sedang memproses data, mohon tunggu..."
        ):

            poll_result = poll_upload_status(
                batch_id
            )

        status = poll_result.get(
            "status"
        )

        poll_data = (
            poll_result.get("data")
            or {}
        )

        if status == "success":

            ss.cbase_page = 1
            go("sukses_edit")
            st.rerun()

        elif status == "failed":

            st.error(
                poll_data.get(
                    "notes"
                )
                or
                "Proses pembaruan data pelanggan gagal."
            )

        else:

            go("proses_edit")
            st.rerun()

        return

    # ========================================================
    # CREATE DATA
    # ========================================================

    with st.spinner(
        "Mengirim data pelanggan ke server..."
    ):

        result = api_post(
            "/api/admin/cbase",
            json={
                "nipnas": nipnas,
                "standard_name": nama,
                "witel_ho": "TELKOM JATIM BARAT",
            },
        )

    if not result["ok"]:
        show_error(result)
        return

    response_data = (
        result.get("data")
        or {}
    )

    batch_id = response_data.get(
        "batch_id"
    )

    if response_data.get("status") == "success":

        ss.cbase_page = 1
        go("sukses_tambah")
        st.rerun()

    if not batch_id:

        st.error(
            "Server menerima permintaan, tetapi tidak "
            "mengembalikan batch_id proses."
        )
        return

    ss.cbase_create_batch_id = batch_id
    ss.cbase_create_nipnas = nipnas

    with st.spinner(
        "Data diterima. Sedang memproses data, mohon tunggu..."
    ):

        poll_result = poll_upload_status(
            batch_id
        )

    status = poll_result.get(
        "status"
    )

    poll_data = (
        poll_result.get("data")
        or {}
    )

    if status == "success":

        ss.cbase_page = 1
        go("sukses_tambah")
        st.rerun()

    elif status == "failed":

        st.error(
            poll_data.get(
                "notes"
            )
            or
            "Proses penambahan data pelanggan gagal."
        )

    else:

        go("proses_tambah")
        st.rerun()


# ============================================================
# UPLOAD
# ============================================================

def render_upload_view():

    render_topbar(
        ["Data Pelanggan", "Upload Data"]
    )

    st.title("Perbarui Data Pelanggan")

    st.write(
        "Gunakan file CBASE terbaru untuk memperbarui "
        "data pelanggan TARA."
    )

    st.markdown(
        "**:red[Data tidak akan diperbarui sebelum "
        "Anda memeriksa dan mengonfirmasi file.]**"
    )

    with st.container(border=True):

        upload_file = st.file_uploader(
            "Tarik dan lepas file di sini, atau pilih file dari perangkat",
            type=["xlsx", "xls"],
            key="cbase_uploader",
        )

        st.caption(
            "Mendukung format XLSX dan XLS "
            "(maksimal 200MB). Header "
            "(NIPNAS, WITEL_HO, STANDARD_NAME, dst) "
            "dicari otomatis di dalam file."
        )

    fingerprint = None
    preview_ready = False

    if upload_file is not None:

        fingerprint = hashlib.sha256(
            upload_file.getvalue()
        ).hexdigest()

        preview_state = (
            ss.get("cbase_preview") or {}
        )

        preview_ready = (
            preview_state.get("fingerprint")
            == fingerprint
        )

        if preview_ready:

            preview_data = (
                preview_state.get("data", {})
            )

            st.success(
                f"Struktur file dikenali: "
                f"{preview_data.get('row_count', 0):,} baris, "
                f"header pada baris "
                f"{preview_data.get('header_row', '-')}, "
                f"sheet {preview_data.get('sheet', '-')}."
            )

            st.caption(
                "Kolom dikenali: "
                + ", ".join(
                    preview_data.get(
                        "columns",
                        []
                    )
                )
            )

            st.dataframe(
                preview_data.get(
                    "preview",
                    []
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.write("")

    bcol1, bcol2, bcol3, _ = st.columns(
        [1, 1, 1.4, 2]
    )

    with bcol1:

        if st.button(
            "Batal",
            use_container_width=True,
            key="cancel_upload_cbase",
        ):

            ss.cbase_preview = None

            go("list")

            st.rerun()

    with bcol2:

        if st.button(
            "🔎 Periksa File",
            use_container_width=True,
            disabled=upload_file is None,
        ):

            with st.spinner(
                "Memeriksa struktur file "
                "tanpa mengubah database..."
            ):

                preview_result = api_upload(
                    "/api/admin/preview/cbase",
                    upload_file.getvalue(),
                    upload_file.name,
                )

            if preview_result["ok"]:

                ss.cbase_preview = {
                    "fingerprint": fingerprint,
                    "data": (
                        preview_result["data"]
                        .get(
                            "data",
                            {}
                        )
                    ),
                }

                st.rerun()

            else:

                show_error(
                    preview_result
                )

    with bcol3:

        if st.button(
            "Proses & Konfirmasi Upload",
            type="primary",
            use_container_width=True,
            disabled=(
                upload_file is None
                or not preview_ready
            ),
            help=(
                None
                if preview_ready
                else
                "Periksa file terlebih dahulu "
                "sebelum mengunggah."
            ),
        ):

            with st.spinner(
                "Mengirim file ke server..."
            ):

                result = api_upload(
                    "/api/admin/upload/cbase",
                    upload_file.getvalue(),
                    upload_file.name,
                )

            if not result["ok"]:

                show_error(
                    result
                )

            else:

                if upload_is_finished(
                    result
                ):

                    ss.cbase_upload_row_count = (
                        upload_row_count(
                            result
                        )
                    )

                    ss.cbase_preview = None

                    go(
                        "sukses_upload"
                    )

                    st.rerun()

                batch_id = (
                    result["data"]
                    .get("batch_id")
                )

                if not batch_id:

                    ss.cbase_upload_error = (
                        "Server tidak mengembalikan "
                        "ID proses (batch_id). "
                        "Cek Riwayat Aktivitas "
                        "secara manual."
                    )

                    go(
                        "gagal_upload"
                    )

                    st.rerun()

                else:

                    with st.spinner(
                        "File diterima, sedang diproses server "
                        "(bronze → silver → matching → gold)... "
                        "Mohon tunggu, jangan tutup atau "
                        "restart backend."
                    ):

                        poll_result = (
                            poll_upload_status(
                                batch_id
                            )
                        )

                    if (
                        poll_result["status"]
                        == "success"
                    ):

                        ss.cbase_upload_row_count = (
                            (
                                poll_result["data"]
                                or {}
                            ).get(
                                "row_count"
                            )
                        )

                        ss.cbase_preview = None

                        go(
                            "sukses_upload"
                        )

                        st.rerun()

                    elif (
                        poll_result["status"]
                        == "failed"
                    ):

                        ss.cbase_upload_error = (
                            (
                                poll_result["data"]
                                or {}
                            ).get(
                                "notes"
                            )
                            or
                            "Proses gagal, tidak ada "
                            "detail error dari server."
                        )

                        go(
                            "gagal_upload"
                        )

                        st.rerun()

                    else:

                        ss.cbase_upload_batch_id = (
                            batch_id
                        )

                        go(
                            "proses_lama_upload"
                        )

                        st.rerun()


# ============================================================
# LIST
# ============================================================

def render_list_view():

    can_create = api_supports(
        "post",
        "/api/admin/cbase"
    )

    can_update = api_supports(
        "put",
        "/api/admin/cbase/{nipnas}"
    )

    can_delete = api_supports(
        "delete",
        "/api/admin/cbase/{nipnas}"
    )

    render_topbar(
        ["Data Pelanggan (CBASE)"]
    )

    hcol1, hcol2 = st.columns(
        [3, 2]
    )

    with hcol1:

        st.title(
            "Data Pelanggan (CBASE)"
        )

        st.caption(
            "Kelola data pelanggan eksisting Telkom."
        )

    with hcol2:

        st.write("")

        bcol1, bcol2 = st.columns(
            2
        )

        with bcol1:

            if st.button(
                "➕ Tambah Pelanggan",
                use_container_width=True,
                disabled=not can_create,
                help=(
                    None
                    if can_create
                    else
                    "Backend yang aktif belum "
                    "menyediakan fitur tambah manual."
                ),
            ):

                ss.cbase_edit_row = None

                go(
                    "tambah"
                )

                st.rerun()

        with bcol2:

            if st.button(
                "⬆️ Upload / Perbarui Data",
                type="primary",
                use_container_width=True,
            ):

                go(
                    "upload"
                )

                st.rerun()

    st.divider()

    fcol1, fcol2 = st.columns(
        [3, 1]
    )

    with fcol1:

        query = st.text_input(
            "Cari",
            label_visibility="collapsed",
            placeholder=(
                "🔍  Cari NIPNAS "
                "atau nama pelanggan..."
            ),
        )

    with fcol2:

        revenue_filter = st.selectbox(
            "Revenue",
            options=[
                "Semua",
                "≥ 75 juta",
                "< 75 juta",
            ],
            label_visibility="collapsed",
        )

    params = pagination_params(
        query=query,
        page=ss.cbase_page,
        page_size=PAGE_SIZE,
    )

    result = api_get(
        "/api/admin/cbase",
        params=params,
    )

    if not result["ok"]:

        show_error(
            result
        )

        return

    # ========================================================
    # RESPONSE HANDLING
    # ========================================================

    rows, total = collection_payload(
        result
    )

    exact_total_available = (
        total is not None
    )

    if total is None:

        # Backend lama tidak mengirim total.
        # Nilai sementara ini menjaga tombol
        # "Berikutnya" tetap bekerja.
        offset = (
            (ss.cbase_page - 1)
            * PAGE_SIZE
        )

        total = (
            offset
            + len(rows)
            + (
                PAGE_SIZE
                if len(rows) == PAGE_SIZE
                else 0
            )
        )

    # ========================================================
    # FILTER REVENUE
    # ========================================================

    if revenue_filter == "≥ 75 juta":

        rows = [
            r
            for r in rows
            if r.get(
                "revenue_ge_75jt"
            )
        ]

    elif revenue_filter == "< 75 juta":

        rows = [
            r
            for r in rows
            if not r.get(
                "revenue_ge_75jt"
            )
        ]

    # ========================================================
    # TABLE
    # ========================================================

    with st.container(
        border=True
    ):

        if not rows:

            st.info(
                "📭 Belum ada data pelanggan "
                "yang cocok. Tambah data manual "
                "atau upload file CBASE di atas."
            )

        else:

            hdr = st.columns(
                [
                    1.4,
                    2.2,
                    1.6,
                    1.4,
                    1.2,
                    0.8,
                ]
            )

            for c, label in zip(
                hdr,
                [
                    "NIPNAS",
                    "Nama Pelanggan",
                    "Witel",
                    "Total Sustain",
                    "Revenue ≥75jt",
                    "Aksi",
                ],
            ):

                c.markdown(
                    f"**{label}**"
                )

            st.markdown(
                "<hr style='margin:4px 0;'>",
                unsafe_allow_html=True,
            )

            for row in rows:

                (
                    c1,
                    c2,
                    c3,
                    c4,
                    c5,
                    c6,
                ) = st.columns(
                    [
                        1.4,
                        2.2,
                        1.6,
                        1.4,
                        1.2,
                        0.8,
                    ]
                )

                nipnas = row.get(
                    "nipnas",
                    "-"
                )

                standard_name = (
                    row.get(
                        "standard_name",
                        "-"
                    )
                )

                c1.write(
                    nipnas
                )

                c2.write(
                    standard_name
                )

                c3.write(
                    row.get(
                        "witel_ho"
                    ) or "-"
                )

                try:

                    sustain = float(
                        row.get(
                            "total_sustain"
                        ) or 0
                    )

                    c4.write(
                        f"Rp {sustain:,.0f}"
                        .replace(
                            ",",
                            "."
                        )
                    )

                except (
                    ValueError,
                    TypeError,
                ):

                    c4.write(
                        str(
                            row.get(
                                "total_sustain"
                            ) or "-"
                        )
                    )

                with c5:

                    if row.get(
                        "revenue_ge_75jt"
                    ):

                        st.markdown(
                            badge(
                                "Ya",
                                "green"
                            ),
                            unsafe_allow_html=True,
                        )

                    else:

                        st.markdown(
                            badge(
                                "Tidak",
                                "gray"
                            ),
                            unsafe_allow_html=True,
                        )

                with c6:

                    ac1, ac2 = st.columns(
                        2
                    )

                    with ac1:

                        if st.button(
                            "✏️",
                            key=f"edit_{nipnas}",
                            help="Edit",
                            disabled=not can_update,
                        ):

                            ss.cbase_edit_row = row

                            go(
                                "edit"
                            )

                            st.rerun()

                    with ac2:

                        if st.button(
                            "🗑️",
                            key=f"del_{nipnas}",
                            help="Hapus",
                            disabled=not can_delete,
                        ):

                            confirm_delete_dialog(
                                row
                            )

    # ========================================================
    # PAGINATION
    # ========================================================

    if exact_total_available:

        render_pagination(
            total=total,
            page_size=PAGE_SIZE,
            page_key="cbase_page",
            item_label="data pelanggan",
        )

    else:

        st.caption(
            f"Menampilkan {len(rows)} data "
            f"pada halaman {ss.cbase_page}. "
            "Jumlah total belum tersedia dari server."
        )


# ============================================================
# ROUTER
# ============================================================

render_sidebar(
    "Data Pelanggan (CBASE)"
)

view = ss.cbase_view


if view == "list":

    render_list_view()


elif view == "tambah":

    render_form_view(
        edit_row=None
    )


elif view == "edit":

    render_form_view(
        edit_row=ss.cbase_edit_row
    )


elif view == "upload":

    render_upload_view()

elif view == "proses_tambah":

    render_topbar(
        [
            "Data Pelanggan",
            "Tambah Data",
        ]
    )

    st.title(
        "Tambah Data Pelanggan"
    )

    st.caption(
        "Data sedang diproses oleh server."
    )

    batch_id = ss.get(
        "cbase_create_batch_id"
    )

    nipnas = ss.get(
        "cbase_create_nipnas",
        "-"
    )

    with st.container(border=True):

        st.info(
            "⏳ Data pelanggan masih diproses melalui "
            "Bronze → Silver → Gold."
        )

        st.write(
            f"**NIPNAS:** {nipnas}"
        )

        st.caption(
            f"Batch ID: {batch_id or '-'}"
        )

        if st.button(
            "🔄 Cek Status Proses",
            type="primary",
            use_container_width=True,
        ):

            if not batch_id:

                st.error(
                    "Batch ID proses tidak ditemukan."
                )

            else:

                with st.spinner(
                    "Memeriksa status proses..."
                ):

                    result = poll_upload_status(
                        batch_id
                    )

                status = result.get(
                    "status"
                )

                data = (
                    result.get("data")
                    or {}
                )

                if status == "success":

                    ss.cbase_page = 1

                    go("sukses_tambah")
                    st.rerun()

                elif status == "failed":

                    st.error(
                        data.get(
                            "notes"
                        )
                        or
                        "Proses penambahan data gagal."
                    )

                else:

                    st.warning(
                        "Data masih diproses server. "
                        "Silakan cek kembali beberapa saat lagi."
                    )

        if st.button(
            "← Kembali ke Data Pelanggan",
            use_container_width=True,
        ):

            go("list")
            st.rerun()

elif view == "proses_hapus":

    render_topbar(
        [
            "Data Pelanggan",
            "Hapus Data",
        ]
    )

    st.title(
        "Hapus Data Pelanggan"
    )

    pending_screen(
        "Penghapusan sedang diproses",
        ss.get(
            "cbase_delete_batch_id",
            "-"
        ),
        "Lihat Data Pelanggan",
        "pages/1_Data_Pelanggan_CBASE.py",
    )


elif view == "sukses_tambah":

    render_topbar(
        [
            "Data Pelanggan",
            "Tambah Data",
        ]
    )

    st.title(
        "Tambah Data Pelanggan"
    )

    st.caption(
        "Proses penambahan data pelanggan "
        "telah selesai dilakukan."
    )

    success_screen(
        "Data pelanggan berhasil ditambahkan",
        "Data terbaru sudah tersedia "
        "untuk digunakan oleh TARA.",
        "Lihat Data Pelanggan",
        "pages/1_Data_Pelanggan_CBASE.py",
    )

    ss.cbase_view = "list"

elif view == "proses_edit":

    render_topbar(
        [
            "Data Pelanggan",
            "Edit Data",
        ]
    )

    st.title(
        "Perbarui Data Pelanggan"
    )

    st.caption(
        "Perubahan data sedang diproses oleh server."
    )

    batch_id = ss.get(
        "cbase_edit_batch_id"
    )

    nipnas = ss.get(
        "cbase_edit_nipnas",
        "-"
    )

    with st.container(border=True):

        st.info(
            "⏳ Perubahan data pelanggan masih diproses "
            "melalui Bronze → Silver → Gold."
        )

        st.write(
            f"**NIPNAS:** {nipnas}"
        )

        st.caption(
            f"Batch ID: {batch_id or '-'}"
        )

        if st.button(
            "🔄 Cek Status Proses",
            type="primary",
            use_container_width=True,
        ):

            if not batch_id:

                st.error(
                    "Batch ID proses tidak ditemukan."
                )

            else:

                with st.spinner(
                    "Memeriksa status proses..."
                ):

                    result = poll_upload_status(
                        batch_id
                    )

                status = result.get(
                    "status"
                )

                data = (
                    result.get("data")
                    or {}
                )

                if status == "success":

                    ss.cbase_page = 1
                    go("sukses_edit")
                    st.rerun()

                elif status == "failed":

                    st.error(
                        data.get(
                            "notes"
                        )
                        or
                        "Proses pembaruan data gagal."
                    )

                else:

                    st.warning(
                        "Data masih diproses server. "
                        "Silakan cek kembali beberapa saat lagi."
                    )

        if st.button(
            "← Kembali ke Data Pelanggan",
            use_container_width=True,
        ):

            go("list")
            st.rerun()

elif view == "sukses_edit":

    render_topbar(
        [
            "Data Pelanggan",
            "Edit Data",
        ]
    )

    st.title(
        "Perbarui Data Pelanggan"
    )

    st.caption(
        "Proses pembaruan data pelanggan "
        "telah selesai dilakukan."
    )

    success_screen(
        "Data pelanggan berhasil diperbarui",
        "Data terbaru sudah tersedia "
        "untuk digunakan oleh TARA.",
        "Lihat Data Pelanggan",
        "pages/1_Data_Pelanggan_CBASE.py",
    )

    ss.cbase_view = "list"


elif view == "sukses_upload":

    render_topbar(
        [
            "Data Pelanggan",
            "Upload Data",
        ]
    )

    st.title(
        "Perbarui Data Pelanggan"
    )

    st.caption(
        "Proses pembaruan data pelanggan "
        "telah selesai dilakukan."
    )

    _row_count = ss.get(
        "cbase_upload_row_count"
    )

    _msg = (
        "Data terbaru sudah tersedia "
        "untuk digunakan oleh TARA."
    )

    if _row_count is not None:

        _msg += (
            f" Total data pelanggan sekarang: "
            f"{_row_count:,}"
            .replace(
                ",",
                "."
            )
            + " baris."
        )

    success_screen(
        "Data pelanggan berhasil diperbarui",
        _msg,
        "Lihat Data Pelanggan",
        "pages/1_Data_Pelanggan_CBASE.py",
    )

    ss.cbase_view = "list"


elif view == "gagal_upload":

    render_topbar(
        [
            "Data Pelanggan",
            "Upload Data",
        ]
    )

    st.title(
        "Perbarui Data Pelanggan"
    )

    st.caption(
        "Proses pembaruan data pelanggan "
        "mengalami masalah."
    )

    error_screen(
        "Upload data pelanggan gagal",
        (
            ss.get(
                "cbase_upload_error"
            )
            or
            "Terjadi kesalahan "
            "yang tidak diketahui."
        ),
        "Lihat Data Pelanggan",
        "pages/1_Data_Pelanggan_CBASE.py",
        retry_view_setter=lambda: go(
            "upload"
        ),
    )


elif view == "proses_lama_upload":

    render_topbar(
        [
            "Data Pelanggan",
            "Upload Data",
        ]
    )

    st.title(
        "Perbarui Data Pelanggan"
    )

    pending_screen(
        "Masih diproses server",
        ss.get(
            "cbase_upload_batch_id",
            "-"
        ),
        "Lihat Data Pelanggan",
        "pages/1_Data_Pelanggan_CBASE.py",
    )