"""
Debug Info Module

This module provides debugging information about the application state, API connections,
and other technical details. It can be toggled on/off through the RAG module settings.
"""

import streamlit as st
from datetime import datetime


def render_debug_info():
    """Render debug information"""
    if not st.session_state.get("show_debug", False):
        return

    with st.expander("Debug Info", expanded=False):
        # ... debug info content ...
        pass
