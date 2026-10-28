"""Streamlit UI:  streamlit run app.py"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

from paperqa import Config, PaperQAAgent

SAMPLE = Path(__file__).parent / "data" / "sample_paper.pdf"

st.set_page_config(page_title="Paper Q&A", page_icon="\U0001F4C4", layout="wide")
st.title("Paper Q&A")
st.caption("Ask questions about a research paper. Answers cite the section and page they came from, "
           "and the agent says so when the paper does not contain the answer.")

with st.sidebar:
    st.header("Paper")
    upload = st.file_uploader("Upload a PDF", type="pdf")
    st.header("Settings")
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    llm = st.selectbox("Answerer", ["auto", "extractive", "anthropic"],
                       help="auto = Claude if ANTHROPIC_API_KEY is set, otherwise the offline extractive answerer")
    embedder = st.selectbox("Embeddings", ["lsa", "st"],
                            help="lsa = offline TF-IDF+SVD. st = sentence-transformers (needs `pip install sentence-transformers`)")
    top_k = st.slider("Passages retrieved (top-k)", 2, 10, 5)
    st.caption(f"Anthropic key detected: {'yes' if has_key else 'no'}")


@st.cache_resource(show_spinner="Reading and indexing the paper...")
def build_agent(pdf_bytes: bytes, llm: str, embedder: str, top_k: int) -> PaperQAAgent:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
    cfg = Config(llm=llm, embedder=embedder, top_k=top_k)
    return PaperQAAgent.from_pdf(f.name, cfg)


pdf_bytes = upload.getvalue() if upload else (SAMPLE.read_bytes() if SAMPLE.exists() else None)
if pdf_bytes is None:
    st.info("Upload a PDF to begin.")
    st.stop()
if not upload:
    st.info("Using the bundled synthetic sample paper. Upload your own PDF in the sidebar.")

try:
    agent = build_agent(pdf_bytes, llm, embedder, top_k)
except Exception as exc:  # surface extraction / backend problems instead of a stack trace
    st.error(f"Could not prepare the paper: {exc}")
    st.stop()

st.sidebar.metric("Chunks indexed", len(agent.chunks))
st.sidebar.caption(f"Answerer in use: {type(agent.llm).__name__}")

if "history" not in st.session_state:
    st.session_state.history = []

for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        st.write(item["answer"])
        if item["citations"]:
            for c in item["citations"]:
                with st.expander(f"[S{c['source_id']}] {c['section']} (p. {', '.join(map(str, c['pages']))})"):
                    st.write(c["quote"])
        elif item["reason"]:
            st.caption(f"Not answered ({item['reason']}).")
        st.caption(f"{item['latency_ms']:.0f} ms")

question = st.chat_input("Ask about the paper...")
if question:
    ans = agent.ask(question)
    st.session_state.history.append({
        "question": question, "answer": ans.text, "reason": ans.reason, "latency_ms": ans.latency_ms,
        "citations": [vars(c) for c in ans.citations],
    })
    st.rerun()
