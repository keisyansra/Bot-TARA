import hashlib



import streamlit as st



from utils.api_client import (

    api_delete,

    api_get,

    api_post,

    api_put,

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

    page_title="Data ODP - TARA",

    page_icon="🔌",

    layout="wide",

)



inject_css()





PAGE_SIZE = 10



ss = st.session_state



ss.setdefault("odp_view", "list")

ss.setdefault("odp_page", 1)

ss.setdefault("odp_edit_row", None)

ss.setdefault("odp_preview", None)





# ================================================================

# STATUS ODP

# ================================================================



STATUS_OPTIONS = [

    "GREEN",

    "YELLOW",

    "RED",

]





# ================================================================

# NAVIGATION

# ================================================================



def go(view):

    ss.odp_view = view





# ================================================================

# HELPERS

# ================================================================



def as_float(value, default=0.0):

    try:

        return float(value)

    except (TypeError, ValueError):

        return default





def as_int(value, default=0):

    try:

        return int(float(value))

    except (TypeError, ValueError):

        return default





def normalize_status(value):

    """

    Samakan status lama dan baru ke:

    GREEN / YELLOW / RED.

    """



    text = str(

        value or ""

    ).strip().upper()



    # Status tersedia / normal

    if text in {

        "GREEN",

        "AKTIF",

        "AVAILABLE",

        "TERSEDIA",

        "READY",

    }:

        return "GREEN"



    # Status hampir penuh / penuh

    if text in {

        "YELLOW",

        "PENUH",

        "FULL",

    }:

        return "YELLOW"



    # Status bermasalah / maintenance

    if text in {

        "RED",

        "PEMELIHARAAN",

        "MAINTENANCE",

        "RUSAK",

        "GANGGUAN",

    }:

        return "RED"



    # Default jika status kosong

    return text or "GREEN"





def normalize_odp_row(row):

    """

    Samakan field ODP dari API bronze lama

    dan API silver baru.

    """



    normalized = dict(row)



    normalized["id_odp"] = (

        row.get("id_odp")

        or row.get("odp_index")

        or row.get("device_id")

        or "-"

    )



    normalized["odp_name"] = (

        row.get("odp_name")

        or row.get("odp_index")

        or "ODP tanpa nama"

    )



    normalized["latitude"] = as_float(

        row.get("latitude")

    )



    normalized["longitude"] = as_float(

        row.get("longitude")

    )



    normalized["available_port"] = as_int(

        row.get(

            "available_port",

            row.get("avai"),

        )

    )



    normalized["used_port"] = as_int(

        row.get(

            "used_port",

            row.get("used"),

        )

    )



    normalized["total_port"] = as_int(

        row.get("total_port"),

        normalized["available_port"]

        + normalized["used_port"],

    )



    normalized["occupancy_status"] = normalize_status(

        row.get("occupancy_status")

        or row.get("cluster_status")

    )



    normalized["witel"] = (

        row.get("witel")

        or row.get("telkom_witel")

    )



    return normalized





def status_badge(text):

    status = normalize_status(text)



    if status == "GREEN":

        return badge(

            "GREEN",

            "green",

        )



    if status == "YELLOW":

        return badge(

            "YELLOW",

            "yellow",

        )



    if status == "RED":

        return badge(

            "RED",

            "red",

        )



    return badge(

        status or "Tidak diketahui",

        "gray",

    )





# ================================================================

# DELETE CONFIRMATION

# ================================================================



@st.dialog("Hapus Data ODP?")

def confirm_delete_dialog(row):



    st.markdown(

        """

        <div style="

            text-align:center;

            font-size:40px;

        ">

            🗑️

        </div>

        """,

        unsafe_allow_html=True,

    )



    st.markdown(

        """

        <p style="text-align:center;">

            Apakah Anda yakin ingin menghapus

            data ODP ini?

        </p>

        """,

        unsafe_allow_html=True,

    )



    with st.container(border=True):



        st.markdown(

            (

                '<p style="'

                'text-align:center; '

                'color:#9098A3; '

                'font-size:0.75rem; '

                'margin-bottom:0;'

                '">'

                'KODE / NAMA ODP'

                '</p>'

                '<p style="'

                'text-align:center; '

                'font-weight:700; '

                'font-size:1.1rem;'

                '">'

                f'{row["odp_name"]}'

                '</p>'

            ),

            unsafe_allow_html=True,

        )



    st.warning(

        "⚠️ Data yang telah dihapus "

        "tidak dapat dikembalikan."

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

                f"/api/admin/odp/"

                f"{row['id_odp']}"

            )



            if result["ok"]:



                ss.odp_page = 1



                st.rerun()



            else:



                show_error(result)





