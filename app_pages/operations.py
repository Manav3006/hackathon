from __future__ import annotations

import streamlit as st


def render_operations_page() -> None:
    st.header("Operations")
    st.write(
        "Every stock-changing action in this app will eventually use one shared stock-posting rule from db.py."
    )

    receipt_tab, delivery_tab, transfer_tab, adjustment_tab = st.tabs(
        ["Receipts", "Deliveries", "Internal Transfers", "Adjustments"]
    )

    with receipt_tab:
        _render_receipt_form()

    with delivery_tab:
        _render_delivery_form()

    with transfer_tab:
        _render_transfer_form()

    with adjustment_tab:
        _render_adjustment_form()


def _render_receipt_form() -> None:
    st.text_input("Supplier Name")
    st.text_input("Product SKU")
    st.number_input("Quantity Received", min_value=0.0, step=1.0)
    st.text_input("Destination Warehouse")
    st.text_input("Destination Location")
    st.button("Validate Receipt", disabled=True)


def _render_delivery_form() -> None:
    st.text_input("Customer Name")
    st.text_input("Product SKU", key="delivery_sku")
    st.number_input("Quantity to Deliver", min_value=0.0, step=1.0, key="delivery_qty")
    st.selectbox("Delivery Status", options=["Draft", "Waiting", "Ready", "Done", "Canceled"])
    st.button("Validate Delivery", disabled=True)


def _render_transfer_form() -> None:
    st.text_input("Product SKU", key="transfer_sku")
    st.number_input("Transfer Quantity", min_value=0.0, step=1.0, key="transfer_qty")
    st.text_input("Source Location")
    st.text_input("Destination Location")
    st.button("Validate Transfer", disabled=True)


def _render_adjustment_form() -> None:
    st.text_input("Product SKU", key="adjustment_sku")
    st.text_input("Location", key="adjustment_location")
    st.number_input("Counted Quantity", min_value=0.0, step=1.0)
    st.text_area("Adjustment Reason")
    st.button("Apply Adjustment", disabled=True)