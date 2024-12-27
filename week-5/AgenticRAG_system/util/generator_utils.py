import os
import time
import torch
import streamlit as st
from typing import List, Dict, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Lataa ympäristömuuttujat
load_dotenv()


class ModelType:
    LOCAL_GEMMA = "Local Gemma-2b (Local)"
    LOCAL_MISTRAL = "Local Mistral-7b (Local)"
    O1_MINI = "O1-mini (OpenAI)"
    O1 = "O1 (OpenAI)"
    GPT4O_REALTIME = "GPT-4o Realtime (Azure)"
    GPT4O = "GPT-4o (Azure)"
    O1_PREVIEW = "O1-preview (Azure)"


class TokenPricing:
    """Token hinnoittelu eri malleille"""

    GPT4O = {
        "input": 2.50 / 1_000_000,  # $2.50 per 1M input tokens
        "output": 10.00 / 1_000_000,  # $10.00 per 1M output tokens
    }
    O1_PREVIEW = {
        "input": 0.50 / 1_000_000,  # Esimerkki hinta
        "output": 2.00 / 1_000_000,
    }


def tokenize_with_rag_prompt(
    query: str, context_items: List[Dict], tokenizer
) -> torch.Tensor:
    """
    Luo RAG-promptin ja tokenisoi sen.

    Args:
        query: Käyttäjän kysymys
        context_items: Lista relevanteista dokumenteista
        tokenizer: Tokenizer-instanssi

    Returns:
        torch.Tensor: Tokenisoidut input_ids
    """
    # Rakenna konteksti dokumenteista
    context = "\n".join([item["sentence_chunk"] for item in context_items])

    # Rakenna RAG-prompt
    prompt = f"""Based on the following context, please answer the question.
    
Context:
{context}

Question: {query}

Answer:"""

    # Tokenisoi
    return tokenizer(prompt, return_tensors="pt")["input_ids"]


def generate_with_openai(prompt: str, model_type: str) -> Tuple[str, int, int]:
    """Generoi vastaus OpenAI:n mallilla ja palauttaa tokenimäärät."""
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY puuttuu .env tiedostosta")
        return "API-avain puuttuu", 0, 0

    client = OpenAI(api_key=api_key)

    # Valitse oikea malli
    if model_type == ModelType.O1_MINI:
        model = "o1-mini-2024-09-12"
    elif model_type == ModelType.O1:
        model = "o1-2024-12-17"
    else:
        st.error(f"Tuntematon OpenAI malli: {model_type}")
        return "Tuntematon malli", 0, 0

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return (
            response.choices[0].message.content,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )
    except Exception as e:
        st.error(f"OpenAI API virhe: {str(e)}")
        return "Virhe OpenAI API:n käytössä", 0, 0


def generate_with_azure(prompt: str, model_type: str) -> Tuple[str, int, int]:
    """Generoi vastaus Azure OpenAI:n mallilla ja palauttaa tokenimäärät."""
    from openai import AzureOpenAI

    client = AzureOpenAI(
        api_key=os.getenv("Azure_API_KEY"),
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv("Azure_ENDPOINT"),
    )

    # Valitse oikea deployment ja parametrit
    if model_type == ModelType.GPT4O_REALTIME:
        deployment = "gpt-4o-realtime-preview"
        params = {"temperature": 0.7}
    elif model_type == ModelType.GPT4O:
        deployment = "gpt-4o"
        params = {"temperature": 0.7}
    elif model_type == ModelType.O1_PREVIEW:
        deployment = "o1-preview"
        params = {}

    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}],
        **params,
    )

    # Laske tokenimäärät
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens

    return (response.choices[0].message.content, input_tokens, output_tokens)


def generate_answer(
    input_ids: torch.Tensor,
    model,
    tokenizer,
    model_type: str,
    max_new_tokens: int = 512,
) -> Tuple[str, float]:
    """Generoi vastaus valitulla mallilla."""
    start_time = time.time()

    if model_type == ModelType.LOCAL_MISTRAL:
        # Mistral-spesifinen käsittely
        with torch.no_grad():
            # Lisää attention mask
            attention_mask = torch.ones_like(input_ids)

            # Aseta padding token
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            output_ids = model.generate(
                input_ids,
                attention_mask=attention_mask,
                pad_token_id=tokenizer.pad_token_id,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
            )
        answer = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    elif model_type == ModelType.LOCAL_GEMMA:
        # Gemma-spesifinen käsittely
        with torch.no_grad():
            output_ids = model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                pad_token_id=tokenizer.pad_token_id,
                do_sample=True,
                temperature=0.7,
            )
        answer = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    elif model_type in [ModelType.O1_MINI, ModelType.O1]:
        # OpenAI mallit
        prompt = tokenizer.decode(input_ids[0], skip_special_tokens=True)
        answer = generate_with_openai(prompt, model_type)

    elif model_type in [ModelType.GPT4O_REALTIME, ModelType.GPT4O]:
        # Azure mallit
        prompt = tokenizer.decode(input_ids[0], skip_special_tokens=True)
        answer = generate_with_azure(prompt, model_type)

    generation_time = time.time() - start_time
    return answer, generation_time


