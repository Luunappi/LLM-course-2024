import streamlit as st
import torch
from pypdf import PdfReader
from io import BytesIO
from aisuite import (
    LLMSelector,
)  # <-- Placeholder for an AISuite-based model picker, if available
from sentence_transformers import SentenceTransformer
from AgenticRAG import AgenticRAG  # Our new agentic RAG class
from util.session_utils import (
    SESSION_VARS,
    get_from_session,
    put_to_session,
)
from util.embedings_utils import embeddings_to_tensor
from util.nlp_utils import sentencize, chunk
from util import pdf_utils
import pandas as pd
from agents.image_agent import ImageAgent
from agents.text_agent import TextAgent


def load_mistral():
    # Example function to load Mistral if needed
    # Adjust to your local environment
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_name = "mistralai/Mistral-7B-Instruct-v0.3"  # or local path
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map={"": "cpu"})
    model.eval()
    return model, tokenizer


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

    st.write("This demo shows a separate UI using the AgenticRAG class.")

    # Step 1: Model selection
    st.subheader("Model Selection")
    # If you have an AISuite-based approach, you'd do something like:
    # available_models = LLMSelector.list_models()  # placeholder
    # user_model_choice = st.selectbox("Choose an LLM", available_models)
    # model, tokenizer = LLMSelector.load_model(user_model_choice)

    # For demonstration, let's do a simpler manual approach:
    llm_option = st.selectbox(
        "Select an LLM to load:", ["Gemma local", "Mistral local", "GPT-2"]
    )

    if llm_option == "Gemma local":
        from util.generator_utils import load_gemma, load_tokenizer

        model = load_gemma()
        tokenizer = load_tokenizer()
    elif llm_option == "Mistral local":
        model, tokenizer = load_mistral()
    else:
        # GPT-2 example
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_name = "gpt2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)

    st.write("Embedding Model")
    embedding_choice = st.selectbox(
        "Select your embedding model:", ["all-mpnet-base-v2", "MyLocalEmbedding"]
    )

    if embedding_choice == "all-mpnet-base-v2":
        embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    else:
        embedding_model = SentenceTransformer(
            "sentence-transformers/all-mpnet-base-v2"
        )  # placeholder

    agent_rag = AgenticRAG(
        embedding_model=embedding_model,
        llm_model=model,
        tokenizer=tokenizer,
        device="cpu",  # or "mps" if on Apple M-series
        top_k=5,
    )

    # Alusta image agent Mac M-sarjalle optimoidusti
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    image_agent = ImageAgent(device=device)

    st.subheader("Upload PDF for RAG")
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded_file is not None:
        st.write("Processing PDF (chunk + embed). This may take a moment...")
        pages_and_texts = pdf_utils.open_and_read_pdf(uploaded_file)

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
