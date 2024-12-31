from model_utils import get_model
import configparser
from pathlib import Path
import argparse
import time
from typing import Dict


def load_system_prompt(config_path: Path) -> str:
    """Lataa järjestelmäkehotteen config-tiedostosta"""
    # Yrittää lukea TEMPLATES-osiosta TOPIC ja NUMBER arvot
    # Jos ei onnistu, palauttaa oletuskehotteen
    prompts = configparser.ConfigParser()
    try:
        prompts.read(config_path)
        return f'Summarize the following text about {prompts.get("TEMPLATES", "TOPIC")} in {prompts.get("TEMPLATES", "NUMBER")} bullet points:'
    except (configparser.NoSectionError, configparser.NoOptionError):
        return "You are a helpful and concise assistant. Please provide clear and informative responses."


def format_metrics(model_name: str, is_local: bool, metrics: Dict) -> str:
    """Muotoilee vastauksen metriikat luettavaan muotoon:
    - Mallin nimi ja suorituspaikka (paikallinen/pilvi)
    - Suoritusaika
    - Käytetyt tokenit
    - Kustannus"""
    location = "locally" if is_local else "in cloud"
    return (
        f"\n{'='*50}\n"
        f"Model: {model_name} (running {location})\n"
        f"Time: {metrics['duration']:.2f} seconds\n"
        f"Tokens: {metrics['prompt_tokens']} prompt + {metrics['completion_tokens']} completion = {metrics['total_tokens']} total\n"
        f"Cost: ${metrics['cost']:.6f}\n"
        f"{'='*50}"
    )


def main():
    parser = argparse.ArgumentParser(description="LLM Prompting Script")
    parser.add_argument(
        "--model",
        default="gemini",
        choices=["gemini", "mistral"],
        help="Which model to use (default: gemini)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "prompts.env",
        help="Path to config file",
    )
    args = parser.parse_args()

    # Initialize model
    model = get_model(args.model)

    # Load system prompt
    system_prompt = load_system_prompt(args.config)

    print("Chat initialized. Type 'quit' to exit.")
    print(f"Using model: {args.model}")
    print(f"System prompt: {system_prompt}\n")

    # Simple chat loop
    messages = [system_prompt]
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["quit", "exit"]:
            break

        messages.append(user_input)
        response, metrics = model.generate_content(messages)

        print(f"\nAssistant: {response}")
        print(format_metrics(args.model, model.is_local(), metrics))
        print()


if __name__ == "__main__":
    main()
