"""Main entry point for AgenticAI chat application"""

import streamlit as st
from agentic.ui import RAGChatUI

st.set_page_config(page_title="AgenticAI Chat", layout="wide")
ui = RAGChatUI()
ui.main()
