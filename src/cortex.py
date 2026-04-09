from snowflake.snowpark import Session


def get_snowpark_session():
    """Get a Snowpark session from within SiS container runtime."""
    return Session.builder.getOrCreate()


def cortex_complete(prompt, model="mistral-large2"):
    """Call Snowflake Cortex COMPLETE function via Snowpark SQL."""
    session = get_snowpark_session()
    prompt_escaped = prompt.replace("'", "''")
    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{prompt_escaped}') AS response"
    result = session.sql(sql).collect()
    return result[0]["RESPONSE"]
