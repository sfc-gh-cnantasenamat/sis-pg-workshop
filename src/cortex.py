from snowflake.snowpark import Session
import streamlit as st


@st.cache_resource
def get_snowpark_session():
    """Get a Snowpark session, works in both SiS container runtime and Community Cloud."""
    if "snowflake" in st.secrets:
        # Community Cloud: build session from explicit credentials
        creds = st.secrets["snowflake"]
        return Session.builder.configs({
            "account": creds["account"],
            "user": creds["user"],
            "password": creds["password"],
            "warehouse": creds.get("warehouse", "COMPUTE_WH"),
            "role": creds.get("role", "ACCOUNTADMIN"),
        }).create()
    # SiS container runtime: ambient session is available
    return Session.builder.getOrCreate()


def cortex_complete(prompt, model="mistral-large2"):
    """Call Snowflake Cortex COMPLETE function via Snowpark SQL."""
    session = get_snowpark_session()
    prompt_escaped = prompt.replace("'", "''")
    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{prompt_escaped}') AS response"
    result = session.sql(sql).collect()
    return result[0]["RESPONSE"]
