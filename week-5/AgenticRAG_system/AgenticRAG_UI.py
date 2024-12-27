import streamlit as st
import torch
from pathlib import Path
import os
import gc
import pandas as pd
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer

# Omat moduulit
from AgenticRAG import AgenticRAG
from agents.image_agent import ImageAgent
from agents.text_agent import TextAgent
from util.session_utils import SESSION_VARS, get_from_session, put_to_session
from util.embeddings_utils import embeddings_to_tensor
from util.nlp_utils import sentencize, chunk
from util.pdf_utils import open_and_read_pdf
from util.generator_utils import (
    load_gemma,
    load_tokenizer,
    load_mistral,
    load_mistral_tokenizer,
    ModelType,
    generate_with_openai,
    generate_with_azure,
)


def extract_text_from_pdf(pdf_file):
    """
    Lukee tekstin PDF-tiedostosta käyttäen pypdf-kirjastoa.
    """
    pdf_reader = PdfReader(pdf_file)
    text_chunks = []
    page_numbers = []

    for page_num, page in enumerate(pdf_reader.pages, 1):
        text = page.extract_text()
        if text.strip():  # Vain jos sivulla on tekstiä
            # Jaa teksti kappaleisiin
            paragraphs = text.split("\n\n")
            for para in paragraphs:
                if para.strip():
                    text_chunks.append(para.strip())
                    page_numbers.append(page_num)

    return pd.DataFrame({"sentence_chunk": text_chunks, "page_num": page_numbers})


def handle_pdf_upload():
    """
    Käsittelee PDF-tiedoston latauksen ja tekstin ekstraktoinnin.
    """
    uploaded_file = st.file_uploader("Lataa PDF-tiedosto", type="pdf")
    if uploaded_file:
        try:
            # Lue PDF ja ekstraktoi teksti
            pdf_bytes = BytesIO(uploaded_file.read())
            df = extract_text_from_pdf(pdf_bytes)

            if not df.empty:
                st.success(
                    f"PDF käsitelty onnistuneesti. Löydettiin {len(df)} tekstikappaletta."
                )
                return df
            else:
                st.error("PDF-tiedostosta ei löytynyt tekstiä.")
                return None
        except Exception as e:
            st.error(f"Virhe PDF:n käsittelyssä: {str(e)}")
            return None
    return None


