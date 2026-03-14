from __future__ import annotations

import streamlit as st

from db import (
    list_locations,
    list_products,
    post_adjustment,
    post_delivery,
    post_receipt,
    post_transfer,
)


def render_operations_page() -> None:
    st.header("Operations")
    st.write("Use the tabs below to receive stock, deliver to customers, transfer between locations, or adjust counts.")

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


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _product_options() -> dict[str, int]:
    """Return {display_label: product_id} for all products."""
    rows = list_products()
    return {f"{r['sku']} — {r['name']}": r["id"] for r in rows}


def _location_options() -> dict[str, int]:
    """Return {display_label: location_id} for all locations."""
    rows = list_locations()
    return {f"{r['name']} ({r['warehouse_name']})": r["id"] for r in rows}


# ── Receipts ───────────────────────────────────────────────────────────────────

def _render_receipt_form() -> None:
    st.subheader("Receive Stock")
    st.caption("Records incoming goods and increases stock at the chosen location.")

    products = _product_options()
    locations = _location_options()

    if not products:
        st.warning("No products found. Add products on the Products page first.")
        return
    if not locations:
        st.warning("No locations found. Add locations in Settings first.")
        return

    with st.form("receipt_form", clear_on_submit=True):
        selected_product = st.selectbox("Product *", options=list(products.keys()))
        selected_location = st.selectbox("Destination Location *", options=list(locations.keys()))
        quantity = st.number_input("Quantity Received *", min_value=0.01, step=1.0, format="%.2f")
        supplier = st.text_input("Supplier / Partner Name", placeholder="Optional")
        notes = st.text_area("Notes", placeholder="Optional")
        submitted = st.form_submit_button("Validate Receipt")

    if submitted:
        ok, message = post_receipt(
            product_id=products[selected_product],
            destination_location_id=locations[selected_location],
            quantity=quantity,
            partner_name=supplier,
            notes=notes,
            created_by_user_id=st.session_state.get("current_user_id", 0),
        )
        if ok:
            st.success(message)
        else:
            st.error(message)


# ── Deliveries ─────────────────────────────────────────────────────────────────

def _render_delivery_form() -> None:
    st.subheader("Deliver Stock")
    st.caption("Records outgoing goods and decreases stock at the chosen location.")

    products = _product_options()
    locations = _location_options()

    if not products:
        st.warning("No products found. Add products on the Products page first.")
        return
    if not locations:
        st.warning("No locations found. Add locations in Settings first.")
        return

    with st.form("delivery_form", clear_on_submit=True):
        selected_product = st.selectbox("Product *", options=list(products.keys()))
        selected_location = st.selectbox("Source Location *", options=list(locations.keys()))
        quantity = st.number_input("Quantity to Deliver *", min_value=0.01, step=1.0, format="%.2f")
        customer = st.text_input("Customer / Partner Name", placeholder="Optional")
        notes = st.text_area("Notes", placeholder="Optional")
        submitted = st.form_submit_button("Validate Delivery")

    if submitted:
        ok, message = post_delivery(
            product_id=products[selected_product],
            source_location_id=locations[selected_location],
            quantity=quantity,
            partner_name=customer,
            notes=notes,
            created_by_user_id=st.session_state.get("current_user_id", 0),
        )
        if ok:
            st.success(message)
        else:
            st.error(message)


# ── Internal Transfers ─────────────────────────────────────────────────────────

def _render_transfer_form() -> None:
    st.subheader("Internal Transfer")
    st.caption("Moves stock from one location to another. Total stock stays the same.")

    products = _product_options()
    locations = _location_options()
    location_keys = list(locations.keys())

    if not products:
        st.warning("No products found. Add products on the Products page first.")
        return
    if len(location_keys) < 2:
        st.warning("At least two locations are needed to perform a transfer. Add more locations in Settings.")
        return

    with st.form("transfer_form", clear_on_submit=True):
        selected_product = st.selectbox("Product *", options=list(products.keys()))
        source_location = st.selectbox("Source Location *", options=location_keys)
        destination_location = st.selectbox("Destination Location *", options=location_keys, index=1)
        quantity = st.number_input("Quantity to Transfer *", min_value=0.01, step=1.0, format="%.2f")
        notes = st.text_area("Notes", placeholder="Optional")
        submitted = st.form_submit_button("Validate Transfer")

    if submitted:
        ok, message = post_transfer(
            product_id=products[selected_product],
            source_location_id=locations[source_location],
            destination_location_id=locations[destination_location],
            quantity=quantity,
            notes=notes,
            created_by_user_id=st.session_state.get("current_user_id", 0),
        )
        if ok:
            st.success(message)
        else:
            st.error(message)


# ── Adjustments ────────────────────────────────────────────────────────────────

def _render_adjustment_form() -> None:
    st.subheader("Stock Adjustment")
    st.caption("Correct inventory after a physical count. Enter the actual counted quantity.")

    products = _product_options()
    locations = _location_options()

    if not products:
        st.warning("No products found. Add products on the Products page first.")
        return
    if not locations:
        st.warning("No locations found. Add locations in Settings first.")
        return

    with st.form("adjustment_form", clear_on_submit=True):
        selected_product = st.selectbox("Product *", options=list(products.keys()))
        selected_location = st.selectbox("Location *", options=list(locations.keys()))
        counted_qty = st.number_input("Counted Quantity *", min_value=0.0, step=1.0, format="%.2f")
        reason = st.text_area("Reason *", placeholder="e.g. Physical count correction")
        submitted = st.form_submit_button("Apply Adjustment")

    if submitted:
        ok, message = post_adjustment(
            product_id=products[selected_product],
            location_id=locations[selected_location],
            counted_quantity=counted_qty,
            reason=reason,
            created_by_user_id=st.session_state.get("current_user_id", 0),
        )
        if ok:
            st.success(message)
        else:
            st.error(message)
