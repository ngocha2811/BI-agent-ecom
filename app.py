import streamlit as st
from dotenv import load_dotenv
from ai.agent import agent
from ai.prompts import SYSTEM_PROMPT
#from db.loader import bootstrap
from dashboard.dashboard import show_dashboard

load_dotenv()

st.set_page_config(
    page_title="E-Commerce BI Agent",
    page_icon=":material/bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Seed the database on first run (no-op if already seeded)
#with st.spinner("Checking database..."):
#    bootstrap()

# ── Dashboard ─────────────────────────────────────────────────────────────────
show_dashboard()

# ── AI Agent ──────────────────────────────────────────────────────────────────
st.divider()
st.subheader("BI Assistant")
st.caption("Your main KPI dashboard is ready. Scroll to explore the metrics and insights. For deeper analysis or specific questions about the data, feel free to ask below.")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Hello, I am a Business Intelligence Agent, ask me what can I do?"},
    ]

for msg in st.session_state.messages[1:]:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask a business question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    response = agent(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)