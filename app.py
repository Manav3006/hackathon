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
        "current_page": "Dashboard",
        "is_authenticated": False,
        "current_user": None,
        "current_role": "Inventory Manager",
    }

    for key, value in default_state.items():
        st.session_state.setdefault(key, value)


def render_sidebar() -> None:
    page_names = list(PAGE_RENDERERS.keys())
    current_page = st.session_state.current_page
    current_index = page_names.index(
        current_page) if current_page in page_names else 0

    st.sidebar.title("CoreInventory")
    st.sidebar.caption("Phase 1 starter shell")
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
    st.sidebar.write(f"Role: {st.session_state.current_role}")
    st.sidebar.info(
        "This build only sets up the project structure and database schema. "
        "Real authentication and CRUD actions come next."
    )


def main() -> None:
    st.set_page_config(page_title="CoreInventory", layout="wide")
    init_db()
    initialize_session_state()

    # Always show Authentication page first if not authenticated
    if not st.session_state.get("is_authenticated", False):
        st.session_state.current_page = "Authentication"
        render_sidebar()
        st.title("CoreInventory")
        PAGE_RENDERERS["Authentication"]()
        return

    # After login, default to Dashboard if just authenticated
    if st.session_state.current_page == "Authentication":
        st.session_state.current_page = "Dashboard"

    render_sidebar()
    st.title("CoreInventory")
    PAGE_RENDERERS[st.session_state.current_page]()


if __name__ == "__main__":
    main()
