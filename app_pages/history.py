from __future__ import annotations

import pandas as pd
import streamlit as st

from db import DOCUMENT_TYPES, list_ledger, list_warehouses


def render_history_page() -> None:
    st.header("Move History")

    # ── Filters ───────────────────────────────────────────────────────────────
    filter_left, filter_right = st.columns(2)

    with filter_left:
        search_sku = st.text_input(
            "Search by SKU or Product Name", placeholder="e.g. SKU-001")
        operation_choice = st.selectbox(
            "Operation Type",
            options=["All"] + list(DOCUMENT_TYPES),
        )

    with filter_right:
        warehouses = list_warehouses()
        warehouse_options = {"All Warehouses": None}
        warehouse_options.update({wh["name"]: wh["id"] for wh in warehouses})
        warehouse_choice = st.selectbox(
            "Warehouse", options=list(warehouse_options.keys()))

    # Resolve filter values
    doc_type_filter = None if operation_choice == "All" else operation_choice
    warehouse_filter = warehouse_options[warehouse_choice]

    # ── Fetch data ────────────────────────────────────────────────────────────
    rows = list_ledger(
        search_sku=search_sku,
        document_type=doc_type_filter,
        warehouse_id=warehouse_filter,
    )

    if not rows:
        st.info(
            "No movements found. Try adjusting the filters or perform a stock operation first.")
        return

    # ── Build DataFrame ───────────────────────────────────────────────────────
    data = [
        {
            # strip timezone, readable
            "Timestamp": row["timestamp"][:19].replace("T", " "),
            "Operation": row["operation"],
            "Reference": row["reference"],
            "SKU": row["sku"],
            "Product": row["product_name"],
            "Warehouse": row["warehouse"],
            "Location": row["location"],
            "Qty Change": row["qty_change"],
            "Balance After": row["balance_after"],
            "Status": row["status"],
            "Note": row["note"],
        }
        for row in rows
    ]

    df = pd.DataFrame(data)

    # Colour-code the Qty Change column using Streamlit's built-in highlighting
    def _colour_qty(val: float) -> str:
        if val > 0:
            return "color: green"
        if val < 0:
            return "color: red"
        return ""

    st.dataframe(
        df.style.map(_colour_qty, subset=["Qty Change"]),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"{len(rows)} record(s) shown.")
