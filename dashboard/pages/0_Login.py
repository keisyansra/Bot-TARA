import base64
from pathlib import Path

import streamlit as st

from utils.auth import (
    authenticate,
    is_logged_in,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Login - TARA",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# PATH / ASSET
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

ASSET_DIR = (
    BASE_DIR
    / "assets"
)

BACKGROUND_PATH = (
    ASSET_DIR
    / "login_bg.jpg"
)

TELKOM_LOGO_PATH = (
    ASSET_DIR
    / "telkom_logo.png"
)


# ============================================================
# IMAGE HELPER
# ============================================================

def image_to_data_uri(
    path: Path,
):

    if not path.exists():
        return None

    try:
        encoded = (
            base64.b64encode(
                path.read_bytes()
            )
            .decode("utf-8")
        )

        suffix = (
            path.suffix
            .lower()
        )

        if suffix == ".png":
            mime = "image/png"

        elif suffix == ".webp":
            mime = "image/webp"

        else:
            mime = "image/jpeg"

        return (
            f"data:{mime};"
            f"base64,{encoded}"
        )

    except Exception:
        return None


background_uri = (
    image_to_data_uri(
        BACKGROUND_PATH
    )
)

telkom_logo_uri = (
    image_to_data_uri(
        TELKOM_LOGO_PATH
    )
)


# ============================================================
# BACKGROUND
# ============================================================

if background_uri:

    HERO_BG = (
        "linear-gradient("
        "135deg,"
        "rgba(182,29,31,0.80),"
        "rgba(224,64,42,0.75)"
        "),"
        f"url('{background_uri}')"
    )

else:

    HERO_BG = (
        "linear-gradient("
        "135deg,"
        "#B61920,"
        "#E24534"
        ")"
    )


# ============================================================
# CSS
# ============================================================

CSS = """
<style>

/* ==========================================================
   HIDE DEFAULT STREAMLIT UI
   ========================================================== */

[data-testid="stSidebar"] {
    display: none !important;
}

[data-testid="collapsedControl"] {
    display: none !important;
}

[data-testid="stSidebarNav"] {
    display: none !important;
}

header[data-testid="stHeader"] {
    display: none !important;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}


/* ==========================================================
   APP
   ========================================================== */

html,
body,
[data-testid="stAppViewContainer"] {
    background: #F7F8FC !important;
}

[data-testid="stAppViewContainer"] {

    background:

        radial-gradient(
            circle at 2% 5%,
            rgba(218, 38, 43, 0.07),
            transparent 30%
        ),

        radial-gradient(
            circle at 97% 95%,
            rgba(235, 91, 63, 0.08),
            transparent 25%
        ),

        #F7F8FC !important;
}

.block-container {

    max-width: 1510px !important;

    padding-top: 2.9rem !important;

    padding-bottom: 1.5rem !important;

    padding-left: 2.8rem !important;

    padding-right: 2.8rem !important;
}


/* ==========================================================
   MAIN HERO
   ========================================================== */

.tara-hero {

    min-height: 690px;

    border-radius: 28px 0 0 28px;

    padding: 48px 52px;

    position: relative;

    overflow: hidden;

    color: #FFFFFF;

    background-image: __HERO_BG__;

    background-size: cover;

    background-position: center;

    display: flex;

    flex-direction: column;

    justify-content: space-between;

    box-shadow:
        0 24px 55px
        rgba(71, 34, 35, 0.14);
}


/* overlay decorative rings */

.tara-hero::before {

    content: "";

    position: absolute;

    width: 420px;

    height: 420px;

    right: -205px;

    bottom: -205px;

    border-radius: 50%;

    border:
        56px solid
        rgba(255, 255, 255, 0.08);

    pointer-events: none;
}


.tara-hero::after {

    content: "";

    position: absolute;

    width: 235px;

    height: 235px;

    left: -125px;

    top: -120px;

    border-radius: 50%;

    background:
        rgba(255, 255, 255, 0.06);

    pointer-events: none;
}


/* ==========================================================
   TELKOM BRAND
   ========================================================== */

.hero-logo-wrap {

    position: relative;

    z-index: 2;

    min-height: 70px;

    display: flex;

    align-items: center;
}


.hero-logo-image {

    max-width: 190px;

    max-height: 70px;

    object-fit: contain;

    filter:
        brightness(0)
        invert(1);
}


.hero-company-fallback {

    display: flex;

    align-items: center;

    gap: 12px;

    font-size: 1rem;

    font-weight: 750;

    letter-spacing: 0.035em;
}


.hero-company-symbol {

    position: relative;

    width: 42px;

    height: 34px;
}


.hero-company-symbol span {

    position: absolute;

    width: 13px;

    height: 13px;

    border-radius: 50%;

    background: #FFFFFF;
}


.hero-company-symbol span:nth-child(1) {

    top: 0;

    left: 14px;
}


.hero-company-symbol span:nth-child(2) {

    bottom: 0;

    left: 0;
}


.hero-company-symbol span:nth-child(3) {

    bottom: 0;

    right: 0;
}


/* ==========================================================
   HERO TEXT
   ========================================================== */

.hero-content {

    position: relative;

    z-index: 2;

    max-width: 690px;

    margin-bottom: 15px;
}


.hero-title {

    margin: 0;

    font-size: 3.35rem;

    line-height: 1.05;

    font-weight: 760;

    letter-spacing: -0.025em;
}


.hero-subtitle {

    margin-top: 9px;

    font-size: 1.24rem;

    font-weight: 600;

    font-style: italic;

    opacity: 0.97;
}


.hero-accent {

    width: 62px;

    height: 4px;

    margin-top: 22px;

    margin-bottom: 21px;

    border-radius: 999px;

    background: #FFFFFF;
}


.hero-description {

    max-width: 630px;

    font-size: 1rem;

    line-height: 1.68;

    opacity: 0.96;
}


/* ==========================================================
   HERO FEATURES
   ========================================================== */

.hero-features {

    margin-top: 30px;

    display: flex;

    align-items: center;

    gap: 22px;

    flex-wrap: wrap;
}


.hero-feature {

    display: flex;

    align-items: center;

    gap: 11px;

    color: #FFFFFF;

    font-size: 0.76rem;

    line-height: 1.35;

    font-weight: 600;
}


.hero-feature-icon {

    width: 34px;

    height: 34px;

    border-radius: 9px;

    display: flex;

    justify-content: center;

    align-items: center;

    border:
        1px solid
        rgba(255,255,255,.32);

    background:
        rgba(255,255,255,.08);

    font-size: 1rem;
}


.hero-feature-divider {

    width: 1px;

    height: 32px;

    background:
        rgba(255,255,255,.35);
}


.hero-bottom {

    position: relative;

    z-index: 2;

    color:
        rgba(
            255,
            255,
            255,
            0.72
        );

    font-size: .70rem;
}


/* ==========================================================
   LOGIN CARD STREAMLIT CONTAINER
   ========================================================== */

.st-key-tara_login_card {

    position: relative;

    z-index: 6;

    margin-left: -35px;

    min-height: 690px;

    background: #FFFFFF;

    border:
        1px solid
        rgba(
            227,
            230,
            236,
            .90
        );

    border-radius: 0 28px 28px 0;

    box-shadow:
        0 24px 60px
        rgba(
            45,
            49,
            59,
            .11
        );

    padding:
        48px
        56px
        38px
        56px;
}


.st-key-tara_login_card
[data-testid="stVerticalBlock"] {

    gap: 0.7rem;
}


/* ==========================================================
   TARA BRAND RIGHT
   ========================================================== */

.tara-brand {

    display: flex;

    align-items: center;

    gap: 15px;

    margin-bottom: 37px;
}


.tara-symbol {

    position: relative;

    width: 61px;

    height: 48px;
}


.tara-symbol span {

    position: absolute;

    width: 19px;

    height: 19px;

    border-radius: 50%;

    background:
        linear-gradient(
            135deg,
            #F04A32,
            #C7181E
        );
}


.tara-symbol span:nth-child(1) {

    left: 20px;

    top: 0;
}


.tara-symbol span:nth-child(2) {

    left: 0;

    bottom: 2px;
}


.tara-symbol span:nth-child(3) {

    right: 0;

    bottom: 2px;
}


.tara-brand-name {

    color: #202632;

    font-size: 2.05rem;

    line-height: 1;

    font-weight: 820;
}


.tara-brand-caption {

    margin-top: 5px;

    color: #939AA6;

    font-size: .72rem;
}


/* ==========================================================
   LOGIN TITLE
   ========================================================== */

.login-heading {

    color: #202632;

    font-size: 2rem;

    font-weight: 760;

    letter-spacing: -0.015em;

    line-height: 1.2;
}


.login-description {

    margin-top: 8px;

    margin-bottom: 25px;

    color: #818A97;

    font-size: .91rem;

    line-height: 1.5;
}


/* ==========================================================
   FORM LABEL
   ========================================================== */

.st-key-tara_login_card
label[data-testid="stWidgetLabel"] p {

    color: #5B6370 !important;

    font-size: .78rem !important;

    font-weight: 620 !important;
}


/* ==========================================================
   INPUTS
   ========================================================== */

.st-key-tara_login_card
div[data-baseweb="input"] {

    min-height: 48px !important;

    background: #FFFFFF !important;

    border:
        1px solid
        #D8DDE6 !important;

    border-radius: 10px !important;

    box-shadow: none !important;
}


.st-key-tara_login_card
div[data-baseweb="input"]:focus-within {

    border:
        1px solid
        #D6272A !important;

    box-shadow:
        0 0 0 3px
        rgba(
            214,
            39,
            42,
            .07
        ) !important;
}


.st-key-tara_login_card
div[data-baseweb="input"]
input {

    color: #252B36 !important;

    background:
        transparent !important;

    font-size: .88rem !important;
}


.st-key-tara_login_card
div[data-baseweb="input"]
input::placeholder {

    color: #A0A7B2 !important;

    opacity: 1 !important;
}


/* eye icon */

.st-key-tara_login_card
div[data-baseweb="input"] svg {

    fill: #8F98A6 !important;
}


/* ==========================================================
   CHECKBOX
   ========================================================== */

.st-key-tara_login_card
[data-testid="stCheckbox"] {

    margin-top: -2px;

    margin-bottom: 5px;
}


.st-key-tara_login_card
[data-testid="stCheckbox"]
label {

    color: #59616D !important;

    font-size: .78rem !important;
}


/* ==========================================================
   INFO BOX
   ========================================================== */

.admin-note {

    display: flex;

    align-items: flex-start;

    gap: 11px;

    padding:
        12px
        14px;

    margin:
        5px 0
        5px 0;

    border:
        1px solid
        #F3D5D7;

    border-radius: 9px;

    background: #FFF1F2;

    color: #734548;

    font-size: .75rem;

    line-height: 1.45;
}


.admin-note-icon {

    font-size: 1.1rem;
}


/* ==========================================================
   BUTTON
   ========================================================== */

.st-key-tara_login_card
button[kind="primaryFormSubmit"] {

    min-height: 48px !important;

    width: 100% !important;

    border:
        1px solid
        #D6272A !important;

    border-radius: 9px !important;

    background:
        linear-gradient(
            90deg,
            #D22027,
            #E42F33
        ) !important;

    color: #FFFFFF !important;

    font-size: .92rem !important;

    font-weight: 700 !important;
}


.st-key-tara_login_card
button[kind="primaryFormSubmit"]:hover {

    background:
        #B61D23 !important;

    border-color:
        #B61D23 !important;
}


/* ==========================================================
   INTERNAL NOTE
   ========================================================== */

.internal-note {

    margin-top: 20px;

    padding-top: 17px;

    border-top:
        1px solid
        #E9EBEF;

    text-align: center;

    color: #9AA1AC;

    font-size: .69rem;
}


/* ==========================================================
   BOTTOM FOOTER
   ========================================================== */

.page-footer {

    display: flex;

    justify-content: space-between;

    align-items: center;

    padding-top: 18px;

    color: #A0A6B0;

    font-size: .65rem;
}


.footer-links {

    display: flex;

    gap: 20px;
}


/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media(max-width: 1000px) {

    .tara-hero {

        border-radius:
            24px;

        min-height:
            520px;
    }


    .st-key-tara_login_card {

        margin-left: 0;

        border-radius:
            24px;

        min-height:
            auto;
    }


    .hero-title {

        font-size:
            2.4rem;
    }


    .page-footer {

        flex-direction:
            column;

        gap:
            8px;
    }

}

</style>
"""


CSS = CSS.replace(
    "__HERO_BG__",
    HERO_BG,
)

st.html(
    CSS
)


# ============================================================
# LOGGED IN
# ============================================================

if is_logged_in():

    st.switch_page(
        "Home.py"
    )

    st.stop()


# ============================================================
# MAIN LAYOUT
# ============================================================

left, right = st.columns(
    [
        1.42,
        0.92,
    ],
    gap="small",
    vertical_alignment="center",
)


# ============================================================
# LEFT PANEL
# ============================================================

with left:

    if telkom_logo_uri:

        brand_html = (
            '<img '
            'class="hero-logo-image" '
            f'src="{telkom_logo_uri}">'
        )

    else:

        brand_html = """
        <div class="hero-company-fallback">

            <div class="hero-company-symbol">

                <span></span>
                <span></span>
                <span></span>

            </div>

            <span>
                TELKOM INDONESIA
            </span>

        </div>
        """

    HERO_HTML = f"""
    <div class="tara-hero">

        <div class="hero-logo-wrap">

            {brand_html}

        </div>


        <div class="hero-content">

            <div class="hero-title">
                TARA Dashboard
            </div>

            <div class="hero-subtitle">

                Telkom Area Recommendation Assistant

            </div>


            <div class="hero-accent">
            </div>


            <div class="hero-description">

                Platform administrasi untuk
                pengelolaan data CBASE, ODP,
                prospek, dan aktivitas secara
                terintegrasi.

            </div>


            <div class="hero-features">


                <div class="hero-feature">

                    <div class="hero-feature-icon">
                        🗄️
                    </div>

                    <div>
                        Data<br>
                        Terintegrasi
                    </div>

                </div>


                <div class="hero-feature-divider">
                </div>


                <div class="hero-feature">

                    <div class="hero-feature-icon">
                        📊
                    </div>

                    <div>
                        Pengelolaan<br>
                        Berbasis Data
                    </div>

                </div>


                <div class="hero-feature-divider">
                </div>


                <div class="hero-feature">

                    <div class="hero-feature-icon">
                        👥
                    </div>

                    <div>
                        Mendukung<br>
                        Kolaborasi Tim
                    </div>

                </div>


            </div>

        </div>


        <div class="hero-bottom">

            Internal Administrative System

        </div>

    </div>
    """

    st.html(
        HERO_HTML
    )


# ============================================================
# RIGHT CARD
# ============================================================

with right:

    with st.container(
        key="tara_login_card",
    ):

        st.html(
            """
            <div class="tara-brand">

                <div class="tara-symbol">

                    <span></span>
                    <span></span>
                    <span></span>

                </div>


                <div>

                    <div class="tara-brand-name">
                        TARA
                    </div>

                    <div class="tara-brand-caption">

                        Telkom Area Recommendation Assistant

                    </div>

                </div>

            </div>


            <div class="login-heading">

                Masuk ke Dashboard TARA

            </div>


            <div class="login-description">

                Silakan masuk menggunakan
                akun administrator.

            </div>
            """
        )


        # ====================================================
        # FORM
        # ====================================================

        with st.form(
            "tara_login_form",
            clear_on_submit=False,
        ):

            admin_name = (
                st.text_input(
                    "Nama Admin",
                    placeholder=(
                        "Masukkan nama admin"
                    ),
                )
            )


            access_code = (
                st.text_input(
                    "Kode Akses",
                    type="password",
                    placeholder=(
                        "Masukkan kode akses"
                    ),
                )
            )


            show_code = (
                st.checkbox(
                    "Tampilkan kode akses",
                    key="show_login_code",
                )
            )


            # Streamlit tidak bisa mengubah type
            # text_input yang sudah dibuat dalam form
            # setelah checkbox diklik.
            # Kita handle rerun di bawah.


            st.html(
                """
                <div class="admin-note">

                    <div class="admin-note-icon">
                        👥
                    </div>

                    <div>

                        Setiap administrator menggunakan
                        akun masing-masing dan dapat bekerja
                        secara bersamaan.

                    </div>

                </div>
                """
            )


            st.write("")


            login_clicked = (
                st.form_submit_button(
                    "Masuk    →",
                    type="primary",
                    use_container_width=True,
                )
            )


        # ====================================================
        # LOGIN PROCESS
        # ====================================================

        if login_clicked:

            with st.spinner(
                "Memverifikasi akun..."
            ):

                ok, error = (
                    authenticate(
                        admin_name,
                        access_code,
                    )
                )

            if ok:

                st.toast(
                    "Login berhasil.",
                    icon="✅",
                )

                st.switch_page(
                    "Home.py"
                )

            else:

                st.error(
                    error
                )


        st.html(
            """
            <div class="internal-note">

                🔒 Khusus untuk pengguna internal
                yang berwenang.

            </div>
            """
        )


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="page-footer">

        <div>

            TARA · Telkom Area Recommendation Assistant

        </div>


        <div class="footer-links">

            <span>
                Sistem Internal
            </span>

            <span>
                Telkom Indonesia
            </span>

        </div>

    </div>
    """
)