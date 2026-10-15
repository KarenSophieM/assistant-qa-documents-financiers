"""Interface web (Streamlit) : pose tes questions sur le rapport BNP Paribas
dans une vraie page, au lieu du terminal. Réutilise retrieval.py/generation.py
tels quels, aucune logique RAG réécrite."""

import pathlib
import sys

import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from generation import answer_question
from retrieval import load_index

st.set_page_config(page_title="Assistant documents financiers", page_icon="📊")


@st.cache_resource
def get_index():
    return load_index()


chunks, embeddings = get_index()

st.title("📊 Assistant Q&A — Documents financiers BNP Paribas")
st.caption(
    f"{len(chunks)} passages indexés · Score mesuré : 17/20 (85%), "
    "100% sur les questions pièges (zéro hallucination)"
)
st.caption(
    "Document source : 2ème amendement au Document d'Enregistrement Universel "
    "BNP Paribas, résultats du 1er semestre 2026"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Pose ta question sur le rapport (ex: Quel est le résultat net du Groupe ?)")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans le document..."):
            answer = answer_question(question, chunks, embeddings)
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