# ================================================================

# VIEW: TAMBAH / EDIT

# ================================================================



def render_form_view(edit_row=None):



    is_edit = (

        edit_row is not None

    )



    render_topbar(

        [

            "Data ODP",

            (

                "Edit Data"

                if is_edit

                else "Tambah Data"

            ),

        ]

    )



    st.title(

        "Perbarui Data ODP"

        if is_edit

        else "Tambah Data ODP"

    )



    st.caption(

        "Lengkapi informasi ODP "

        "dengan data yang sesuai."

    )



    with st.container(

        border=True

    ):



        with st.form(

            "form_odp"

        ):



            # ====================================================

            # INFORMASI DASAR

            # ====================================================



            st.markdown(

                "**📄 Informasi Dasar**"

            )



            fc1, fc2 = st.columns(2)



            with fc1:



                if is_edit:



                    st.text_input(

                        "ID ODP",

                        value=str(

                            edit_row[

                                "id_odp"

                            ]

                        ),

                        disabled=True,

                    )



                    f_id = (

                        edit_row[

                            "id_odp"

                        ]

                    )



                else:



                    f_id = (

                        st.number_input(

                            "ID ODP *",

                            min_value=1,

                            step=1,

                            format="%d",

                        )

                    )



                f_name = (

                    st.text_input(

                        "Kode / Nama ODP *",

                        value=(

                            edit_row[

                                "odp_name"

                            ]

                            if is_edit

                            else ""

                        ),

                        placeholder=(

                            "Contoh: "

                            "ODP-JKT-123"

                        ),

                    )

                )



            with fc2:



                current_status = (

                    normalize_status(

                        edit_row.get(

                            "occupancy_status"

                        )

                    )

                    if is_edit

                    else "GREEN"

                )



                status_index = (

                    STATUS_OPTIONS.index(

                        current_status

                    )

                    if current_status

                    in STATUS_OPTIONS

                    else 0

                )



                f_status = (

                    st.selectbox(

                        "Status ODP *",

                        options=(

                            STATUS_OPTIONS

                        ),

                        index=(

                            status_index

                        ),

                    )

                )



                f_witel = (

                    st.text_input(

                        "Wilayah / Witel",

                        value=(

                            (

                                edit_row.get(

                                    "witel"

                                )

                                or ""

                            )

                            if is_edit

                            else ""

                        ),

                        placeholder=(

                            "Contoh: MALANG"

                        ),

                    )

                )



            # ====================================================

            # INFORMASI LOKASI

            # ====================================================



            st.divider()



            st.markdown(

                "**📍 Informasi Lokasi**"

            )



            st.caption(

                "Masukkan koordinat lokasi "

                "ODP sesuai data sumber."

            )



            fc3, fc4 = st.columns(2)



            with fc3:



                f_lat = (

                    st.number_input(

                        "Latitude *",

                        value=(

                            float(

                                edit_row[

                                    "latitude"

                                ]

                            )

                            if is_edit

                            else -7.250445

                        ),

                        format="%.6f",

                    )

                )



            with fc4:



                f_lon = (

                    st.number_input(

                        "Longitude *",

                        value=(

                            float(

                                edit_row[

                                    "longitude"

                                ]

                            )

                            if is_edit

                            else 112.768845

                        ),

                        format="%.6f",

                    )

                )



            # ====================================================

            # KAPASITAS

            # ====================================================



            st.divider()



            st.markdown(

                "**🔋 Detail Kapasitas**"

            )



            fc5, fc6 = (

                st.columns(2)

            )



            with fc5:



                f_total = (

                    st.number_input(

                        "Kapasitas (Total)",

                        min_value=0,

                        step=1,

                        value=(

                            int(

                                edit_row.get(

                                    "total_port"

                                )

                                or 8

                            )

                            if is_edit

                            else 8

                        ),

                    )

                )



            with fc6:



                f_used = (

                    st.number_input(

                        "Port Terpakai",

                        min_value=0,

                        step=1,

                        value=(

                            int(

                                edit_row.get(

                                    "used_port"

                                )

                                or 0

                            )

                            if is_edit

                            else 0

                        ),

                    )

                )



            f_avai = max(

                f_total - f_used,

                0,

            )



            st.caption(

                f"Ketersediaan Port "

                f"(otomatis): "

                f"**{f_avai}** "

                f"dari {f_total}"

            )



            st.write("")



            bcol1, bcol2, _ = (

                st.columns(

                    [

                        1,

                        1,

                        3,

                    ]

                )

            )



            with bcol1:



                cancel = (

                    st.form_submit_button(

                        "Batal",

                        use_container_width=True,

                    )

                )



            with bcol2:



                submit = (

                    st.form_submit_button(

                        "💾 Simpan Data",

                        type="primary",

                        use_container_width=True,

                    )

                )



    # ============================================================

    # MAP PREVIEW

    # ============================================================



    if not is_edit:



        with st.expander(

            "🗺️ Pratinjau lokasi di peta"

        ):



            st.map(

                {

                    "lat": [

                        f_lat

                    ],

                    "lon": [

                        f_lon

                    ],

                },

                zoom=12,

            )



    # ============================================================

    # CANCEL

    # ============================================================



    if cancel:



        go("list")



        st.rerun()



    # ============================================================

    # SUBMIT

    # ============================================================



    if submit:



        f_name = (

            f_name.strip()

        )



        if not f_name:



            st.warning(

                "Kode / Nama ODP "

                "wajib diisi."

            )



            return



        if f_used > f_total:



            st.warning(

                "Port terpakai tidak boleh "

                "lebih besar dari kapasitas total."

            )



            return



        payload = {

            "odp_name": f_name,

            "latitude": f_lat,

            "longitude": f_lon,

            "available_port": int(

                f_avai

            ),

            "used_port": int(

                f_used

            ),

            "total_port": int(

                f_total

            ),

            "occupancy_status": (

                f_status

            ),

            "witel": (

                f_witel.strip()

                or None

            ),

        }



        # ========================================================

        # EDIT

        # ========================================================



        if is_edit:



            with st.spinner(

                "Menyimpan perubahan "

                "data ODP..."

            ):



                result = api_put(

                    (

                        "/api/admin/odp/"

                        f"{f_id}"

                    ),

                    json=payload,

                )



        # ========================================================

        # TAMBAH

        # ========================================================



        else:



            with st.spinner(

                "Menambahkan data ODP..."

            ):



                result = api_post(

                    "/api/admin/odp",

                    json={

                        "id_odp": int(

                            f_id

                        ),

                        **payload,

                    },

                )



        if result["ok"]:



            ss.odp_page = 1



            go(

                "sukses_edit"

                if is_edit

                else "sukses_tambah"

            )



            st.rerun()



        else:



            show_error(result)





