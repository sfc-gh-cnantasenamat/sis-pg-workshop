import psycopg2
import streamlit as st


@st.cache_resource
def get_connection():
    """Get a persistent Postgres connection (cached across reruns)."""
    creds = st.secrets["postgres"]
    conn = psycopg2.connect(
        host=creds["host"],
        port=creds["port"],
        dbname=creds["dbname"],
        user=creds["user"],
        password=creds["password"]
    )
    conn.autocommit = True
    return conn


def run_query(sql, params=None):
    """Execute a query and return results as a list of dicts."""
    conn = get_connection()
    # Reconnect if the connection was closed or broken
    if conn.closed:
        st.cache_resource.clear()
        conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    except psycopg2.OperationalError:
        # Connection lost mid-query, reconnect and retry once
        conn.close()
        st.cache_resource.clear()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    finally:
        cur.close()
    return [dict(zip(columns, row)) for row in rows]


def get_tables():
    """List all user tables in the public schema."""
    return run_query("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)


@st.cache_data(ttl=300)
def get_schema_context():
    """Build a text description of all tables and columns for LLM prompts."""
    tables = get_tables()
    context_parts = []
    for t in tables:
        table_name = t["table_name"]
        cols = run_query("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        col_list = ", ".join([f"{c['column_name']} ({c['data_type']})" for c in cols])
        context_parts.append(f"Table: {table_name}\n  Columns: {col_list}")
    return "\n\n".join(context_parts)
