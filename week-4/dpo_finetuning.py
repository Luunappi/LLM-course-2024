# Tarvittavat asennukset:
# pip install datasets transformers torch trl peft bitsandbytes accelerate
# pip install --upgrade huggingface-hub
# pip install wandb  # Jos haluat seurata trainingia

import torch
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, prepare_model_for_kbit_training
from huggingface_hub import login
import json

# Ladataan ympäristömuuttujat
load_dotenv()

# Määritellään logging ennen muita importteja
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'dpo_training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
    ],
)

# Kirjaudutaan Hugging Faceen
try:
    logging.info("Kirjaudutaan Hugging Faceen...")
    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        raise ValueError("HUGGINGFACE_TOKEN puuttuu .env tiedostosta")
    login(token=token)
    logging.info("Kirjautuminen onnistui")
except Exception as e:
    logging.error(f"Hugging Face kirjautuminen epäonnistui: {e}")
    logging.error("Varmista että olet kirjautunut: huggingface-cli login")
    raise

# Yritetään ladata trl ja logata mahdolliset virheet
try:
    logging.info("Ladataan TRL-kirjasto...")
    from trl import SFTTrainer

    logging.info("TRL-kirjasto ladattu onnistuneesti")
except Exception as e:
    logging.error(f"TRL-kirjaston lataus epäonnistui: {e}")
    logging.error("Varmista että setuptools on asennettu: pip install setuptools")
    raise


def print_gpu_memory():
    """Tulostaa GPU:n muistinkäytön jos saatavilla."""
    if torch.cuda.is_available():
        logging.info(
            f"GPU Memory: {torch.cuda.memory_allocated()/1024**2:.2f}MB / {torch.cuda.memory_reserved()/1024**2:.2f}MB"
        )


def inspect_dataset(dataset, num_examples=2):
    """Tulostaa esimerkkejä datasetistä."""
    logging.info(f"\nDataset size: {len(dataset)}")
    logging.info("\nEsimerkkejä datasetistä:")
    for i in range(min(num_examples, len(dataset))):
        example = dataset[i]
        logging.info(f"\nEsimerkki {i+1}:")
        for key, value in example.items():
            if isinstance(value, str):
                logging.info(f"{key}: {value[:200]}...")


def log_model_info(model):
    """Tulostaa mallin tietoja."""
    logging.info(f"\nMalli: {model.config._name_or_path}")
    logging.info(f"Parametrien määrä: {model.num_parameters():,}")
    logging.info(f"Laite: {next(model.parameters()).device}")


# Määritellään laite (CPU M4 Macilla)
device = "mps" if torch.backends.mps.is_available() else "cpu"
logging.info(f"Using device: {device}")

# Konfiguroidaan kvantisaatio M4:lle sopivaksi
logging.info("\nKonfiguroidaan kvantisaatio...")
# Käytetään float16 tarkkuutta MPS:llä
torch_dtype = torch.float16  # MPS tukee vain float16

# Määritellään selkeät polut malleille
MODEL_PATHS = {
    "base": "models/mistral",  # Base mallin välimuisti
    "checkpoints": "models/checkpoints",  # Training checkpointit
    "final": "models/finetuned",  # Lopullinen finetuunattu malli
    "logs": "models/logs",  # Training logit
}

# Luodaan tarvittavat kansiot
for path in MODEL_PATHS.values():
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Luotiin kansio: {path}")

# Määritellään logging uudestaan oikeaan kansioon
log_file = os.path.join(
    MODEL_PATHS["logs"], f'dpo_training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)
logging.getLogger().handlers = []  # Poistetaan vanhat handlerit
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file),
    ],
)

# Ladataan aiemmin käytetty malli
logging.info("\nLadataan malli...")
model_name = "mistralai/Mistral-7B-Instruct-v0.3"  # Uusin Mistral versio
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch_dtype,
    device_map={"": device},
    trust_remote_code=True,
    cache_dir=MODEL_PATHS["base"],  # Määritellään latauskansio
)
model = prepare_model_for_kbit_training(model)
log_model_info(model)

# Ladataan tokenizer
logging.info("\nLadataan tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# Ladataan DeepSpeed Chat datasetti
logging.info("\nLadataan datasetti...")
dataset = load_dataset("Anthropic/hh-rlhf", split="train[:1000]")
inspect_dataset(dataset)

# Muokataan data DPO formaattiin
logging.info("\nMuokataan data DPO formaattiin...")


def format_dataset(example):
    return {
        "prompt": example["chosen"],
        "response": example["chosen"],
    }


dataset = dataset.map(format_dataset)

# Määritellään LoRA konfiguraatio
peft_config = LoraConfig(
    lora_alpha=16,
    lora_dropout=0.1,
    r=8,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
)

# Lisätään muistin hallintaa
logging.info("\nTyhjennnetään GPU muisti...")
torch.cuda.empty_cache()
print_gpu_memory()
model.config.use_cache = False

# Muokataan training argumentteja
training_args = TrainingArguments(
    output_dir=MODEL_PATHS["checkpoints"],
    num_train_epochs=1,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    gradient_checkpointing=True,
    optim="adamw_torch",
    save_steps=5,  # Tallennetaan useammin
    save_total_limit=3,  # Säilytetään 3 viimeisintä checkpointtia
    logging_steps=10,
    learning_rate=5e-5,
    max_grad_norm=0.3,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    evaluation_strategy="no",
    report_to="none",
)

# Jaetaan datasetti training ja eval osiin
dataset_dict = dataset.train_test_split(test_size=0.1)
train_dataset = dataset_dict["train"]
eval_dataset = dataset_dict["test"]

# Luodaan trainer
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,  # Lisätään evaluaatiodatasetti
    tokenizer=tokenizer,
    peft_config=peft_config,
    max_seq_length=1024,
    dataset_text_field="prompt",
    formatting_func=lambda x: x["prompt"],
)

# Käynnistetään training
logging.info("\nAloitetaan training...")
try:
    trainer.train()
except Exception as e:
    logging.error(f"Training failed with error: {e}")
    if hasattr(trainer, "model"):
        logging.info("Tallennetaan checkpoint...")
        trainer.save_model("checkpoint-error")

# Tallennetaan malli
logging.info("\nTallennetaan malli...")
final_model_path = MODEL_PATHS["final"]
trainer.save_model(final_model_path)
logging.info(f"Malli tallennettu hakemistoon: {final_model_path}")

# Tallennetaan mallin metadata
metadata = {
    "training_date": datetime.now().isoformat(),
    "base_model": model_name,
    "dataset": "Anthropic/hh-rlhf",
    "dataset_size": len(dataset),
    "training_args": training_args.to_dict(),
}

metadata_path = os.path.join(final_model_path, "training_metadata.json")
with open(metadata_path, "w") as f:
    json.dump(metadata, f, indent=2)
logging.info(f"Metadata tallennettu: {metadata_path}")

# Testataan mallia
logging.info("\nTestataan mallia...")


def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    model.config.use_cache = True
    model.eval()
    outputs = model.generate(
        **inputs,
        max_length=200,
        num_return_sequences=1,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    model.config.use_cache = False
    model.train()
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# Testataan eri prompteilla
test_prompts = [
    "Write a short story about a robot who learns to feel emotions.",
    "What are the main ethical concerns with artificial intelligence?",
    "Explain how neural networks learn, using a cooking analogy.",
]

for prompt in test_prompts:
    response = generate_response(prompt)
    logging.info(f"\nPrompt: {prompt}")
    logging.info(f"Response: {response}")
    logging.info("-" * 80)  # Erottaja vastausten väliin
