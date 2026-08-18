"""Streamlit interface for the governance RAG assistant."""

import os
from pathlib import Path

import streamlit as st

from governance_rag.generation import answer_question
from governance_rag.retrieval import TfidfRetriever

ROOT = Path(__file__).parent
CORPUS_DIR = ROOT / "data" / "documents"

st.set_page_config(page_title="Governance RAG Assistant", page_icon="🔎", layout="wide")


@st.cache_resource
def load_retriever() -> TfidfRetriever:
    return TfidfRetriever.from_directory(CORPUS_DIR)


st.title("Governance RAG Assistant")
st.caption("Retrieve evidence first; generate only when the answer can be grounded.")
st.warning(
    "Demo guidance only — not legal advice, an organizational policy, or a substitute "
    "for human review."
)

retriever = load_retriever()
question = st.text_input(
    "Ask a question about the indexed governance documents",
    placeholder="What should be included in an approval record?",
)
top_k = st.slider("Evidence chunks", min_value=1, max_value=5, value=3)

if question:
    results = retriever.retrieve(question, top_k=top_k)
    answer, mode = answer_question(
        question,
        results,
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    st.subheader(f"Answer ({mode})")
    st.markdown(answer)

    st.subheader("Retrieved evidence")
    if not results:
        st.info("No indexed evidence matched this question.")
    for result in results:
        with st.expander(f"{result.chunk.citation} — score {result.score:.3f}"):
            st.write(result.chunk.text)

st.sidebar.header("Corpus")
st.sidebar.write(f"{len(retriever.chunks)} indexed chunks")
st.sidebar.write("Local TF-IDF retrieval baseline")
st.sidebar.caption(
    "Set OPENAI_API_KEY and OPENAI_MODEL only when an approved compatible endpoint "
    "is available."
)
