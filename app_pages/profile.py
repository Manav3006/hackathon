from __future__ import annotations

import streamlit as st


def render_profile_page() -> None:
    st.header("My Profile")
    st.write("This page will show the logged-in user and later provide a real logout action.")

    st.text_input(
        "Full Name",
        value=st.session_state.get("current_user") or "Not signed in yet",
        disabled=True,
    )
    st.text_input(
        "Role",
        value=st.session_state.get("current_role", "Inventory Manager"),
        disabled=True,
    )
    st.button("Logout", disabled=True)

    st.info(
        "Next step: once auth is connected, this page can read the active user from session state."
    )