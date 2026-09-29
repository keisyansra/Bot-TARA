import html

from datetime import datetime



import pandas as pd

import streamlit as st



from utils.api_client import (

    api_delete,

    api_get,

    api_put,

    show_error,

)



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

    page_title="User & Approval Bot - TARA",

    page_icon="🔐",

    layout="wide",

)





# ============================================================

# GLOBAL STYLE

# ============================================================



inject_css()





# ============================================================

# PAGE CSS

# ============================================================



USER_CSS = """

<style>



/* ==========================================================

   PAGE HEADER

   ========================================================== */



.user-page-title {

    margin-top: 3px;

    margin-bottom: 7px;



    color: #1F2937;



    font-size: 2.15rem;

    font-weight: 800;

    line-height: 1.15;



    letter-spacing: -0.025em;

}



.user-page-subtitle {

    max-width: 850px;



    margin-bottom: 26px;



    color: #7E8794;



    font-size: 0.87rem;

    line-height: 1.65;

}





/* ==========================================================

   KPI CARDS

   ========================================================== */



/* ==========================================================
   KPI CARDS — STANDARD TARA
   ========================================================== */

.user-kpi {
    min-height:
        188px;

    padding:
        20px
        22px
        18px
        22px;

    box-sizing:
        border-box;

    border:
        1px solid
        #E2E6EB;

    border-radius:
        14px;

    background:
        #FFFFFF;

    box-shadow:
        0 3px 12px
        rgba(15, 23, 42, 0.025);

    display:
        flex;

    flex-direction:
        column;
}


/* ==========================================================
   KPI LABEL
   ========================================================== */

.user-kpi-label {
    display:
        flex;

    align-items:
        center;

    gap:
        8px;

    min-height:
        38px;

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


/* ==========================================================
   KPI VALUE
   ========================================================== */

.user-kpi-value {
    margin-top:
        14px;

    color:
        #20242E;

    font-size:
        1.95rem;

    font-weight:
        800;

    line-height:
        1.05;
}


/* MENUNGGU */

.user-kpi-value.pending {
    color:
        #A66A00;
}


/* SALES / BERHASIL */

.user-kpi-value.sales {
    color:
        #16865B;
}


/* ADMIN */

.user-kpi-value.admin {
    color:
        #7153A6;
}


/* GAGAL / DITOLAK jika nanti diperlukan */

.user-kpi-value.danger {
    color:
        #D32F3A;
}


/* ==========================================================
   KPI CAPTION
   ========================================================== */

.user-kpi-caption {
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



.user-kpi-label {

    display: flex;



    align-items: center;



    gap: 8px;



    color: #68717F;



    font-size: 0.72rem;

    font-weight: 750;



    letter-spacing: 0.035em;

}



.user-kpi-value {

    margin-top: 14px;



    color: #20242E;



    font-size: 1.75rem;

    font-weight: 800;



    line-height: 1;

}



.user-kpi-value.pending {

    color: #A66A00;

}



.user-kpi-value.sales {

    color: #167C50;

}



.user-kpi-value.admin {

    color: #7153A6;

}



.user-kpi-caption {

    margin-top: 9px;



    color: #969EA9;



    font-size: 0.70rem;

}





/* ==========================================================

   SECTION

   ========================================================== */



.user-section {

    margin-top: 30px;

    margin-bottom: 13px;

}



.user-section-title {

    color: #20242E;



    font-size: 1.08rem;

    font-weight: 750;

}



.user-section-subtitle {

    margin-top: 4px;



    color: #9199A5;



    font-size: 0.75rem;

}





/* ==========================================================

   USER MANAGEMENT CARD

   ========================================================== */



.user-profile-card {

    padding: 20px 22px;



    border: 1px solid #E2E6EB;

    border-radius: 13px;



    background: #FFFFFF;



    box-shadow:

        0 3px 12px

        rgba(15, 23, 42, 0.025);

}



.user-profile-header {

    display: flex;



    align-items: center;

    justify-content: space-between;



    gap: 20px;

}



.user-profile-identity {

    display: flex;



    align-items: center;



    gap: 13px;

}



.user-profile-avatar {

    width: 44px;

    height: 44px;



    flex-shrink: 0;



    display: flex;



    align-items: center;

    justify-content: center;



    border-radius: 12px;



    background: #F1F3F6;



    color: #4E5866;



    font-size: 1.15rem;

}



.user-profile-name {

    color: #20242E;



    font-size: 0.96rem;

    font-weight: 750;

}



.user-profile-username {

    margin-top: 3px;



    color: #929AA6;



    font-size: 0.74rem;

}



.user-profile-meta {

    margin-top: 17px;



    padding-top: 16px;



    border-top: 1px solid #EDF0F3;



    display: grid;



    grid-template-columns:

        repeat(3, minmax(0, 1fr));



    gap: 18px;

}



.user-meta-label {

    color: #9AA2AD;



    font-size: 0.66rem;

    font-weight: 700;



    letter-spacing: 0.04em;



    text-transform: uppercase;

}



.user-meta-value {

    margin-top: 5px;



    color: #46505D;



    font-size: 0.80rem;

    font-weight: 600;

}





/* ==========================================================

   ROLE BADGES

   ========================================================== */



.user-role-badge {

    display: inline-flex;



    align-items: center;



    gap: 6px;



    padding: 6px 10px;



    border-radius: 999px;



    font-size: 0.71rem;

    font-weight: 750;



    white-space: nowrap;

}



.user-role-badge.pending {

    color: #926100;



    background: #FFF3D8;

}



.user-role-badge.sales {

    color: #14784C;



    background: #E8F7ED;

}



.user-role-badge.admin {

    color: #664A96;



    background: #F0EAF8;

}



.user-role-badge.rejected {

    color: #697381;



    background: #EFF1F4;

}



.user-role-dot {

    width: 7px;

    height: 7px;



    border-radius: 50%;

}



.user-role-dot.pending {

    background: #E0A11D;

}



.user-role-dot.sales {

    background: #26B56D;

}



.user-role-dot.admin {

    background: #8163AF;

}



.user-role-dot.rejected {

    background: #8993A0;

}





/* ==========================================================

   ACTION SECTION

   ========================================================== */



.user-action-box {

    margin-top: 17px;



    padding: 15px 17px;



    border: 1px solid #E7EAEE;

    border-radius: 11px;



    background: #FAFBFC;

}



.user-action-title {

    color: #424C59;



    font-size: 0.78rem;

    font-weight: 750;

}



.user-action-help {

    margin-top: 4px;



    color: #949CA7;



    font-size: 0.71rem;

    line-height: 1.5;

}





/* ==========================================================

   DANGER BUTTON

   ========================================================== */



div[class*="st-key-user_delete_"]

.stButton > button {



    color: #C43138 !important;



    border:

        1px solid

        #EDC9CB !important;



    background: #FFFFFF !important;

}



div[class*="st-key-user_delete_"]

.stButton > button * {

    color: #C43138 !important;

}



div[class*="st-key-user_delete_"]

.stButton > button:hover {



    color: #B5232B !important;



    border-color: #DFA7AA !important;



    background: #FFF5F5 !important;

}





/* ==========================================================

   REJECT BUTTON

   ========================================================== */



div[class*="st-key-user_reject_"]

.stButton > button {



    color: #B7791F !important;



    border:

        1px solid

        #ECD7AE !important;



    background: #FFFFFF !important;

}



div[class*="st-key-user_reject_"]

.stButton > button * {

    color: #B7791F !important;

}



div[class*="st-key-user_reject_"]

.stButton > button:hover {



    background: #FFF9ED !important;



    border-color: #D8BA7A !important;

}





/* ==========================================================

   TABLE

   ========================================================== */



[data-testid="stDataFrame"] {



    overflow: hidden;



    border:

        1px solid

        #E1E5EA;



    border-radius: 12px;



    background: #FFFFFF;



    box-shadow:

        0 3px 12px

        rgba(15, 23, 42, 0.025);

}





/* ==========================================================

   UPDATE INFO

   ========================================================== */



.user-refresh-note {

    color: #9AA2AD;



    font-size: 0.70rem;



    text-align: right;

}





/* ==========================================================

   EMPTY

   ========================================================== */



.user-empty {

    padding: 38px 20px;



    text-align: center;



    border:

        1px solid

        #E2E6EB;



    border-radius: 12px;



    background: #FFFFFF;

}



.user-empty-title {

    margin-top: 7px;



    color: #404A57;



    font-size: 0.90rem;

    font-weight: 700;

}



.user-empty-caption {

    margin-top: 4px;



    color: #969EA9;



    font-size: 0.74rem;

}





/* ==========================================================

   RESPONSIVE

   ========================================================== */



@media(max-width: 900px) {



    .user-profile-meta {

        grid-template-columns: 1fr;

    }



}



</style>

"""





