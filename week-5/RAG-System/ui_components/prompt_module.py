"""
Prompt Module

Displays and manages system prompts and response settings.
"""

import streamlit as st
from RAG_Orchestrator import RAGOrchestrator


def render_prompt_module():
    """Render prompt settings"""
    with st.expander("Prompt Settings", expanded=False):
        st.markdown("### System Prompts")

        # Tool Selection Prompt
        st.markdown("#### Tool Selection Prompt")
        st.code(RAGOrchestrator.TOOL_SELECTION_PROMPT, language="text")

        # System Prompt
        st.markdown("#### System Prompt")
        new_prompt = st.text_area(
            "Customize system prompt:",
            st.session_state.get("system_prompt", "You are an assistant..."),
        )
        if st.button("Update System Prompt"):
            st.session_state["system_prompt"] = new_prompt
            st.success("System prompt updated!")

        # Response Settings
        st.markdown("#### Response Settings")
        max_words = st.slider(
            "Max words in response:",
            min_value=0,
            max_value=250,
            value=st.session_state.get("max_words", 50),
            step=10,
            help="Limit the length of model responses (0 = no limit)",
        )
        if max_words != st.session_state.get("max_words"):
            st.session_state["max_words"] = max_words
            st.success(f"Max words set to: {max_words}")
