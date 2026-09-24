from datetime import datetime

import streamlit as st

from utils.api_client import api_get
from utils.auth import current_admin
from utils.ui import (
    inject_css,
    render_sidebar,
    render_topbar,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Dashboard - TARA",
    page_icon="🔴",
    layout="wide",
)


# ============================================================
# GLOBAL UI
# ============================================================

inject_css()


# ============================================================
# HOME CSS
# ============================================================

HOME_CSS = """
<style>

/* ==========================================================
   HOME HEADER
   ========================================================== */

.home-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;

    gap: 20px;

    margin-top: 4px;
    margin-bottom: 4px;
}

.home-title {
    color: #20242E;

    font-size: 2.35rem;
    font-weight: 760;

    line-height: 1.15;

    letter-spacing: -0.025em;
}

.home-subtitle {
    margin-top: 8px;

    color: #8A929F;

    font-size: 0.88rem;
}


/* ==========================================================
   SYSTEM STATUS
   ========================================================== */

.home-system-pill {
    display: inline-flex;

    align-items: center;

    gap: 7px;

    padding: 7px 13px;

    border-radius: 999px;

    background: #E8F7ED;

    color: #137A4E;

    font-size: 0.77rem;
    font-weight: 700;
}

.home-system-dot {
    width: 8px;
    height: 8px;

    border-radius: 50%;

    background: #25B66A;

    box-shadow:
        0 0 0 3px
        rgba(37, 182, 106, 0.11);
}


.home-system-pill-error {
    display: inline-flex;

    align-items: center;

    gap: 7px;

    padding: 7px 13px;

    border-radius: 999px;

    background: #FDEBEC;

    color: #BF252C;

    font-size: 0.77rem;
    font-weight: 700;
}

.home-system-dot-error {
    width: 8px;
    height: 8px;

    border-radius: 50%;

    background: #D92E35;
}


/* ==========================================================
   STAT CARDS
   ========================================================== */

.home-stat-card {
    min-height: 135px;

    padding: 18px 19px;

    border: 1px solid #E4E7EC;
    border-radius: 12px;

    background: #FFFFFF;
}

.home-stat-label {
    display: flex;

    align-items: center;

    gap: 7px;

    color: #596271;

    font-size: 0.78rem;
    font-weight: 650;
}

.home-stat-value {
    margin-top: 17px;

    color: #20242E;

    font-size: 1.55rem;
    font-weight: 730;

    line-height: 1.15;
}

.home-stat-value-success {
    margin-top: 17px;

    color: #159354;

    font-size: 1.55rem;
    font-weight: 730;

    line-height: 1.15;
}

.home-stat-caption {
    margin-top: 10px;

    color: #9AA2AD;

    font-size: 0.72rem;
}


/* ==========================================================
   MAIN CARDS
   ========================================================== */

.home-panel-title {
    color: #20242E;

    font-size: 1.25rem;
    font-weight: 730;

    margin-bottom: 4px;
}

.home-panel-subtitle {
    color: #838C98;

    font-size: 0.79rem;

    line-height: 1.5;

    margin-bottom: 18px;
}


/* make the two main cards visually balanced */

.st-key-home_manage_panel,
.st-key-home_activity_panel {
    min-height: 400px;
}


/* ==========================================================
   MANAGE CARDS
   ========================================================== */

.home-manage-item {
    min-height: 158px;

    padding: 18px;

    border: 1px solid #E3E6EB;
    border-radius: 11px;

    background: #FBFCFD;
}

.home-manage-label {
    display: flex;

    align-items: center;

    gap: 8px;

    color: #434C59;

    font-size: 0.84rem;
    font-weight: 700;
}

.home-manage-description {
    min-height: 48px;

    margin-top: 12px;

    color: #929AA6;

    font-size: 0.75rem;

    line-height: 1.55;
}


/* ==========================================================
   ACTIVITY
   ========================================================== */

.home-activity-header {
    display: flex;

    align-items: center;
    justify-content: space-between;

    gap: 10px;

    margin-bottom: 3px;
}

.home-activity-count {
    padding: 4px 9px;

    border-radius: 999px;

    color: #737C89;

    background: #F0F2F5;

    font-size: 0.68rem;
    font-weight: 650;
}

.home-activity-item {
    padding: 14px 2px;

    border-bottom: 1px solid #ECEEF1;
}

.home-activity-item:last-child {
    border-bottom: none;
}

.home-activity-title {
    display: flex;

    align-items: center;

    gap: 8px;

    color: #3D4653;

    font-size: 0.81rem;
    font-weight: 700;
}

.home-activity-meta {
    display: flex;

    align-items: center;

    gap: 8px;

    margin-top: 7px;

    color: #929AA6;

    font-size: 0.70rem;
}

.home-activity-detail {
    margin-top: 8px;

    color: #5F6875;

    font-size: 0.74rem;

    line-height: 1.5;

    display: -webkit-box;

    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;

    overflow: hidden;
}


/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media (max-width: 950px) {

    .st-key-home_manage_panel,
    .st-key-home_activity_panel {
        min-height: auto;
    }

}

</style>
"""


