import pandas as pd
import streamlit as st

from utils.api_client import (
    api_get,
    show_error,
    check_capability,
)
from utils.ui import (
    inject_css,
    render_sidebar,
    render_topbar,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Data Prospek - TARA",
    page_icon="📍",
    layout="wide",
)


# ============================================================
# GLOBAL UI
# ============================================================

inject_css()

render_sidebar(
    "Data Prospek"
)

render_topbar(
    [
        "Data Prospek"
    ]
)


# ============================================================
# PAGE CSS
# ============================================================

st.html(
    """
    <style>

    /* ========================================================
       KPI CARD - STANDARD TARA
       ======================================================== */

    .prospect-kpi {
        min-height: 188px;

        padding:
            20px
            22px
            18px
            22px;

        box-sizing:
            border-box;

        background:
            #FFFFFF;

        border:
            1px solid
            #E2E6EB;

        border-radius:
            14px;

        box-shadow:
            0 3px 12px
            rgba(15, 23, 42, 0.025);

        display:
            flex;

        flex-direction:
            column;
    }


    /* ========================================================
       KPI HEADER
       ======================================================== */

    .prospect-kpi-header {
        display:
            flex;

        align-items:
            center;

        gap:
            11px;
    }


    /* ========================================================
       KPI ICON
       ======================================================== */

    .prospect-kpi-icon {
        width:
            38px;

        height:
            38px;

        display:
            flex;

        align-items:
            center;

        justify-content:
            center;

        flex-shrink:
            0;

        border-radius:
            10px;

        font-size:
            1rem;

        font-weight:
            700;
    }


    .prospect-kpi-icon.neutral {
        background:
            #F0F1F3;

        color:
            #667085;
    }


    .prospect-kpi-icon.purple {
        background:
            #F1ECFA;

        color:
            #7153A6;
    }


    .prospect-kpi-icon.green {
        background:
            #E6F6EE;

        color:
            #16865B;
    }


    /* ========================================================
       KPI LABEL
       ======================================================== */

    .prospect-kpi-label {
        color:
            #68717F;

        font-size:
            0.72rem;

        font-weight:
            750;

        letter-spacing:
            0.035em;

        text-transform:
            uppercase;
    }


    /* ========================================================
       KPI VALUE
       ======================================================== */

    .prospect-kpi-value {
        margin-top:
            17px;

        color:
            #20242E;

        font-size:
            1.95rem;

        font-weight:
            800;

        line-height:
            1.05;
    }


    .prospect-kpi-value.purple {
        color:
            #7153A6;
    }


    .prospect-kpi-value.green {
        color:
            #16865B;
    }


    /* ========================================================
       KPI CAPTION
       ======================================================== */

    .prospect-kpi-caption {
        margin-top:
            auto;

        padding-top:
            18px;

        color:
            #969EA9;

        font-size:
            0.70rem;

        line-height:
            1.45;
    }


    /* ========================================================
       DETAIL PROSPEK
       ======================================================== */

    .prospect-detail-title {
        margin-top:
            8px;

        margin-bottom:
            12px;

        color:
            #20242E;

        font-size:
            1.05rem;

        font-weight:
            750;
    }


    /* ========================================================
       RESPONSIVE
       ======================================================== */

    @media(max-width: 900px) {

        .prospect-kpi {
            min-height:
                165px;
        }

    }

    </style>
    """
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "Data Prospek"
)

st.caption(
    "Data calon pelanggan potensial yang dapat ditindaklanjuti sales, "
    "dilengkapi informasi ODP terdekat sebagai pendukung prospecting."
)


# ============================================================
# CEK ENDPOINT
# ============================================================

if not check_capability(
    "/api/prospects/search"
):

    st.warning(
        "🚧 **Data Prospek belum dapat diakses.** "
        "Endpoint `/api/prospects/search` belum tersedia "
        "pada backend yang sedang aktif."
    )

    st.stop()


# ============================================================
# FILTER
# ============================================================

col1, col2 = st.columns(
    [
        3,
        1,
    ]
)


with col1:

    query = st.text_input(
        "Cari",
        key="prospect_q",
        label_visibility="collapsed",
        placeholder="Cari nama prospek...",
    )


with col2:

    wilayah_filter = st.text_input(
        "Wilayah",
        key="prospect_wilayah",
        label_visibility="collapsed",
        placeholder="Filter wilayah...",
    )


