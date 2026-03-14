from __future__ import annotations

import streamlit as st


def render_products_page() -> None:
    st.header("Products")
    st.write("This page is where Inventory Managers will create and update products.")

    with st.form("product_form"):
        left_column, right_column = st.columns(2)

        with left_column:
            st.text_input("Product Name")
            st.text_input("SKU / Code")
            st.text_input("Category")

        with right_column:
            st.text_input("Unit of Measure")
            st.number_input("Reorder Level", min_value=0.0, step=1.0)
            st.number_input("Initial Stock (Optional)", min_value=0.0, step=1.0)

        st.form_submit_button("Save Product", disabled=True)

    st.text_input("Search by SKU", disabled=True)
    st.info(
        "Next step: save product form data into the products table and show a live table below it."
    )