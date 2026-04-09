import streamlit as st
import pandas as pd
import altair as alt
from src.db import run_query


def render():
    st.header("E-Commerce Dashboard")

    # --- KPI Cards ---
    kpis = run_query("""
        SELECT
            COUNT(DISTINCT c.id) AS total_customers,
            COUNT(DISTINCT o.id) AS total_orders,
            COALESCE(SUM(o.total), 0) AS total_revenue,
            COALESCE(ROUND(AVG(o.total), 2), 0) AS avg_order_value
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.id
    """)
    kpi = kpis[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Customers", f"{kpi['total_customers']:,}")
    col2.metric("Orders", f"{kpi['total_orders']:,}")
    col3.metric("Revenue", f"${float(kpi['total_revenue']):,.2f}")
    col4.metric("Avg Order", f"${float(kpi['avg_order_value']):,.2f}")

    st.divider()

    # --- Revenue Over Time ---
    st.subheader("Monthly Revenue")
    revenue_data = run_query("""
        SELECT
            DATE_TRUNC('month', order_date)::date AS month,
            SUM(total) AS revenue
        FROM orders
        WHERE status != 'cancelled'
        GROUP BY 1
        ORDER BY 1
    """)
    if revenue_data:
        df_rev = pd.DataFrame(revenue_data)
        chart = alt.Chart(df_rev).mark_line(point=True).encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("revenue:Q", title="Revenue ($)"),
            tooltip=["month:T", "revenue:Q"]
        ).properties(height=350)
        st.altair_chart(chart, use_container_width=True)

    # --- Top 10 Customers ---
    st.subheader("Top 10 Customers by Spend")
    top_customers = run_query("""
        SELECT c.name, SUM(o.total) AS total_spent
        FROM customers c
        JOIN orders o ON o.customer_id = c.id
        WHERE o.status != 'cancelled'
        GROUP BY c.name
        ORDER BY total_spent DESC
        LIMIT 10
    """)
    if top_customers:
        df_top = pd.DataFrame(top_customers)
        bar = alt.Chart(df_top).mark_bar().encode(
            x=alt.X("total_spent:Q", title="Total Spent ($)"),
            y=alt.Y("name:N", sort="-x", title="Customer"),
            tooltip=["name:N", "total_spent:Q"]
        ).properties(height=350)
        st.altair_chart(bar, use_container_width=True)

    # --- Orders by Region ---
    st.subheader("Orders by Region")
    region_data = run_query("""
        SELECT c.region, COUNT(o.id) AS order_count
        FROM customers c
        JOIN orders o ON o.customer_id = c.id
        GROUP BY c.region
        ORDER BY order_count DESC
    """)
    if region_data:
        df_region = pd.DataFrame(region_data)
        pie = alt.Chart(df_region).mark_arc().encode(
            theta="order_count:Q",
            color="region:N",
            tooltip=["region:N", "order_count:Q"]
        ).properties(height=300)
        st.altair_chart(pie, use_container_width=True)
