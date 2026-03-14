from __future__ import annotations

import streamlit as st

from db import DOCUMENT_TYPES, STATUS_OPTIONS


def render_dashboard_page() -> None:
    st.header("Dashboard")
    st.write(
        "This page will show live KPIs and filters once the query helpers are added."
    )

    metric_labels = [
        "Total Products in Stock",
        "Low / Out of Stock",
        "Pending Receipts",
        "Pending Deliveries",
        "Scheduled Transfers",
    ]
    metric_columns = st.columns(len(metric_labels))

    for column, label in zip(metric_columns, metric_labels):
        column.metric(label, 0)

    filter_left, filter_right = st.columns(2)
    with filter_left:
        st.selectbox("Document Type", options=("All",) + DOCUMENT_TYPES, disabled=True)
        st.selectbox("Status", options=("All",) + STATUS_OPTIONS, disabled=True)
    with filter_right:
        st.text_input("Warehouse or Location", disabled=True)
        st.text_input("Product Category", disabled=True)

    st.info(
        "Next step: replace these placeholder metrics with real SQL queries from db.py."
    )