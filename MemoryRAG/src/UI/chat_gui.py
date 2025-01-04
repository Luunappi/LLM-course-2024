"""Graafinen käyttöliittymä MemoryRAG:n testaamiseen"""

import streamlit as st
import asyncio
import sys
from pathlib import Path

# Lisää projektin juurihakemisto Python-polkuun
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from src.orchestrator import RAGOrchestrator


async def main():
    st.title("MemoryRAG GUI")
    rag = st.session_state.get("rag_orchestrator")
    if not rag:
        rag = await RAGOrchestrator.create()
        st.session_state.rag_orchestrator = rag

    query = st.text_input("Kysymys?")
    if query:
        response = await rag.process_query(query)
        st.write("Vastaus:", response)


if __name__ == "__main__":
    asyncio.run(main())
