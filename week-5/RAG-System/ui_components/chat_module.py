"""
Chat Module

Handles the chat interface and message processing functionality.
Includes direct LLM queries and RAG-enhanced responses.
"""

import streamlit as st
from ui_components.rag_module import semantic_search, generate_answer
from openai import OpenAI
import os
from datetime import datetime
from ui_components.model_module import Models

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def direct_llm_answer(user_input):
    """Generate an answer by calling the language model with no doc context."""
    print(f"\nDEBUG: Calling direct_llm_answer with input: {user_input}")
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

        print(f"\nDEBUG: Using model: {model_name} with max words: {max_words}")

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": content},
            ],
            max_tokens=model_config.max_tokens,
        )

        print(f"DEBUG: Full API response: {response}")

        answer = response.choices[0].message.content
        print(f"DEBUG: Raw response content: {answer}")

        if not answer:  # Tarkista onko vastaus tyhjä
            raise ValueError("Empty response from API")

        # Update token counts
        st.session_state["current_model"] = model_name
        st.session_state["input_tokens"] = response.usage.prompt_tokens
        st.session_state["output_tokens"] = response.usage.completion_tokens
        st.session_state["last_query_time"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return answer

    except Exception as e:
        print(f"DEBUG: Error in direct_llm_answer: {str(e)}")
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


def process_input(user_input, query_type):
    """Process the user input"""
    print(f"\nDEBUG: Processing input: '{user_input}' with query_type: {query_type}")

    if not user_input.strip():
        st.warning("Please enter a question")
        return None

    try:
        if query_type == "Document (RAG)":
            if "chunks" not in st.session_state or st.session_state.chunks is None:
                st.warning("Please load a document first")
                return None

            status_text = st.empty()
            status_text.markdown(
                '<p style="color: gray; font-size: 0.8em;">Preparing query...</p>',
                unsafe_allow_html=True,
            )
            translated_query = translate_query_if_needed(user_input)

            relevant_chunks = semantic_search(
                translated_query, st.session_state.chunks, st.session_state.embeddings
            )

            answer = generate_answer(translated_query, relevant_chunks, user_input)
            status_text.empty()

            return answer
        else:
            print("DEBUG: Using Direct LLM mode")
            answer = direct_llm_answer(user_input)
            print(f"DEBUG: Got answer: {answer}")

            if answer and answer.startswith("Error"):
                st.error(answer)
                return None

            return answer

    except Exception as e:
        print(f"DEBUG: Error in process_input: {str(e)}")
        st.error(f"Error processing input: {str(e)}")
        return None


def handle_input():
    """Callback for text input"""
    print("\nDEBUG: handle_input called")  # Debug
    if st.session_state.user_input:
        print(f"DEBUG: Processing user input: {st.session_state.user_input}")  # Debug
        query_type = st.session_state.get("query_type", "Direct LLM")
        answer = process_input(st.session_state.user_input, query_type)

        if answer:
            print(f"DEBUG: Got answer in handle_input: {answer[:100]}...")  # Debug
            if isinstance(answer, str) and answer.startswith("Error"):
                st.error(answer)

        st.session_state.user_input = ""
        st.rerun()


def render_chat_module():
    """Render the chat interface"""
    # Näytä chat-historia
    if "chat_history" in st.session_state and st.session_state.chat_history:
        with st.expander("Chat History", expanded=False):
            st.subheader("Chat History")
            for i, (q, a) in enumerate(st.session_state.chat_history):
                st.markdown(f"**Q{i+1}:** {q}")
                st.markdown(f"**A{i+1}:** {a}")
                st.markdown("---")

    # Tarkista onko dokumentteja ladattu
    has_documents = (
        "processed_files" in st.session_state
        and len(st.session_state.processed_files) > 0
    )

    # Aseta oletusvalinta dokumenttien perusteella
    default_index = 0 if has_documents else 1  # 0 = Document (RAG), 1 = Direct LLM

    # Store query type in session state
    query_type = st.radio(
        "Choose answer source:",
        ["Document (RAG)", "Direct LLM"],
        index=default_index,
        key="query_type",
        help="Document: Uses loaded document for answers\nDirect LLM: Answers without document context",
        disabled=not has_documents,  # Estä RAG-valinnan jos ei dokumentteja
    )

    # Initialize answer container
    if "answer_container" not in st.session_state:
        st.session_state.answer_container = st.empty()

    # Callback function to process input
    def process_and_clear():
        user_input = st.session_state.user_input
        if user_input:
            with st.spinner("Processing..."):
                answer = process_input(user_input, query_type)
                if answer and not answer.startswith("Error"):
                    # Add to history first
                    if "chat_history" not in st.session_state:
                        st.session_state.chat_history = []
                    st.session_state.chat_history.append((user_input, answer))

                    # Store answer for display
                    st.session_state.last_answer = answer
                    st.session_state.show_answer = True
                else:
                    st.error(answer if answer else "Failed to get response")

    # Text input with callback
    user_input = st.text_input(
        "Ask something:",
        key="user_input",
        on_change=process_and_clear,
        placeholder="Enter your question here and press Enter",
    )

    # Show answer if available
    if st.session_state.get("show_answer", False):
        st.markdown("### Answer:")
        st.markdown(st.session_state.last_answer)
        # Reset flag
        st.session_state.show_answer = False