def load_mistral():
    """Lataa Mistral-mallin."""
    models_dir = Path(
        os.getenv("MODELS_DIR", Path(__file__).parent.parent.parent.parent / "models")
    )
    local_path = models_dir / "mistral-7b"

    print(f"Ladataan Mistral-malli kansioon {local_path}")
    st.info("Ladataan Mistral-mallia... Tämä voi kestää useita minuutteja.")

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Lataa malli osissa
        status_text.text("Ladataan mallia (vaihe 1/3)...")
        progress_bar.progress(30)

        model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.3",
            device_map={"": "cpu"},  # Pakotetaan CPU:lle
            torch_dtype=torch.float16,
            token=os.getenv("HUGGINGFACE_TOKEN"),
            low_cpu_mem_usage=True,
        )

        status_text.text("Ladataan tokenizeria (vaihe 2/3)...")
        progress_bar.progress(60)

        tokenizer = AutoTokenizer.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.3",
            token=os.getenv("HUGGINGFACE_TOKEN"),
        )

        # Siirrä malli CPU:lle
        model = model.to("cpu")

        # Tallenna malli ja tokenizer
        if not local_path.exists():
            local_path.mkdir(parents=True, exist_ok=True)

            status_text.text("Tallennetaan mallia (vaihe 3/3)...")
            progress_bar.progress(90)

            model.save_pretrained(local_path)
            tokenizer.save_pretrained(local_path)

        progress_bar.progress(100)
        status_text.text("Valmis!")
        return model, tokenizer

    except Exception as e:
        st.error(f"Virhe mallin latauksessa: {str(e)}")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise e


def load_mistral_tokenizer():
    """Lataa Mistral-tokenizerin."""
    models_dir = Path(
        os.getenv("MODELS_DIR", Path(__file__).parent.parent.parent.parent / "models")
    )
    local_path = models_dir / "mistral-7b"

    if local_path.exists():
        return AutoTokenizer.from_pretrained(local_path, local_files_only=True)
    else:
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3")
        tokenizer.save_pretrained(local_path)
        return tokenizer


def load_gemma():
    """Lataa Gemma-mallin."""
    models_dir = Path(
        os.getenv("MODELS_DIR", Path(__file__).parent.parent.parent.parent / "models")
    )
    models_dir.mkdir(exist_ok=True)  # Luo kansio jos ei ole olemassa

    local_path = models_dir / "gemma-2b"

    if local_path.exists():
        return AutoModelForCausalLM.from_pretrained(
            local_path,
            device_map={"": "cpu"},
            local_files_only=True,
            torch_dtype=torch.float16,
        )
    else:
        print(f"Ladataan Gemma-malli kansioon {local_path}")
        model = AutoModelForCausalLM.from_pretrained(
            "google/gemma-2b",
            device_map={"": "cpu"},
            torch_dtype=torch.float16,
            token=os.getenv("HUGGINGFACE_TOKEN"),  # Lisätty token
        )
        model.save_pretrained(local_path)
        return model


def load_tokenizer():
    """Lataa Gemma-tokenizerin."""
    models_dir = Path(
        os.getenv("MODELS_DIR", Path(__file__).parent.parent.parent.parent / "models")
    )
    models_dir.mkdir(exist_ok=True)  # Luo kansio jos ei ole olemassa

    local_path = models_dir / "gemma-2b"

    if local_path.exists():
        return AutoTokenizer.from_pretrained(local_path, local_files_only=True)
    else:
        print(f"Ladataan Gemma-tokenizer kansioon {local_path}")
        tokenizer = AutoTokenizer.from_pretrained(
            "google/gemma-2b",
            token=os.getenv("HUGGINGFACE_TOKEN"),  # Lisätty token
        )
        tokenizer.save_pretrained(local_path)
        return tokenizer


def calculate_token_cost(
    input_tokens: int, output_tokens: int, model_type: str
) -> float:
    """Laskee tokenien hinnan."""
    if model_type in [ModelType.GPT4O, ModelType.GPT4O_REALTIME]:
        pricing = TokenPricing.GPT4O
    elif model_type == ModelType.O1_PREVIEW:
        pricing = TokenPricing.O1_PREVIEW
    else:
        return 0.0  # Lokaalit mallit ilmaisia

    cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])
    return cost
