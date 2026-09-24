import pandas as pd
import streamlit as st

from utils.api_client import api_get, show_error, check_capability
from utils.ui import inject_css, render_sidebar, render_topbar


st.set_page_config(
    page_title="Data Prospek - TARA",
    page_icon="📍",
    layout="wide"
)

inject_css()
render_sidebar("Data Prospek")
render_topbar(["Data Prospek"])

st.title("Data Prospek")
st.caption(
    "Data prospek yang digunakan TARA untuk membantu sales "
    "menemukan calon pelanggan dan ODP terdekat."
)

st.caption(
    "Data ditampilkan langsung dari backend TARA yang berjalan "
    "pada server Docker."
)


# ============================================================
# CEK ENDPOINT
# ============================================================

if not check_capability("/api/prospects/search"):
    st.warning(
        "🚧 **Data Prospek belum dapat diakses.** "
        "Endpoint `/api/prospects/search` belum tersedia "
        "pada backend yang sedang aktif."
    )
    st.stop()


# ============================================================
# FILTER
# ============================================================

col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "Cari",
        key="prospect_q",
        label_visibility="collapsed",
        placeholder="Cari nama prospek..."
    )

with col2:
    wilayah_filter = st.text_input(
        "Wilayah",
        key="prospect_wilayah",
        label_visibility="collapsed",
        placeholder="Filter wilayah..."
    )


# ============================================================
# REQUEST KE BACKEND
# Endpoint asli backend:
# GET /api/prospects/search
#
# Parameter yang tersedia dari backend:
# query
# wilayah
# limit
# ============================================================

params = {
    "limit": 20
}

if query:
    params["query"] = query

if wilayah_filter:
    params["wilayah"] = wilayah_filter


result = api_get(
    "/api/prospects/search",
    params=params
)


# ============================================================
# HASIL
# ============================================================

if not result["ok"]:
    show_error(result)

else:
    payload = result["data"]

    raw_rows = payload.get("data", [])

    if not raw_rows:
        st.info(
            "Tidak ada data prospek yang sesuai dengan pencarian."
        )

    else:
        rows = []

        for item in raw_rows:
            prospect = item.get("prospect") or {}
            odp = item.get("nearest_odp") or {}

            distance = odp.get("distance_m")

            if distance is not None:
                try:
                    distance = round(float(distance), 2)
                except (TypeError, ValueError):
                    pass

            match_score = prospect.get(
                "customer_match_score"
            )

            if match_score is not None:
                try:
                    match_score = round(
                        float(match_score),
                        2
                    )
                except (TypeError, ValueError):
                    pass

            rows.append({
                "ID": prospect.get("id"),
                "Nama Prospek": prospect.get("name"),
                "Kategori": prospect.get("kategori"),
                "Alamat": prospect.get("alamat"),
                "Wilayah": prospect.get("wilayah"),

                "Latitude": prospect.get("latitude"),
                "Longitude": prospect.get("longitude"),

                "Status CBASE": prospect.get(
                    "customer_match_status"
                ),
                "Score CBASE": match_score,

                "ODP Terdekat": odp.get("name"),
                "Jarak ODP (m)": distance,
                "Port Tersedia": odp.get(
                    "available_port"
                ),
                "Status ODP": odp.get("status"),
            })

        df = pd.DataFrame(rows)

        # ====================================================
        # RINGKASAN
        # ====================================================

        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric(
                "Prospek Ditampilkan",
                len(df)
            )

        with m2:
            jumlah_wilayah = (
                df["Wilayah"]
                .dropna()
                .nunique()
            )

            st.metric(
                "Wilayah",
                jumlah_wilayah
            )

        with m3:
            odp_available = (
                df["ODP Terdekat"]
                .notna()
                .sum()
            )

            st.metric(
                "Memiliki ODP Terdekat",
                int(odp_available)
            )

        st.write("")

        # ====================================================
        # TABEL
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
        st.subheader("Detail Prospek")

        if not df.empty:

            # Buat pilihan yang lebih mudah dibaca:
            # "20201 - Nama Prospek"
            prospect_options = {}

            for _, row in df.iterrows():
                prospect_id = row["ID"]

                nama = row["Nama Prospek"]

                if pd.isna(nama) or str(nama).strip() == "":
                    nama = "Tanpa Nama"

                label = f"{int(prospect_id)} - {nama}"

                prospect_options[label] = prospect_id

            selected_label = st.selectbox(
                "Pilih Prospek",
                options=list(prospect_options.keys()),
                key="selected_prospect_detail",
            )

            selected_id = prospect_options[selected_label]

            selected = df[
                df["ID"] == selected_id
            ].iloc[0]

            # Helper agar NaN / None tidak muncul
            def display_value(value, default="-"):
                if value is None:
                    return default

                try:
                    if pd.isna(value):
                        return default
                except:
                    pass

                if str(value).strip() == "":
                    return default

                return value

            d1, d2 = st.columns(2)

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

            with d2:
                st.markdown(
                    f"**ODP Terdekat:** "
                    f"{display_value(selected['ODP Terdekat'])}"
                )

                jarak = display_value(
                    selected["Jarak ODP (m)"]
                )

                if jarak != "-":
                    jarak = f"{jarak} meter"

                st.markdown(
                    f"**Jarak ODP:** {jarak}"
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
                    selected["Latitude"]
                )

                longitude = display_value(
                    selected["Longitude"]
                )

                st.markdown(
                    f"**Koordinat:** "
                    f"{latitude}, {longitude}"
                )