# ================================================================

# VIEW: UPLOAD

# ================================================================



def render_upload_view():



    render_topbar(

        [

            "Data ODP",

            "Upload Data",

        ]

    )



    st.title(

        "Perbarui Data ODP"

    )



    st.write(

        "Gunakan file master ODP terbaru "

        "untuk memperbarui data TARA."

    )



    st.markdown(

        "**:red[Data tidak akan diperbarui "

        "sebelum Anda memeriksa dan "

        "mengonfirmasi file.]**"

    )



    with st.container(

        border=True

    ):



        upload_file = (

            st.file_uploader(

                (

                    "Tarik dan lepas file di sini, "

                    "atau pilih file dari perangkat"

                ),

                type=[

                    "csv",

                    "xlsx",

                    "xls",

                ],

                key="odp_uploader",

            )

        )



        st.caption(

            "Mendukung format CSV, XLSX, XLS "

            "(maksimal 50MB). Wilayah tiap baris "

            "ODP diambil otomatis dari kolom "

            "TELDA di file."

        )



        sheet_name = None



        if (

            upload_file is not None

            and upload_file.name.lower().endswith(

                (

                    ".xlsx",

                    ".xls",

                )

            )

        ):



            with st.expander(

                "Pengaturan lanjutan (opsional)"

            ):



                sheet_name = (

                    st.text_input(

                        "Nama sheet",

                        help=(

                            "Kosongkan agar sistem "

                            "memilih sheet data ODP "

                            "secara otomatis."

                        ),

                    )

                )



    fingerprint = None



    preview_ready = False



    if upload_file is not None:



        fingerprint = (

            hashlib.sha256(

                upload_file.getvalue()

            ).hexdigest()

        )



        preview_state = (

            ss.get(

                "odp_preview"

            )

            or {}

        )



        preview_ready = (

            preview_state.get(

                "fingerprint"

            )

            == fingerprint

            and preview_state.get(

                "sheet_name"

            )

            == (

                sheet_name

                or None

            )

        )



        if preview_ready:



            preview_data = (

                preview_state.get(

                    "data",

                    {},

                )

            )



            st.success(

                (

                    "Struktur file dikenali: "

                    f"{preview_data.get('row_count', 0):,} "

                    "baris, header pada baris "

                    f"{preview_data.get('header_row', '-')}, "

                    "sheet "

                    f"{preview_data.get('sheet', '-')} "

                    "dipilih otomatis."

                )

            )



            st.caption(

                "Kolom dikenali: "

                + ", ".join(

                    preview_data.get(

                        "columns",

                        [],

                    )

                )

            )



            st.dataframe(

                preview_data.get(

                    "preview",

                    [],

                ),

                use_container_width=True,

                hide_index=True,

            )



    st.write("")



    bcol1, bcol2, bcol3, _ = (

        st.columns(

            [

                1,

                1,

                1.4,

                2,

            ]

        )

    )



    # ============================================================

    # CANCEL UPLOAD

    # ============================================================



    with bcol1:



        if st.button(

            "Batal",

            use_container_width=True,

            key="cancel_upload_odp",

        ):



            go("list")



            st.rerun()



    # ============================================================

    # PREVIEW

    # ============================================================



    with bcol2:



        if st.button(

            "🔎 Periksa File",

            use_container_width=True,

            disabled=(

                upload_file

                is None

            ),

        ):



            with st.spinner(

                "Memeriksa sheet dan header "

                "tanpa mengubah database..."

            ):



                preview_result = (

                    api_upload(

                        "/api/admin/preview/odp",

                        upload_file.getvalue(),

                        upload_file.name,

                        extra_data=(

                            {

                                "sheet":

                                sheet_name

                            }

                            if sheet_name

                            else None

                        ),

                    )

                )



            if preview_result["ok"]:



                ss.odp_preview = {

                    "fingerprint": (

                        fingerprint

                    ),

                    "sheet_name": (

                        sheet_name

                        or None

                    ),

                    "data": (

                        preview_result[

                            "data"

                        ].get(

                            "data",

                            {},

                        )

                    ),

                }



                st.rerun()



            else:



                show_error(

                    preview_result

                )



    # ============================================================

    # PROCESS UPLOAD

    # ============================================================



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

                else (

                    "Periksa file terlebih dahulu "

                    "sebelum mengunggah."

                )

            ),

        ):



            with st.spinner(

                "Mengirim file ke server..."

            ):



                result = api_upload(

                    "/api/admin/upload/odp",

                    upload_file.getvalue(),

                    upload_file.name,

                    extra_data=(

                        {

                            "sheet":

                            sheet_name

                        }

                        if sheet_name

                        else None

                    ),

                )



            if not result["ok"]:



                show_error(

                    result

                )



            else:



                if upload_is_finished(

                    result

                ):



                    ss.odp_upload_row_count = (

                        upload_row_count(

                            result

                        )

                    )



                    ss.odp_preview = None



                    go(

                        "sukses_upload"

                    )



                    st.rerun()



                batch_id = (

                    result[

                        "data"

                    ].get(

                        "batch_id"

                    )

                )



                if not batch_id:



                    ss.odp_upload_error = (

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

                        "File diterima, sedang "

                        "diproses server "

                        "(bronze → silver → "

                        "enrich nearest ODP)... "

                        "Mohon tunggu, jangan "

                        "tutup atau restart backend."

                    ):



                        poll_result = (

                            poll_upload_status(

                                batch_id

                            )

                        )



                    if (

                        poll_result[

                            "status"

                        ]

                        == "success"

                    ):



                        ss.odp_upload_row_count = (

                            (

                                poll_result[

                                    "data"

                                ]

                                or {}

                            ).get(

                                "row_count"

                            )

                        )



                        ss.odp_preview = (

                            None

                        )



                        go(

                            "sukses_upload"

                        )



                        st.rerun()



                    elif (

                        poll_result[

                            "status"

                        ]

                        == "failed"

                    ):



                        ss.odp_upload_error = (

                            (

                                poll_result[

                                    "data"

                                ]

                                or {}

                            ).get(

                                "notes"

                            )

                            or (

                                "Proses gagal, "

                                "tidak ada detail "

                                "error dari server."

                            )

                        )



                        go(

                            "gagal_upload"

                        )



                        st.rerun()



                    else:



                        ss.odp_upload_batch_id = (

                            batch_id

                        )



                        go(

                            "proses_lama_upload"

                        )



                        st.rerun()





