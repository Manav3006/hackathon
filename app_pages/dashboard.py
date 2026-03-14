from __future__ import annotations

import pandas as pd
import streamlit as st

from db import get_dashboard_kpis, get_stock_by_product


def render_dashboard_page() -> None:
    st.header("Dashboard")

    kpis = get_dashboard_kpis()

    # ── KPI cards row 1 ───────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", kpis["total_products"])
    col2.metric("Total Units in Stock", f"{kpis['total_stock']:g}")
    col3.metric("Low / At Reorder Level", kpis["low_stock"])
    col4.metric("Out of Stock", kpis["out_of_stock"])

    st.divider()

    # ── KPI cards row 2 ───────────────────────────────────────────────────────
    col5, col6, col7 = st.columns(3)
    col5.metric("Pending Receipts", kpis["pending_receipts"])
    col6.metric("Pending Deliveries", kpis["pending_deliveries"])
    col7.metric("Operations Today", kpis["ops_today"])

    st.divider()

    # ── Stock by product bar chart ────────────────────────────────────────────
    st.subheader("Stock by Product (Top 15)")

    rows = get_stock_by_product(limit=15)
    if not rows:
        st.info("No stock data yet. Perform a Receipt operation to see the chart.")
        return

    chart_data = pd.DataFrame(
        [{"Product": f"{r['sku']} — {r['product_name']}", "Units": r["total_stock"]} for r in rows]
    ).set_index("Product")

    st.bar_chart(chart_data, y="Units", use_container_width=True)