st.html(
    HOME_CSS
)


# ============================================================
# HELPERS
# ============================================================

MONTHS_ID = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def as_int(
    value,
    default=0,
):
    try:
        return int(
            value
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):
        return default


def format_number(
    value,
):
    return (
        f"{as_int(value):,}"
        .replace(
            ",",
            ".",
        )
    )


def parse_datetime(
    value,
):
    if not value:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    text = str(
        value
    ).strip()

    if text.endswith(
        "Z"
    ):
        text = (
            text[:-1]
            + "+00:00"
        )

    try:
        return datetime.fromisoformat(
            text
        )

    except ValueError:
        return None


def format_datetime_long(
    value,
):
    dt = parse_datetime(
        value
    )

    if dt is None:
        return "-"

    month = MONTHS_ID.get(
        dt.month,
        "",
    )

    return (
        f"{dt.day} "
        f"{month} "
        f"{dt.year}, "
        f"{dt.strftime('%H.%M')} WIB"
    )


def format_activity_time(
    value,
):
    dt = parse_datetime(
        value
    )

    if dt is None:
        return "-"

    return (
        f"{dt.day:02d} "
        f"{MONTHS_ID.get(dt.month, '')} "
        f"{dt.year} · "
        f"{dt.strftime('%H.%M')} WIB"
    )


def extract_activity_rows(
    response,
):
    """
    Dibuat toleran terhadap beberapa bentuk response API.
    """

    if not response.get(
        "ok"
    ):
        return []

    body = (
        response.get(
            "data"
        )
        or {}
    )

    if isinstance(
        body,
        list,
    ):
        return body

    if not isinstance(
        body,
        dict,
    ):
        return []

    data = body.get(
        "data"
    )

    if isinstance(
        data,
        list,
    ):
        return data

    if isinstance(
        data,
        dict,
    ):

        for key in (
            "items",
            "rows",
            "activities",
            "data",
        ):
            value = data.get(
                key
            )

            if isinstance(
                value,
                list,
            ):
                return value

    for key in (
        "items",
        "rows",
        "activities",
    ):
        value = body.get(
            key
        )

        if isinstance(
            value,
            list,
        ):
            return value

    return []


def safe_text(
    value,
):
    import html

    return html.escape(
        str(
            value
            or ""
        )
    )


# ============================================================
# SIDEBAR + TOPBAR
# ============================================================

render_sidebar(
    "Dashboard"
)

render_topbar(
    [
        "Dashboard"
    ]
)


# ============================================================
# LOAD DATA
# ============================================================

stats_result = api_get(
    "/api/admin/stats"
)


if stats_result.get(
    "ok"
):

    stats_body = (
        stats_result.get(
            "data"
        )
        or {}
    )

    stats = (
        stats_body.get(
            "data"
        )
        if isinstance(
            stats_body,
            dict,
        )
        and isinstance(
            stats_body.get(
                "data"
            ),
            dict,
        )
        else stats_body
    )

    if not isinstance(
        stats,
        dict,
    ):
        stats = {}

    system_ok = True

else:

    stats = {}

    system_ok = False


total_cbase = as_int(
    stats.get(
        "total_cbase",
        stats.get(
            "cbase_count",
            0,
        ),
    )
)

total_odp = as_int(
    stats.get(
        "total_odp",
        stats.get(
            "odp_count",
            0,
        ),
    )
)

