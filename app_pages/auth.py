from __future__ import annotations

import streamlit as st


def render_auth_page() -> None:
    st.header("Authentication")
    st.write(
        "This page will handle signup, login, OTP reset, and logout in the next step."
    )

    login_tab, signup_tab, reset_tab = st.tabs(["Login", "Signup", "Reset Password"])

    with login_tab:
        st.text_input("Email", key="login_email")
        st.text_input("Password", type="password", key="login_password")
        st.button("Login", disabled=True)
        st.caption("The button is disabled because the database auth logic is not connected yet.")

    with signup_tab:
        st.text_input("Full name", key="signup_full_name")
        st.text_input("Email", key="signup_email")
        st.selectbox(
            "Role",
            options=["Inventory Manager", "Warehouse Staff"],
            key="signup_role",
        )
        st.text_input("Password", type="password", key="signup_password")
        st.button("Create account", disabled=True)

    with reset_tab:
        st.text_input("Registered email", key="reset_email")
        st.text_input("OTP code", key="reset_otp")
        st.text_input("New password", type="password", key="reset_password")
        st.button("Reset password", disabled=True)

    st.info(
        "Next step: connect these forms to the users and password_reset_otps tables in db.py."
    )