import streamlit as st
import pandas as pd
from src.db import run_query, get_tables


def render():
    st.header("Data Explorer")

    # --- Table Selection ---
    tables = get_tables()
    table_names = [t["table_name"] for t in tables]

    if not table_names:
        st.warning("No tables found in the database.")
        return

    selected_table = st.selectbox("Select a table", table_names)

    # --- Get columns for the selected table ---
    columns_info = run_query("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (selected_table,))

    col_names = [c["column_name"] for c in columns_info]

    # --- Column filter ---
    selected_cols = st.multiselect(
        "Select columns to display",
        col_names,
        default=col_names
    )

    if not selected_cols:
        st.info("Select at least one column.")
        return

    # --- Optional text filter ---
    filter_col = st.selectbox("Filter by column (optional)", ["None"] + col_names)
    filter_val = ""
    if filter_col != "None":
        filter_val = st.text_input(f"Filter value for {filter_col}")

    # --- Build and run query ---
    cols_str = ", ".join(selected_cols)
    query = f"SELECT {cols_str} FROM {selected_table}"
    params = None

    if filter_col != "None" and filter_val:
        query += f" WHERE {filter_col}::text ILIKE %s"
        params = (f"%{filter_val}%",)

    query += " LIMIT 500"

    data = run_query(query, params)

    # --- Display ---
    st.caption(f"Showing up to 500 rows from `{selected_table}`")
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(data)} rows returned")
    else:
        st.info("No data matching the filter.")