last_update = (
    stats.get(
        "last_update"
    )
    or
    stats.get(
        "last_cbase_update"
    )
    or
    stats.get(
        "last_odp_update"
    )
)


# Dashboard cukup minta 3 aktivitas terakhir.
activity_result = api_get(
    "/api/admin/activity",
    params={
        "page": 1,
        "page_size": 3,
    },
)

activities = extract_activity_rows(
    activity_result
)

activities = activities[
    :3
]


# ============================================================
# HEADER
# ============================================================

head_left, head_right = st.columns(
    [
        5,
        1.4,
    ],
    vertical_alignment="center",
)


with head_left:

    st.html(
        """
        <div class="home-title">
            Dashboard
        </div>

        <div class="home-subtitle">
            Monitoring dan pengelolaan data TARA.
        </div>
        """
    )


with head_right:

    if system_ok:

        st.html(
            """
            <div style="
                display:flex;
                justify-content:flex-end;
            ">

                <div class="
                    home-system-pill
                ">

                    <span class="
                        home-system-dot
                    ">
                    </span>

                    Sistem Aktif

                </div>

            </div>
            """
        )

    else:

        st.html(
            """
            <div style="
                display:flex;
                justify-content:flex-end;
            ">

                <div class="
                    home-system-pill-error
                ">

                    <span class="
                        home-system-dot-error
                    ">
                    </span>

                    Sistem Bermasalah

                </div>

            </div>
            """
        )


st.write("")


# ============================================================
# SUMMARY STATISTICS
# ============================================================

s1, s2, s3, s4 = st.columns(
    4
)


with s1:

    st.html(
        f"""
        <div class="home-stat-card">

            <div class="home-stat-label">
                👥
                Data Pelanggan
            </div>

            <div class="home-stat-value">
                {format_number(total_cbase)}
            </div>

            <div class="home-stat-caption">
                Jumlah data pelanggan CBASE
            </div>

        </div>
        """
    )


with s2:

    st.html(
        f"""
        <div class="home-stat-card">

            <div class="home-stat-label">
                🔌
                Data ODP
            </div>

            <div class="home-stat-value">
                {format_number(total_odp)}
            </div>

            <div class="home-stat-caption">
                Jumlah data ODP
            </div>

        </div>
        """
    )


with s3:

    st.html(
        f"""
        <div class="home-stat-card">

            <div class="home-stat-label">
                🕘
                Pembaruan Terakhir
            </div>

            <div style="
                margin-top:17px;
                color:#20242E;
                font-size:.95rem;
                font-weight:700;
                line-height:1.4;
            ">
                {safe_text(
                    format_datetime_long(
                        last_update
                    )
                )}
            </div>

            <div class="home-stat-caption">
                Waktu pembaruan data terakhir
            </div>

        </div>
        """
    )


with s4:

    if system_ok:

        status_text = "Aktif"

        status_caption = (
            "Sistem berjalan normal"
        )

        value_class = (
            "home-stat-value-success"
        )

    else:

        status_text = (
            "Bermasalah"
        )

        status_caption = (
            "Backend tidak dapat diakses"
        )

        value_class = (
            "home-stat-value"
        )

    st.html(
        f"""
        <div class="home-stat-card">

            <div class="home-stat-label">
                🛡️
                Status Sistem
            </div>

            <div class="{value_class}">
                {status_text}
            </div>

            <div class="home-stat-caption">
                {status_caption}
            </div>

        </div>
        """
    )


st.write("")
st.write("")


# ============================================================
# MAIN CONTENT
# ============================================================

manage_col, activity_col = st.columns(
    [
        1.65,
        0.85,
    ],
    gap="large",
)


# ============================================================
# KELOLA DATA
# ============================================================

