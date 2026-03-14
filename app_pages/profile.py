from __future__ import annotations

import streamlit as st

from app_pages.auth import logout_current_user


def render_profile_page() -> None:
    st.header("My Profile")
    st.write("This page shows the current user and provides logout.")

    if not st.session_state.get("is_authenticated"):
        st.warning("You are not logged in. Please use the Authentication page first.")
        return

    st.text_input(
        "Full Name",
        value=st.session_state.get("current_user") or "",
        disabled=True,
    )
    st.text_input(
        "Email",
        value=st.session_state.get("current_user_email") or "",
        disabled=True,
    )
    st.text_input(
        "Role",
        value=st.session_state.get("current_role", "Inventory Manager"),
        disabled=True,
    )

    if st.button("Logout"):
        logout_current_user()
        st.success("You have been logged out.")
        st.rerun()