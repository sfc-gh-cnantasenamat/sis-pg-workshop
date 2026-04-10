import streamlit as st
from src.db import get_schema_context, run_query
from src.cortex import cortex_complete
import pandas as pd


def render():
    st.header("AI Chart Builder")
    st.caption("Describe a chart in plain English and the AI will generate it.")

    # --- Get schema context for LLM ---
    schema_ctx = get_schema_context()

    # --- User input ---
    user_request = st.text_area(
        "Describe the chart you want",
        placeholder="e.g., Show monthly revenue as a bar chart"
    )

    model = st.selectbox("Model", ["claude-sonnet-4", "gpt-4o", "llama3.1-8b"])

    if st.button("Generate Chart") and user_request:
        with st.spinner("Generating chart..."):
            prompt = f"""You are a data analyst. Given this PostgreSQL database schema:

{schema_ctx}

The user wants: {user_request}

Generate:
1. A SQL query to fetch the data from PostgreSQL
2. Python code using Altair to create the chart

Return your response in this exact format:
```sql
<your SQL query>
```
```python
<your Altair chart code that assumes a pandas DataFrame called 'df' already exists>
```

Rules:
- The SQL must be valid PostgreSQL
- The Python code must use Altair and assume 'df' is a pandas DataFrame with the query results
- The chart variable must be called 'chart'
- Do not include imports or data fetching in the Python code
"""
            response = cortex_complete(prompt, model=model)

        # --- Parse response ---
        try:
            # Extract SQL
            sql_start = response.find("```sql") + 6
            sql_end = response.find("```", sql_start)
            sql_code = response[sql_start:sql_end].strip()

            # Extract Python
            py_start = response.find("```python") + 9
            py_end = response.find("```", py_start)
            py_code = response[py_start:py_end].strip()

            # Show generated code
            with st.expander("Generated SQL"):
                st.code(sql_code, language="sql")
            with st.expander("Generated Chart Code"):
                st.code(py_code, language="python")

            # Execute SQL
            data = run_query(sql_code)
            if data:
                df = pd.DataFrame(data)

                # Execute chart code
                import altair as alt
                local_ns = {"df": df, "alt": alt, "pd": pd}
                exec(py_code, local_ns)

                if "chart" in local_ns:
                    st.altair_chart(local_ns["chart"], use_container_width=True)
                else:
                    st.warning("The generated code did not produce a 'chart' variable.")
            else:
                st.info("The query returned no data.")

        except Exception as e:
            st.error(f"Error generating chart: {e}")
            st.caption("Try rephrasing your request or using a different model.")
