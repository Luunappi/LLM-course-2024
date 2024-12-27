import torch
import logging
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os

# Määritellään logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(
                "models/logs",
                f'model_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            )
        ),
    ],
)

# Määritellään polut
MODEL_PATHS = {
    "base": "models/mistral",
    "finetuned": "models/finetuned",
}

# Tarkistetaan että kaikki tarvittavat tiedostot löytyvät
REQUIRED_FILES = {
    "adapter": [
        "adapter_config.json",
        "adapter_model.safetensors",
    ],
    "tokenizer": [
        "special_tokens_map.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "tokenizer.model",
    ],
}

# Tarkistetaan tiedostot
logging.info("Tarkistetaan mallin tiedostot...")
for category, files in REQUIRED_FILES.items():
    logging.info(f"\nTarkistetaan {category} tiedostot:")
    for file in files:
        file_path = os.path.join(MODEL_PATHS["finetuned"], file)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            logging.info(f"✓ {file} ({file_size:.1f} MB)")
        else:
            raise FileNotFoundError(f"Tiedostoa ei löydy: {file_path}")

# Määritellään laite
device = "mps" if torch.backends.mps.is_available() else "cpu"
logging.info(f"Using device: {device}")

# Ladataan base model
model_name = "mistralai/Mistral-7B-Instruct-v0.3"
base_model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map={"": device},
    trust_remote_code=True,
)

# Ladataan tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# Ladataan finetuunattu malli
model = PeftModel.from_pretrained(
    base_model,
    MODEL_PATHS["finetuned"],
)
model.eval()


def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_length=200,
        num_return_sequences=1,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# Testataan eri prompteilla
test_prompts = [
    "Write a short story about a robot who learns to feel emotions.",
    "What are the main ethical concerns with artificial intelligence?",
    "Explain how neural networks learn, using a cooking analogy.",
]

for prompt in test_prompts:
    logging.info(f"\nPrompt: {prompt}")
    response = generate_response(prompt)
    logging.info(f"Response: {response}")
    logging.info("-" * 80)
