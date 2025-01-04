"""
Chat Module

Handles the chat interface and message processing functionality.
"""

import streamlit as st
from openai import OpenAI
import os
from datetime import datetime
from ui_components.model_module import Models
from tools.rag_tool import RAGTool
from tools.diagram_tool import DiagramTool

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
diagram_tool = DiagramTool()
rag_tool = RAGTool()


def direct_llm_answer(user_input):
    """Generate an answer by calling the language model with no doc context."""
    try:
        # Get current model configuration
        model_name = st.session_state.get("current_model", Models.get_default_model())
        model_config = Models.get_model_config(model_name)

        # Get max words setting
        max_words = st.session_state.get("max_words", 50)

        # Add word limit instruction to prompt if limit is set
        content = user_input
        if max_words > 0:
            content = f"Answer the following question in {max_words} words or less: {user_input}"

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": content},
            ],
            max_tokens=model_config.max_tokens,
        )

        answer = response.choices[0].message.content

        # Update token counts
        st.session_state["current_model"] = model_name
        st.session_state["input_tokens"] = response.usage.prompt_tokens
        st.session_state["output_tokens"] = response.usage.completion_tokens
        st.session_state["last_query_time"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return answer

    except Exception as e:
        print(f"DEBUG: API key used: {os.getenv('OPENAI_API_KEY')[:10]}...")
        return f"Error in direct query: {str(e)}"


def translate_query_if_needed(query, doc_language="english"):
    """Translate query to document language if needed"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate the query to {doc_language} if it's in another language. If already in {doc_language}, return as is.",
                },
                {"role": "user", "content": query},
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return query


def translate_answer(answer, target_language):
    """Translate answer to target language"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate the following text to {target_language}. Preserve any formatting.",
                },
                {"role": "user", "content": answer},
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.session_state["system_warnings"].append(f"Translation error: {str(e)}")
        return answer


