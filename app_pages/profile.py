from __future__ import annotations

import streamlit as st


def render_profile_page() -> None:
    st.header("My Profile")
    if st.session_state.get("is_authenticated", False):
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
        if st.button("Logout"):
            st.session_state.is_authenticated = False
            st.session_state.current_user = None
            st.session_state.current_role = "Inventory Manager"
            st.success("You have been logged out.")
    else:
        st.info("You are not logged in. Please use the Authentication page to log in.")
