import streamlit as st
from ui_components.rag_module import semantic_search, generate_answer
from openai import OpenAI
import os
from datetime import datetime

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def direct_llm_answer(user_input):
    """Generate an answer by calling the language model with no doc context."""
    try:
        response = client.chat.completions.create(
            model="o1-mini",  # STANDARD model for direct questions
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers general questions without context.",
                },
                {"role": "user", "content": user_input},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        # Update token counts and model info in session state
        st.session_state["current_model"] = "o1-mini"
        st.session_state["input_tokens"] = response.usage.prompt_tokens
        st.session_state["output_tokens"] = response.usage.completion_tokens
        st.session_state["last_query_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return response.choices[0].message.content

    except Exception as e:
        st.error(f"Error in direct query: {str(e)}")
        return "Error generating response"


def translate_query_if_needed(query, doc_language="english"):
    """Translate query to document language if needed"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate the query to {doc_language} if it's in another language. If already in {doc_language}, return as is."
                },
                {"role": "user", "content": query}
            ],
            temperature=0.3,  # Lower temperature for more precise translation
            max_tokens=100
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return query  # Return original query if translation fails


def generate_answer(query, relevant_chunks, original_query):
    """Generate answer using OpenAI API"""
    if not relevant_chunks:
        return "I couldn't find relevant information from the document to answer your question."
        
    context = "\n".join(relevant_chunks)
    needs_translation = query != original_query
    
    prompt = f"""Based on the following context, answer the question.
If you cannot answer based on the context, say so.
{f'Translate your answer to match the language of the original question: "{original_query}"' if needs_translation else 'Answer in the same language as the question.'}
Be specific and use numbers and facts from the context when available.

Context:
{context}

Question: {query}
Original Question: {original_query}

Answer:"""

    try:
        # Debug info before API call
        st.write("Debug: Calling OpenAI API with gpt-4o-mini model...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant that answers questions based on provided context.
                    Ensure your answer matches the language of the original question.
                    If you can't find the answer in the context, say so clearly.
                    Use specific numbers and facts from the context when available."""
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        # Update token counts and model info BEFORE debug info
        st.session_state.update({
            "current_model": "gpt-4o-mini",
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "last_query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Debug info after API call and state update
        st.write(f"Debug: API response received. Tokens used - Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}")

        return response.choices[0].message.content

    except Exception as e:
        st.error(f"Error generating answer: {str(e)}")
        return "Error generating response. Please try again."


def render_chat_module():
    st.subheader("Chat / QA")

    # Show chat history
    if st.session_state.chat_history:
        with st.expander("Chat History", expanded=True):
            for i, (q, a) in enumerate(st.session_state.chat_history):
                st.write(f"Q{i+1}: {q}")
                st.write(f"A{i+1}: {a}")
                st.write("---")

    # Clear history button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Clear History"):
            st.session_state.chat_history = []
            st.rerun()

    # Add model selection
    query_type = st.radio(
        "Choose answer source:",
        ["Document (RAG)", "Direct LLM"],
        help="Document: Uses loaded document for answers\nDirect LLM: Answers without document context"
    )

    # Input and response
    user_input = st.text_input(
        "Ask something:",
        placeholder="Enter your question here..."
    )
    
    if st.button("Send", type="primary"):
        if not user_input.strip():
            st.warning("Please enter a question")
            return

        status_container = st.empty()
        with st.spinner("Thinking..."):
            # Näytä tilannetieto harmaalla ja pienemmällä
            status_text = status_container.markdown(
                '<p style="color: gray; font-size: 0.8em;">Initializing...</p>', 
                unsafe_allow_html=True
            )

            if query_type == "Document (RAG)":
                if "chunks" not in st.session_state or st.session_state.chunks is None:
                    st.warning("Please load a document first")
                    return
                    
                # Translate query to document language for better semantic search
                status_text.markdown(
                    '<p style="color: gray; font-size: 0.8em;">Preparing query...</p>', 
                    unsafe_allow_html=True
                )
                translated_query = translate_query_if_needed(user_input)
                
                # Use translated query for semantic search
                relevant_chunks = semantic_search(
                    translated_query, 
                    st.session_state.chunks, 
                    st.session_state.embeddings
                )

                # Generate answer using both original and translated queries
                answer = generate_answer(translated_query, relevant_chunks, user_input)
                
                status_text.empty()  # Tyhjennä tilannetieto
                st.write("### Answer (RAG-based):")
                st.write(answer)
                
                # Show relevant chunks
                with st.expander("Relevant chunks"):
                    for i, chunk in enumerate(relevant_chunks, start=1):
                        st.write(f"Chunk {i}: {chunk}")
            else:
                # Direct LLM
                status_text.markdown(
                    '<p style="color: gray; font-size: 0.8em;">Generating direct answer without document context...</p>', 
                    unsafe_allow_html=True
                )
                answer = direct_llm_answer(user_input)
                
                status_text.empty()  # Tyhjennä tilannetieto
                st.write("### Answer (direct LLM):")
                st.write(answer)
            
            # Add to history
            st.session_state.chat_history.append((user_input, answer))