def main():
    st.title("Agentic RAG - Standalone UI")

    # Mallin valinta
    model_type = st.selectbox(
        "Select Model:",
        [
            ModelType.LOCAL_GEMMA,  # Local Gemma-2b (Local)
            ModelType.LOCAL_MISTRAL,  # Local Mistral-7b (Local)
            ModelType.O1_MINI,  # O1-mini (OpenAI)
            ModelType.O1_PREVIEW,  # O1-preview (Azure)
            ModelType.GPT4O_REALTIME,  # GPT-4o Realtime (Azure)
            ModelType.GPT4O,  # GPT-4o (Azure)
        ],
    )

    # Lataa valittu malli
    if model_type == ModelType.LOCAL_GEMMA:
        models_dir = Path(os.getenv("MODELS_DIR", "models"))
        gemma_path = models_dir / "gemma-2b"

        if not gemma_path.exists():
            st.write("Ladataan Gemma-malli ensimmäistä kertaa...")
            model = load_gemma()
            tokenizer = load_tokenizer()
            model.save_pretrained(gemma_path)
            tokenizer.save_pretrained(gemma_path)
        else:
            st.write("Käytetään lokaalisti tallennettua Gemma-mallia")
            model = AutoModelForCausalLM.from_pretrained(
                gemma_path,
                device_map={"": "cpu"},
                local_files_only=True,
                torch_dtype=torch.float16,
            )
            tokenizer = AutoTokenizer.from_pretrained(gemma_path, local_files_only=True)

    elif model_type == ModelType.LOCAL_MISTRAL:
        models_dir = Path(os.getenv("MODELS_DIR", "models"))
        mistral_path = models_dir / "mistral-7b"

        if (
            not mistral_path.exists()
            or not (mistral_path / "pytorch_model.bin").exists()
        ):
            st.write("Ladataan Mistral-malli ensimmäistä kertaa...")
            model, tokenizer = load_mistral()
        else:
            st.write("Käytetään lokaalisti tallennettua Mistral-mallia")
            model = AutoModelForCausalLM.from_pretrained(
                mistral_path,
                device_map={"": "cpu"},
                local_files_only=True,
                torch_dtype=torch.float16,
            )
            tokenizer = AutoTokenizer.from_pretrained(
                mistral_path, local_files_only=True
            )
    else:
        # Pilvimalleille ei tarvita lokaalia mallia
        model = None
        tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")

    # Kyselytavan valinta
    query_type = st.radio(
        "Select Query Type:", ["Direct Question", "RAG-Enhanced Question"]
    )

    if query_type == "Direct Question":
        # Suora kysymys mallille
        query = st.text_input(
            "Ask a direct question to the model", "What is artificial intelligence?"
        )
        if st.button("Ask Model"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                with st.spinner("Model thinking..."):
                    if model_type in [ModelType.O1_MINI, ModelType.O1]:
                        status_text.text("Sending request to OpenAI API...")
                        answer = generate_with_openai(query, model_type)

                    elif model_type in [
                        ModelType.GPT4O_REALTIME,
                        ModelType.GPT4O,
                        ModelType.O1_PREVIEW,
                    ]:
                        status_text.text("Sending request to Azure API...")
                        answer = generate_with_azure(query, model_type)

                    elif model_type in [ModelType.LOCAL_GEMMA, ModelType.LOCAL_MISTRAL]:
                        # Lokaalit mallit
                        status_text.text("Tokenizing input...")
                        progress_bar.progress(25)

                        input_ids = tokenizer(query, return_tensors="pt")["input_ids"]

                        status_text.text(
                            "Generating response (this might take a while)..."
                        )
                        progress_bar.progress(50)

                        with torch.no_grad():
                            output_ids = model.generate(
                                input_ids,
                                max_new_tokens=512,
                                do_sample=True,
                                temperature=0.7,
                                max_time=60,
                            )

                        status_text.text("Decoding response...")
                        progress_bar.progress(75)

                        answer = tokenizer.decode(
                            output_ids[0], skip_special_tokens=True
                        )

                    else:
                        st.error(f"Unknown model type: {model_type}")
                        return

                    progress_bar.progress(100)
                    status_text.text("Done!")
                    st.write(f"Answer: {answer}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    else:
        # RAG-pohjainen kysely (alkuperäinen toiminnallisuus)
        st.write("Embedding Model")
        embedding_choice = st.selectbox(
            "Select your embedding model:", ["all-mpnet-base-v2", "MyLocalEmbedding"]
        )

        if embedding_choice == "all-mpnet-base-v2":
            embedding_model = SentenceTransformer(
                "sentence-transformers/all-mpnet-base-v2"
            )
        else:
            embedding_model = SentenceTransformer(
                "sentence-transformers/all-mpnet-base-v2"
            )

        agent_rag = AgenticRAG(
            embedding_model=embedding_model,
            llm_model=model,
            tokenizer=tokenizer,
            device="cpu",
            top_k=5,
            model_type=model_type,
        )

        st.subheader("Upload PDF for RAG")
        uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

        if uploaded_file is not None:
            # Vapauta muisti ennen uuden tiedoston käsittelyä
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None

            st.write("Processing PDF...")
            pages_and_texts = open_and_read_pdf(uploaded_file)

            # Sentencize & chunk
            nlp = get_from_session(st, SESSION_VARS.NLP)
            if not nlp:
                import spacy

                nlp = spacy.load("en_core_web_sm")
                nlp.add_pipe("sentencizer")
                put_to_session(st, SESSION_VARS.NLP, nlp)

            sentences_by_page = []
            for page_txt in pages_and_texts:
                sents = sentencize(page_txt["text"], nlp)
                sentences_by_page.append(sents)

            # Chunk
            chunks = chunk(sentences_by_page, min_token_length=30)
            df = pd.DataFrame(chunks)

            # Embeddings
            embeddings = []
            for i, row in df.iterrows():
                text_chunk = row["sentence_chunk"]
                emb = embedding_model.encode(text_chunk).tolist()
                embeddings.append(emb)
            embeddings_tensor = torch.tensor(embeddings, dtype=torch.float32)

            st.success("Preprocessing complete!")

            # Let the user ask a question
            st.subheader("Agentic RAG Query")
            query = st.text_input(
                "Ask something about this PDF", "What is signal boosting?"
            )
            if st.button("Run Agentic RAG"):
                with st.spinner("Agent reasoning..."):
                    answer, gen_time = agent_rag.run_agentic_search(
                        query, df, embeddings_tensor
                    )
                st.write(f"Answer: {answer}")
                st.write(f"Generation time: {gen_time:.2f}s")

            # Jos PDF:ssä on kuvia, analysoi ne
            for page in pages_and_texts:
                if "images" in page:
                    for img in page["images"]:
                        image_description = image_agent.analyze_image(img)
                        if image_description:
                            # Lisää kuvaus tekstidataan
                            chunks.append(
                                {
                                    "sentence_chunk": image_description,
                                    "page_num": page["page_num"],
                                    "is_image_description": True,
                                }
                            )


if __name__ == "__main__":
    main()
