import streamlit as st
import re
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
import os
from dotenv import load_dotenv
import fitz  # PyMuPDF
from datetime import datetime
import pandas as pd
import time

# Load environment variables from root .env
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Estä tokenizer-varoitukset


# Load the embedding model
@st.cache_resource
def get_embedding_model():
    return SentenceTransformer("sentence-transformers/all-mpnet-base-v2")


def get_embeddings(texts, model):
    """Get embeddings for a list of texts"""
    try:
        st.write(f"Creating embeddings for {len(texts)} texts...")  # Debug
        embeddings = model.encode(texts)
        st.write("Embeddings created successfully")  # Debug
        return torch.tensor(embeddings)
    except Exception as e:
        st.error(f"Error in get_embeddings: {str(e)}")
        raise


def semantic_search(query, chunks, embeddings, top_k=3):
    """Find most relevant chunks using cosine similarity"""
    try:
        model = get_embedding_model()
        # Muunna query embedding samaan muotoon kuin dokumentin embeddings
        query_embedding = model.encode([query])
        query_embedding = torch.tensor(query_embedding)
        
        # Varmista että embeddings on oikeassa muodossa
        if len(query_embedding.shape) == 2:
            query_embedding = query_embedding.squeeze(0)
        
        # Normalisoi embeddings
        query_embedding = query_embedding / query_embedding.norm()
        embeddings = embeddings / embeddings.norm(dim=1, keepdim=True)
        
        # Laske similarity
        similarities = torch.matmul(embeddings, query_embedding)
        
        # Hae top_k indeksit
        top_indices = similarities.argsort(descending=True)[:top_k]
        
        # Debug tulostus
        st.write(f"Found {len(top_indices)} relevant chunks")
        
        return [chunks[idx] for idx in top_indices]
    except Exception as e:
        st.error(f"Error in semantic search: {str(e)}")
        return []


