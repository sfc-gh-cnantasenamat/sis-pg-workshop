import streamlit as st

st.set_page_config(page_title="SiS + Postgres Workshop", layout="wide")

PAGES = {
    "Dashboard": "src.dashboard",
    "Data Explorer": "src.explorer",
    "Chart Builder": "src.chart_builder",
    "Chatbot": "src.chatbot",
}

st.sidebar.title("SiS + Postgres")
choice = st.sidebar.radio("Navigate", list(PAGES.keys()))

if choice == "Dashboard":
    from src.dashboard import render
elif choice == "Data Explorer":
    from src.explorer import render
elif choice == "Chart Builder":
    from src.chart_builder import render
elif choice == "Chatbot":
    from src.chatbot import render

render()
