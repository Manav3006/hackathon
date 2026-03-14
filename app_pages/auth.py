from __future__ import annotations

import streamlit as st

from db import (
    ROLE_OPTIONS,
    authenticate_user,
    create_user,
    generate_password_reset_otp,
    reset_password_with_otp,
)


def logout_current_user() -> None:
    st.session_state.is_authenticated = False
    st.session_state.current_user = None
    st.session_state.current_user_id = None
    st.session_state.current_user_email = None
    st.session_state.current_role = "Inventory Manager"
    st.session_state.current_page = "Authentication"


def _login_user(user: dict) -> None:
    st.session_state.is_authenticated = True
    st.session_state.current_user = user["full_name"]
    st.session_state.current_user_id = user["id"]
    st.session_state.current_user_email = user["email"]
    st.session_state.current_role = user["role"]
    st.session_state.current_page = "Dashboard"


def render_auth_page() -> None:
    st.header("Authentication")

    if st.session_state.get("is_authenticated"):
        st.success(
            "You are already signed in as "
            f"{st.session_state.get('current_user')} ({st.session_state.get('current_role')})."
        )
        if st.button("Logout", key="auth_logout_button"):
            logout_current_user()
            st.rerun()
        return

    login_tab, signup_tab, reset_tab = st.tabs(
        ["Login", "Signup", "Reset Password"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input(
                "Password", type="password", key="login_password")
            login_clicked = st.form_submit_button("Login")

        if login_clicked:
            if not email.strip() or not password:
                st.error("Please fill both email and password.")
            else:
                user = authenticate_user(email=email, password=password)
                if user is None:
                    st.error("Invalid email or password.")
                else:
                    _login_user(user)
                    st.success("Login successful.")
                    st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            full_name = st.text_input("Full name", key="signup_full_name")
            email = st.text_input("Email", key="signup_email")
            role = st.selectbox(
                "Role", options=ROLE_OPTIONS, key="signup_role")
            password = st.text_input(
                "Password", type="password", key="signup_password")
            signup_clicked = st.form_submit_button("Create account")

        if signup_clicked:
            success, message = create_user(
                full_name=full_name,
                email=email,
                password=password,
                role=role,
            )
            if success:
                st.success(message)
            else:
                st.error(message)

    with reset_tab:
        st.subheader("Step 1: Generate OTP")
        with st.form("request_otp_form"):
            otp_email = st.text_input(
                "Registered email", key="otp_request_email")
            otp_request_clicked = st.form_submit_button("Generate Demo OTP")

        if otp_request_clicked:
            if not otp_email.strip():
                st.error("Please enter your registered email.")
            else:
                success, message = generate_password_reset_otp(email=otp_email)
                if success:
                    st.session_state.latest_demo_otp = message
                    st.session_state.latest_demo_otp_email = otp_email.strip().lower()
                    st.success("OTP generated for demo use.")
                else:
                    st.error(message)

        latest_otp = st.session_state.get("latest_demo_otp")
        if latest_otp:
            st.code(
                f"Email: {st.session_state.get('latest_demo_otp_email')}\n"
                f"OTP: {latest_otp}"
            )

        st.subheader("Step 2: Apply OTP and set new password")
        with st.form("reset_password_form"):
            reset_email = st.text_input("Registered email", key="reset_email")
            otp_code = st.text_input("OTP code", key="reset_otp")
            new_password = st.text_input(
                "New password",
                type="password",
                key="reset_password",
            )
            reset_clicked = st.form_submit_button("Reset password")

        if reset_clicked:
            success, message = reset_password_with_otp(
                email=reset_email,
                otp_code=otp_code,
                new_password=new_password,
            )
            if success:
                st.success(message)
            else:
                st.error(message)