# ============================================================
# REQUEST KE BACKEND
#
# Endpoint:
# GET /api/prospects/search
#
# Parameter:
# - query
# - wilayah
# - limit
# ============================================================

params = {
    "limit": 20
}


if query:

    params[
        "query"
    ] = query


if wilayah_filter:

    params[
        "wilayah"
    ] = wilayah_filter


result = api_get(
    "/api/prospects/search",
    params=params,
)


# ============================================================
# HASIL
# ============================================================

if not result["ok"]:

    show_error(
        result
    )


else:

    payload = result[
        "data"
    ]

    raw_rows = payload.get(
        "data",
        [],
    )


    # ========================================================
    # DATA KOSONG
    # ========================================================

    if not raw_rows:

        st.info(
            "Tidak ada data prospek yang sesuai "
            "dengan pencarian."
        )


    # ========================================================
    # DATA TERSEDIA
    # ========================================================

    else:

        rows = []


        for item in raw_rows:

            prospect = (
                item.get(
                    "prospect"
                )
                or {}
            )

            odp = (
                item.get(
                    "nearest_odp"
                )
                or {}
            )


            # =================================================
            # JARAK ODP
            # =================================================

            distance = odp.get(
                "distance_m"
            )


            if distance is not None:

                try:

                    distance = round(
                        float(
                            distance
                        ),
                        2,
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    pass


            # =================================================
            # SCORE CBASE
            # =================================================

            match_score = (
                prospect.get(
                    "customer_match_score"
                )
            )


            if match_score is not None:

                try:

                    match_score = round(
                        float(
                            match_score
                        ),
                        2,
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    pass


            # =================================================
            # ROW
            # =================================================

            rows.append(
                {
                    "ID": prospect.get(
                        "id"
                    ),

                    "Nama Prospek": prospect.get(
                        "name"
                    ),

                    "Kategori": prospect.get(
                        "kategori"
                    ),

                    "Alamat": prospect.get(
                        "alamat"
                    ),

                    "Wilayah": prospect.get(
                        "wilayah"
                    ),

                    "Latitude": prospect.get(
                        "latitude"
                    ),

                    "Longitude": prospect.get(
                        "longitude"
                    ),

                    "Status CBASE": prospect.get(
                        "customer_match_status"
                    ),

                    "Score CBASE": match_score,

                    "ODP Terdekat": odp.get(
                        "name"
                    ),

                    "Jarak ODP (m)": distance,

                    "Port Tersedia": odp.get(
                        "available_port"
                    ),

                    "Status ODP": odp.get(
                        "status"
                    ),
                }
            )


        df = pd.DataFrame(
            rows
        )


        # ====================================================
        # RINGKASAN
        # ====================================================

        jumlah_wilayah = (
            df[
                "Wilayah"
            ]
            .dropna()
            .nunique()
        )


        odp_available = (
            df[
                "ODP Terdekat"
            ]
            .notna()
            .sum()
        )


        m1, m2, m3 = st.columns(
            3,
            gap="medium",
        )


        # ====================================================
        # KPI 1 - PROSPEK DITAMPILKAN
        # ====================================================

        with m1:

            st.html(
                f"""
                <div class="prospect-kpi">

                    <div class="prospect-kpi-header">

                        <div class="
                            prospect-kpi-icon
                            neutral
                        ">
                            📍
                        </div>

                        <div class="
                            prospect-kpi-label
                        ">
                            Prospek Ditampilkan
                        </div>

                    </div>

                    <div class="
                        prospect-kpi-value
                    ">
                        {len(df)}
                    </div>

                    <div class="
                        prospect-kpi-caption
                    ">
                        Data prospek dari hasil
                        pencarian backend TARA.
                    </div>

                </div>
                """
            )


        # ====================================================
        # KPI 2 - WILAYAH
        # ====================================================

        with m2:

            st.html(
                f"""
                <div class="prospect-kpi">

                    <div class="prospect-kpi-header">

                        <div class="
                            prospect-kpi-icon
                            purple
                        ">
                            🗺️
                        </div>

                        <div class="
                            prospect-kpi-label
                        ">
                            Wilayah
                        </div>

                    </div>

                    <div class="
                        prospect-kpi-value
                        purple
                    ">
                        {jumlah_wilayah}
                    </div>

                    <div class="
                        prospect-kpi-caption
                    ">
                        Jumlah wilayah yang tercakup
                        pada data prospek ditampilkan.
                    </div>

                </div>
                """
            )


        # ====================================================
        # KPI 3 - ODP TERDEKAT
        # ====================================================

        with m3:

            st.html(
                f"""
                <div class="prospect-kpi">

                    <div class="prospect-kpi-header">

                        <div class="
                            prospect-kpi-icon
                            green
                        ">
                            📡
                        </div>

                        <div class="
                            prospect-kpi-label
                        ">
                            Memiliki ODP Terdekat
                        </div>

                    </div>

                    <div class="
                        prospect-kpi-value
                        green
                    ">
                        {int(odp_available)}
                    </div>

                    <div class="
                        prospect-kpi-caption
                    ">
                        Prospek yang telah memiliki
                        informasi ODP terdekat.
                    </div>

                </div>
                """
            )


        st.write("")


        # ====================================================
        # TABEL DATA PROSPEK
        # ====================================================

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )


        st.caption(
            f"Menampilkan {len(df)} data prospek "
            "dari hasil pencarian backend."
        )


        # ====================================================
        # DETAIL PROSPEK
        # ====================================================

        st.write("")

        st.subheader(
            "Detail Prospek"
        )


        if not df.empty:

            # =================================================
            # PILIHAN PROSPEK
            # =================================================

            prospect_options = {}


            for _, row in df.iterrows():

                prospect_id = row[
                    "ID"
                ]

                nama = row[
                    "Nama Prospek"
                ]


                if (
                    pd.isna(
                        nama
                    )
                    or str(
                        nama
                    ).strip()
                    == ""
                ):

                    nama = (
                        "Tanpa Nama"
                    )


                # ---------------------------------------------
                # ID
                # ---------------------------------------------

                try:

                    prospect_id_label = int(
                        prospect_id
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    prospect_id_label = (
                        prospect_id
                    )


                label = (
                    f"{prospect_id_label} "
                    f"- {nama}"
                )


                prospect_options[
                    label
                ] = prospect_id


            selected_label = st.selectbox(
                "Pilih Prospek",
                options=list(
                    prospect_options.keys()
                ),
                key="selected_prospect_detail",
            )


            selected_id = (
                prospect_options[
                    selected_label
                ]
            )


            selected = df[
                df[
                    "ID"
                ]
                == selected_id
            ].iloc[0]


            # =================================================
            # HELPER DISPLAY
            # =================================================

            def display_value(
                value,
                default="-",
            ):

                if value is None:

                    return default


                try:

                    if pd.isna(
                        value
                    ):

                        return default

                except Exception:

                    pass


                if (
                    str(
                        value
                    )
                    .strip()
                    == ""
                ):

                    return default


                return value


            # =================================================
            # DETAIL 2 KOLOM
            # =================================================

            d1, d2 = st.columns(
                2,
                gap="large",
            )


            # =================================================
            # DETAIL KIRI
            # =================================================

            with d1:

                st.markdown(
                    f"**Nama Prospek:** "
                    f"{display_value(selected['Nama Prospek'])}"
                )


                st.markdown(
                    f"**Kategori:** "
                    f"{display_value(selected['Kategori'])}"
                )


                st.markdown(
                    f"**Wilayah:** "
                    f"{display_value(selected['Wilayah'])}"
                )


                st.markdown(
                    f"**Alamat:** "
                    f"{display_value(selected['Alamat'])}"
                )


                st.markdown(
                    f"**Status CBASE:** "
                    f"{display_value(selected['Status CBASE'])}"
                )


                st.markdown(
                    f"**Score CBASE:** "
                    f"{display_value(selected['Score CBASE'])}"
                )


            # =================================================
            # DETAIL KANAN
            # =================================================

            with d2:

                st.markdown(
                    f"**ODP Terdekat:** "
                    f"{display_value(selected['ODP Terdekat'])}"
                )


                jarak = display_value(
                    selected[
                        "Jarak ODP (m)"
                    ]
                )


                if jarak != "-":

                    jarak = (
                        f"{jarak} meter"
                    )


                st.markdown(
                    f"**Jarak ODP:** "
                    f"{jarak}"
                )


                st.markdown(
                    f"**Port Tersedia:** "
                    f"{display_value(selected['Port Tersedia'])}"
                )


                st.markdown(
                    f"**Status ODP:** "
                    f"{display_value(selected['Status ODP'])}"
                )


                latitude = display_value(
                    selected[
                        "Latitude"
                    ]
                )


                longitude = display_value(
                    selected[
                        "Longitude"
                    ]
                )


                st.markdown(
                    f"**Koordinat:** "
                    f"{latitude}, {longitude}"
                )