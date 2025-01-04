import streamlit as st

# Aseta sivun konfiguraatio
st.set_page_config(
    page_title="RAG",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# Sitten muut importit
import warnings
import logging
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime

# Muut asetukset
warnings.filterwarnings("ignore")
logging.getLogger("torch").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

load_dotenv()

# Importit
from ui_components.chat_module import render_chat_module
from ui_components.rag_module import render_rag_module
from ui_components.diagram_module import render_diagram_module
from ui_components.prompt_module import render_prompt_module
from ui_components.token_module import render_token_module
from ui_components.info_module import render_info_module
from ui_components.model_module import render_model_selector
from ui_components.debug_info_module import render_debug_info


def initialize_session_state():
    """Initialize session state once"""
    if not st.session_state.get("_initialized", False):
        defaults = {
            "system_prompt": "You are an assistant. Use RAG approach...",
            "chat_history": [],
            "processed_files": {},
            "max_words": 50,
            "show_debug": False,
            "show_model_settings": False,
            "show_prompt_settings": False,
            "show_token_info": False,
            "show_system_info": False,
            "system_warnings": [],
            "callback_warnings": ["Calling st.rerun() within a callback is a no-op."],
            "init_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "_initialized": True,
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value


def toggle_setting(setting_name):
    """Toggle setting and force rerun"""
    st.session_state[setting_name] = not st.session_state.get(setting_name, False)
    st.rerun()


def main():
    initialize_session_state()

    # Pääsisältö
    render_rag_module()
    st.write("---")
    render_diagram_module()
    st.write("---")
    render_chat_module()
    st.write("---")

    # Settings section
    st.subheader("Settings")
    col1, col2, col3, col4 = st.columns(4)

    # Model Settings
    with col1:
        st.toggle(
            "Model Settings",
            value=st.session_state.get("show_model_settings", False),
            key="model_toggle",
            on_change=toggle_setting,
            args=("show_model_settings",),
            help="Configure model settings",
        )
        if st.session_state.get("show_model_settings", False):
            with st.container():
                render_model_selector()

    # Prompt Settings
    with col2:
        st.toggle(
            "Prompt Settings",
            value=st.session_state.get("show_prompt_settings", False),
            key="prompt_toggle",
            on_change=toggle_setting,
            args=("show_prompt_settings",),
            help="Configure system prompt",
        )
        if st.session_state.get("show_prompt_settings", False):
            with st.container():
                render_prompt_module()

    # Token Info
    with col3:
        st.toggle(
            "Token Info",
            value=st.session_state.get("show_token_info", False),
            key="token_toggle",
            on_change=toggle_setting,
            args=("show_token_info",),
            help="View token usage and costs",
        )
        if st.session_state.get("show_token_info", False):
            with st.container():
                render_token_module()

    # System Info
    with col4:
        st.toggle(
            "System Info",
            value=st.session_state.get("show_system_info", False),
            key="info_toggle",
            on_change=toggle_setting,
            args=("show_system_info",),
            help="View system information and warnings",
        )
        if st.session_state.get("show_system_info", False):
            with st.container():
                render_info_module()

    # Debug info
    if st.session_state.get("show_debug", False):
        st.write("---")
        render_debug_info()


if __name__ == "__main__":
    main()
