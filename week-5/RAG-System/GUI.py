import streamlit as st

# Aseta sivun konfiguraatio heti alussa
st.set_page_config(
    page_title="RAG",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
    initial_sidebar_state="collapsed",  # Piilota sivupalkki
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
from ui_components.prompt_module import render_prompt_module
from ui_components.token_info_module import render_token_module
from ui_components.system_info_module import render_info_module
from ui_components.model_module import render_model_selector
from ui_components.debug_info_module import render_debug_info
from ui_components.document_info_module import render_document_module


def initialize_session_state():
    """Initialize session state once"""
    if not st.session_state.get("_initialized", False):
        # Tarkista API-avain ja aseta tila
        api_key = os.getenv("OPENAI_API_KEY")
        api_key_loaded = bool(api_key and api_key.startswith("sk-"))

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
            "show_document_info": False,
            "system_warnings": [],
            "init_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_key_loaded": api_key_loaded,  # Lisätty API-avaimen tila
            "_initialized": True,
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

        # Jos API-avainta ei löydy, lisää varoitus
        if not api_key_loaded:
            st.session_state["system_warnings"].append(
                "OpenAI API key not found or invalid. Please check your .env file."
            )

        # Initialize orchestrator
        from RAG_Orchestrator import RAGOrchestrator

        st.session_state.orchestrator = RAGOrchestrator()

        st.session_state._initialized = True


def toggle_setting(setting_name):
    """Toggle setting and force rerun"""
    st.session_state[setting_name] = not st.session_state.get(setting_name, False)
    st.rerun()


def main():
    initialize_session_state()

    # Pääotsikko ja alaotsikko
    st.title("AI SEARCH")
    st.subheader("Chat, Upload & Search")

    # Lisää selittävä teksti
    st.markdown(
        '<div style="font-size: 0.9em; color: #666;">'
        "The system automatically evaluates visualization needs based on your questions "
        "and creates appropriate visualizations when needed."
        "</div>",
        unsafe_allow_html=True,
    )

    # Käytä containeria rajoittamaan leveyttä
    with st.container():
        st.markdown(
            """
            <style>
            /* Rajoita koko sivun leveyttä */
            .block-container {
                max-width: 1000px !important;
                padding-left: 5rem !important;
                padding-right: 5rem !important;
            }
            /* Sisällön container */
            .main-container {
                max-width: 800px;
                margin: auto;
                padding: 0 1rem;
            }
            /* Napit */
            .stButton button {
                height: 42px;
                margin-top: 0;
            }
            /* Input-kentät */
            .stTextInput, 
            .stFileUploader > div,
            .input-container {
                width: 100% !important;
                max-width: 100% !important;
            }
            /* Upload-kenttä */
            .stFileUploader > div > div {
                width: 100% !important;
                max-width: 100% !important;
            }
            /* Browse files -nappi */
            .stFileUploader > div > div > button {
                position: absolute;
                right: 0;
                border-radius: 4px;
            }
            /* Radio-napit */
            .st-emotion-cache-1gulkj5 {
                max-width: 800px;
                margin: auto;
            }
            /* Moduulien välit */
            .main-container > div {
                margin-bottom: 0;
            }
            
            /* Viivat ja moduulien otsikot */
            hr {
                margin: 0 !important;
            }
            .module-label {
                margin: 0;
                text-align: right;
                color: #666;
                font-size: 0.8em;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Kääri sisältö div-elementtiin
        st.markdown('<div class="main-container">', unsafe_allow_html=True)

        # Harmaa viiva ennen chat-modulia
        st.markdown(
            """
            <hr>
            <div class="module-label">chat module</div>
            """,
            unsafe_allow_html=True,
        )

        render_chat_module()

        # Harmaa viiva chat- ja RAG-modulin väliin
        st.markdown(
            """
            <hr>
            <div class="module-label">rag module</div>
            """,
            unsafe_allow_html=True,
        )

        render_rag_module()

        # Harmaa viiva ennen settings-osiota
        st.markdown("<hr>", unsafe_allow_html=True)

        # Settings section
        st.subheader("Settings")
        settings = [
            (
                "Model Settings",
                "show_model_settings",
                render_model_selector,
                "model module",
            ),
            (
                "Prompt Settings",
                "show_prompt_settings",
                render_prompt_module,
                "prompt module",
            ),
            ("Token Info", "show_token_info", render_token_module, "token module"),
            ("System Info", "show_system_info", render_info_module, "info module"),
            (
                "Document Info",
                "show_document_info",
                render_document_module,
                "document module",
            ),
        ]

        for label, state_key, render_func, module_name in settings:
            if st.toggle(
                label,
                value=st.session_state.get(state_key, False),
                key=f"{state_key}_toggle",
                on_change=toggle_setting,
                args=(state_key,),
            ):
                st.markdown(
                    f'<div style="text-align:right;color:#666;font-size:0.8em;margin-bottom:1rem">{module_name}</div>',
                    unsafe_allow_html=True,
                )
                render_func()

        # Sulje main-container div
        st.markdown("</div>", unsafe_allow_html=True)

    # Virheilmoitus siirretty loppuun
    if st.session_state.get("error_message"):
        st.error(st.session_state["error_message"])


if __name__ == "__main__":
    main()
