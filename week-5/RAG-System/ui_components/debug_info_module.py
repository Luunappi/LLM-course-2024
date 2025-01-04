"""
Debug Info Module

This module provides debugging information about the application state, API connections,
and other technical details. It can be toggled on/off through the RAG module settings.
"""

import streamlit as st
from datetime import datetime


def render_debug_info():
    """Render debug information"""
    # Tarkista onko debug päällä
    if not st.session_state.get("show_debug", False):
        return

    # API Status
    if "api_key_loaded" in st.session_state:
        st.success("OpenAI API key loaded successfully")
    else:
        st.error("OpenAI API key not loaded")

    # Session State Info
    st.markdown("#### Session State")
    st.write(f"Initialization time: {st.session_state.get('init_time', 'Not set')}")
    st.write(f"Current model: {st.session_state.get('current_model', 'Not set')}")
    st.write(f"Max words: {st.session_state.get('max_words', 'Not set')}")

    # Document Info
    st.markdown("#### Document Status")
    files = len(st.session_state.get("processed_files", {}))
    st.write(f"Processed files: {files}")

    # Chat History Info
    history_len = len(st.session_state.get("chat_history", []))
    st.write(f"Chat history entries: {history_len}")

    # Last Update
    st.markdown("#### Last Update")
    st.write(
        f"Last query time: {st.session_state.get('last_query_time', 'No queries yet')}"
    )