with manage_col:

    with st.container(
        border=True,
        key="home_manage_panel",
    ):

        st.html(
            """
            <div class="home-panel-title">
                Kelola Data TARA
            </div>

            <div class="home-panel-subtitle">

                Pilih data yang ingin dikelola
                dan dipantau melalui Dashboard TARA.

            </div>
            """
        )

        manage_1, manage_2 = (
            st.columns(
                2,
                gap="medium",
            )
        )


        # ----------------------------------------------------
        # CBASE
        # ----------------------------------------------------

        with manage_1:

            with st.container(
                border=True
            ):

                st.html(
                    """
                    <div class="home-manage-label">
                        👥
                        Data Pelanggan
                    </div>

                    <div class="
                        home-manage-description
                    ">

                        Kelola dan pantau data
                        pelanggan CBASE yang digunakan
                        oleh TARA.

                    </div>
                    """
                )

                if st.button(
                    "Kelola Data Pelanggan",
                    type="primary",
                    use_container_width=True,
                    key="home_manage_cbase",
                ):

                    st.switch_page(
                        "pages/1_Data_Pelanggan_CBASE.py"
                    )


        # ----------------------------------------------------
        # ODP
        # ----------------------------------------------------

        with manage_2:

            with st.container(
                border=True
            ):

                st.html(
                    """
                    <div class="home-manage-label">
                        🔌
                        Data ODP
                    </div>

                    <div class="
                        home-manage-description
                    ">

                        Kelola dan pantau data
                        infrastruktur ODP yang digunakan
                        oleh TARA.

                    </div>
                    """
                )

                if st.button(
                    "Kelola Data ODP",
                    type="primary",
                    use_container_width=True,
                    key="home_manage_odp",
                ):

                    st.switch_page(
                        "pages/2_Data_ODP.py"
                    )


        st.write("")

        st.caption(
            "Data yang diperbarui melalui dashboard "
            "akan digunakan oleh sistem TARA."
        )


# ============================================================
# AKTIVITAS TERBARU
# ============================================================

with activity_col:

    with st.container(
        border=True,
        key="home_activity_panel",
    ):

        st.html(
            """
            <div class="home-activity-header">

                <div class="
                    home-panel-title
                ">
                    Aktivitas Terbaru
                </div>

                <div class="
                    home-activity-count
                ">
                    3 terbaru
                </div>

            </div>

            <div class="
                home-panel-subtitle
            ">
                Ringkasan perubahan terakhir
                pada Dashboard TARA.
            </div>
            """
        )


        # ----------------------------------------------------
        # EMPTY
        # ----------------------------------------------------

        if not activities:

            st.info(
                "Belum ada aktivitas terbaru "
                "yang dapat ditampilkan."
            )


        # ----------------------------------------------------
        # ACTIVITY ITEMS
        # ----------------------------------------------------

        else:

            for activity in activities:

                action = (
                    activity.get(
                        "action"
                    )
                    or
                    activity.get(
                        "activity"
                    )
                    or
                    "Aktivitas Administrator"
                )

                admin_name = (
                    activity.get(
                        "admin_name"
                    )
                    or
                    activity.get(
                        "admin"
                    )
                    or
                    "Administrator"
                )

                detail = (
                    activity.get(
                        "detail"
                    )
                    or
                    activity.get(
                        "description"
                    )
                    or
                    "-"
                )

                created_at = (
                    activity.get(
                        "created_at"
                    )
                    or
                    activity.get(
                        "timestamp"
                    )
                )

                status = (
                    str(
                        activity.get(
                            "status"
                        )
                        or
                        "success"
                    )
                    .lower()
                )

                if status in (
                    "success",
                    "berhasil",
                ):

                    activity_icon = "✅"

                elif status in (
                    "failed",
                    "error",
                    "gagal",
                ):

                    activity_icon = "❌"

                else:

                    activity_icon = "ℹ️"


                st.html(
                    f"""
                    <div class="
                        home-activity-item
                    ">

                        <div class="
                            home-activity-title
                        ">

                            <span>
                                {activity_icon}
                            </span>

                            <span>
                                {safe_text(action)}
                            </span>

                        </div>


                        <div class="
                            home-activity-meta
                        ">

                            <span>
                                👤
                                {safe_text(admin_name)}
                            </span>

                            <span>
                                •
                            </span>

                            <span>
                                {
                                    safe_text(
                                        format_activity_time(
                                            created_at
                                        )
                                    )
                                }
                            </span>

                        </div>


                        <div class="
                            home-activity-detail
                        ">

                            {safe_text(detail)}

                        </div>

                    </div>
                    """
                )


        st.write("")


        if st.button(
            "Lihat Semua Aktivitas  →",
            use_container_width=True,
            key="home_all_activity",
        ):

            st.switch_page(
                "pages/4_Riwayat_Aktivitas.py"
            )