def generate_answer(query, relevant_chunks):
    """Generate answer using OpenAI API"""
    context = "\n".join(relevant_chunks)
    prompt = f"""Based on the following context, answer the question.
If you cannot answer based on the context, say so.

Context:
{context}

Question: {query}

Answer:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # FAST model for RAG responses
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided context.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        # Update token counts in session state
        st.session_state["current_model"] = "gpt-4o-mini"
        st.session_state["input_tokens"] = response.usage.prompt_tokens
        st.session_state["output_tokens"] = response.usage.completion_tokens

        return response.choices[0].message.content

    except Exception as e:
        st.error(f"Error generating answer: {str(e)}")
        return "Error generating response"


def render_rag_module():
    st.subheader("RAG Module: Upload & Search")
    
    # Debug info for embeddings
    if "processed_files" in st.session_state:
        with st.expander("Debug Info", expanded=False):
            st.write("Cached files:")
            for filename, data in st.session_state.processed_files.items():
                st.write(f"File: {filename}")
                st.write(f"- Chunks: {len(data['chunks'])}")
                st.write(f"- Embeddings shape: {data['embeddings'].shape if 'embeddings' in data else 'No embeddings'}")

    # Show loaded files expander
    with st.expander("Loaded Documents", expanded=True):
        if st.session_state.processed_files:
            st.markdown("### Currently loaded documents:")
            
            # Create a table of loaded documents
            data = []
            for filename, file_data in st.session_state.processed_files.items():
                chunks_count = len(file_data["chunks"])
                timestamp = file_data.get("timestamp", "N/A")
                data.append({
                    "Filename": filename,
                    "Chunks": chunks_count,
                    "Loaded": timestamp
                })
            
            # Display as a DataFrame
            df = pd.DataFrame(data)
            st.dataframe(df)

    uploaded_file = st.file_uploader("Upload PDF/TXT/MD", type=["pdf", "txt", "md"])

    if uploaded_file:
        if uploaded_file.name not in st.session_state.processed_files:
            process_pdf(uploaded_file)
        else:
            st.success(f"Using cached data for {uploaded_file.name}")
            # Load cached data
            cached_data = st.session_state.processed_files[uploaded_file.name]
            st.session_state.chunks = cached_data["chunks"]
            st.session_state.embeddings = cached_data["embeddings"]


def process_pdf(file):
    try:
        bytes_data = file.getvalue()
        
        # Create a progress container that we'll clear at the end
        progress_container = st.empty()
        with progress_container.container():
            progress_text = st.empty()
            progress_bar = st.progress(0)
            status_text = st.empty()

            # PDF Processing phase
            progress_text.text("Processing PDF...")
            doc = fitz.open(stream=bytes_data, filetype="pdf")
            total_pages = len(doc)
            text_pages = []

            for page_num in range(total_pages):
                try:
                    page = doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        text_pages.append(text)
                    
                    progress = (page_num + 1) / total_pages
                    progress_bar.progress(progress)
                    status_text.text(f"Reading page {page_num + 1}/{total_pages}")
                except Exception as e:
                    st.warning(f"Error on page {page_num + 1}: {str(e)}")

            all_text = "\n".join(text_pages)
            status_text.text(f"✓ Successfully extracted {len(text_pages)} pages")
            
            # Chunking phase
            progress_text.text("Chunking text...")
            progress_bar.progress(0)  # Reset progress bar
            chunks = chunk_text_by_sentences(all_text)
            st.session_state.chunks = chunks
            status_text.text(f"✓ Created {len(chunks)} text chunks")
            
            # Embeddings phase with better progress tracking
            with progress_container.container():
                progress_text.text("Creating embeddings...")
                progress_bar.progress(0)
                model = get_embedding_model()
                batch_size = 16  # Pienempi batch-koko
                all_embeddings = []
                
                total_chunks = len(chunks)
                for i in range(0, total_chunks, batch_size):
                    try:
                        batch = chunks[i : min(i + batch_size, total_chunks)]
                        status_text.text(f"Processing batch {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size}")
                        
                        # Create embeddings for batch
                        batch_embeddings = get_embeddings(batch, model)
                        all_embeddings.append(batch_embeddings)
                        
                        # Update progress
                        progress = (i + len(batch)) / total_chunks
                        progress_bar.progress(progress)
                        
                    except Exception as e:
                        st.error(f"Error in batch {i//batch_size + 1}: {str(e)}")
                        continue

                try:
                    # Combine all embeddings
                    st.session_state.embeddings = torch.cat(all_embeddings, dim=0)
                    status_text.text(f"✓ Created embeddings: shape {st.session_state.embeddings.shape}")
                except Exception as e:
                    st.error(f"Error combining embeddings: {str(e)}")
                    return False

                # Verify embeddings
                if st.session_state.embeddings is not None:
                    st.success(f"Embeddings created successfully: {st.session_state.embeddings.shape}")
                else:
                    st.error("Failed to create embeddings")
                    return False

            # Cache the processed data
            st.session_state.processed_files[file.name] = {
                "chunks": chunks,
                "embeddings": st.session_state.embeddings,
                "timestamp": datetime.now().isoformat(),
                "total_chunks": total_chunks,
                "total_pages": total_pages
            }
            
            # Final success message inside container
            progress_text.text("✓ All processing completed!")
            progress_bar.progress(1.0)
            time.sleep(1)  # Show completion for a moment
            
        # Clear the progress container
        progress_container.empty()
        
        # Show final success message outside the container
        st.success(f"""Successfully processed {file.name}:
        - Pages processed: {total_pages}
        - Chunks created: {total_chunks}
        - Embeddings created: {total_chunks}
        
        Done. Now you can ask something about the document.""")
        return True

    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return False


def process_text_file(file):
    text = file.read().decode("utf-8")
    st.session_state["doc_chunks"] = chunk_text_by_sentences(text)
    st.write("Text chunked by sentence boundaries.")
    if st.button("Search with RAG"):
        st.write("Mock RAG search performed on text file...")


def chunk_text_by_sentences(text, min_len=100):  # Kasvatettu min_len
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        words = sentence.split()
        sentence_length = len(words)

        if current_length + sentence_length > min_len and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
