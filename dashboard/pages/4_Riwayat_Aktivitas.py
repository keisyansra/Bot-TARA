from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from utils.api_client import (
    api_get,
    show_error,
)

from utils.ui import (
    inject_css,
    render_sidebar,
    render_topbar,
    render_pagination,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Riwayat Aktivitas - TARA",
    page_icon="🕘",
    layout="wide",
)


# ============================================================
# GLOBAL STYLE
# ============================================================

inject_css()


ACTIVITY_CSS = """
<style>

/* ==========================================================
   PAGE HEADER
   ========================================================== */

.activity-page-title {
    margin-top: 2px;
    margin-bottom: 7px;

    color: #1F2937;

    font-size: 2.15rem;
    font-weight: 800;
    line-height: 1.15;

    letter-spacing: -0.025em;
}

.activity-page-subtitle {
    margin-bottom: 28px;

    color: #7B8491;

    font-size: 0.88rem;
    line-height: 1.6;
}


/* ==========================================================
   KPI CARD
   ========================================================== */

.activity-kpi-card {
    height: 190px;

    display: flex;
    flex-direction: column;
    justify-content: space-between;

    padding: 20px 22px;

    border: 1px solid #E2E6EB;
    border-radius: 14px;

    background: #FFFFFF;

    box-shadow:
        0 4px 14px
        rgba(15, 23, 42, 0.035);

    box-sizing: border-box;
}

.activity-kpi-header {
    display: flex;

    align-items: center;

    gap: 11px;
}

.activity-kpi-icon {
    width: 38px;
    height: 38px;

    display: flex;

    align-items: center;
    justify-content: center;

    flex-shrink: 0;

    border-radius: 10px;

    font-size: 1rem;
    font-weight: 800;
}

.activity-kpi-icon.total {
    color: #596270;

    background: #F1F3F5;
}

.activity-kpi-icon.success {
    color: #14804A;

    background: #E8F7ED;
}

.activity-kpi-icon.failed {
    color: #C9363E;

    background: #FDEBEC;
}

.activity-kpi-label {
    color: #68717F;

    font-size: 0.72rem;
    font-weight: 800;

    letter-spacing: 0.04em;
}

.activity-kpi-value {
    margin-top: 14px;

    color: #20242E;

    font-size: 2.05rem;
    font-weight: 800;

    line-height: 1;
}

.activity-kpi-value.success {
    color: #168451;
}

.activity-kpi-value.failed {
    color: #C93239;
}

.activity-kpi-description {
    color: #9098A5;

    font-size: 0.73rem;
    line-height: 1.5;
}


/* ==========================================================
   KPI BADGE
   ========================================================== */

.activity-kpi-badge {
    width: fit-content;

    display: inline-flex;

    align-items: center;

    gap: 6px;

    margin-top: 10px;

    padding: 5px 9px;

    border-radius: 999px;

    font-size: 0.68rem;
    font-weight: 700;
}

.activity-kpi-badge.success {
    color: #147A4D;

    background: #E8F7ED;
}

.activity-kpi-badge.failed {
    color: #C3272F;

    background: #FDEBEC;
}

.activity-kpi-badge.neutral {
    color: #66717F;

    background: #F1F3F5;
}

.activity-dot {
    width: 6px;
    height: 6px;

    display: inline-block;

    border-radius: 50%;
}

.activity-dot.success {
    background: #21B66B;
}

.activity-dot.failed {
    background: #E6373F;
}

.activity-dot.neutral {
    background: #8E98A5;
}


/* ==========================================================
   SECTION
   ========================================================== */

.activity-section {
    margin-top: 30px;
    margin-bottom: 13px;
}

.activity-section-title {
    color: #20242E;

    font-size: 1.08rem;
    font-weight: 750;
}

.activity-section-subtitle {
    margin-top: 4px;

    color: #929AA6;

    font-size: 0.75rem;
}


/* ==========================================================
   TABLE
   ========================================================== */

[data-testid="stDataFrame"] {
    overflow: hidden;

    border: 1px solid #E1E5EA;
    border-radius: 12px;

    background: #FFFFFF;

    box-shadow:
        0 3px 12px
        rgba(15, 23, 42, 0.025);
}


/* ==========================================================
   EMPTY
   ========================================================== */

.activity-empty {
    padding: 42px 20px;

    text-align: center;

    border: 1px solid #E1E5EA;
    border-radius: 12px;

    background: #FFFFFF;
}

.activity-empty-icon {
    font-size: 2rem;
}

.activity-empty-title {
    margin-top: 8px;

    color: #3E4754;

    font-size: 0.95rem;
    font-weight: 700;
}

.activity-empty-text {
    margin-top: 5px;

    color: #929AA6;

    font-size: 0.75rem;
}


/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media(max-width: 900px) {

    .activity-kpi-card {
        height: auto;
        min-height: 185px;
    }

}

</style>
"""


