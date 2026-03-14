from __future__ import annotations

import streamlit as st

from db import create_location, create_warehouse, list_locations, list_warehouses


def render_settings_page() -> None:
    st.header("Settings")

    warehouse_column, location_column = st.columns(2)

    # ── Warehouse form ────────────────────────────────────────────────────────
    with warehouse_column:
        st.subheader("Add Warehouse")
        with st.form("warehouse_form", clear_on_submit=True):
            wh_name = st.text_input(
                "Warehouse Name *", placeholder="e.g. Main Warehouse")
            wh_code = st.text_input(
                "Warehouse Code *", placeholder="e.g. WH-MAIN")
            wh_address = st.text_area(
                "Address", placeholder="Optional street address")
            submitted = st.form_submit_button("Save Warehouse")

        if submitted:
            ok, message = create_warehouse(wh_name, wh_code, wh_address)
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

        # Show existing warehouses
        st.divider()
        st.caption("Existing Warehouses")
        warehouses = list_warehouses()
        if warehouses:
            for wh in warehouses:
                st.markdown(f"**{wh['name']}** — `{wh['code']}`")
                if wh["address"]:
                    st.caption(wh["address"])
        else:
            st.info("No warehouses yet.")

    # ── Location form ─────────────────────────────────────────────────────────
    with location_column:
        st.subheader("Add Location")

        warehouses = list_warehouses()
        if not warehouses:
            st.warning("Create a warehouse first before adding locations.")
        else:
            warehouse_options = {wh["name"]: wh["id"] for wh in warehouses}

            with st.form("location_form", clear_on_submit=True):
                loc_name = st.text_input(
                    "Location Name *", placeholder="e.g. Rack A")
                loc_code = st.text_input(
                    "Location Code *", placeholder="e.g. LOC-RACK-A")
                loc_warehouse = st.selectbox(
                    "Warehouse *", options=list(warehouse_options.keys()))
                submitted_loc = st.form_submit_button("Save Location")

            if submitted_loc:
                selected_warehouse_id = warehouse_options[loc_warehouse]
                ok, message = create_location(
                    loc_name, loc_code, selected_warehouse_id)
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

            # Show existing locations
            st.divider()
            st.caption("Existing Locations")
            locations = list_locations()
            if locations:
                for loc in locations:
                    st.markdown(
                        f"**{loc['name']}** — `{loc['code']}` "
                        f"<span style='color:grey'>({loc['warehouse_name']})</span>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No locations yet.")
