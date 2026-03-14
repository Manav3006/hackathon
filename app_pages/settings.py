from __future__ import annotations

import streamlit as st


def render_settings_page() -> None:
    st.header("Settings")
    st.write("This page will manage warehouses and locations for multi-warehouse inventory.")

    warehouse_column, location_column = st.columns(2)

    with warehouse_column:
        st.subheader("Warehouse Setup")
        st.text_input("Warehouse Name")
        st.text_input("Warehouse Code")
        st.text_area("Address")
        st.button("Save Warehouse", disabled=True)

    with location_column:
        st.subheader("Location Setup")
        st.text_input("Location Name")
        st.text_input("Location Code")
        st.text_input("Parent Warehouse")
        st.button("Save Location", disabled=True)

    st.info(
        "Next step: connect these forms to the warehouses and locations tables in db.py."
    )