st.html(

    USER_CSS

)





# ============================================================

# SESSION

# ============================================================



ss = st.session_state



ss.setdefault(

    "user_role_filter",

    "Semua",

)



ss.setdefault(

    "selected_user_id",

    None,

)





# ============================================================

# HELPERS

# ============================================================



def esc(

    value,

):



    return html.escape(

        str(

            value

            if value is not None

            else "-"

        )

    )





def normalize_user(

    user,

):

    """

    Mendukung data user berupa dictionary atau tuple/list.

    """



    if isinstance(

        user,

        dict,

    ):



        return {

            "user_id":

                user.get(

                    "user_id"

                )

                or

                user.get(

                    "id"

                ),



            "username":

                user.get(

                    "username"

                )

                or "",



            "full_name":

                user.get(

                    "full_name"

                )

                or

                user.get(

                    "name"

                )

                or

                "-",



            "role":

                str(

                    user.get(

                        "role"

                    )

                    or

                    "pending"

                )

                .strip()

                .lower(),



            "created_at":

                user.get(

                    "created_at"

                )

                or

                user.get(

                    "registered_at"

                )

                or

                user.get(

                    "created"

                ),

        }





    if isinstance(

        user,

        (list, tuple),

    ):



        values = list(

            user

        )





        return {

            "user_id":

                values[0]

                if len(values) > 0

                else None,



            "username":

                values[1]

                if len(values) > 1

                else "",



            "full_name":

                values[2]

                if len(values) > 2

                else "-",



            "role":

                str(

                    values[3]

                    if len(values) > 3

                    else "pending"

                )

                .strip()

                .lower(),



            "created_at":

                values[4]

                if len(values) > 4

                else None,

        }





    return {

        "user_id": None,

        "username": "",

        "full_name": "-",

        "role": "pending",

        "created_at": None,

    }





