import streamlit as st
from src.db import get_schema_context, run_query
from src.cortex import cortex_complete


def render():
    st.header("AI Data Chatbot")
    st.caption("Ask questions about your e-commerce data in natural language.")

    # --- Initialize chat history ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- Model selection ---
    model = st.sidebar.selectbox(
        "Chatbot Model",
        ["mistral-large2", "llama3.1-70b", "llama3.1-8b"],
        key="chatbot_model"
    )

    # --- Display chat history ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- Chat input ---
    if user_input := st.chat_input("Ask about your data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # --- Build prompt with schema context and history ---
        schema_ctx = get_schema_context()
        history = "\n".join(
            [f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages[-6:]]
        )

        prompt = f"""You are a helpful data analyst assistant. You have access to a PostgreSQL database with this schema:

{schema_ctx}

Conversation history:
{history}

When the user asks a data question:
1. Write a PostgreSQL query to answer it
2. Present the results in a clear, readable format
3. Add brief insights about what the data shows

If the user asks a general question (not about data), answer conversationally.

Format any SQL you show in ```sql code blocks.
Always be concise and helpful.

USER: {user_input}
ASSISTANT:"""

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = cortex_complete(prompt, model=model)

            st.markdown(response)

            # Check if response contains SQL and offer to run it
            if "```sql" in response:
                sql_start = response.find("```sql") + 6
                sql_end = response.find("```", sql_start)
                sql_code = response[sql_start:sql_end].strip()

                if st.button("Run this query", key=f"run_{len(st.session_state.messages)}"):
                    try:
                        import pandas as pd
                        data = run_query(sql_code)
                        if data:
                            df = pd.DataFrame(data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.info("Query returned no results.")
                    except Exception as e:
                        st.error(f"Query error: {e}")

        st.session_state.messages.append({"role": "assistant", "content": response})

    # --- Clear chat button ---
    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
