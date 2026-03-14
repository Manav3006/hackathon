from __future__ import annotations

import pandas as pd
import streamlit as st


def render_history_page() -> None:
    st.header("Move History")
    st.write(
        "This page will show the stock ledger so every movement can be tracked and filtered."
    )

    filter_left, filter_right = st.columns(2)
    with filter_left:
        st.text_input("Search by SKU", disabled=True)
        st.selectbox("Filter by Operation", ["All", "Receipt", "Delivery", "Internal Transfer", "Adjustment"], disabled=True)
    with filter_right:
        st.selectbox("Filter by Status", ["All", "Draft", "Waiting", "Ready", "Done", "Canceled"], disabled=True)
        st.text_input("Warehouse or Location", disabled=True)

    empty_history = pd.DataFrame(
        columns=[
            "Timestamp",
            "Operation",
            "Reference",
            "SKU",
            "Warehouse",
            "Location",
            "Quantity Change",
            "Status",
        ]
    )
    st.dataframe(empty_history, use_container_width=True)

    st.info(
        "Next step: read rows from the stock_ledger and stock_documents tables to fill this grid."
    )