def extract_users(

    result,

):



    if not result.get(

        "ok"

    ):



        return []





    body = (

        result.get(

            "data"

        )

        or {}

    )





    # api_client membungkus response API

    if isinstance(

        body,

        dict,

    ):



        users = (

            body.get(

                "data"

            )

        )



        if isinstance(

            users,

            list,

        ):



            return [

                normalize_user(

                    user

                )

                for user in users

            ]





    if isinstance(

        body,

        list,

    ):



        return [

            normalize_user(

                user

            )

            for user in body

        ]





    return []





def format_datetime(

    value,

):



    if not value:



        return "-"





    text = str(

        value

    ).strip()





    try:



        cleaned = (

            text.replace(

                "Z",

                "+00:00",

            )

        )



        dt = (

            datetime.fromisoformat(

                cleaned

            )

        )





        return (

            f"{dt.day:02d}/"

            f"{dt.month:02d}/"

            f"{dt.year} "

            f"{dt.strftime('%H:%M')}"

        )



    except Exception:



        return text





def role_info(

    role,

):



    role = (

        str(

            role

            or "pending"

        )

        .lower()

    )





    mapping = {

        "pending": (

            "pending",

            "Menunggu Persetujuan",

            "🟡",

        ),



        "sales": (

            "sales",

            "Sales",

            "🟢",

        ),



        "admin": (

            "admin",

            "Admin",

            "🟣",

        ),



        "rejected": (

            "rejected",

            "Ditolak",

            "⚪",

        ),

    }





    return mapping.get(

        role,

        (

            "rejected",

            role.title(),

            "⚪",

        ),

    )





def role_badge_html(

    role,

):



    role_class, label, _ = (

        role_info(

            role

        )

    )





    return (

        f"""

        <span class="

            user-role-badge

            {role_class}

        ">



            <span class="

                user-role-dot

                {role_class}

            ">

            </span>



            {esc(label)}



        </span>

        """

    )





def current_dashboard_admin():



    try:



        admin = (

            current_admin()

            or {}

        )



    except Exception:



        admin = {}





    admin_name = (

        admin.get(

            "name"

        )

        or

        admin.get(

            "username"

        )

        or

        "Administrator"

    )





    admin_id = (

        admin.get(

            "id"

        )

        or

        admin.get(

            "username"

        )

        or

        admin_name

    )





    return (

        str(

            admin_id

        ),

        str(

            admin_name

        ),

    )





def perform_role_update(

    user,

    new_role,

):



    admin_id, admin_name = (

        current_dashboard_admin()

    )





    with st.spinner(

        "Memperbarui hak akses user..."

    ):



        result = api_put(

            (

                "/api/admin/users/"

                f"{user['user_id']}"

            ),

            json={

                "role":

                    new_role,



                "admin_id":

                    admin_id,



                "admin_name":

                    admin_name,

            },

        )





    if not result.get(

        "ok"

    ):



        show_error(

            result

        )



        return False





    ss[

        "_user_flash"

    ] = (

        f"Hak akses {user['full_name']} "

        "berhasil diperbarui."

    )



    # Jika user yang baru diproses sebelumnya masih pending,
    # setelah approve/reject arahkan ke pending berikutnya.
    if (

        str(

            user.get(

                "role",

                "",

            )

        )

        .strip()

        .lower()

        == "pending"

    ):

        ss[

            "_prefer_pending_after_update"

        ] = True





    return True





