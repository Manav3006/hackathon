from __future__ import annotations

import streamlit as st

from app_pages.auth import render_auth_page
from app_pages.dashboard import render_dashboard_page
from app_pages.history import render_history_page
from app_pages.operations import render_operations_page
from app_pages.products import render_products_page
from app_pages.profile import render_profile_page
from app_pages.settings import render_settings_page
from db import init_db


APP_NAME = "StockFlow"
APP_TAGLINE = "Inventory Management System"


PAGE_RENDERERS = {
    "Authentication": render_auth_page,
    "Dashboard": render_dashboard_page,
    "Products": render_products_page,
    "Operations": render_operations_page,
    "Move History": render_history_page,
    "Settings": render_settings_page,
    "My Profile": render_profile_page,
}


def sync_sidebar_page_selection() -> None:
    st.session_state.current_page = st.session_state.sidebar_page


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


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

            :root {
                --sf-bg: #0b1117;
                --sf-surface: #111c27;
                --sf-surface-soft: #162331;
                --sf-text: #e6edf4;
                --sf-subtle: #96a6b8;
                --sf-accent: #2aa198;
                --sf-accent-strong: #22897f;
                --sf-border: #253444;
            }

            .stApp {
                font-family: 'Space Grotesk', sans-serif;
                color: var(--sf-text);
                background:
                    radial-gradient(1000px 500px at -10% -10%, #163345 0%, transparent 52%),
                    radial-gradient(900px 340px at 110% 0%, #102633 0%, transparent 50%),
                    var(--sf-bg);
            }

            [data-testid="stSidebar"] {
                border-right: 1px solid var(--sf-border);
                background: linear-gradient(180deg, #0f1720 0%, #0b1117 100%);
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            .block-container {
                padding-top: 1.2rem;
                padding-bottom: 2rem;
                animation: sfFadeIn 0.35s ease-out;
            }

            @keyframes sfFadeIn {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }

            h1, h2, h3 {
                letter-spacing: -0.02em;
                color: var(--sf-text);
            }

            div[data-testid="stMetric"] {
                background: var(--sf-surface);
                border: 1px solid var(--sf-border);
                border-radius: 14px;
                padding: 0.6rem 0.75rem;
            }

            div[data-testid="stForm"] {
                background: var(--sf-surface);
                border: 1px solid var(--sf-border);
                border-radius: 14px;
                padding: 0.9rem 1rem;
            }

            [data-baseweb="input"] > div,
            [data-baseweb="select"] > div,
            textarea {
                background: var(--sf-surface-soft) !important;
                border-color: var(--sf-border) !important;
            }

            input, textarea {
                color: var(--sf-text) !important;
            }

            div.stButton > button, div.stDownloadButton > button, div[data-testid="stFormSubmitButton"] button {
                border-radius: 10px;
                border: 1px solid var(--sf-accent);
                background: var(--sf-accent);
                color: #03131b;
                font-weight: 600;
            }

            div.stButton > button:hover, div.stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] button:hover {
                background: var(--sf-accent-strong);
                border-color: var(--sf-accent-strong);
                color: #e8f8f7;
            }

            [data-testid="stAlert"] {
                border-radius: 12px;
            }

            [data-testid="stMarkdownContainer"] p {
                color: var(--sf-subtle);
            }

            [data-testid="stDataFrame"],
            [data-testid="stTable"] {
                border: 1px solid var(--sf-border);
                border-radius: 12px;
            }

            .stockflow-hero {
                background: linear-gradient(120deg, #101b26 0%, #142231 100%);
                border: 1px solid var(--sf-border);
                border-radius: 16px;
                padding: 0.75rem 0.95rem;
                margin-bottom: 0.55rem;
            }

            .stockflow-hero h2 {
                margin: 0 0 0.15rem 0;
                color: var(--sf-text);
            }

            .stockflow-hero p {
                margin: 0;
                color: var(--sf-subtle);
                font-size: 0.92rem;
            }

            @media (max-width: 768px) {
                .block-container {
                    padding-top: 1rem;
                    padding-left: 0.8rem;
                    padding-right: 0.8rem;
                }
            }

            #MainMenu, footer {
                visibility: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    if st.session_state.is_authenticated:
        page_names = [
            name for name in PAGE_RENDERERS if name != "Authentication"]
    else:
        page_names = ["Authentication"]

    if st.session_state.current_page not in page_names:
        st.session_state.current_page = page_names[0]

    if st.session_state.get("sidebar_page") != st.session_state.current_page:
        st.session_state.sidebar_page = st.session_state.current_page

    st.sidebar.title(APP_NAME)
    st.sidebar.caption("Inventory")
    st.sidebar.radio(
        "Navigation",
        options=page_names,
        key="sidebar_page",
        on_change=sync_sidebar_page_selection,
    )
    st.session_state.current_page = st.session_state.sidebar_page

    st.sidebar.divider()
    if st.session_state.is_authenticated:
        st.sidebar.caption(f"User: {st.session_state.current_user}")
        st.sidebar.caption(f"Role: {st.session_state.current_role}")
    else:
        st.sidebar.caption("Please log in")


def main() -> None:
    st.set_page_config(page_title=APP_NAME, layout="wide")
    init_db()
    initialize_session_state()
    apply_global_styles()
    render_sidebar()

    st.markdown(
        f"""
        <div class=\"stockflow-hero\">
            <h2>{APP_NAME}</h2>
            <p>{APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.is_authenticated and st.session_state.current_page != "Authentication":
        st.session_state.current_page = "Authentication"
        st.warning("Please log in first to continue.")

    PAGE_RENDERERS[st.session_state.current_page]()


if __name__ == "__main__":
    main()
