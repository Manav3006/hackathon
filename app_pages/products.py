from __future__ import annotations

import pandas as pd
import streamlit as st

from db import (
    UNIT_OF_MEASURE_OPTIONS,
    create_product,
    get_product_by_id,
    list_categories,
    list_locations,
    list_products,
    update_product,
)


def render_products_page() -> None:
    st.header("Products")

    if not st.session_state.get("is_authenticated"):
        st.warning("Please log in first to access products.")
        return

    is_inventory_manager = st.session_state.get(
        "current_role") == "Inventory Manager"
    categories = list_categories()
    locations = list_locations()

    category_labels: dict[int | None, str] = {None: "Uncategorized"}
    for category in categories:
        category_labels[category["id"]] = category["name"]

    location_labels: dict[int | None, str] = {None: "Select location"}
    for location in locations:
        location_labels[location["id"]] = (
            f"{location['warehouse_name']} / {location['name']} ({location['code']})"
        )

    if is_inventory_manager:
        create_tab, update_tab = st.tabs(["Create Product", "Update Product"])

        with create_tab:
            with st.form("product_form"):
                left_column, right_column = st.columns(2)

                with left_column:
                    product_name = st.text_input("Product Name")
                    sku = st.text_input("SKU / Code")
                    selected_category_id = st.selectbox(
                        "Category",
                        options=list(category_labels.keys()),
                        format_func=lambda option: category_labels[option],
                    )

                with right_column:
                    unit_of_measure = st.selectbox(
                        "Unit of Measure",
                        options=list(UNIT_OF_MEASURE_OPTIONS),
                        format_func=lambda option: option.title(),
                    )
                    reorder_level = st.number_input(
                        "Reorder Level", min_value=0.0, step=1.0)
                    initial_stock = st.number_input(
                        "Initial Stock (Optional)",
                        min_value=0.0,
                        step=1.0,
                    )
                    selected_location_id = st.selectbox(
                        "Initial Stock Location",
                        options=list(location_labels.keys()),
                        format_func=lambda option: location_labels[option],
                        help=(
                            "Required only if Initial Stock is greater than 0. "
                            "Use Settings page later to add more locations."
                        ),
                    )

                submitted = st.form_submit_button("Save Product")

            if submitted:
                success, message = create_product(
                    name=product_name,
                    sku=sku,
                    category_id=selected_category_id,
                    unit_of_measure=unit_of_measure,
                    reorder_level=float(reorder_level),
                    initial_stock=float(initial_stock),
                    initial_location_id=selected_location_id,
                )
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        with update_tab:
            all_products = list_products()
            if not all_products:
                st.info("No products found yet. Create a product first.")
            else:
                product_options = {
                    f"{product['sku']} - {product['name']}": product["id"] for product in all_products
                }
                selected_product_label = st.selectbox(
                    "Select Product",
                    options=list(product_options.keys()),
                )
                selected_product_id = product_options[selected_product_label]
                selected_product = get_product_by_id(selected_product_id)

                if selected_product is not None:
                    category_ids = list(category_labels.keys())
                    current_category_id = selected_product["category_id"]
                    category_index = (
                        category_ids.index(current_category_id)
                        if current_category_id in category_ids
                        else 0
                    )

                    unit_options = list(UNIT_OF_MEASURE_OPTIONS)
                    current_unit = (
                        selected_product["unit_of_measure"] or "").lower()
                    unit_index = unit_options.index(
                        current_unit) if current_unit in unit_options else 0

                    with st.form("update_product_form"):
                        edit_left, edit_right = st.columns(2)

                        with edit_left:
                            updated_name = st.text_input(
                                "Product Name", value=selected_product["name"])
                            updated_sku = st.text_input(
                                "SKU / Code", value=selected_product["sku"])
                            updated_category_id = st.selectbox(
                                "Category",
                                options=category_ids,
                                index=category_index,
                                format_func=lambda option: category_labels[option],
                            )

                        with edit_right:
                            updated_unit = st.selectbox(
                                "Unit of Measure",
                                options=unit_options,
                                index=unit_index,
                                format_func=lambda option: option.title(),
                            )
                            updated_reorder = st.number_input(
                                "Reorder Level",
                                min_value=0.0,
                                step=1.0,
                                value=float(selected_product["reorder_level"]),
                            )

                        update_submitted = st.form_submit_button(
                            "Update Product")

                    if update_submitted:
                        success, message = update_product(
                            product_id=selected_product_id,
                            name=updated_name,
                            sku=updated_sku,
                            category_id=updated_category_id,
                            unit_of_measure=updated_unit,
                            reorder_level=float(updated_reorder),
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
    else:
        st.info(
            "You are in Warehouse Staff mode, so create/edit product actions are hidden. "
            "You can still search and view products below."
        )

    st.subheader("Product List")
    search_query = st.text_input("Search by SKU or Name")
    filter_category_id = st.selectbox(
        "Filter by Category",
        options=[None] + [category["id"] for category in categories],
        format_func=lambda option: "All Categories" if option is None else category_labels[
            option],
    )

    product_rows = list_products(
        search_query=search_query, category_id=filter_category_id)

    if not product_rows:
        st.info("No products found yet. Create one from the form above.")
        return

    product_table = pd.DataFrame([dict(row) for row in product_rows]).rename(
        columns={
            "id": "ID",
            "name": "Product",
            "sku": "SKU",
            "category": "Category",
            "unit": "Unit",
            "reorder_level": "Reorder Level",
            "total_stock": "Total Stock",
            "low_stock": "Low Stock",
        }
    )
    st.dataframe(product_table, use_container_width=True, hide_index=True)
