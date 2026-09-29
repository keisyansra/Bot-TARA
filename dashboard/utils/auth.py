import hmac

import streamlit as st


# ============================================================
# AUTH SESSION
# ============================================================

def init_auth_state():
    """
    Menyiapkan session login TARA.
    Session Streamlit terpisah untuk tiap browser/user.
    """

    st.session_state.setdefault(
        "tara_logged_in",
        False,
    )

    st.session_state.setdefault(
        "tara_admin",
        None,
    )


# ============================================================
# STATUS LOGIN
# ============================================================

def is_logged_in():
    init_auth_state()

    return bool(
        st.session_state.get(
            "tara_logged_in"
        )
    )


# ============================================================
# CURRENT ADMIN
# ============================================================

def current_admin():
    init_auth_state()

    return (
        st.session_state.get(
            "tara_admin"
        )
        or {}
    )


# ============================================================
# AUTHENTICATE
# ============================================================

def authenticate(
    admin_name: str,
    access_code: str,
):
    """
    Login menggunakan:
    - Nama Admin
    - Kode Akses

    Semua administrator memiliki role yang sama.
    """

    admin_name = (
        str(admin_name or "")
        .strip()
        .lower()
    )

    access_code = (
        str(access_code or "")
        .strip()
    )

    if not admin_name:
        return (
            False,
            "Nama admin wajib diisi.",
        )

    if not access_code:
        return (
            False,
            "Kode akses wajib diisi.",
        )

    try:
        admins = st.secrets[
            "admins"
        ]

    except Exception:
        return (
            False,
            "Konfigurasi akun administrator belum tersedia.",
        )

    for account_key in admins:

        account = (
            admins[
                account_key
            ]
        )

        stored_name = (
            str(
                account.get(
                    "name",
                    "",
                )
            )
            .strip()
        )

        stored_name_normalized = (
            stored_name.lower()
        )

        stored_code = (
            str(
                account.get(
                    "access_code",
                    "",
                )
            )
        )

        name_match = (
            admin_name
            == stored_name_normalized
        )

        code_match = (
            hmac.compare_digest(
                access_code,
                stored_code,
            )
        )

        if (
            name_match
            and code_match
        ):

            st.session_state[
                "tara_logged_in"
            ] = True

            st.session_state[
                "tara_admin"
            ] = {
                "id": account_key,
                "name": stored_name,
                "role": "admin",
            }

            return (
                True,
                None,
            )

    return (
        False,
        "Nama admin atau kode akses tidak sesuai.",
    )


# ============================================================
# LOGOUT
# ============================================================

def logout():
    """
    Logout admin dan membersihkan state sensitif.
    """

    st.session_state.pop(
        "tara_logged_in",
        None,
    )

    st.session_state.pop(
        "tara_admin",
        None,
    )

    st.session_state.pop(
        "_pending_count_seen",
        None,
    )

    for key in list(
        st.session_state.keys()
    ):

        if (
            key.startswith(
                "cbase_"
            )
            or
            key.startswith(
                "odp_"
            )
            or
            key.startswith(
                "_tara_process_"
            )
        ):

            st.session_state.pop(
                key,
                None,
            )


# ============================================================
# PAGE GUARD
# ============================================================

def require_login():
    """
    Memblokir dashboard jika user belum login.
    """

    if is_logged_in():
        return

    st.switch_page(
        "pages/0_Login.py"
    )

    st.stop()