import base64

import html

import time

from pathlib import Path



import streamlit as st



from utils.api_client import (

    api_get,

    api_supports,

)



from utils.auth import (

    current_admin,

    logout,

    require_login,

)


# ============================================================
# ASSETS
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

SIDEBAR_LOGO_PATH = (
    ASSET_DIR
    / "logo_tara.png"
)


def _image_to_data_uri(
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
        elif suffix in (".jpg", ".jpeg"):
            mime = "image/jpeg"
        elif suffix == ".webp":
            mime = "image/webp"
        else:
            mime = "image/png"

        return (
            f"data:{mime};"
            f"base64,{encoded}"
        )

    except Exception:
        return None


SIDEBAR_LOGO_URI = (
    _image_to_data_uri(
        SIDEBAR_LOGO_PATH
    )
)





# ============================================================

# NAVIGATION

# ============================================================



NAV_SECTIONS = [

    (

        "BERANDA",

        [

            (

                "Dashboard",

                "Home.py",

                "🏠",

            ),

        ],

    ),

    (

        "KELOLA DATA",

        [

            (

                "Data Pelanggan (CBASE)",

                "pages/1_Data_Pelanggan_CBASE.py",

                "👥",

            ),

            (

                "Data ODP",

                "pages/2_Data_ODP.py",

                "🔌",

            ),

        ],

    ),

    (

        "AKTIVITAS",

        [

            (

                "Riwayat Aktivitas",

                "pages/4_Riwayat_Aktivitas.py",

                "🕘",

            ),

        ],

    ),

    (

        "LAINNYA",

        [

            (

                "Data Prospek",

                "pages/3_Data_Prospek.py",

                "📍",

            ),

            (

                "User & Approval Bot",

                "pages/5_User_Approval.py",

                "🔐",

            ),

        ],

    ),

]





NAV_CAPABILITY_PROBE = {

    "Data Prospek": "/api/prospects/search",

    "User & Approval Bot": "/api/admin/users",

}





# ============================================================

# GLOBAL CSS

# ============================================================



CUSTOM_CSS = """

<style>



/* ==========================================================

   GLOBAL

   ========================================================== */



[data-testid="stAppViewContainer"] {

    background: #F7F8FA !important;

    color: #20242E !important;

}



[data-testid="stMain"] {

    background: #F7F8FA !important;

}



[data-testid="stSidebar"] {

    background: #F4F6F9 !important;

}



[data-testid="stSidebarNav"] {

    display: none !important;

}



[data-testid="stSidebar"] * {

    color: #4A5361;

}





/* ==========================================================

   TEXT

   ========================================================== */



h1,

h2,

h3,

h4,

h5,

h6 {

    color: #20242E !important;

}



p,

label {

    color: #596271;

}





/* ==========================================================
   SIDEBAR BRAND
   ========================================================== */

.tara-sidebar-brand {
    position: relative;
    width: 100%;
    height: 72px;
    margin: 0 0 4px 0;
    padding: 0;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    background: transparent !important;
}

.tara-sidebar-logo {
    display: block;

    width: 195px;

    max-width: none;

    height: auto;

    object-fit: contain;

    object-position: left center;

    transform:
        translate(
            -6px,
            0px
        );

    transform-origin:
        left center;

    background: transparent !important;

    /* Membuat background putih logo menyatu dengan sidebar */
    mix-blend-mode: multiply;
}

.tara-sidebar-brand-fallback {
    padding: 6px 3px 12px 3px;
}

.tara-brand-main {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #172033 !important;
    font-size: 1.12rem;
    font-weight: 800;
}

.tara-brand-sub {
    margin-top: 4px;
    color: #9098A3 !important;
    font-size: 0.75rem;
    line-height: 1.5;
}


/* ==========================================================

   TOP BAR

   ========================================================== */



.tara-breadcrumb {

    color: #7E8794 !important;



    font-size: 0.82rem;

}



.tara-breadcrumb strong {

    color: #303744 !important;

}



.tara-topbar-line {

    width: 100%;

    height: 1px;



    margin-top: 4px;

    margin-bottom: 18px;



    background: #F0D5D6;

}





/* ==========================================================

   BUTTON GENERAL

   ========================================================== */



.stButton > button {

    min-height: 40px;



    border-radius: 9px !important;



    font-weight: 600 !important;



    transition:

        background-color .15s ease,

        border-color .15s ease,

        box-shadow .15s ease;

}





/* ==========================================================

   PRIMARY BUTTON

   ========================================================== */



.stButton > button[kind="primary"] {

    background: #D71920 !important;



    border: 1px solid #D71920 !important;



    color: #FFFFFF !important;



    font-weight: 650 !important;



    box-shadow:

        0 2px 5px

        rgba(215, 25, 32, 0.14);

}



.stButton > button[kind="primary"] *,

.stButton > button[kind="primary"] p,

.stButton > button[kind="primary"] span,

.stButton > button[kind="primary"] div {

    color: #FFFFFF !important;

}



.stButton > button[kind="primary"]:hover {

    background: #B9141B !important;



    border-color: #B9141B !important;



    color: #FFFFFF !important;

}





/* ==========================================================

   FORM PRIMARY

   ========================================================== */



button[kind="primaryFormSubmit"] {

    min-height: 42px !important;



    border-radius: 9px !important;



    border: 1px solid #D71920 !important;



    background: #D71920 !important;



    color: #FFFFFF !important;



    font-weight: 650 !important;

}



button[kind="primaryFormSubmit"] *,

button[kind="primaryFormSubmit"] p,

button[kind="primaryFormSubmit"] span {

    color: #FFFFFF !important;

}





/* ==========================================================

   SECONDARY BUTTON

   ========================================================== */



.stButton > button[kind="secondary"] {

    background: #FFFFFF !important;



    border: 1px solid #D9DEE6 !important;



    color: #505966 !important;



    font-weight: 600 !important;

}



.stButton > button[kind="secondary"] *,

.stButton > button[kind="secondary"] p,

.stButton > button[kind="secondary"] span {

    color: #505966 !important;

}



.stButton > button[kind="secondary"]:hover {

    background: #F8F9FB !important;



    border-color: #C8CED8 !important;



    color: #303744 !important;

}





/* ==========================================================

   INPUT

   ========================================================== */



div[data-baseweb="input"] {

    background: #FFFFFF !important;



    border: 1px solid #D9DEE6 !important;



    border-radius: 9px !important;

}



div[data-baseweb="input"]:focus-within {

    border-color: #D71920 !important;



    box-shadow:

        0 0 0 2px

        rgba(215, 25, 32, 0.07) !important;

}



div[data-baseweb="input"] input {

    background: transparent !important;



    color: #303744 !important;

}



div[data-baseweb="input"] input::placeholder {

    color: #9BA3AF !important;



    opacity: 1 !important;

}





/* ==========================================================

   SELECT

   ========================================================== */



div[data-baseweb="select"] > div {

    background: #FFFFFF !important;



    border-color: #D9DEE6 !important;



    border-radius: 9px !important;



    color: #303744 !important;

}



div[data-baseweb="select"] span {

    color: #303744 !important;

}





/* ==========================================================

   CARDS

   ========================================================== */



div[data-testid="stVerticalBlockBorderWrapper"] > div {

    border-radius: 12px;

}



/* ==========================================================

   STANDARD KPI CARD

   Dipakai supaya metric antar halaman TARA konsisten

   ========================================================== */



div[data-testid="stMetric"] {

    min-height: 188px !important;



    padding:

        20px

        22px

        18px

        22px !important;



    box-sizing: border-box !important;



    background:

        #FFFFFF !important;



    border:

        1px solid

        #E2E6EB !important;



    border-radius:

        14px !important;



    box-shadow:

        0 3px 12px

        rgba(15, 23, 42, 0.025)

        !important;



    display: flex !important;



    flex-direction: column !important;



    justify-content: flex-start !important;

}





/* LABEL KPI */



div[data-testid="stMetricLabel"] {

    margin-bottom:

        14px !important;

}





/* teks label */



div[data-testid="stMetricLabel"] p {

    color:

        #68717F !important;



    font-size:

        0.72rem !important;



    font-weight:

        750 !important;



    letter-spacing:

        0.035em !important;



    text-transform:

        uppercase !important;

}





/* NILAI KPI */



div[data-testid="stMetricValue"] {

    margin-top:

        3px !important;



    color:

        #20242E !important;



    font-size:

        1.95rem !important;



    font-weight:

        800 !important;



    line-height:

        1.05 !important;

}





/* DELTA / TEKS TAMBAHAN */



div[data-testid="stMetricDelta"] {

    margin-top:

        12px !important;



    font-size:

        0.70rem !important;



    font-weight:

        650 !important;

}





/* ==========================================================

   BADGES

   ========================================================== */



.badge {

    display: inline-block;



    padding: 3px 11px;



    border-radius: 999px;



    font-size: 0.76rem;

    font-weight: 650;

}



.badge-green {

    background: #E4F6EA;

    color: #15764B;

}



.badge-red {

    background: #FDE9EA;

    color: #C0262D;

}



.badge-yellow {

    background: #FFF3D8;

    color: #9A6808;

}



.badge-gray {

    background: #EEF0F3;

    color: #606977;

}





/* ==========================================================

   FILE UPLOADER

   ========================================================== */



[data-testid="stFileUploaderDropzone"] {

    background: #FFFFFF !important;



    border:

        1.5px dashed

        #E6B5B7 !important;



    border-radius: 11px !important;

}





/* ==========================================================

   STATUS

   ========================================================== */



.pill-active {

    display: inline-block;



    padding: 4px 13px;



    border-radius: 999px;



    background: #E4F6EA;



    color: #14764B;



    font-size: 0.81rem;

    font-weight: 650;

}



.pill-inactive {

    display: inline-block;



    padding: 4px 13px;



    border-radius: 999px;



    background: #FDE9EA;



    color: #C0262D;



    font-size: 0.81rem;

    font-weight: 650;

}





/* ==========================================================

   PROCESS

   ========================================================== */



.tara-result-icon {

    padding-top: 20px;



    text-align: center;



    font-size: 48px;

}



.tara-process-heading {

    margin-top: 7px;



    color: #20242E !important;



    text-align: center;



    font-size: 1.35rem;

    font-weight: 750;

}



.tara-process-desc {

    max-width: 650px;



    margin: 8px auto 17px auto;



    color: #737C89 !important;



    text-align: center;



    font-size: 0.91rem;

    line-height: 1.55;

}





/* ==========================================================

   LOADING CLOCK

   ========================================================== */



.tara-loader-wrap {

    display: flex;



    justify-content: center;



    padding-top: 22px;

}



.tara-clock {

    position: relative;



    width: 66px;

    height: 66px;



    border: 4px solid #F1CFD1;

    border-radius: 50%;



    background: #FFFFFF;

}



.tara-clock::after {

    content: "";



    position: absolute;



    left: 50%;

    top: 50%;



    width: 8px;

    height: 8px;



    transform:

        translate(

            -50%,

            -50%

        );



    border-radius: 50%;



    background: #D71920;

}



.clock-minute {

    position: absolute;



    left:

        calc(

            50% - 1.5px

        );



    top: 9px;



    width: 3px;

    height: 24px;



    border-radius: 999px;



    background: #D71920;



    transform-origin: 50% 24px;



    animation:

        clockMove

        1.2s

        linear

        infinite;

}



.clock-hour {

    position: absolute;



    left:

        calc(

            50% - 2px

        );



    top: 16px;



    width: 4px;

    height: 17px;



    border-radius: 999px;



    background: #434B58;



    transform-origin: 50% 17px;



    animation:

        clockMoveSlow

        8s

        linear

        infinite;

}



@keyframes clockMove {

    from {

        transform: rotate(0deg);

    }



    to {

        transform: rotate(360deg);

    }

}



@keyframes clockMoveSlow {

    from {

        transform: rotate(45deg);

    }



    to {

        transform: rotate(405deg);

    }

}





/* ==========================================================

   PROCESS STEPS

   ========================================================== */



.process-steps {

    display: flex;



    justify-content: center;



    gap: 8px;



    flex-wrap: wrap;



    margin-bottom: 15px;

}



.process-step {

    padding: 5px 11px;



    border-radius: 999px;



    background: #EFF1F4;



    color: #7A8390 !important;



    font-size: 0.73rem;

    font-weight: 650;

}



.process-step.done {

    background: #E4F6EA;

    color: #14764B !important;

}



.process-step.active {

    background: #FDE9EA;

    color: #C0262D !important;

}





/* ==========================================================

   SIDEBAR BUTTON

   ========================================================== */



[data-testid="stSidebar"]

.stButton > button {

    width: 100%;



    background: transparent !important;



    border-color: #D9DEE5 !important;



    color: #505866 !important;

}



[data-testid="stSidebar"]

.stButton > button * {

    color: #505866 !important;

}



[data-testid="stSidebar"]

.stButton > button:hover {

    background: #FFFFFF !important;



    border-color: #D9A7A9 !important;



    color: #D71920 !important;

}





/* ==========================================================

   ENTERPRISE PAGINATION

   ========================================================== */



.tara-pagination-summary {

    color: #89919D !important;



    font-size: 0.78rem;

    line-height: 1.4;

}



.tara-pagination-summary strong {

    color: #424B58 !important;



    font-weight: 700;

}





.tara-pagination-label {

    display: flex;



    align-items: center;

    justify-content: center;



    height: 40px;



    color: #747D89 !important;



    font-size: 0.74rem;



    white-space: nowrap;

}





.tara-pagination-label strong {

    margin-left: 4px;



    color: #303744 !important;



    font-weight: 700;

}





/* Pagination area */



div[class*="st-key-tara_pagination_"] {

    margin-top: 10px;

}





/* Navigation icon buttons */



div[class*="st-key-tara_pagination_"]

.stButton > button {



    min-height: 40px !important;

    height: 40px !important;



    padding: 0 !important;



    border:

        1px solid

        #DDE2E8 !important;



    border-radius: 8px !important;



    background: #FFFFFF !important;



    color: #4D5663 !important;



    box-shadow: none !important;



    font-size: 1.05rem !important;

    font-weight: 600 !important;

}





div[class*="st-key-tara_pagination_"]

.stButton > button * {

    color: #4D5663 !important;

}





div[class*="st-key-tara_pagination_"]

.stButton > button:hover:not(:disabled) {



    border-color: #D71920 !important;



    background: #FFF7F7 !important;



    color: #D71920 !important;

}





div[class*="st-key-tara_pagination_"]

.stButton > button:hover:not(:disabled) * {

    color: #D71920 !important;

}





div[class*="st-key-tara_pagination_"]

.stButton > button:disabled {



    border-color: #E8EBEF !important;



    background: #F4F5F7 !important;



    color: #B9BFC7 !important;



    opacity: 1 !important;

}





/* Direct page input */



div[class*="st-key-tara_pagination_"]

[data-testid="stNumberInput"] {



    margin: 0 !important;

}





div[class*="st-key-tara_pagination_"]

[data-testid="stNumberInput"]

div[data-baseweb="input"] {



    height: 40px !important;



    min-height: 40px !important;



    border:

        1px solid

        #DDE2E8 !important;



    border-radius: 8px !important;



    background: #FFFFFF !important;



    box-shadow: none !important;

}





div[class*="st-key-tara_pagination_"]

[data-testid="stNumberInput"]

div[data-baseweb="input"]:focus-within {



    border-color: #D71920 !important;



    box-shadow:

        0 0 0 2px

        rgba(

            215,

            25,

            32,

            0.06

        ) !important;

}





div[class*="st-key-tara_pagination_"]

[data-testid="stNumberInput"]

input {



    text-align: center !important;



    color: #303744 !important;



    font-size: 0.80rem !important;

    font-weight: 700 !important;

}





/* hide number +/- */



div[class*="st-key-tara_pagination_"]

[data-testid="stNumberInput"]

button {



    display: none !important;

}





/* ==========================================================

   RESPONSIVE

   ========================================================== */



@media(max-width: 950px) {



    .tara-pagination-summary {

        margin-bottom: 8px;

    }



}



</style>

"""





# ============================================================

# HELPERS

# ============================================================



def inject_css():



    st.html(

        CUSTOM_CSS

    )





def _safe_text(

    value,

):



    return html.escape(

        str(

            value

            or ""

        )

    )





def _safe_key(

    value,

):



    return (

        str(value)

        .replace("/", "_")

        .replace("\\\\", "_")

        .replace(" ", "_")

        .replace(":", "_")

        .replace(">", "_")

    )





def _format_number(

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





# ============================================================

# PENDING USER

# ============================================================



@st.fragment(

    run_every=15

)

def _pending_users_badge():



    result = api_get(

        "/api/admin/users",

        params={

            "role": "pending",

        },

    )



    if not result.get(

        "ok"

    ):

        return



    response = (

        result.get(

            "data"

        )

        or {}

    )



    users = (

        response.get(

            "data"

        )

        or []

    )



    count = len(

        users

    )



    previous = (

        st.session_state.get(

            "_pending_count_seen"

        )

    )



    if (

        previous is not None

        and

        count > previous

    ):



        st.toast(

            (

                f"Ada {count - previous} "

                "user baru meminta akses "

                "ke Bot TARA."

            ),

            icon="🔔",

        )



    st.session_state[

        "_pending_count_seen"

    ] = count



    if count:



        st.caption(

            f"🔴 {count} menunggu approval"

        )





# ============================================================

# ADMIN PROFILE

# ============================================================



@st.dialog("Profil Administrator")

def show_admin_profile():



    admin = current_admin() or {}



    name = (

        admin.get("name")

        or admin.get("username")

        or "Administrator"

    )



    username = (

        admin.get("username")

        or ""

    )



    # ========================================================

    # INITIALS

    # ========================================================



    words = [

        word

        for word in str(name).strip().split()

        if word

    ]



    if len(words) >= 2:

        initials = (

            words[0][0]

            +

            words[-1][0]

        ).upper()



    elif len(words) == 1:

        initials = (

            words[0][:2]

        ).upper()



    else:

        initials = "AD"





    # ========================================================

    # PROFILE STYLE

    # ========================================================



    st.html(

        """

        <style>



        /* ================================================

           PROFILE SHELL

           ================================================ */



        .profile-shell {

            padding-top: 2px;

        }





        /* ================================================

           MAIN ACCOUNT CARD

           ================================================ */



        .profile-account-card {

            padding: 20px;



            border: 1px solid #E5E7EB;

            border-radius: 14px;



            background: #FFFFFF;



            box-shadow:

                0 3px 12px

                rgba(15, 23, 42, 0.035);

        }





        /* ================================================

           TOP IDENTITY

           ================================================ */



        .profile-identity {

            display: flex;



            align-items: center;

            justify-content: space-between;



            gap: 18px;

        }





        .profile-identity-left {

            display: flex;



            align-items: center;



            gap: 13px;

        }





        .profile-avatar {

            width: 48px;

            height: 48px;



            flex-shrink: 0;



            display: flex;



            align-items: center;

            justify-content: center;



            border-radius: 12px;



            background: #FFF1F2;



            border: 1px solid #F5D5D7;



            color: #C92830;



            font-size: 0.94rem;

            font-weight: 800;



            letter-spacing: 0.02em;

        }





        .profile-name {

            color: #20242E;



            font-size: 1rem;

            font-weight: 780;



            line-height: 1.25;

        }





        .profile-subtitle {

            margin-top: 4px;



            color: #8E97A3;



            font-size: 0.73rem;

        }





        /* ================================================

           ACTIVE STATUS

           ================================================ */



        .profile-active {

            display: inline-flex;



            align-items: center;



            gap: 6px;



            padding: 6px 10px;



            border-radius: 999px;



            background: #EAF8EF;



            color: #167A4D;



            font-size: 0.68rem;

            font-weight: 750;



            white-space: nowrap;

        }





        .profile-active-dot {

            width: 6px;

            height: 6px;



            border-radius: 50%;



            background: #26B66D;

        }





        /* ================================================

           ACCOUNT INFORMATION

           ================================================ */



        .profile-divider {

            height: 1px;



            margin: 18px 0;



            background: #ECEFF2;

        }





        .profile-info-grid {

            display: grid;



            grid-template-columns:

                repeat(2, minmax(0, 1fr));



            gap: 12px;

        }





        .profile-info-item {

            padding: 12px 14px;



            border-radius: 10px;



            background: #F8F9FB;

        }





        .profile-info-label {

            color: #9AA2AE;



            font-size: 0.63rem;

            font-weight: 750;



            letter-spacing: 0.055em;



            text-transform: uppercase;

        }





        .profile-info-value {

            margin-top: 5px;



            color: #3C4653;



            font-size: 0.79rem;

            font-weight: 700;

        }





        /* ================================================

           NOTE

           ================================================ */



        .profile-note {

            margin-top: 14px;



            padding: 11px 13px;



            border-radius: 9px;



            background: #F8F9FB;



            color: #7F8895;



            font-size: 0.69rem;

            line-height: 1.55;

        }





        /* ================================================

           LOGOUT AREA

           ================================================ */



        .profile-logout-label {

            margin-top: 18px;

            margin-bottom: 7px;



            color: #A1A8B1;



            font-size: 0.65rem;

            font-weight: 650;

        }





        div[class*="st-key-profile_logout_wrap"]

        .stButton > button {



            min-height: 40px !important;



            background: #FFFFFF !important;



            border:

                1px solid

                #E7BFC2 !important;



            border-radius: 9px !important;



            color: #C52E35 !important;



            font-weight: 650 !important;



            box-shadow: none !important;

        }





        div[class*="st-key-profile_logout_wrap"]

        .stButton > button * {



            color: #C52E35 !important;

        }





        div[class*="st-key-profile_logout_wrap"]

        .stButton > button:hover {



            background: #FFF6F6 !important;



            border-color: #DA999D !important;

        }





        @media(max-width: 700px) {



            .profile-info-grid {

                grid-template-columns: 1fr;

            }



        }



        </style>

        """

    )





    # ========================================================

    # USERNAME / SUBTITLE

    # ========================================================



    if username:



        subtitle = (

            f"@{_safe_text(username)}"

        )



    else:



        subtitle = (

            "Administrator TARA"

        )





    # ========================================================

    # ACCOUNT CARD

    # ========================================================



    st.html(

        f"""

        <div class="profile-shell">



            <div class="profile-account-card">



                <div class="profile-identity">



                    <div class="profile-identity-left">



                        <div class="profile-avatar">

                            {_safe_text(initials)}

                        </div>





                        <div>



                            <div class="profile-name">

                                {_safe_text(name)}

                            </div>



                            <div class="profile-subtitle">

                                {subtitle}

                            </div>



                        </div>



                    </div>





                    <div class="profile-active">



                        <span class="profile-active-dot">

                        </span>



                        Aktif



                    </div>



                </div>





                <div class="profile-divider">

                </div>





                <div class="profile-info-grid">



                    <div class="profile-info-item">



                        <div class="profile-info-label">

                            Peran

                        </div>



                        <div class="profile-info-value">

                            Administrator

                        </div>



                    </div>





                    <div class="profile-info-item">



                        <div class="profile-info-label">

                            Hak Akses

                        </div>



                        <div class="profile-info-value">

                            Akses Penuh

                        </div>



                    </div>



                </div>



            </div>





            <div class="profile-note">

                Akun administrator memiliki hak untuk

                mengelola data, user, serta fungsi administratif TARA.

            </div>



        </div>

        """

    )





    # ========================================================

    # LOGOUT

    # ========================================================



    st.html(

        """

        <div class="profile-logout-label">

            SESI AKUN

        </div>

        """

    )





    left, logout_col = st.columns(

        [

            1.7,

            1,

        ]

    )





    with logout_col:



        with st.container(

            key="profile_logout_wrap"

        ):



            logout_clicked = st.button(

                "↩ Keluar dari akun",

                use_container_width=True,

                key="profile_logout_button",

            )





    if logout_clicked:



        logout()



        st.switch_page(

            "pages/0_Login.py"

        )





# ============================================================

# SIDEBAR

# ============================================================



def render_sidebar(

    active_label: str,

):



    require_login()



    admin = (

        current_admin()

    )



    with st.sidebar:



        # ====================================================
        # TARA LOGO
        # ====================================================

        if SIDEBAR_LOGO_URI:

            st.html(
                f"""
                <div class="tara-sidebar-brand">
                    <img
                        src="{SIDEBAR_LOGO_URI}"
                        class="tara-sidebar-logo"
                        alt="TARA Logo"
                    >
                </div>
                """
            )

        else:

            st.html(
                """
                <div class="tara-sidebar-brand-fallback">
                    <div class="tara-brand-main">
                        🔴
                        <span>TARA</span>
                    </div>
                    <div class="tara-brand-sub">
                        Telkom Area Recommendation Assistant
                    </div>
                </div>
                """
            )



        for (

            section_label,

            items,

        ) in NAV_SECTIONS:



            st.html(

                f"""

                <div class="

                    tara-section-label

                ">

                    {_safe_text(section_label)}

                </div>

                """

            )



            for (

                label,

                target,

                icon,

            ) in items:



                probe_path = (

                    NAV_CAPABILITY_PROBE.get(

                        label

                    )

                )



                if (

                    probe_path

                    and

                    not api_supports(

                        "get",

                        probe_path,

                    )

                ):



                    st.caption(

                        f"{icon} {label}"

                    )



                    continue



                display_label = (

                    f"🔸 {label}"

                    if label == active_label

                    else

                    f"{icon}  {label}"

                )



                st.page_link(

                    target,

                    label=display_label,

                )



                if (

                    label

                    ==

                    "User & Approval Bot"

                ):



                    _pending_users_badge()



        st.divider()



        if st.button(

            "🛡️  Administrator",

            use_container_width=True,

            key=(

                "sidebar_admin_"

                +

                _safe_key(

                    active_label

                )

            ),

        ):



            show_admin_profile()



        st.caption(

            "Masuk sebagai "

            +

            str(

                admin.get(

                    "name",

                    "Administrator",

                )

            )

        )



        if st.button(

            "↩️  Keluar",

            use_container_width=True,

            key=(

                "sidebar_logout_"

                +

                _safe_key(

                    active_label

                )

            ),

        ):



            logout()



            st.switch_page(

                "pages/0_Login.py"

            )





# ============================================================

# TOPBAR

# ============================================================



def render_topbar(

    breadcrumb: list[str],

):



    require_login()



    parts = []



    for (

        index,

        item,

    ) in enumerate(

        breadcrumb

    ):



        safe = _safe_text(

            item

        )



        if (

            index

            ==

            len(breadcrumb) - 1

        ):



            parts.append(

                f"<strong>"

                f"{safe}"

                f"</strong>"

            )



        else:



            parts.append(

                safe

            )





    trail = (

        " &nbsp;›&nbsp; "

        .join(

            parts

        )

    )





    key_base = (

        _safe_key(

            "_".join(

                breadcrumb

            )

        )

    )





    # ========================================================

    # TOPBAR LAYOUT

    # ========================================================



    breadcrumb_col, action_col = (

    st.columns(

        [

            11,

            1.20,

        ],

        vertical_alignment="center",

    )

)





    # ========================================================

    # BREADCRUMB

    # ========================================================



    with breadcrumb_col:



        st.html(

            f"""

            <div class="

                tara-breadcrumb

            ">

                {trail}

            </div>

            """

        )





    # ========================================================

    # ACTION BUTTONS

    # ========================================================



    with action_col:



        notification_col, profile_col = (

            st.columns(

                [

                    1,

                    1,

                ],

                gap="small",

                vertical_alignment="center",

            )

        )





        # ----------------------------------------------------

        # NOTIFICATION

        # ----------------------------------------------------



        with notification_col:



            if st.button(

                "🔔",

                help="User & Approval Bot",

                key=(

                    "notification_"

                    +

                    key_base

                ),

                use_container_width=True,

            ):



                st.switch_page(

                    "pages/5_User_Approval.py"

                )





        # ----------------------------------------------------

        # PROFILE

        # ----------------------------------------------------



        with profile_col:



            if st.button(

                "👤",

                help="Profil Administrator",

                key=(

                    "profile_"

                    +

                    key_base

                ),

                use_container_width=True,

            ):



                show_admin_profile()





    # ========================================================

    # DIVIDER

    # ========================================================



    st.html(

        """

        <div class="

            tara-topbar-line

        ">

        </div>

        """

    )





# ============================================================

# HEADER

# ============================================================



def render_header(

    title: str,

    subtitle: str,

):



    st.title(

        title

    )



    st.caption(

        subtitle

    )





# ============================================================

# BADGE

# ============================================================



def badge(

    text: str,

    color: str,

) -> str:



    return (

        f'<span class="badge '

        f'badge-{color}">'

        f'● {_safe_text(text)}'

        '</span>'

    )





# ============================================================

# SUCCESS SCREEN

# ============================================================



def success_screen(

    title: str,

    message: str,

    back_list_label: str,

    back_list_target: str,

):



    key_base = (

        _safe_key(

            back_list_target

        )

    )



    _, center, _ = (

        st.columns(

            [

                1.1,

                5.8,

                1.1,

            ]

        )

    )



    with center:



        with st.container(

            border=True

        ):



            st.html(

                f"""

                <div class="

                    tara-result-icon

                ">

                    ✅

                </div>



                <div class="

                    tara-process-heading

                ">

                    {_safe_text(title)}

                </div>



                <div class="

                    tara-process-desc

                ">

                    {_safe_text(message)}

                </div>

                """

            )



            st.divider()



            c1, c2 = (

                st.columns(

                    2

                )

            )



            with c1:



                go_list = (

                    st.button(

                        back_list_label,

                        type="primary",

                        use_container_width=True,

                        key=(

                            "success_list_"

                            +

                            key_base

                        ),

                    )

                )



            with c2:



                go_home = (

                    st.button(

                        "Kembali ke Dashboard",

                        use_container_width=True,

                        key=(

                            "success_home_"

                            +

                            key_base

                        ),

                    )

                )



            if go_list:



                target = (

                    str(

                        back_list_target

                    )

                    .replace(

                        "\\\\",

                        "/",

                    )

                )



                if target.endswith(

                    "1_Data_Pelanggan_CBASE.py"

                ):



                    st.session_state[

                        "cbase_view"

                    ] = "list"



                    st.session_state[

                        "cbase_page"

                    ] = 1



                elif target.endswith(

                    "2_Data_ODP.py"

                ):



                    st.session_state[

                        "odp_view"

                    ] = "list"



                    st.session_state[

                        "odp_page"

                    ] = 1



                st.switch_page(

                    back_list_target

                )



            if go_home:



                st.switch_page(

                    "Home.py"

                )





# ============================================================

# ERROR SCREEN

# ============================================================



def error_screen(

    title: str,

    message: str,

    back_list_label: str,

    back_list_target: str,

    retry_view_setter=None,

):



    _, center, _ = (

        st.columns(

            [

                1.1,

                5.8,

                1.1,

            ]

        )

    )



    with center:



        with st.container(

            border=True

        ):



            st.html(

                f"""

                <div class="

                    tara-result-icon

                ">

                    ❌

                </div>



                <div class="

                    tara-process-heading

                ">

                    {_safe_text(title)}

                </div>



                <div class="

                    tara-process-desc

                ">

                    {_safe_text(message)}

                </div>

                """

            )



            st.divider()



            c1, c2 = (

                st.columns(

                    2

                )

            )



            with c1:



                retry = (

                    st.button(

                        "Coba Lagi",

                        type="primary",

                        use_container_width=True,

                    )

                )



            with c2:



                home = (

                    st.button(

                        "Kembali ke Dashboard",

                        use_container_width=True,

                    )

                )



            if retry:



                if (

                    retry_view_setter

                    is not None

                ):



                    retry_view_setter()



                st.rerun()



            if home:



                st.switch_page(

                    "Home.py"

                )





# ============================================================

# LIVE PROCESS

# ============================================================



@st.fragment(

    run_every=5

)

def _pending_status_fragment(

    batch_id: str,

):



    batch_id = str(

        batch_id

        or "-"

    )



    timer_key = (

        "_tara_process_start_"

        +

        batch_id

    )



    if (

        timer_key

        not in

        st.session_state

    ):



        st.session_state[

            timer_key

        ] = time.time()



    elapsed = max(

        0,

        int(

            time.time()

            -

            st.session_state[

                timer_key

            ]

        ),

    )



    minutes, seconds = (

        divmod(

            elapsed,

            60,

        )

    )



    hours, minutes = (

        divmod(

            minutes,

            60,

        )

    )



    if hours:



        elapsed_text = (

            f"{hours:02d}:"

            f"{minutes:02d}:"

            f"{seconds:02d}"

        )



    else:



        elapsed_text = (

            f"{minutes:02d}:"

            f"{seconds:02d}"

        )



    result = api_get(

        (

            "/api/admin/upload/status/"

            +

            batch_id

        )

    )



    status = "unknown"

    row_count = None

    notes = ""



    if result.get(

        "ok"

    ):



        body = (

            result.get(

                "data"

            )

            or {}

        )



        data = (

            body.get(

                "data"

            )

            or {}

        )



        status = (

            str(

                data.get(

                    "status"

                )

                or "unknown"

            )

            .lower()

        )



        row_count = (

            data.get(

                "row_count"

            )

        )



        notes = (

            data.get(

                "notes"

            )

            or ""

        )





    # ========================================================

    # SUCCESS

    # ========================================================



    if status == "success":



        message = (

            "Data berhasil diproses "

            "dan sudah tersedia di TARA."

        )



        if row_count is not None:



            try:



                count_text = (

                    f"{int(row_count):,}"

                    .replace(

                        ",",

                        ".",

                    )

                )



                message += (

                    f" Total data sekarang "

                    f"{count_text} baris."

                )



            except Exception:

                pass



        st.html(

            f"""

            <div class="

                tara-result-icon

            ">

                ✅

            </div>



            <div class="

                tara-process-heading

            ">

                Pemrosesan selesai

            </div>



            <div class="

                tara-process-desc

            ">

                {_safe_text(message)}

            </div>



            <div class="

                process-steps

            ">



                <span class="

                    process-step done

                ">

                    ✓ File diterima

                </span>



                <span class="

                    process-step done

                ">

                    ✓ Diproses

                </span>



                <span class="

                    process-step done

                ">

                    ✓ Selesai

                </span>



            </div>

            """

        )



        return





    # ========================================================

    # FAILED

    # ========================================================



    if status == "failed":



        st.html(

            f"""

            <div class="

                tara-result-icon

            ">

                ❌

            </div>



            <div class="

                tara-process-heading

            ">

                Pemrosesan gagal

            </div>



            <div class="

                tara-process-desc

            ">

                {

                    _safe_text(

                        notes

                        or

                        "Server mengalami masalah "

                        "saat memproses data."

                    )

                }

            </div>

            """

        )



        return





    # ========================================================

    # RUNNING

    # ========================================================



    st.html(

        f"""

        <div class="

            tara-loader-wrap

        ">



            <div class="

                tara-clock

            ">



                <div class="

                    clock-hour

                ">

                </div>



                <div class="

                    clock-minute

                ">

                </div>



            </div>



        </div>





        <div class="

            tara-process-heading

        ">

            Data sedang diproses

        </div>





        <div class="

            tara-process-desc

        ">



            File sudah diterima server.

            Sistem sedang memperbarui data TARA.



            <br><br>



            Waktu berjalan:

            <strong>

                {elapsed_text}

            </strong>



        </div>





        <div class="

            process-steps

        ">



            <span class="

                process-step done

            ">

                ✓ File diterima

            </span>



            <span class="

                process-step active

            ">

                ● Sedang diproses

            </span>



            <span class="

                process-step

            ">

                Selesai

            </span>



        </div>

        """

    )



    if notes:



        st.info(

            notes

        )





# ============================================================

# PENDING SCREEN

# ============================================================



def pending_screen(

    title: str,

    batch_id: str,

    back_list_label: str,

    back_list_target: str,

):



    key_base = (

        _safe_key(

            (

                str(

                    batch_id

                )

                +

                "_"

                +

                back_list_target

            )

        )

    )



    _, center, _ = (

        st.columns(

            [

                1.1,

                5.8,

                1.1,

            ]

        )

    )



    with center:



        with st.container(

            border=True

        ):



            _pending_status_fragment(

                batch_id

            )



            st.divider()



            c1, c2, c3 = (

                st.columns(

                    3

                )

            )



            with c1:



                go_list = (

                    st.button(

                        back_list_label,

                        type="primary",

                        use_container_width=True,

                        key=(

                            "pending_list_"

                            +

                            key_base

                        ),

                    )

                )



            with c2:



                activity = (

                    st.button(

                        "Riwayat Aktivitas",

                        use_container_width=True,

                        key=(

                            "pending_activity_"

                            +

                            key_base

                        ),

                    )

                )



            with c3:



                home = (

                    st.button(

                        "Dashboard",

                        use_container_width=True,

                        key=(

                            "pending_home_"

                            +

                            key_base

                        ),

                    )

                )



            if go_list:



                target = (

                    str(

                        back_list_target

                    )

                    .replace(

                        "\\\\",

                        "/",

                    )

                )



                if target.endswith(

                    "1_Data_Pelanggan_CBASE.py"

                ):



                    st.session_state[

                        "cbase_view"

                    ] = "list"



                    st.session_state[

                        "cbase_page"

                    ] = 1



                    st.session_state[

                        "cbase_edit_row"

                    ] = None



                    st.session_state.pop(

                        "cbase_upload_batch_id",

                        None,

                    )



                elif target.endswith(

                    "2_Data_ODP.py"

                ):



                    st.session_state[

                        "odp_view"

                    ] = "list"



                    st.session_state[

                        "odp_page"

                    ] = 1



                    st.session_state[

                        "odp_edit_row"

                    ] = None



                    st.session_state.pop(

                        "odp_upload_batch_id",

                        None,

                    )



                st.switch_page(

                    back_list_target

                )



            if activity:



                st.switch_page(

                    "pages/4_Riwayat_Aktivitas.py"

                )



            if home:



                st.switch_page(

                    "Home.py"

                )





# ============================================================

# ENTERPRISE SHARED PAGINATION

# ============================================================



def render_pagination(

    *,

    total: int,

    page_size: int,

    page_key: str,

    item_label: str = "data",

):



    # ========================================================

    # NORMALIZE

    # ========================================================



    try:



        total = max(

            0,

            int(

                total

                or 0

            ),

        )



    except (

        TypeError,

        ValueError,

    ):



        total = 0





    try:



        page_size = max(

            1,

            int(

                page_size

                or 10

            ),

        )



    except (

        TypeError,

        ValueError,

    ):



        page_size = 10





    total_pages = max(

        1,

        (

            total

            +

            page_size

            - 1

        )

        //

        page_size,

    )





    try:



        current_page = int(

            st.session_state.get(

                page_key,

                1,

            )

            or 1

        )



    except (

        TypeError,

        ValueError,

    ):



        current_page = 1





    current_page = max(

        1,

        min(

            current_page,

            total_pages,

        ),

    )





    st.session_state[

        page_key

    ] = current_page





    # ========================================================

    # ROW RANGE

    # ========================================================



    if total == 0:



        start_row = 0

        end_row = 0



    else:



        start_row = (

            (

                current_page

                - 1

            )

            *

            page_size

            +

            1

        )



        end_row = min(

            current_page

            *

            page_size,

            total,

        )





    # ========================================================

    # FORMAT

    # ========================================================



    def fmt(

        value,

    ):



        return (

            f"{int(value):,}"

            .replace(

                ",",

                ".",

            )

        )





    # ========================================================

    # WIDGET STATE

    # ========================================================



    input_key = (

        f"_page_input_"

        f"{page_key}"

    )



    sync_key = (

        f"_page_sync_"

        f"{page_key}"

    )





    if (

        input_key

        not in

        st.session_state

    ):



        st.session_state[

            input_key

        ] = current_page





    # Setelah menggunakan arrow,

    # sinkronkan angka input

    # sebelum widget dibuat.



    if st.session_state.pop(

        sync_key,

        False,

    ):



        st.session_state[

            input_key

        ] = current_page





    # ========================================================

    # DIRECT JUMP CALLBACK

    # ========================================================



    def jump_to_page():



        try:



            target_page = int(

                st.session_state.get(

                    input_key,

                    current_page,

                )

            )



        except (

            TypeError,

            ValueError,

        ):



            target_page = (

                current_page

            )





        target_page = max(

            1,

            min(

                target_page,

                total_pages,

            ),

        )





        st.session_state[

            page_key

        ] = target_page





    # ========================================================

    # LAYOUT

    # ========================================================



    summary_col, navigation_col = (

        st.columns(

            [

                1.45,

                1.05,

            ],

            vertical_alignment="center",

        )

    )





    # ========================================================

    # SUMMARY

    # ========================================================



    with summary_col:



        st.html(

            f"""

            <div class="

                tara-pagination-summary

            ">



                Menampilkan



                <strong>

                    {fmt(start_row)}–{fmt(end_row)}

                </strong>



                dari



                <strong>

                    {fmt(total)}

                </strong>



                {html.escape(item_label)}.



            </div>

            """

        )





    # ========================================================

    # NAVIGATION

    # ========================================================



    with navigation_col:



        with st.container(

            key=(

                f"tara_pagination_"

                f"{page_key}"

            )

        ):



            (

                first_col,

                previous_col,

                label_col,

                input_col,

                total_col,

                next_col,

                last_col,

            ) = st.columns(

                [

                    0.42,

                    0.42,

                    0.76,

                    0.64,

                    0.92,

                    0.42,

                    0.42,

                ],

                vertical_alignment="center",

            )





            # =================================================

            # FIRST PAGE

            # =================================================



            with first_col:



                first_clicked = (

                    st.button(

                        "«",

                        key=(

                            f"page_first_"

                            f"{page_key}"

                        ),

                        disabled=(

                            current_page <= 1

                        ),

                        use_container_width=True,

                        help="Halaman pertama",

                    )

                )





            # =================================================

            # PREVIOUS

            # =================================================



            with previous_col:



                previous_clicked = (

                    st.button(

                        "‹",

                        key=(

                            f"page_prev_"

                            f"{page_key}"

                        ),

                        disabled=(

                            current_page <= 1

                        ),

                        use_container_width=True,

                        help="Halaman sebelumnya",

                    )

                )





            # =================================================

            # LABEL

            # =================================================



            with label_col:



                st.html(

                    """

                    <div class="

                        tara-pagination-label

                    ">

                        Halaman

                    </div>

                    """

                )





            # =================================================

            # PAGE INPUT

            # =================================================



            with input_col:



                st.number_input(

                    "Nomor halaman",

                    min_value=1,

                    max_value=total_pages,

                    step=1,

                    key=input_key,

                    label_visibility="collapsed",

                    on_change=jump_to_page,

                )





            # =================================================

            # TOTAL PAGES

            # =================================================



            with total_col:



                st.html(

                    f"""

                    <div class="

                        tara-pagination-label

                    ">



                        dari



                        <strong>

                            {fmt(total_pages)}

                        </strong>



                    </div>

                    """

                )





            # =================================================

            # NEXT

            # =================================================



            with next_col:



                next_clicked = (

                    st.button(

                        "›",

                        key=(

                            f"page_next_"

                            f"{page_key}"

                        ),

                        disabled=(

                            current_page

                            >= total_pages

                        ),

                        use_container_width=True,

                        help="Halaman berikutnya",

                    )

                )





            # =================================================

            # LAST PAGE

            # =================================================



            with last_col:



                last_clicked = (

                    st.button(

                        "»",

                        key=(

                            f"page_last_"

                            f"{page_key}"

                        ),

                        disabled=(

                            current_page

                            >= total_pages

                        ),

                        use_container_width=True,

                        help="Halaman terakhir",

                    )

                )





    # ========================================================

    # BUTTON ACTIONS

    # ========================================================



    if first_clicked:



        st.session_state[

            page_key

        ] = 1



        st.session_state[

            sync_key

        ] = True



        st.rerun()





    if previous_clicked:



        st.session_state[

            page_key

        ] = max(

            1,

            current_page - 1,

        )



        st.session_state[

            sync_key

        ] = True



        st.rerun()





    if next_clicked:



        st.session_state[

            page_key

        ] = min(

            total_pages,

            current_page + 1,

        )



        st.session_state[

            sync_key

        ] = True



        st.rerun()





    if last_clicked:



        st.session_state[

            page_key

        ] = total_pages



        st.session_state[

            sync_key

        ] = True



        st.rerun()