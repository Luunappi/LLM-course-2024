"""
RAG Module

Handles document upload and processing UI.
"""

import streamlit as st
from tools.rag_tool import RAGTool

rag_tool = RAGTool()


def render_rag_module():
    """Render the RAG upload interface"""
    # Vain tiedoston lataus ja käsittely
    uploaded_file = st.file_uploader("Upload PDF/TXT/MD", type=["pdf", "txt", "md"])

    if uploaded_file:
        if uploaded_file.name not in st.session_state.processed_files:
            # Näytä prosessointipalkki
            progress_container = st.empty()
            with progress_container.container():
                progress_text = st.empty()
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Prosessoi tiedosto RAGToolin avulla
                success = rag_tool.process_document(
                    uploaded_file, progress_text, progress_bar, status_text
                )

                if success:
                    st.success(f"Successfully processed {uploaded_file.name}")
                else:
                    st.error("Failed to process document")

            # Tyhjennä prosessointipalkki
            progress_container.empty()
        else:
            st.success(f"Using cached data for {uploaded_file.name}")
            # Lataa välimuistista
            cached_data = st.session_state.processed_files[uploaded_file.name]
            st.session_state.chunks = cached_data["chunks"]
            st.session_state.embeddings = cached_data["embeddings"]