# ================================================================

# VIEW: LIST

# ================================================================



def render_list_view():



    can_create = (

        api_supports(

            "post",

            "/api/admin/odp",

        )

    )



    can_update = (

        api_supports(

            "put",

            (

                "/api/admin/odp/"

                "{id_odp}"

            ),

        )

    )



    can_delete = (

        api_supports(

            "delete",

            (

                "/api/admin/odp/"

                "{id_odp}"

            ),

        )

    )



    render_topbar(

        [

            "Data ODP"

        ]

    )



    hcol1, hcol2 = (

        st.columns(

            [

                3,

                2,

            ]

        )

    )



    with hcol1:



        st.title(

            "Data ODP"

        )



        st.caption(

            "Kelola data infrastruktur "

            "ODP yang digunakan oleh TARA."

        )



    with hcol2:



        st.write("")



        bcol1, bcol2 = (

            st.columns(2)

        )



        with bcol1:



            if st.button(

                "➕ Tambah ODP",

                use_container_width=True,

                disabled=(

                    not can_create

                ),

                help=(

                    None

                    if can_create

                    else (

                        "Backend yang aktif "

                        "belum menyediakan "

                        "fitur tambah manual."

                    )

                ),

            ):



                ss.odp_edit_row = (

                    None

                )



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



    # ============================================================

    # FILTER

    # ============================================================



    witel_result = (

        api_get(

            "/api/admin/odp/witel-list"

        )

    )



    witel_options = [

        "Wilayah"

    ]



    if witel_result["ok"]:



        witel_options += (

            witel_result[

                "data"

            ].get(

                "data",

                [],

            )

        )



    fcol1, fcol2, fcol3 = (

        st.columns(

            [

                3,

                1.2,

                1.2,

            ]

        )

    )



    with fcol1:



        query = (

            st.text_input(

                "Cari",

                label_visibility=(

                    "collapsed"

                ),

                placeholder=(

                    "🔍  Cari kode atau nama ODP..."

                ),

            )

        )



    with fcol2:



        status_filter = (

            st.selectbox(

                "Status ODP",

                options=(

                    [

                        "Status ODP"

                    ]

                    + STATUS_OPTIONS

                ),

                label_visibility=(

                    "collapsed"

                ),

            )

        )



    with fcol3:



        witel_filter = (

            st.selectbox(

                "Wilayah",

                options=(

                    witel_options

                ),

                label_visibility=(

                    "collapsed"

                ),

            )

        )



    # ============================================================

    # API PARAMS

    # ============================================================



    params = (

        pagination_params(

            query=query,

            page=(

                ss.odp_page

            ),

            page_size=(

                PAGE_SIZE

            ),

        )

    )



    if (

        witel_filter

        and witel_filter

        != "Wilayah"

    ):



        params[

            "witel"

        ] = (

            witel_filter

        )



    if (

        status_filter

        and status_filter

        != "Status ODP"

    ):



        params[

            "status"

        ] = (

            status_filter

        )



    # ============================================================

    # GET DATA

    # ============================================================



    result = api_get(

        "/api/admin/odp",

        params=params,

    )



    if not result["ok"]:



        show_error(

            result

        )



        return



    rows, total = (

        collection_payload(

            result

        )

    )



    rows = [

        normalize_odp_row(

            row

        )

        for row in rows

    ]



    exact_total_available = (

        total is not None

    )



    if total is None:



        offset = (

            (

                ss.odp_page

                - 1

            )

            * PAGE_SIZE

        )



        total = (

            offset

            + len(rows)

            + (

                PAGE_SIZE

                if len(rows)

                == PAGE_SIZE

                else 0

            )

        )



    # ============================================================

    # TABLE

    # ============================================================



    with st.container(

        border=True

    ):



        if not rows:



            st.info(

                "📭 Belum ada data ODP yang cocok. "

                "Tambah data manual atau upload file "

                "di atas."

            )



        else:



            hdr = st.columns(

                [

                    2,

                    1.1,

                    1.1,

                    1.3,

                    1.8,

                    0.8,

                ]

            )



            for c, label in zip(

                hdr,

                [

                    "Kode / Nama ODP",

                    "Latitude",

                    "Longitude",

                    "Status ODP",

                    "Ketersediaan Port",

                    "Aksi",

                ],

            ):



                c.markdown(

                    f"**{label}**"

                )



            st.markdown(

                (

                    "<hr style='"

                    "margin:4px 0;"

                    "'>"

                ),

                unsafe_allow_html=True,

            )



            # ====================================================

            # ROWS

            # ====================================================



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

                        2,

                        1.1,

                        1.1,

                        1.3,

                        1.8,

                        0.8,

                    ]

                )



                # ================================================

                # NAMA ODP

                # ================================================



                with c1:



                    st.write(

                        row[

                            "odp_name"

                        ]

                    )



                    st.caption(

                        row.get(

                            "witel"

                        )

                        or (

                            f"ID "

                            f"{row['id_odp']}"

                        )

                    )



                # ================================================

                # LATITUDE

                # ================================================



                c2.write(

                    f"{row['latitude']:.4f}"

                )



                # ================================================

                # LONGITUDE

                # ================================================



                c3.write(

                    f"{row['longitude']:.4f}"

                )



                # ================================================

                # STATUS

                # ================================================



                with c4:



                    st.markdown(

                        status_badge(

                            row.get(

                                "occupancy_status"

                            )

                        ),

                        unsafe_allow_html=True,

                    )



                # ================================================

                # PORT

                # ================================================



                with c5:



                    total_port = (

                        row.get(

                            "total_port"

                        )

                        or row.get(

                            "available_port"

                        )

                        or 1

                    )



                    available_port = (

                        row.get(

                            "available_port"

                        )

                        or 0

                    )



                    used = max(

                        total_port

                        - available_port,

                        0,

                    )



                    pc1, pc2 = (

                        st.columns(

                            [

                                3,

                                1,

                            ]

                        )

                    )



                    with pc1:



                        st.progress(

                            (

                                min(

                                    used

                                    / total_port,

                                    1.0,

                                )

                                if total_port

                                else 0.0

                            )

                        )



                    with pc2:



                        st.caption(

                            (

                                f"{available_port}"

                                f"/{total_port}"

                            )

                        )



                # ================================================

                # ACTIONS

                # ================================================



                with c6:



                    ac1, ac2 = (

                        st.columns(2)

                    )



                    # EDIT

                    with ac1:



                        if st.button(

                            "✏️",

                            key=(

                                f"edit_"

                                f"{row['id_odp']}"

                            ),

                            help="Edit",

                            disabled=(

                                not can_update

                            ),

                        ):



                            ss.odp_edit_row = (

                                row

                            )



                            go(

                                "edit"

                            )



                            st.rerun()



                    # DELETE

                    with ac2:



                        if st.button(

                            "🗑️",

                            key=(

                                f"del_"

                                f"{row['id_odp']}"

                            ),

                            help="Hapus",

                            disabled=(

                                not can_delete

                            ),

                        ):



                            confirm_delete_dialog(

                                row

                            )



    # ============================================================
    # PAGINATION
    # ============================================================

    render_pagination(
        total=total,
        page_size=PAGE_SIZE,
        page_key="odp_page",
        item_label="data ODP",
    )


