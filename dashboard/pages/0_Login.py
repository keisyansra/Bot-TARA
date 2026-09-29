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
    / "BG_Login.jpg"
)

LOGO_PATH = (
    ASSET_DIR
    / "logo_tara.png"
)


# ============================================================
# IMAGE HELPER
# ============================================================

def image_to_data_uri(path: Path):

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

logo_uri = (
    image_to_data_uri(
        LOGO_PATH
    )
)


# ============================================================
# BACKGROUND HERO
# ============================================================

if background_uri:

    HERO_BG = (
        "linear-gradient("
        "135deg,"
        "rgba(181,24,30,0.42),"
        "rgba(219,54,43,0.34)"
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
# LOGO HTML
# ============================================================

if logo_uri:

    BRAND_HTML = f"""
    <div class="tara-brand-image-wrap">

        <img
            src="{logo_uri}"
            class="tara-brand-image"
            alt="TARA Logo"
        >

    </div>
    """

else:

    BRAND_HTML = """
    <div class="tara-brand-fallback">

        <div class="tara-brand-fallback-title">
            TARA
        </div>

        <div class="tara-brand-fallback-subtitle">
            Telkom Area Recommendation Assistant
        </div>

    </div>
    """


# ============================================================
# CSS
# ============================================================

CSS = """
<style>


/* ==========================================================
   HIDE DEFAULT STREAMLIT
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
    visibility: hidden !important;
}

footer {
    visibility: hidden !important;
}


/* ==========================================================
   APP BACKGROUND
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
            rgba(218,38,43,0.055),
            transparent 28%
        ),
        radial-gradient(
            circle at 98% 95%,
            rgba(235,91,63,0.055),
            transparent 24%
        ),
        #F7F8FC !important;
}

.block-container {
    max-width: 1500px !important;

    padding-top: 1.4rem !important;
    padding-bottom: 1rem !important;

    padding-left: 1.8rem !important;
    padding-right: 1.8rem !important;
}


/* ==========================================================
   LEFT HERO
   ========================================================== */

.tara-hero {
    position: relative;

    min-height: 690px;

    overflow: hidden;

    box-sizing: border-box;

    border-radius:
        28px
        0
        0
        28px;

    padding:
        50px
        52px
        40px
        52px;

    color: #FFFFFF;

    background-image:
        __HERO_BG__;

    background-size: cover;

    background-position:
        center center;

    box-shadow:
        0 22px 55px
        rgba(34,38,48,0.12);

    display: flex;

    flex-direction: column;

    justify-content: space-between;
}


/* dekorasi kiri atas */

.tara-hero::before {
    content: "";

    position: absolute;

    width: 190px;
    height: 190px;

    left: -95px;
    top: -95px;

    border-radius: 50%;

    background:
        rgba(255,255,255,0.055);

    pointer-events: none;
}


/* dekorasi kanan bawah */

.tara-hero::after {
    content: "";

    position: absolute;

    width: 330px;
    height: 330px;

    right: -165px;
    bottom: -165px;

    border-radius: 50%;

    border:
        46px solid
        rgba(255,255,255,0.075);

    pointer-events: none;
}


/* ==========================================================
   HERO CONTENT
   ========================================================== */

.hero-content {
    position: relative;

    z-index: 2;

    max-width: 620px;
}

.hero-title {
    margin: 0;

    color: #FFFFFF;

    font-size: 3.45rem;

    line-height: 1.04;

    font-weight: 820;

    letter-spacing: -0.04em;
}

.hero-subtitle {
    margin-top: 11px;

    color:
        rgba(255,255,255,0.97);

    font-size: 1.12rem;

    font-weight: 620;

    font-style: italic;

    line-height: 1.4;
}

.hero-accent {
    width: 62px;
    height: 4px;

    margin-top: 22px;

    border-radius: 999px;

    background:
        rgba(255,255,255,0.95);
}

.hero-bottom {
    position: relative;

    z-index: 2;

    color:
        rgba(255,255,255,0.78);

    font-size: 0.68rem;
}


/* ==========================================================
   LOGIN CARD
   ========================================================== */

.st-key-tara_login_card {
    position: relative;

    z-index: 5;

    margin-left: -18px;

    min-height: 690px;

    box-sizing: border-box;

    padding:
        28px
        56px
        32px
        56px;

    background: #FFFFFF;

    border:
        1px solid
        #E5E8EE;

    border-radius:
        0
        28px
        28px
        0;

    box-shadow:
        0 22px 55px
        rgba(34,38,48,0.10);
}


.st-key-tara_login_card
[data-testid="stVerticalBlock"] {
    gap: 0.60rem;
}


/* ==========================================================
   TARA LOGO
   ========================================================== */

.tara-brand-image-wrap {
    position: relative;

    width: 100%;

    height: 108px;

    margin:
        0
        0
        0
        0;

    padding: 0;

    overflow: hidden;

    display: flex;

    align-items: center;

    justify-content: flex-start;
}


.tara-brand-image {
    display: block;

    width: 260px;

    max-width: none;

    height: auto;

    object-fit: contain;

    object-position:
        left center;

    transform:
        translate(
            -8px,
            0px
        );

    transform-origin:
        left center;
}


/* fallback */

.tara-brand-fallback {
    margin:
        12px
        0
        12px
        0;
}

.tara-brand-fallback-title {
    color: #172033;

    font-size: 1.9rem;

    line-height: 1;

    font-weight: 830;
}

.tara-brand-fallback-subtitle {
    margin-top: 5px;

    color: #949EAC;

    font-size: 0.70rem;
}


/* ==========================================================
   LOGIN TITLE
   ========================================================== */

.login-heading {
    margin-top: -3px;

    margin-bottom: 0;

    color: #172033;

    font-size: 1.95rem;

    font-weight: 800;

    line-height: 1.18;

    letter-spacing:
        -0.025em;
}


.login-description {
    margin-top: 6px;

    margin-bottom: 16px;

    color: #858F9E;

    font-size: 0.85rem;

    line-height: 1.55;
}


/* ==========================================================
   LOGIN INPUT
   ========================================================== */

.st-key-tara_username_input,
.st-key-tara_password_input {
    position: relative !important;

    min-height: 52px !important;

    background:
        #FFFFFF !important;

    border:
        1.4px solid
        #D9DEE8 !important;

    border-radius:
        12px !important;

    box-sizing:
        border-box !important;

    overflow:
        hidden !important;

    box-shadow:
        0 1px 2px
        rgba(15,23,42,0.025)
        !important;

    transition:
        border-color 0.15s ease,
        box-shadow 0.15s ease
        !important;
}


/* hover */

.st-key-tara_username_input:hover,
.st-key-tara_password_input:hover {
    border-color:
        #C7CED8 !important;
}


/* focus */

.st-key-tara_username_input:focus-within,
.st-key-tara_password_input:focus-within {
    border-color:
        #D6272A !important;

    box-shadow:
        0 0 0 3px
        rgba(214,39,42,0.08)
        !important;
}


/* hapus border internal Streamlit */

.st-key-tara_username_input
div[data-baseweb="input"],

.st-key-tara_password_input
div[data-baseweb="input"],

.st-key-tara_username_input
div[data-baseweb="base-input"],

.st-key-tara_password_input
div[data-baseweb="base-input"],

.st-key-tara_username_input
[data-testid="stTextInputRootElement"],

.st-key-tara_password_input
[data-testid="stTextInputRootElement"] {

    border:
        none !important;

    outline:
        none !important;

    box-shadow:
        none !important;

    background:
        transparent !important;

    border-radius:
        12px !important;
}


/* text input */

.st-key-tara_username_input input,
.st-key-tara_password_input input {
    min-height:
        50px !important;

    width:
        100% !important;

    background:
        transparent !important;

    border:
        none !important;

    outline:
        none !important;

    box-shadow:
        none !important;

    color:
        #29313D !important;

    font-size:
        0.86rem !important;

    padding-top:
        0 !important;

    padding-bottom:
        0 !important;
}


/* placeholder */

.st-key-tara_username_input input::placeholder,
.st-key-tara_password_input input::placeholder {
    color:
        #8F98A6 !important;

    opacity:
        1 !important;
}


/* ==========================================================
   USERNAME ICON
   ========================================================== */

.st-key-tara_username_input::before {
    content: "";

    position: absolute;

    z-index: 10;

    left: 15px;

    top: 50%;

    transform:
        translateY(-50%);

    width: 18px;

    height: 18px;

    pointer-events: none;

    background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238F98A6' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E");

    background-repeat:
        no-repeat;

    background-position:
        center;

    background-size:
        contain;
}


.st-key-tara_username_input input {
    padding-left:
        43px !important;
}


/* ==========================================================
   PASSWORD ICON
   ========================================================== */

.st-key-tara_password_input::before {
    content: "";

    position: absolute;

    z-index: 10;

    left: 15px;

    top: 50%;

    transform:
        translateY(-50%);

    width: 18px;

    height: 18px;

    pointer-events: none;

    background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238F98A6' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E");

    background-repeat:
        no-repeat;

    background-position:
        center;

    background-size:
        contain;
}


.st-key-tara_password_input input {
    padding-left:
        43px !important;

    padding-right:
        44px !important;
}


/* ==========================================================
   PASSWORD EYE
   ========================================================== */

.st-key-tara_password_input button {
    border:
        none !important;

    outline:
        none !important;

    background:
        transparent !important;

    box-shadow:
        none !important;

    color:
        #8F98A6 !important;
}


.st-key-tara_password_input button:hover {
    background:
        transparent !important;
}


/* ==========================================================
   CHECKBOX
   ========================================================== */

.st-key-tara_login_card
[data-testid="stCheckbox"] {
    margin-top:
        -1px;

    margin-bottom:
        2px;
}


.st-key-tara_login_card
[data-testid="stCheckbox"]
label {
    color:
        #59616D !important;

    font-size:
        0.77rem !important;
}


/* ==========================================================
   ADMIN NOTE
   ========================================================== */

.admin-note {
    display: flex;

    align-items:
        flex-start;

    gap:
        10px;

    padding:
        12px
        14px;

    margin:
        4px
        0
        3px
        0;

    border:
        1px solid
        #F2D0D3;

    border-radius:
        10px;

    background:
        #FFF4F5;

    color:
        #754A4E;

    font-size:
        0.71rem;

    line-height:
        1.5;
}


.admin-note-icon {
    flex-shrink:
        0;

    font-size:
        1rem;
}


/* ==========================================================
   LOGIN BUTTON
   ========================================================== */

.st-key-tara_login_card
button[kind^="primary"] {
    min-height:
        49px !important;

    width:
        100% !important;

    border:
        1px solid
        #D6272A !important;

    border-radius:
        10px !important;

    background:
        linear-gradient(
            90deg,
            #D22027,
            #E42F33
        )
        !important;

    color:
        #FFFFFF !important;

    font-size:
        0.87rem !important;

    font-weight:
        700 !important;

    box-shadow:
        0 8px 18px
        rgba(210,32,39,0.14)
        !important;
}


.st-key-tara_login_card
button[kind^="primary"]:hover {
    background:
        #B91C23 !important;

    border-color:
        #B91C23 !important;
}


/* ==========================================================
   INTERNAL NOTE
   ========================================================== */

.internal-note {
    margin-top:
        14px;

    padding-top:
        14px;

    border-top:
        1px solid
        #E9ECF0;

    text-align:
        center;

    color:
        #9AA3AF;

    font-size:
        0.66rem;
}


/* ==========================================================
   ERROR
   ========================================================== */

.st-key-tara_login_card
[data-testid="stAlert"] {
    border-radius:
        10px !important;

    font-size:
        0.78rem !important;
}


/* ==========================================================
   FOOTER
   ========================================================== */

.page-footer {
    display:
        flex;

    justify-content:
        space-between;

    align-items:
        center;

    padding-top:
        14px;

    color:
        #A0A8B3;

    font-size:
        0.62rem;
}


.footer-links {
    display:
        flex;

    gap:
        19px;
}


/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media(max-width: 1000px) {

    .tara-hero {
        min-height:
            450px;

        border-radius:
            24px;

        padding:
            36px
            32px;
    }


    .hero-title {
        font-size:
            2.6rem;
    }


    .st-key-tara_login_card {
        margin-left:
            0;

        min-height:
            auto;

        border-radius:
            24px;

        padding:
            30px
            32px;
    }


    .tara-brand-image-wrap {
        height:
            95px;
    }


    .tara-brand-image {
        width:
            235px;

        transform:
            translate(
                -6px,
                0px
            );
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
# REDIRECT IF LOGGED IN
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
# LEFT HERO
# ============================================================

with left:

    st.html(
        """
        <div class="tara-hero">

            <div class="hero-content">

                <div class="hero-title">
                    TARA Dashboard
                </div>

                <div class="hero-subtitle">
                    Telkom Area Recommendation Assistant
                </div>

                <div class="hero-accent">
                </div>

            </div>

            <div class="hero-bottom">
                Internal Administrative System
            </div>

        </div>
        """
    )


# ============================================================
# RIGHT LOGIN CARD
# ============================================================

with right:

    with st.container(
        key="tara_login_card",
    ):


        # ====================================================
        # LOGO
        # ====================================================

        st.html(
            BRAND_HTML
        )


        # ====================================================
        # TITLE
        # ====================================================

        st.html(
            """
            <div class="login-heading">
                Masuk ke Dashboard TARA
            </div>

            <div class="login-description">
                Silakan masuk menggunakan akun administrator.
            </div>
            """
        )


        # ====================================================
        # PASSWORD VISIBILITY
        # ====================================================

        show_code = (
            st.session_state.get(
                "show_login_code",
                False,
            )
        )


        # ====================================================
        # USERNAME
        # ====================================================

        admin_name = st.text_input(
            "Username",
            placeholder="Username",
            label_visibility="collapsed",
            autocomplete="username",
            key="tara_username_input",
        )


        # ====================================================
        # PASSWORD
        # ====================================================

        access_code = st.text_input(
            "Kata Sandi",
            type=(
                "default"
                if show_code
                else "password"
            ),
            placeholder="Kata Sandi",
            label_visibility="collapsed",
            autocomplete="current-password",
            key="tara_password_input",
        )


        # ====================================================
        # SHOW PASSWORD
        # ====================================================

        st.checkbox(
            "Tampilkan kata sandi",
            key="show_login_code",
        )


        # ====================================================
        # ADMIN NOTE
        # ====================================================

        st.html(
            """
            <div class="admin-note">

                <div class="admin-note-icon">
                </div>
                <div>
                    Gunakan akun administrator yang telah terdaftar
                    untuk mengakses Dashboard TARA.
                </div>

            </div>
            """
        )


        st.write("")


        # ====================================================
        # LOGIN BUTTON
        # ====================================================

        login_clicked = st.button(
            "Masuk   →",
            type="primary",
            use_container_width=True,
            key="tara_login_submit",
        )


        # ====================================================
        # LOGIN PROCESS
        # ====================================================

        if login_clicked:

            admin_name_clean = (
                str(
                    admin_name
                    or ""
                )
                .strip()
            )

            access_code_clean = (
                str(
                    access_code
                    or ""
                )
                .strip()
            )


            if not admin_name_clean:

                st.error(
                    "Username / Email wajib diisi."
                )


            elif not access_code_clean:

                st.error(
                    "Kata sandi wajib diisi."
                )


            else:

                with st.spinner(
                    "Memverifikasi akun..."
                ):

                    ok, error = authenticate(
                        admin_name_clean,
                        access_code_clean,
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
                        or
                        "Username atau kata sandi tidak sesuai."
                    )


        # ====================================================
        # INTERNAL NOTE
        # ====================================================

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
            © 2026 Telkom Indonesia.
            All rights reserved.
        </div>

        <div class="footer-links">

            <span>
                Kebijakan Privasi
            </span>

            <span>
                Syarat dan Ketentuan
            </span>

            <span>
                Bantuan
            </span>

        </div>

    </div>
    """
)