# ============================================================

# CONFIRM ROLE DIALOG

# ============================================================



@st.dialog(

    "Konfirmasi Perubahan Akses"

)

def confirm_role_dialog(

    user,

    new_role,

    action_title,

    description,

):



    _, role_label, _ = (

        role_info(

            new_role

        )

    )





    st.html(

        f"""

        <div style="

            text-align:center;

            padding:5px 5px 16px 5px;

        ">



            <div style="

                width:46px;

                height:46px;



                margin:0 auto 12px auto;



                display:flex;

                align-items:center;

                justify-content:center;



                border-radius:13px;



                background:#F1F3F6;



                font-size:1.2rem;

            ">

                👤

            </div>





            <div style="

                color:#20242E;

                font-size:1rem;

                font-weight:750;

            ">

                {esc(user["full_name"])}

            </div>





            <div style="

                margin-top:3px;



                color:#929AA6;

                font-size:.75rem;

            ">

                @{esc(user["username"] or "-")}

                &nbsp;·&nbsp;

                ID {esc(user["user_id"])}

            </div>



        </div>

        """

    )





    st.info(

        description

    )





    st.caption(

        "Role setelah perubahan"

    )





    st.html(

        role_badge_html(

            new_role

        )

    )





    st.write("")





    cancel_col, confirm_col = (

        st.columns(

            2

        )

    )





    with cancel_col:



        if st.button(

            "Batal",

            use_container_width=True,

            key=(

                "role_cancel_"

                f"{user['user_id']}_"

                f"{new_role}"

            ),

        ):



            st.rerun()





    with confirm_col:



        if st.button(

            action_title,

            type="primary",

            use_container_width=True,

            key=(

                "role_confirm_"

                f"{user['user_id']}_"

                f"{new_role}"

            ),

        ):



            if perform_role_update(

                user,

                new_role,

            ):



                st.rerun()





# ============================================================

# DELETE DIALOG

# ============================================================



@st.dialog(

    "Hapus User?"

)

def confirm_delete_user(

    user,

):



    st.html(

        f"""

        <div style="

            text-align:center;

            padding:5px 5px 14px 5px;

        ">



            <div style="

                font-size:2rem;

            ">

                🗑️

            </div>





            <div style="

                margin-top:8px;



                color:#20242E;

                font-size:1rem;

                font-weight:750;

            ">

                {esc(user["full_name"])}

            </div>





            <div style="

                margin-top:3px;



                color:#929AA6;

                font-size:.75rem;

            ">

                @{esc(user["username"] or "-")}

                &nbsp;·&nbsp;

                ID {esc(user["user_id"])}

            </div>



        </div>

        """

    )





    st.warning(

        "User akan dihapus dari daftar akses Bot TARA. "

        "Pastikan tindakan ini memang diperlukan."

    )





    cancel_col, delete_col = (

        st.columns(

            2

        )

    )





    with cancel_col:



        if st.button(

            "Batal",

            use_container_width=True,

            key=(

                "delete_cancel_"

                f"{user['user_id']}"

            ),

        ):



            st.rerun()





    with delete_col:



        if st.button(

            "Ya, Hapus User",

            type="primary",

            use_container_width=True,

            key=(

                "delete_confirm_"

                f"{user['user_id']}"

            ),

        ):



            with st.spinner(

                "Menghapus user..."

            ):



                result = api_delete(

                    (

                        "/api/admin/users/"

                        f"{user['user_id']}"

                    )

                )





            if not result.get(

                "ok"

            ):



                show_error(

                    result

                )



                return





            ss[

                "_user_flash"

            ] = (

                f"User {user['full_name']} "

                "berhasil dihapus."

            )





            ss.selected_user_id = (

                None

            )





            st.rerun()





# ============================================================

# SIDEBAR

# ============================================================



render_sidebar(

    "User & Approval Bot"

)





# ============================================================

# TOPBAR

# ============================================================



render_topbar(

    [

        "User & Approval Bot",

    ]

)





# ============================================================

# HEADER

# ============================================================



header_left, header_right = (

    st.columns(

        [

            5,

            1,

        ],

        vertical_alignment="bottom",

    )

)





