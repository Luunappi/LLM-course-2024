import os
import sys
from pathlib import Path
import base64
import pandas as pd

# Lisää projektin juurikansio Python-polkuun
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import streamlit as st
import spacy
import torch
import time
from sentence_transformers import SentenceTransformer
from util import pdf_utils
from util.embedings_utils import embed_chunks, embeddings_to_tensor
from util.nlp_utils import sentencize, chunk, chunks_to_text_elems
from util.generator_utils import (
    load_tokenizer,
    tokenize_with_chat,
    tokenize_with_rag_prompt,
    load_gemma,
    generate_answer,
)
from util.session_utils import (
    SESSION_VARS,
    put_to_session,
    get_from_session,
    print_session,
    load_processed_data,
    save_processed_data,
)
from util.vector_search_utils import retrieve_relevant_resources
from util.timer_utils import ProcessTimer

min_token_length = 30


def debug_info(message, data=None, show_time=True):
    """Näyttää debug-informaatiota käyttöliittymässä"""
    # Alusta debug_history jos sitä ei ole
    if "debug_history" not in st.session_state:
        st.session_state.debug_history = []
        st.session_state.current_phase = ""
        st.session_state.phase_start_time = time.time()
        st.session_state.start_time = time.time()

    # Laske kulunut aika
    current_time = time.time()
    phase_elapsed = current_time - st.session_state.get("start_time", current_time)

    # Luo debug-viesti
    debug_msg = {
        "time": f"{phase_elapsed:.1f}s",
        "message": message,
        "data": data,
    }

    # Lisää historiaan
    st.session_state.debug_history.append(debug_msg)

    # Päivitä nykyinen vaihe ja näytä se
    if show_time:
        st.session_state.current_phase = message
        st.session_state.phase_start_time = current_time


def get_device():
    """Palauttaa sopivan laitteen mallille"""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


# Luo globaali timer
timer = ProcessTimer()

# Lataa mallit ensin
if not get_from_session(st, SESSION_VARS.LOADED_MODELS):
    device = get_device()
    debug_info("Loading models", f"Device: {device}")

    # Lataa NLP malli
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("sentencizer")
    put_to_session(st, SESSION_VARS.NLP, nlp)

    # Lataa Embedding malli
    # NOTE: Here "device='cpu'" is specified, even if get_device() indicates "cuda" or "mps".
    #       If you want to use GPU or MPS for embedding, pass device=device instead.
    embedding_model = SentenceTransformer(
        "sentence-transformers/all-mpnet-base-v2", device="cpu"
    )
    put_to_session(st, SESSION_VARS.EMBEDDING_MODEL_CPU, embedding_model)

    # Lataa Gemma malli
    model = "google/gemma-2b-it"
    gemma_model = load_gemma(model).to("cpu")
    tokenizer = load_tokenizer(model)
    put_to_session(st, SESSION_VARS.MODEL, gemma_model)
    put_to_session(st, SESSION_VARS.TOKENIZER, tokenizer)

    put_to_session(st, SESSION_VARS.LOADED_MODELS, True)
    debug_info("Models loaded successfully")
else:
    debug_info("Using previously loaded models")

apple_style = """
<style>
    .apple-status {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        border-radius: 6px;
        background-color: #2A2A2A;  /* Dark gray */
        border: 1px solid #BBBBBB;  /* Thin light border */
        margin: 10px 0;
        color: #FFFFFF;             /* White text */
    }
    .apple-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255, 255, 255, 0.3);  /* Light white spin track */
        border-radius: 50%;
        border-top-color: #FFFFFF;  /* White spinner top */
        animation: spin 1s ease-in-out infinite;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Logo tyylit */
    .hy-logo {
        width: 80px;
        margin-bottom: 1rem;
        filter: brightness(0) invert(1);  /* Muuta logo valkoiseksi */
    }
    
    /* Container logo + title */
    .header-container {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 2rem;
    }
</style>
"""
st.markdown(apple_style, unsafe_allow_html=True)

# Määritä polku logolle img-kansiosta
logo_path = root_dir / "img" / "HYlogo.png"

# Logo ja otsikko
try:
    with open(logo_path, "rb") as f:  # Huomaa rb-moodi binääritiedostolle
        logo_data = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div class="header-container">
            <img src="data:image/png;base64,{logo_data}" class="hy-logo" />
            <h1>Simpple PDF RAG Demo</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
except FileNotFoundError:
    st.error(f"Logo file not found at {logo_path}")
    st.title("Simpple PDF RAG Demo")

# Poista vanha title
# st.title("Simpple PDF RAG Demo")

# UI elementit
query = st.text_input("Type your query here", "What is Lossless Tokenization?")
gen_variant = st.selectbox(
    "Select model type",
    ("rag (Gemma 2B + Embeddings)", "vanilla (Gemma 2B)"),
    index=0,  # RAG oletuksena
)

# -------------------------
# Summarize Mode
# -------------------------
st.subheader("Choose Your Action:")
use_summarize = st.checkbox(
    "Summarize Entire PDF (RAG only)",
    value=False,
    help=(
        "If checked, will try to summarize the entire PDF. "
        "For large documents, context-limit issues may occur."
    ),
)


def create_summarize_prompt(full_text: str) -> str:
    return (
        "Please summarize the following PDF content comprehensively:\n\n"
        f"{full_text}\n\n"
        "Focus on the main arguments, methods, and conclusions."
    )


model_type = "vanilla" if "vanilla" in gen_variant else "rag"
debug_info("User selected model_type", model_type)

uploaded_file = None
if model_type == "rag":
    uploaded_file = st.file_uploader(
        label="Upload a PDF file",
        help="For RAG mode, please upload a PDF",
        type="pdf",
    )

