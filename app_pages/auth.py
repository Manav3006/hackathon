from __future__ import annotations

import streamlit as st
import re
from db import check_user_credentials, create_user, email_exists, create_password_reset_otp, validate_password_reset_otp, update_user_password
from datetime import datetime, timedelta
import random


def render_auth_page() -> None:
    st.header("Authentication")
    st.write(
        "This page handles signup, login, OTP reset, and logout. Only login/logout is wired up for now."
    )

    if not st.session_state.get("is_authenticated", False):
        login_tab, signup_tab, reset_tab = st.tabs(
            ["Login", "Signup", "Reset Password"])

        with login_tab:
            email = st.text_input("Email", key="login_email")
            password = st.text_input(
                "Password", type="password", key="login_password")
            login_clicked = st.button("Login")
            login_error = st.empty()
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if login_clicked:
                if not re.match(email_pattern, email):
                    login_error.error("Please enter a valid email address.")
                else:
                    user = check_user_credentials(email, password)
                    if user:
                        st.session_state.is_authenticated = True
                        st.session_state.current_user = user["full_name"]
                        st.session_state.current_role = user["role"]
                        st.success(f"Welcome, {user['full_name']}!")
                    else:
                        login_error.error("Invalid email or password.")
            st.caption(
                "Enter your credentials to log in. Email must be in a valid format.")

        with signup_tab:
            signup_full_name = st.text_input(
                "Full name", key="signup_full_name")
            signup_email = st.text_input("Email", key="signup_email")
            signup_role = st.selectbox(
                "Role",
                options=["Inventory Manager", "Warehouse Staff"],
                key="signup_role",
            )
            signup_password = st.text_input(
                "Password", type="password", key="signup_password")
            signup_error = st.empty()
            signup_success = st.empty()
            if st.button("Create account"):
                if not signup_full_name or not signup_email or not signup_password:
                    signup_error.error("All fields are required.")
                elif not re.match(email_pattern, signup_email):
                    signup_error.error("Please enter a valid email address.")
                elif email_exists(signup_email):
                    signup_error.error("Email already registered.")
                else:
                    ok = create_user(signup_full_name, signup_email,
                                     signup_password, signup_role)
                    if ok:
                        signup_success.success(
                            "Account created! You can now log in.")
                    else:
                        signup_error.error(
                            "Could not create account. Try again.")

        with reset_tab:
            reset_email = st.text_input("Registered email", key="reset_email")
            reset_otp = st.text_input("OTP code", key="reset_otp")
            reset_password = st.text_input(
                "New password", type="password", key="reset_password")
            reset_error = st.empty()
            reset_success = st.empty()
            if st.button("Send OTP"):
                if not re.match(email_pattern, reset_email):
                    reset_error.error("Please enter a valid email address.")
                elif not email_exists(reset_email):
                    reset_error.error("Email not found.")
                else:
                    # For demo, generate a 6-digit OTP and set expiry 5 min from now
                    otp_code = str(random.randint(100000, 999999))
                    expires_at = (datetime.now() + timedelta(minutes=5)
                                  ).strftime("%Y-%m-%d %H:%M:%S")
                    create_password_reset_otp(
                        reset_email, otp_code, expires_at)
                    reset_success.success(f"OTP sent! (Demo: {otp_code})")
            if st.button("Reset password"):
                if not reset_email or not reset_otp or not reset_password:
                    reset_error.error("All fields are required.")
                elif not validate_password_reset_otp(reset_email, reset_otp):
                    reset_error.error("Invalid or expired OTP.")
                else:
                    update_user_password(reset_email, reset_password)
                    reset_success.success(
                        "Password updated! You can now log in.")

        st.info(
            "Signup and reset forms are now connected to the users and password_reset_otps tables."
        )
    else:
        st.success(
            f"You are logged in as {st.session_state.current_user} ({st.session_state.current_role})")
        if st.button("Logout"):
            st.session_state.is_authenticated = False
            st.session_state.current_user = None
            st.session_state.current_role = "Inventory Manager"
            st.success("You have been logged out.")
