import streamlit as st
from core.graph import build_graph
from config import run_name
from agents.injection_guard import is_prompt_injection, sanitize_context
from langsmith import traceable

st.set_page_config(page_title="AI Customer Support", layout="centered")
st.title("Autonomus Customer Support AI")

@traceable(
    name = run_name,
    metadata={
        "ui": "streamlit",
        "app": "customer-support-ai"
    }
)
def run_support_query(query: str):
    return graph.invoke({"user_query": query})


graph = build_graph()

query = st.text_area("Describe your issue")

if st.button("Submit") and query.strip():
    if is_prompt_injection(query):
        st.error("This request cannot be processed automatically.")
        st.stop()

    query = sanitize_context(query)

    result = run_support_query(query)

    st.subheader("Answer")
    st.write(result["answer"])

    if "answer_confidence" in result:
        st.metric("Confidence", round(result["answer_confidence"], 2))

    if result.get("action") == "escalate":
        st.error("Escalated to human support")