st.html(
    ACTIVITY_CSS
)


# ============================================================
# CONSTANTS
# ============================================================

PAGE_SIZE = 10

WIB = ZoneInfo(
    "Asia/Jakarta"
)

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


# ============================================================
# SESSION STATE
# ============================================================

ss = st.session_state

ss.setdefault(
    "activity_page",
    1,
)


# ============================================================
# HELPERS
# ============================================================

def format_number(
    value,
):

    try:

        return (
            f"{int(value):,}"
            .replace(
                ",",
                ".",
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return "0"


def parse_datetime(
    value,
):

    if not value:
        return None


    if isinstance(
        value,
        datetime,
    ):

        dt = value

    else:

        raw = (
            str(value)
            .strip()
        )

        if raw.endswith(
            "Z"
        ):

            raw = (
                raw[:-1]
                +
                "+00:00"
            )

        try:

            dt = (
                datetime.fromisoformat(
                    raw
                )
            )

        except Exception:

            return None


    if dt.tzinfo is None:

        dt = dt.replace(
            tzinfo=timezone.utc
        )


    try:

        return dt.astimezone(
            WIB
        )

    except Exception:

        return dt


def format_datetime_wib(
    value,
):

    dt = parse_datetime(
        value
    )


    if dt is None:

        return "-"


    return (
        f"{dt.day} "
        f"{MONTHS_ID.get(dt.month, '')} "
        f"{dt.year}, "
        f"{dt.strftime('%H.%M')} WIB"
    )


def normalize_activity_response(
    result,
):

    if not result.get(
        "ok"
    ):

        return (
            [],
            0,
        )


    body = (
        result.get(
            "data"
        )
        or {}
    )


    if isinstance(
        body,
        list,
    ):

        return (
            body,
            len(body),
        )


    if not isinstance(
        body,
        dict,
    ):

        return (
            [],
            0,
        )


    rows = (
        body.get(
            "data"
        )
    )

    total = (
        body.get(
            "total"
        )
    )


    if isinstance(
        rows,
        dict,
    ):

        nested = rows

        rows = (
            nested.get(
                "data"
            )
            or
            nested.get(
                "items"
            )
            or
            nested.get(
                "rows"
            )
            or
            []
        )

        if total is None:

            total = (
                nested.get(
                    "total"
                )
            )


    if not isinstance(
        rows,
        list,
    ):

        rows = (
            body.get(
                "items"
            )
            or
            body.get(
                "rows"
            )
            or
            body.get(
                "activities"
            )
            or
            []
        )


    if not isinstance(
        rows,
        list,
    ):

        rows = []


    if total is None:

        total = len(
            rows
        )


    try:

        total = int(
            total
        )

    except (
        TypeError,
        ValueError,
    ):

        total = len(
            rows
        )


    return (
        rows,
        total,
    )


def normalize_summary_response(
    result,
):

    if not result.get(
        "ok"
    ):

        return None


    body = (
        result.get(
            "data"
        )
        or {}
    )


    if (
        isinstance(
            body,
            dict,
        )
        and
        isinstance(
            body.get(
                "data"
            ),
            dict,
        )
    ):

        body = (
            body.get(
                "data"
            )
        )


    if not isinstance(
        body,
        dict,
    ):

        return None


    return {
        "total_activity":
            int(
                body.get(
                    "total_activity",
                    0,
                )
                or 0
            ),

        "total_success":
            int(
                body.get(
                    "total_success",
                    0,
                )
                or 0
            ),

        "total_failed":
            int(
                body.get(
                    "total_failed",
                    0,
                )
                or 0
            ),

        "success_rate":
            float(
                body.get(
                    "success_rate",
                    0,
                )
                or 0
            ),
    }


def kpi_card(
    *,
    icon,
    icon_type,
    label,
    value,
    description,
    value_type="",
    badge_text=None,
    badge_type="neutral",
):

    badge_html = ""

    if badge_text:

        badge_html = (
            f"""
            <div class="activity-kpi-badge {badge_type}">

                <span class="activity-dot {badge_type}">
                </span>

                {badge_text}

            </div>
            """
        )


    return (
        f"""
        <div class="activity-kpi-card">

            <div>

                <div class="activity-kpi-header">

                    <div class="activity-kpi-icon {icon_type}">
                        {icon}
                    </div>

                    <div class="activity-kpi-label">
                        {label}
                    </div>

                </div>


                <div class="activity-kpi-value {value_type}">
                    {value}
                </div>


                {badge_html}

            </div>


            <div class="activity-kpi-description">
                {description}
            </div>

        </div>
        """
    )


# ============================================================
# SIDEBAR
# ============================================================

render_sidebar(
    "Riwayat Aktivitas"
)


# ============================================================
# TOPBAR
# ============================================================

render_topbar(
    [
        "Riwayat Aktivitas",
    ]
)


# ============================================================
# HEADER
# ============================================================

st.html(
    """
    <div class="activity-page-title">
        Riwayat Aktivitas
    </div>

    <div class="activity-page-subtitle">
        Pantau seluruh aktivitas administratif
        dan perubahan data yang dilakukan melalui Dashboard TARA.
    </div>
    """
)


# ============================================================
# API SUMMARY
# ============================================================

summary_result = api_get(
    "/api/admin/activity-summary"
)

summary = (
    normalize_summary_response(
        summary_result
    )
)


# ============================================================
# API ACTIVITY
# ============================================================

activity_result = api_get(
    "/api/admin/activity",
    params={
        "page":
            ss.activity_page,

        "page_size":
            PAGE_SIZE,
    },
)


if not activity_result.get(
    "ok"
):

    show_error(
        activity_result
    )

    st.stop()


rows, list_total = (
    normalize_activity_response(
        activity_result
    )
)


# ============================================================
# SUMMARY FALLBACK
# ============================================================

if summary is None:

    summary = {
        "total_activity":
            list_total,

        "total_success":
            None,

        "total_failed":
            None,

        "success_rate":
            None,
    }


total_activity = (
    summary.get(
        "total_activity"
    )
    or 0
)

total_success = (
    summary.get(
        "total_success"
    )
)

total_failed = (
    summary.get(
        "total_failed"
    )
)

success_rate = (
    summary.get(
        "success_rate"
    )
)


# ============================================================
# KPI VALUES
# ============================================================

if total_success is None:

    success_value = "—"

    success_badge = (
        "Statistik belum tersedia"
    )

    success_badge_type = (
        "neutral"
    )

else:

    success_value = (
        format_number(
            total_success
        )
    )

    success_badge = (
        f"{success_rate:.1f}% dari seluruh aktivitas"
        if success_rate is not None
        else
        "Aktivitas berhasil"
    )

    success_badge_type = (
        "success"
    )


if total_failed is None:

    failed_value = "—"

    failed_badge = (
        "Statistik belum tersedia"
    )

    failed_badge_type = (
        "neutral"
    )


elif total_failed == 0:

    failed_value = "0"

    failed_badge = (
        "Tidak ada kegagalan"
    )

    failed_badge_type = (
        "neutral"
    )


else:

    failed_value = (
        format_number(
            total_failed
        )
    )

    failed_badge = (
        "Membutuhkan perhatian"
    )

    failed_badge_type = (
        "failed"
    )


# ============================================================
# KPI CARDS
# ============================================================

c1, c2, c3 = st.columns(
    3,
    gap="large",
)


with c1:

    st.html(
        kpi_card(
            icon="🕘",
            icon_type="total",
            label="TOTAL AKTIVITAS",
            value=format_number(
                total_activity
            ),
            description=(
                "Seluruh aktivitas administratif "
                "yang tercatat pada sistem TARA."
            ),
        )
    )


with c2:

    st.html(
        kpi_card(
            icon="✓",
            icon_type="success",
            label="BERHASIL",
            value=success_value,
            value_type="success",
            badge_text=success_badge,
            badge_type=success_badge_type,
            description=(
                "Aktivitas yang selesai "
                "tanpa kendala pada sistem."
            ),
        )
    )


with c3:

    st.html(
        kpi_card(
            icon="!",
            icon_type="failed",
            label="GAGAL",
            value=failed_value,
            value_type="failed",
            badge_text=failed_badge,
            badge_type=failed_badge_type,
            description=(
                "Aktivitas yang memerlukan "
                "pemeriksaan administrator."
            ),
        )
    )


# ============================================================
# TABLE SECTION
# ============================================================

st.html(
    """
    <div class="activity-section">

        <div class="activity-section-title">
            Daftar Aktivitas
        </div>

        <div class="activity-section-subtitle">
            Aktivitas terbaru ditampilkan terlebih dahulu.
        </div>

    </div>
    """
)


# ============================================================
# EMPTY
# ============================================================

if not rows:

    st.html(
        """
        <div class="activity-empty">

            <div class="activity-empty-icon">
                🕘
            </div>

            <div class="activity-empty-title">
                Belum ada aktivitas
            </div>

            <div class="activity-empty-text">
                Aktivitas administrator akan muncul di halaman ini.
            </div>

        </div>
        """
    )

    st.stop()


# ============================================================
# TABLE DATA
# ============================================================

table_data = []


for row in rows:

    status_raw = (
        str(
            row.get(
                "status"
            )
            or ""
        )
        .strip()
        .lower()
    )


    if status_raw in (
        "success",
        "berhasil",
    ):

        status_display = (
            "✅ Berhasil"
        )


    elif status_raw in (
        "failed",
        "gagal",
        "error",
    ):

        status_display = (
            "❌ Gagal"
        )


    elif status_raw in (
        "running",
        "processing",
    ):

        status_display = (
            "⏳ Diproses"
        )


    else:

        status_display = (
            str(
                row.get(
                    "status"
                )
                or "-"
            )
        )


    table_data.append(
        {
            "Waktu":
                format_datetime_wib(
                    row.get(
                        "created_at"
                    )
                    or
                    row.get(
                        "timestamp"
                    )
                ),

            "Admin":
                row.get(
                    "admin_name"
                )
                or
                row.get(
                    "admin"
                )
                or
                "Administrator",

            "Aktivitas":
                row.get(
                    "action"
                )
                or
                row.get(
                    "activity"
                )
                or
                "-",

            "Target":
                row.get(
                    "target_id"
                )
                or
                row.get(
                    "target"
                )
                or
                "-",

            "Detail":
                row.get(
                    "detail"
                )
                or
                row.get(
                    "description"
                )
                or
                "-",

            "Status":
                status_display,
        }
    )


df = pd.DataFrame(
    table_data
)


# ============================================================
# TABLE
# ============================================================

st.dataframe(
    df,
    hide_index=True,
    use_container_width=True,
    height=(
        min(
            470,
            48
            +
            len(df)
            * 37
        )
    ),
    column_config={
        "Waktu":
            st.column_config.TextColumn(
                "Waktu",
                width="medium",
            ),

        "Admin":
            st.column_config.TextColumn(
                "Admin",
                width="small",
            ),

        "Aktivitas":
            st.column_config.TextColumn(
                "Aktivitas",
                width="medium",
            ),

        "Target":
            st.column_config.TextColumn(
                "Target",
                width="small",
            ),

        "Detail":
            st.column_config.TextColumn(
                "Detail",
                width="large",
            ),

        "Status":
            st.column_config.TextColumn(
                "Status",
                width="small",
            ),
    },
)


# ============================================================
# PAGINATION
# ============================================================

render_pagination(
    total=total_activity,
    page_size=PAGE_SIZE,
    page_key="activity_page",
    item_label="aktivitas",
)