with header_left:



    st.html(

        """

        <div class="

            user-page-title

        ">

            User & Approval Bot

        </div>



        <div class="

            user-page-subtitle

        ">



            Kelola permintaan akses dan hak akses

            pengguna Bot TARA secara terpusat.



        </div>

        """

    )





with header_right:



    if st.button(

        "↻ Perbarui",

        use_container_width=True,

        key="refresh_user_page",

    ):



        st.rerun()





# ============================================================

# FLASH MESSAGE

# ============================================================



flash = ss.pop(

    "_user_flash",

    None,

)





if flash:



    st.success(

        flash

    )





# ============================================================

# USER MODULE

# ============================================================



@st.fragment(

    run_every=10

)

def render_user_module():



    # ========================================================

    # GET USERS

    # ========================================================



    result = api_get(

        "/api/admin/users"

    )





    if not result.get(

        "ok"

    ):



        show_error(

            result

        )



        return





    users = extract_users(

        result

    )





    # ========================================================

    # COUNTS

    # ========================================================



    total_users = len(

        users

    )





    pending_count = sum(

        1

        for user in users

        if user["role"]

        == "pending"

    )





    sales_count = sum(

        1

        for user in users

        if user["role"]

        == "sales"

    )





    admin_count = sum(

        1

        for user in users

        if user["role"]

        == "admin"

    )





    # ========================================================

    # KPI

    # ========================================================



    k1, k2, k3, k4 = (

        st.columns(

            4,

            gap="medium",

        )

    )





    with k1:



        st.html(

            f"""

            <div class="

                user-kpi

            ">



                <div class="

                    user-kpi-label

                ">

                    👥 TOTAL USER

                </div>



                <div class="

                    user-kpi-value

                ">

                    {total_users}

                </div>



                <div class="

                    user-kpi-caption

                ">

                    Seluruh user Bot TARA

                </div>



            </div>

            """

        )





    with k2:



        st.html(

            f"""

            <div class="

                user-kpi

            ">



                <div class="

                    user-kpi-label

                ">

                    🕘 MENUNGGU

                </div>



                <div class="

                    user-kpi-value pending

                ">

                    {pending_count}

                </div>



                <div class="

                    user-kpi-caption

                ">

                    Memerlukan persetujuan

                </div>



            </div>

            """

        )





    with k3:



        st.html(

            f"""

            <div class="

                user-kpi

            ">



                <div class="

                    user-kpi-label

                ">

                    👤 SALES

                </div>



                <div class="

                    user-kpi-value sales

                ">

                    {sales_count}

                </div>



                <div class="

                    user-kpi-caption

                ">

                    User dengan akses sales

                </div>



            </div>

            """

        )





    with k4:



        st.html(

            f"""

            <div class="

                user-kpi

            ">



                <div class="

                    user-kpi-label

                ">

                    🛡️ ADMIN

                </div>



                <div class="

                    user-kpi-value admin

                ">

                    {admin_count}

                </div>



                <div class="

                    user-kpi-caption

                ">

                    User dengan akses admin

                </div>



            </div>

            """

        )





    # ========================================================

    # USERS SECTION

    # ========================================================



    st.html(

        """

        <div class="

            user-section

        ">



            <div class="

                user-section-title

            ">

                Daftar User

            </div>



            <div class="

                user-section-subtitle

            ">

                Lihat status akses user Bot TARA

                dan pilih user yang ingin dikelola.

            </div>



        </div>

        """

    )





    if not users:



        st.html(

            """

            <div class="

                user-empty

            ">



                <div style="

                    font-size:1.8rem;

                ">

                    👥

                </div>



                <div class="

                    user-empty-title

                ">

                    Belum ada user

                </div>



                <div class="

                    user-empty-caption

                ">

                    User Bot TARA akan muncul di halaman ini.

                </div>



            </div>

            """

        )



        return





    # ========================================================

    # FILTER

    # ========================================================



    filter_map = {

        "Semua":

            None,



        "Menunggu Persetujuan":

            "pending",



        "Sales":

            "sales",



        "Admin":

            "admin",



        "Ditolak":

            "rejected",

    }





    selected_filter = (

        st.selectbox(

            "Filter berdasarkan role",

            list(

                filter_map.keys()

            ),

            key="user_role_filter",

        )

    )





    role_filter = (

        filter_map.get(

            selected_filter

        )

    )





    filtered_users = (

        users

        if role_filter is None

        else [

            user

            for user in users

            if user["role"]

            == role_filter

        ]

    )





    # ========================================================

    # TABLE

    # ========================================================



    table_rows = []





    for user in filtered_users:



        role_class, role_label, role_icon = (

            role_info(

                user["role"]

            )

        )





        username = (

            (

                "@"

                + user["username"]

            )

            if user["username"]

            else "-"

        )





        table_rows.append(

            {

                "User ID":

                    str(

                        user["user_id"]

                    ),



                "Username":

                    username,



                "Nama Lengkap":

                    user["full_name"],



                "Role":

                    (

                        f"{role_icon} "

                        f"{role_label}"

                    ),



                "Terdaftar Sejak":

                    format_datetime(

                        user["created_at"]

                    ),

            }

        )





    if filtered_users:



        df = pd.DataFrame(

            table_rows

        )





        st.dataframe(

            df,

            hide_index=True,

            use_container_width=True,

            height=(

                min(

                    390,

                    45

                    +

                    len(df)

                    * 37

                )

            ),

            column_config={

                "User ID":

                    st.column_config.TextColumn(

                        "User ID",

                        width="small",

                    ),



                "Username":

                    st.column_config.TextColumn(

                        "Username",

                        width="medium",

                    ),



                "Nama Lengkap":

                    st.column_config.TextColumn(

                        "Nama Lengkap",

                        width="large",

                    ),



                "Role":

                    st.column_config.TextColumn(

                        "Role",

                        width="medium",

                    ),



                "Terdaftar Sejak":

                    st.column_config.TextColumn(

                        "Terdaftar Sejak",

                        width="medium",

                    ),

            },

        )





    else:



        st.info(

            "Tidak ada user pada kategori ini."

        )





    st.html(

        """

        <div class="

            user-refresh-note

        ">

            Data diperbarui otomatis setiap 10 detik.

        </div>

        """

    )





    # ========================================================

    # MANAGEMENT SECTION

    # ========================================================



    st.html(

        """

        <div class="

            user-section

        ">



            <div class="

                user-section-title

            ">

                Kelola Akses User

            </div>



            <div class="

                user-section-subtitle

            ">

                Permintaan akses baru diprioritaskan secara otomatis.

                Pilih user untuk melihat detail dan mengelola hak aksesnya.

            </div>



        </div>

        """

    )





    # ========================================================

    # USER SELECT

    # ========================================================



    users_by_id = {

        str(

            user["user_id"]

        ):

            user



        for user in users



        if user["user_id"]

        is not None

    }





    user_ids = list(

        users_by_id.keys()

    )





    if not user_ids:



        return





    # ========================================================
    # PRIORITAS USER PENDING
    # ========================================================

    pending_user_ids = [

        user_id

        for user_id in user_ids

        if (

            users_by_id[

                user_id

            ].get(

                "role"

            )

            == "pending"

        )

    ]



    other_user_ids = [

        user_id

        for user_id in user_ids

        if user_id

        not in pending_user_ids

    ]



    ordered_user_ids = (

        pending_user_ids

        +

        other_user_ids

    )





    # ========================================================
    # DETEKSI PENDING BARU
    # ========================================================

    previous_pending_ids = set(

        ss.get(

            "_pending_user_ids_seen",

            [],

        )

    )



    new_pending_ids = [

        user_id

        for user_id in pending_user_ids

        if user_id

        not in previous_pending_ids

    ]



    prefer_pending_after_update = bool(

        ss.pop(

            "_prefer_pending_after_update",

            False,

        )

    )



    # Setelah approve/reject, pindah ke pending berikutnya.
    if (

        prefer_pending_after_update

        and pending_user_ids

    ):

        ss.selected_user_id = (

            pending_user_ids[0]

        )



    # Jika ada user baru meminta akses, langsung tampilkan user tersebut.
    elif new_pending_ids:



        ss.selected_user_id = (

            new_pending_ids[0]

        )



    # Saat pertama masuk halaman, prioritaskan pending.
    elif (

        ss.selected_user_id

        not in ordered_user_ids

    ):



        ss.selected_user_id = (

            ordered_user_ids[0]

        )





    # Simpan pending yang sudah pernah terlihat agar polling 10 detik
    # tidak terus-menerus memindahkan pilihan admin.
    ss[

        "_pending_user_ids_seen"

    ] = list(

        pending_user_ids

    )





    # ========================================================
    # INFORMASI ANTREAN APPROVAL
    # ========================================================

    if pending_user_ids:



        st.caption(

            (

                f"🟡 {len(pending_user_ids)} "

                "permintaan akses sedang menunggu persetujuan. "

                "Permintaan baru diprioritaskan."

            )

        )



    else:



        st.caption(

            "✅ Tidak ada permintaan akses baru."

        )





    selected_user_id = (

        st.selectbox(

            "Pilih user",

            options=ordered_user_ids,

            key="selected_user_id",

            format_func=lambda user_id: (

                (

                    users_by_id[

                        user_id

                    ][

                        "full_name"

                    ]

                )

                +

                (

                    "  ·  @"

                    +

                    users_by_id[

                        user_id

                    ][

                        "username"

                    ]

                    if users_by_id[

                        user_id

                    ][

                        "username"

                    ]

                    else ""

                )

                +

                "  ·  ID "

                +

                user_id

                +

                (

                    "  ·  🟡 Menunggu Persetujuan"

                    if (

                        users_by_id[

                            user_id

                        ].get(

                            "role"

                        )

                        == "pending"

                    )

                    else ""

                )

            ),

        )

    )





    selected_user = (

        users_by_id[

            selected_user_id

        ]

    )





    role_class, role_label, _ = (

        role_info(

            selected_user[

                "role"

            ]

        )

    )





    username_display = (

        (

            "@"

            +

            selected_user[

                "username"

            ]

        )

        if selected_user[

            "username"

        ]

        else "-"

    )





    # ========================================================

    # PROFILE CARD

    # ========================================================



    st.html(

        f"""

        <div class="

            user-profile-card

        ">



            <div class="

                user-profile-header

            ">



                <div class="

                    user-profile-identity

                ">



                    <div class="

                        user-profile-avatar

                    ">

                        👤

                    </div>





                    <div>



                        <div class="

                            user-profile-name

                        ">

                            {esc(

                                selected_user[

                                    "full_name"

                                ]

                            )}

                        </div>



                        <div class="

                            user-profile-username

                        ">

                            {esc(

                                username_display

                            )}

                        </div>



                    </div>



                </div>





                {role_badge_html(

                    selected_user[

                        "role"

                    ]

                )}



            </div>





            <div class="

                user-profile-meta

            ">



                <div>



                    <div class="

                        user-meta-label

                    ">

                        User ID

                    </div>



                    <div class="

                        user-meta-value

                    ">

                        {esc(

                            selected_user[

                                "user_id"

                            ]

                        )}

                    </div>



                </div>





                <div>



                    <div class="

                        user-meta-label

                    ">

                        Role Saat Ini

                    </div>



                    <div class="

                        user-meta-value

                    ">

                        {esc(

                            role_label

                        )}

                    </div>



                </div>





                <div>



                    <div class="

                        user-meta-label

                    ">

                        Terdaftar Sejak

                    </div>



                    <div class="

                        user-meta-value

                    ">

                        {esc(

                            format_datetime(

                                selected_user[

                                    "created_at"

                                ]

                            )

                        )}

                    </div>



                </div>



            </div>



        </div>

        """

    )





    # ========================================================

    # CONTEXTUAL ACTIONS

    # ========================================================



    st.html(

        """

        <div class="

            user-action-box

        ">



            <div class="

                user-action-title

            ">

                Tindakan yang tersedia

            </div>



            <div class="

                user-action-help

            ">

                Sistem hanya menampilkan tindakan

                yang relevan dengan role user saat ini.

            </div>



        </div>

        """

    )





    st.write("")





    current_role = (

        selected_user[

            "role"

        ]

    )





    # ========================================================

    # PENDING

    # ========================================================



    if current_role == "pending":



        approve_col, admin_col, reject_col = (

            st.columns(

                [

                    1.2,

                    1,

                    1,

                ]

            )

        )





        with approve_col:



            if st.button(

                "✓ Setujui sebagai Sales",

                type="primary",

                use_container_width=True,

                key=(

                    "approve_sales_"

                    f"{selected_user_id}"

                ),

            ):



                confirm_role_dialog(

                    selected_user,

                    "sales",

                    "Ya, Setujui",

                    (

                        "User akan memperoleh akses "

                        "sebagai Sales pada Bot TARA."

                    ),

                )





        with admin_col:



            if st.button(

                "🛡️ Jadikan Admin",

                use_container_width=True,

                key=(

                    "approve_admin_"

                    f"{selected_user_id}"

                ),

            ):



                confirm_role_dialog(

                    selected_user,

                    "admin",

                    "Ya, Jadikan Admin",

                    (

                        "User akan memperoleh hak akses "

                        "Admin pada Bot TARA."

                    ),

                )





        with reject_col:



            with st.container(

                key=(

                    "user_reject_"

                    f"{selected_user_id}"

                )

            ):



                if st.button(

                    "Tolak Permintaan",

                    use_container_width=True,

                    key=(

                        "reject_"

                        f"{selected_user_id}"

                    ),

                ):



                    confirm_role_dialog(

                        selected_user,

                        "rejected",

                        "Ya, Tolak",

                        (

                            "Permintaan akses user akan "

                            "ditandai sebagai ditolak."

                        ),

                    )





    # ========================================================

    # SALES

    # ========================================================



    elif current_role == "sales":



        st.caption(

            "User saat ini memiliki akses Sales. "

            "Anda dapat meningkatkan akses menjadi Admin "

            "atau menghapus user."

        )



        # ====================================================

        # CENTERED ACTION GROUP

        # ====================================================



        spacer_left, admin_col, delete_col, spacer_right = st.columns(

            [

                2.2,

                1.25,

                1.05,

                2.2,

            ],

            gap="small",

        )



        with admin_col:



            if st.button(

                "🛡️ Jadikan Admin",

                type="primary",

                use_container_width=True,

                key=(

                    "sales_to_admin_"

                    f"{selected_user_id}"

                ),

            ):



                confirm_role_dialog(

                    selected_user,

                    "admin",

                    "Ya, Jadikan Admin",

                    (

                        "Hak akses user akan ditingkatkan "

                        "dari Sales menjadi Admin."

                    ),

                )



        with delete_col:



            with st.container(

                key=(

                    "user_delete_"

                    f"{selected_user_id}"

                )

            ):



                if st.button(

                    "🗑️ Hapus User",

                    use_container_width=True,

                    key=(

                        "delete_sales_"

                        f"{selected_user_id}"

                    ),

                ):



                    confirm_delete_user(

                        selected_user

                    )



    # ========================================================

    # ADMIN

    # ========================================================



    elif current_role == "admin":



        st.caption(

            "User saat ini memiliki akses Admin. "

            "Anda dapat mengubah akses menjadi Sales "

            "atau menghapus user."

        )



        # ====================================================
        # CENTERED ACTION GROUP
        # ====================================================



        spacer_left, sales_col, delete_col, spacer_right = st.columns(

            [

                2.2,

                1.25,

                1.05,

                2.2,

            ],

            gap="small",

        )



        with sales_col:



            if st.button(

                "👤 Ubah menjadi Sales",

                type="primary",

                use_container_width=True,

                key=(

                    "admin_to_sales_"

                    f"{selected_user_id}"

                ),

            ):



                confirm_role_dialog(

                    selected_user,

                    "sales",

                    "Ya, Ubah Role",

                    (

                        "Hak akses Admin akan diubah "

                        "menjadi akses Sales."

                    ),

                )



        with delete_col:



            with st.container(

                key=(

                    "user_delete_"

                    f"{selected_user_id}"

                )

            ):



                if st.button(

                    "🗑️ Hapus User",

                    use_container_width=True,

                    key=(

                        "delete_admin_"

                        f"{selected_user_id}"

                    ),

                ):



                    confirm_delete_user(

                        selected_user

                    )



    # ========================================================

    # REJECTED

    # ========================================================



    elif current_role == "rejected":



        sales_col, admin_col, delete_col = (

            st.columns(

                [

                    1.2,

                    1,

                    1,

                ]

            )

        )





        with sales_col:



            if st.button(

                "✓ Aktifkan sebagai Sales",

                type="primary",

                use_container_width=True,

                key=(

                    "rejected_to_sales_"

                    f"{selected_user_id}"

                ),

            ):



                confirm_role_dialog(

                    selected_user,

                    "sales",

                    "Ya, Aktifkan",

                    (

                        "User akan diaktifkan kembali "

                        "dengan akses Sales."

                    ),

                )





        with admin_col:



            if st.button(

                "🛡️ Jadikan Admin",

                use_container_width=True,

                key=(

                    "rejected_to_admin_"

                    f"{selected_user_id}"

                ),

            ):



                confirm_role_dialog(

                    selected_user,

                    "admin",

                    "Ya, Jadikan Admin",

                    (

                        "User akan diaktifkan "

                        "dengan hak akses Admin."

                    ),

                )





        with delete_col:



            with st.container(

                key=(

                    "user_delete_"

                    f"{selected_user_id}"

                )

            ):



                if st.button(

                    "🗑 Hapus User",

                    use_container_width=True,

                    key=(

                        "delete_rejected_"

                        f"{selected_user_id}"

                    ),

                ):



                    confirm_delete_user(

                        selected_user

                    )


# ============================================================
# RENDER
# ============================================================


render_user_module()