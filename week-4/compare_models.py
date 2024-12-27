"""
Model Comparison Tool

Vertailee finetuunatun ja tuunaamattoman Mistral-mallin sekä Geminin vastauksia.
Gemini toimii arvioijana vertaillen vastausten laatua.
"""

import torch
import logging
from datetime import datetime
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import google.generativeai as genai
from dotenv import load_dotenv

# Määritellään logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(
                "models/logs",
                f'model_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            )
        ),
    ],
)

# Ladataan ympäristömuuttujat
load_dotenv()

# Alustetaan Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
evaluator = genai.GenerativeModel("gemini-pro")

# Määritellään laite
device = "mps" if torch.backends.mps.is_available() else "cpu"
logging.info(f"Using device: {device}")


def load_base_model():
    """Lataa alkuperäinen Mistral-malli"""
    logging.info("\nLadataan base model...")
    model_name = "mistralai/Mistral-7B-Instruct-v0.3"
    logging.info(f"- Malli: {model_name}")
    logging.info(f"- Laite: {device}")
    logging.info(f"- Tarkkuus: {torch.float16}")

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map={"": device},
        trust_remote_code=True,
    )
    logging.info(f"- Parametrien määrä: {model.num_parameters():,}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    logging.info("Base model ladattu onnistuneesti")
    return model, tokenizer


def load_finetuned_model(base_model):
    """Lataa finetuunattu malli"""
    logging.info("\nLadataan finetuned model...")
    logging.info(f"- Polku: models/finetuned")

    return PeftModel.from_pretrained(
        base_model,
        "models/finetuned",
    )


def generate_response(model, tokenizer, prompt):
    """Generoi vastaus mallilla"""
    logging.info(f"\nGeneroidaan vastausta...")
    logging.info(f"- Prompt pituus: {len(prompt)} merkkiä")
    logging.info(f"- Max pituus: 200 tokenia")
    logging.info(f"- Temperature: 0.7")

    generation_start = datetime.now()
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_length=200,
        num_return_sequences=1,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    generation_time = (datetime.now() - generation_start).total_seconds()
    logging.info(f"- Generointiaika: {generation_time:.1f}s")
    logging.info(f"- Vastauksen pituus: {len(response)} merkkiä")
    return response


def evaluate_responses(prompt, base_response, finetuned_response):
    """Käyttää Geminiä arvioimaan vastausten laadun"""
    logging.info("\nArvioidaan vastauksia Geminillä...")
    evaluation_start = datetime.now()

    evaluation_prompt = f"""
    Compare and evaluate these two AI responses to the prompt: "{prompt}"

    Response 1 (Base Model):
    {base_response}

    Response 2 (Finetuned Model):
    {finetuned_response}

    Please analyze:
    1. Accuracy and relevance
    2. Clarity and coherence
    3. Depth of understanding
    4. Overall quality

    Which response is better and why? Be specific and provide a structured comparison.
    """

    evaluation = evaluator.generate_content(evaluation_prompt)
    evaluation_time = (datetime.now() - evaluation_start).total_seconds()
    logging.info(f"- Arviointiaika: {evaluation_time:.1f}s")
    return evaluation.text


# Test prompts
test_prompts = [
    "Explain quantum computing to a 10-year old.",
    "What are the ethical implications of AI in healthcare?",
    "Write a creative story about time travel in exactly three sentences.",
    "Compare and contrast machine learning and traditional programming.",
    "How would you solve climate change using technology?",
]


def main():
    logging.info("\n=== Aloitetaan mallien vertailu ===")
    logging.info(f"Aikaleima: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Laite: {device}")

    base_model, tokenizer = load_base_model()
    finetuned_model = load_finetuned_model(base_model)

    base_model.eval()
    finetuned_model.eval()

    logging.info("\n=== Aloitetaan testit ===")
    logging.info(f"Testattavia prompteja: {len(test_prompts)}")

    for i, prompt in enumerate(test_prompts, 1):
        logging.info(f"\n=== Testi {i}: {prompt} ===\n")

        # Generoidaan vastaukset
        logging.info("Base model vastaus:")
        base_response = generate_response(base_model, tokenizer, prompt)
        logging.info(base_response)

        logging.info("\nFinetuned model vastaus:")
        finetuned_response = generate_response(finetuned_model, tokenizer, prompt)
        logging.info(finetuned_response)

        # Arvioidaan vastaukset
        logging.info("\nGeminin arvio:")
        evaluation = evaluate_responses(prompt, base_response, finetuned_response)
        logging.info(evaluation)
        logging.info("\n" + "=" * 80)


if __name__ == "__main__":
    main()