button_clicked = st.button("Generate")

if model_type == "rag" and not uploaded_file:
    st.warning("⚠ Please upload a PDF file for RAG mode")
    debug_info("No PDF uploaded, set button_clicked to False", None)
    button_clicked = False

# Lisää vastauksen generointi tähän
if button_clicked:
    try:
        if model_type == "rag" and uploaded_file:
            debug_info("Starting RAG mode setup")

            # Prosessoi PDF
            timer.start("pdf_processing")
            pages_and_texts = pdf_utils.open_and_read_pdf(uploaded_file)

            # Chunkkaa teksti
            debug_info("Processing text chunks")
            # Extract sentences
            sentencize(pages_and_texts, get_from_session(st, SESSION_VARS.NLP))
            # Chunk the sentences
            chunk(pages_and_texts)
            # Convert to text elements
            pages_and_chunks = chunks_to_text_elems(pages_and_texts)

            df = pd.DataFrame(pages_and_chunks)
            chunks = df[df["chunk_token_count"] > min_token_length].to_dict(
                orient="records"
            )

            # Luo embeddings
            debug_info("Creating embeddings")
            embeddings_tensor, pages_and_chunks = embeddings_to_tensor(
                get_from_session(st, SESSION_VARS.EMBEDDINGS_FILENAME)
            )

            # Hae relevantit chunkit
            debug_info("Retrieving relevant chunks")
            scores, indices = retrieve_relevant_resources(
                query,
                embeddings_tensor,
                get_from_session(st, SESSION_VARS.EMBEDDING_MODEL_CPU),
                st,
            )

            # Create context items from results
            context_items = [pages_and_chunks[i] for i in indices]
            # Add scores to context items
            for i, item in enumerate(context_items):
                item["score"] = scores[i].cpu()

            # Generoi vastaus
            debug_info("Starting answer generation")
            tokenizer = get_from_session(st, SESSION_VARS.TOKENIZER)
            input_ids, prompt = tokenize_with_rag_prompt(
                get_from_session(st, SESSION_VARS.TOKENIZER), query, context_items
            )
            answer, gen_time, token_stats = generate_answer(
                get_from_session(st, SESSION_VARS.MODEL),
                input_ids,
                get_from_session(st, SESSION_VARS.TOKENIZER),
                prompt,
            )

            # Näytä vastaus
            st.markdown("### Answer")
            st.markdown(answer)

        elif model_type == "vanilla":
            debug_info("Starting vanilla generation")
            tokenizer = get_from_session(st, SESSION_VARS.TOKENIZER)
            input_ids, prompt = tokenize_with_chat(
                get_from_session(st, SESSION_VARS.TOKENIZER), query
            )

            answer, gen_time, token_stats = generate_answer(
                get_from_session(st, SESSION_VARS.MODEL),
                input_ids,
                get_from_session(st, SESSION_VARS.TOKENIZER),
                prompt,
            )

            # Näytä vastaus
            st.markdown("### Answer")
            st.markdown(answer)

    except Exception as e:
        st.error(f"❌ Error during generation: {str(e)}")
        debug_info("Generation error details", str(e))

# Luo containerit UI:n alaosaan
current_phase_container = st.container()  # Uusi container current phaselle
info_container = st.container()

# Näytä current phase expanderin yläpuolella
with current_phase_container:
    if "current_phase" in st.session_state:
        phase_elapsed = time.time() - st.session_state.get(
            "phase_start_time", time.time()
        )
        st.write(
            f"Current Phase: {st.session_state.current_phase} ({phase_elapsed:.1f}s)"
        )

# Process Information expander
with info_container:
    with st.expander("ℹ️ Process Information", expanded=False):
        # Process Timeline
        if "debug_history" in st.session_state:
            st.write("### Process Timeline")
            phases = [
                ("PDF Processing", "📄"),
                ("Text Chunking", "✂️"),
                ("Embedding", "🔢"),
                ("Retrieval", "🔍"),
                ("Generation", "🤖"),
            ]

            current_phase_idx = -1
            for i, (phase, emoji) in enumerate(phases):
                if phase in st.session_state.get("current_phase", ""):
                    current_phase_idx = i
                    break

            for i, (phase, emoji) in enumerate(phases):
                if i < current_phase_idx:
                    st.write(f"{emoji} ~~{phase}~~ ✓")
                elif i == current_phase_idx:
                    phase_elapsed = time.time() - st.session_state.get(
                        "phase_start_time", time.time()
                    )
                    st.write(f"{emoji} **{phase}** ({phase_elapsed:.1f}s)")
                else:
                    st.write(f"{emoji} {phase}")

            # Model Info
            st.write("\n### Model Configuration")
            device_info = {
                "Embedding model": {
                    "device": "cpu",  # Kiinteä arvo
                    "max_seq_length": 384,
                    "embedding_dim": 768,
                },
                "LLM": {
                    "model": "Gemma 2B",
                    "device": "CPU",
                    "hidden_size": 2048,
                    "vocab_size": 256000,
                    "num_layers": 18,
                },
                "Hardware": {
                    "MPS available": torch.backends.mps.is_available(),
                    "CUDA available": torch.cuda.is_available(),
                },
            }

            for section, details in device_info.items():
                st.write(f"#### {section}")
                for key, value in details.items():
                    st.write(f"- **{key}:** {value}")

            # Process Log
            st.write("\n### Detailed Log")
            for msg in st.session_state.debug_history:
                st.write(f"🔍 {msg['time']}: {msg['message']}")
                if msg["data"]:
                    st.write(f"• Data: {msg['data']}")