# ================================================================

# ROUTER

# ================================================================



render_sidebar(

    "Data ODP"

)



view = (

    ss.odp_view

)





# ================================================================

# LIST

# ================================================================



if view == "list":



    render_list_view()





# ================================================================

# TAMBAH

# ================================================================



elif view == "tambah":



    render_form_view(

        edit_row=None

    )





# ================================================================

# EDIT

# ================================================================



elif view == "edit":



    render_form_view(

        edit_row=(

            ss.odp_edit_row

        )

    )





# ================================================================

# UPLOAD

# ================================================================



elif view == "upload":



    render_upload_view()





# ================================================================

# SUKSES TAMBAH

# ================================================================



elif view == "sukses_tambah":



    render_topbar(

        [

            "Data ODP",

            "Tambah Data",

        ]

    )



    st.title(

        "Tambah Data ODP"

    )



    st.caption(

        "Proses penambahan data ODP "

        "telah selesai dilakukan."

    )



    success_screen(

        "Data ODP berhasil ditambahkan",

        (

            "Data terbaru sudah tersedia "

            "untuk digunakan oleh TARA."

        ),

        "Lihat Data ODP",

        "pages/2_Data_ODP.py",

    )



    ss.odp_view = (

        "list"

    )





# ================================================================

# SUKSES EDIT