def detect_language(text):
    """Detect the language of the input text"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Detect the language of the following text and return only the language name in English.",
                },
                {"role": "user", "content": text},
            ],
            max_tokens=50,
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        st.session_state["system_warnings"].append(
            f"Language detection error: {str(e)}"
        )
        return "english"


def process_input(user_input, query_type):
    """Process the user input"""
    if not user_input.strip():
        return None

    try:
        question_language = detect_language(user_input)

        if query_type == "Document (RAG)":
            # Käytetään RAGToolia dokumenttihakuun
            result = rag_tool.process(user_input)
            if result:
                answer = result["content"]
                if question_language != "english":
                    answer = translate_answer(answer, question_language)
                return answer
            return "Please load a document first"
        else:
            answer = direct_llm_answer(user_input)
            return answer

    except Exception as e:
        st.session_state["system_warnings"].append(f"Error processing input: {str(e)}")
        return None


def process_and_clear():
    """Process input and clear the input field"""
    user_input = st.session_state.user_input
    if user_input:
        # Set processing state
        st.session_state["processing"] = True

        # Käytetään DiagramToolia visualisointipyyntöjen käsittelyyn
        result = diagram_tool.process(user_input)
        if result and result["type"] == "visualization":
            st.plotly_chart(result["content"], use_container_width=True)
            st.session_state.chat_history.append((user_input, result["message"]))
            st.session_state["processing"] = False
            st.session_state.user_input = ""
            st.rerun()
            return

        # Normal query processing
        query_type = st.session_state.get("query_type", "Direct LLM")
        answer = process_input(user_input, query_type)

        if answer and not answer.startswith("Error"):
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            st.session_state.chat_history.append((user_input, answer))
            st.session_state.last_answer = answer
            st.session_state.show_answer = True

        st.session_state["processing"] = False
        st.session_state.user_input = ""
        st.rerun()


def process_input_callback():
    """Callback for processing input"""
    if "user_input" in st.session_state and st.session_state.user_input:
        st.session_state["processing"] = True
        user_input = st.session_state.user_input

        # Use orchestrator to process query
        result = st.session_state.orchestrator.process_query(user_input)

        # Initialize chat history if needed
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Create complete answer with text and visualization
        complete_answer = ""
        if result.get("text"):
            complete_answer += result["text"]

        # Add visualization and its summary if present
        if result.get("visualizations"):
            for viz in result["visualizations"]:
                # Store visualization for immediate display
                if "current_visualizations" not in st.session_state:
                    st.session_state.current_visualizations = []
                st.session_state.current_visualizations.append(viz)

                # Store visualization in chat history
                if "chat_visualizations" not in st.session_state:
                    st.session_state.chat_visualizations = {}
                st.session_state.chat_visualizations[
                    len(st.session_state.chat_history)
                ] = viz

                # Add visualization summary to answer
                complete_answer += f"\n\n{viz['summary']}"

        # Add to chat history
        st.session_state.chat_history.append((user_input, complete_answer))
        st.session_state.last_answer = complete_answer
        st.session_state.show_answer = True
        st.session_state["processing"] = False


def render_chat_module():
    """Render the chat interface"""
    # Query type selection
    has_documents = (
        "processed_files" in st.session_state
        and len(st.session_state.processed_files) > 0
    )
    default_index = 0 if has_documents else 1

    query_type = st.radio(
        "Choose answer source:",
        ["Document (RAG)", "Direct LLM"],
        index=default_index,
        key="query_type",
        help="Document: Uses loaded document for answers\nDirect LLM: Answers without document context",
        disabled=not has_documents,
    )

    # CSS tyyli napin asemointiin
    st.markdown(
        """
        <style>
        .input-container {
            position: relative;
            width: 100%;
            max-width: 100%;
            margin-bottom: 2rem;
        }
        .stTextInput {
            width: 100% !important;
        }
        .stTextInput > div {
            width: 100% !important;
        }
        .stTextInput > div > div {
            width: 100% !important;
        }
        .stButton {
            position: absolute;
            right: 0;
            top: 0;
            z-index: 1;
        }
        .stButton button {
            border-top-left-radius: 0;
            border-bottom-left-radius: 0;
            height: 42px;
            margin-right: 0;
        }
        .stTextInput > div > div > input {
            padding-right: 80px !important;
            width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Create columns for input and processing indicator
    col1, col2 = st.columns([9, 1])

    # Text input and send button in the first column
    with col1:
        with st.container():
            # Käytä div-elementtiä asemointiin
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            user_input = st.text_input(
                "Ask something:",
                key="user_input",
                placeholder="Enter your question here and press Enter",
                on_change=process_input_callback,
                label_visibility="collapsed",
            )
            if st.button("Send", type="primary", on_click=process_input_callback):
                pass
            st.markdown("</div>", unsafe_allow_html=True)

    # Processing indicator in the second column
    with col2:
        if st.session_state.get("processing", False):
            st.markdown(
                '<div style="color: gray; font-size: 0.9em; padding-top: 5px;">Processing...</div>',
                unsafe_allow_html=True,
            )

    # Show answer if available
    if st.session_state.get("show_answer", False):
        st.markdown("### Answer:")
        st.markdown(st.session_state.last_answer)
        # Show current visualizations
        if st.session_state.get("current_visualizations"):
            for i, viz in enumerate(st.session_state.current_visualizations):
                st.plotly_chart(
                    viz["figure"], use_container_width=True, key=f"current_viz_{i}"
                )
            # Clear visualizations after showing
            st.session_state.current_visualizations = []
        st.session_state.show_answer = False

    # Chat history after the answer
    if "chat_history" in st.session_state and st.session_state.chat_history:
        with st.expander("Chat History", expanded=False):
            st.subheader("Chat History")
            for i, (q, a) in enumerate(st.session_state.chat_history):
                st.markdown(f"**Q{i+1}:** {q}")
                st.markdown(f"**A{i+1}:** {a}")
                # Show visualization if exists for this chat entry
                if st.session_state.get("chat_visualizations", {}).get(i):
                    viz = st.session_state.chat_visualizations[i]
                    st.plotly_chart(
                        viz["figure"], use_container_width=True, key=f"history_viz_{i}"
                    )
                st.markdown("---")
