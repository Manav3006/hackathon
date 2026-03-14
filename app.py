from __future__ import annotations

import streamlit as st

from app_pages.auth import render_auth_page
from app_pages.dashboard import render_dashboard_page
from app_pages.history import render_history_page
from app_pages.operations import render_operations_page
from app_pages.products import render_products_page
from app_pages.profile import render_profile_page
from app_pages.settings import render_settings_page
from db import DATABASE_PATH, init_db


PAGE_RENDERERS = {
    "Authentication": render_auth_page,
    "Dashboard": render_dashboard_page,
    "Products": render_products_page,
    "Operations": render_operations_page,
    "Move History": render_history_page,
    "Settings": render_settings_page,
    "My Profile": render_profile_page,
}


def initialize_session_state() -> None:
    default_state = {
        "current_page": "Authentication",
        "is_authenticated": False,
        "current_user": None,
        "current_user_id": None,
        "current_user_email": None,
        "current_role": "Inventory Manager",
    }

    for key, value in default_state.items():
        st.session_state.setdefault(key, value)


def render_sidebar() -> None:
    if st.session_state.is_authenticated:
        page_names = [name for name in PAGE_RENDERERS if name != "Authentication"]
    else:
        page_names = ["Authentication"]

    if st.session_state.current_page not in page_names:
        st.session_state.current_page = page_names[0]

    current_page = st.session_state.current_page
    current_index = page_names.index(current_page)

    st.sidebar.title("CoreInventory")
    st.sidebar.caption("Phase 1: auth + schema foundation")
    st.session_state.current_page = st.sidebar.radio(
        "Navigation",
        options=page_names,
        index=current_index,
    )

    st.sidebar.divider()
    st.sidebar.write(f"Database file: {DATABASE_PATH.name}")
    st.sidebar.write(
        f"Authenticated: {'Yes' if st.session_state.is_authenticated else 'No'}"
    )
    if st.session_state.is_authenticated:
        st.sidebar.write(f"User: {st.session_state.current_user}")
        st.sidebar.write(f"Role: {st.session_state.current_role}")
        st.sidebar.success("You are signed in. Business pages are unlocked.")
    else:
        st.sidebar.info("Please log in from the Authentication page to access business pages.")


def main() -> None:
    st.set_page_config(page_title="CoreInventory", layout="wide")
    init_db()
    initialize_session_state()
    render_sidebar()

    st.title("CoreInventory")
    st.caption(
        "This app now includes real signup/login/reset-password behavior, while "
        "products and operations pages are still being connected."
    )

    if not st.session_state.is_authenticated and st.session_state.current_page != "Authentication":
        st.session_state.current_page = "Authentication"
        st.warning("Please log in first to continue.")

    PAGE_RENDERERS[st.session_state.current_page]()


if __name__ == "__main__":
    main()