# ================================================================



elif view == "sukses_edit":



    render_topbar(

        [

            "Data ODP",

            "Edit Data",

        ]

    )



    st.title(

        "Perbarui Data ODP"

    )



    st.caption(

        "Proses pembaruan data ODP "

        "telah selesai dilakukan."

    )



    success_screen(

        "Data ODP berhasil diperbarui",

        (

            "Data terbaru sudah tersedia "

            "untuk digunakan oleh TARA."

        ),

        "Lihat Data ODP",

        "pages/2_Data_ODP.py",

    )



    ss.odp_view = (

        "list"

    )





# ================================================================

# SUKSES UPLOAD

# ================================================================



elif view == "sukses_upload":



    render_topbar(

        [

            "Data ODP",

            "Upload Data",

        ]

    )



    st.title(

        "Perbarui Data ODP"

    )



    st.caption(

        "Proses pembaruan data ODP "

        "telah selesai dilakukan."

    )



    _row_count = (

        ss.get(

            "odp_upload_row_count"

        )

    )



    _msg = (

        "Data terbaru sudah tersedia "

        "untuk digunakan oleh TARA."

    )



    if _row_count is not None:



        _msg += (

            f" Total data ODP sekarang: "

            f"{_row_count:,}"

            .replace(

                ",",

                ".",

            )

            + " baris."

        )



    success_screen(

        "Data ODP berhasil diperbarui",

        _msg,

        "Lihat Data ODP",

        "pages/2_Data_ODP.py",

    )



    ss.odp_view = (

        "list"

    )





# ================================================================

# GAGAL UPLOAD

# ================================================================



elif view == "gagal_upload":



    render_topbar(

        [

            "Data ODP",

            "Upload Data",

        ]

    )



    st.title(

        "Perbarui Data ODP"

    )



    st.caption(

        "Proses pembaruan data ODP "

        "mengalami masalah."

    )



    error_screen(

        "Upload data ODP gagal",

        (

            ss.get(

                "odp_upload_error"

            )

            or (

                "Terjadi kesalahan "

                "yang tidak diketahui."

            )

        ),

        "Lihat Data ODP",

        "pages/2_Data_ODP.py",

        retry_view_setter=(

            lambda: go(

                "upload"

            )

        ),

    )





# ================================================================

# PROSES UPLOAD LAMA

# ================================================================



elif view == "proses_lama_upload":



    render_topbar(

        [

            "Data ODP",

            "Upload Data",

        ]

    )



    st.title(

        "Perbarui Data ODP"

    )



    pending_screen(

        "Masih diproses server",

        ss.get(

            "odp_upload_batch_id",

            "-",

        ),

        "Lihat Data ODP",

        "pages/2_Data_ODP.py",

    )