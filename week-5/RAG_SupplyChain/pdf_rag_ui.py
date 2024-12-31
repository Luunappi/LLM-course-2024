import warnings
warnings.filterwarnings('ignore')

# Torch-specific warning suppression
import logging
logging.getLogger("torch").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# UI modules
from ui_components.side_info_module import render_side_panel
from ui_components.chat_module import render_chat_module
from ui_components.rag_module import render_rag_module
from ui_components.diagram_module import render_diagram_module
from ui_components.prompt_module import render_prompt_module
from ui_components.info_module import render_info_module

# Initialize session state
if "system_prompt" not in st.session_state:
    st.session_state["system_prompt"] = "You are an assistant. Use RAG approach..."
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "processed_files" not in st.session_state:
    st.session_state["processed_files"] = {}  # Store processed files data


def main():
    st.set_page_config(page_title="RAG UI", layout="wide")
    st.title("RAG UI")

    # Everything in the sidebar:
    with st.sidebar:
        render_side_panel()  # Left side panel: top area
        render_prompt_module()  # Prompt module
        render_info_module()  # Info module (e.g. token usage & cost)

    # Main layout (single column):
    render_rag_module()
    st.write("---")
    render_diagram_module()
    st.write("---")
    # Chat module (can handle direct LLM queries or RAG-based)
    render_chat_module()


if __name__ == "__main__":
    main()
