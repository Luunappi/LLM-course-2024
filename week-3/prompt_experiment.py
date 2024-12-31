import time
import os
import requests
import openai
from dotenv import load_dotenv

def ask_model(model_name, prompt):
    """
    Query either local Mistral model or OpenAI API
    """
    if model_name == "mistral_local":
        try:
            response = requests.post('http://localhost:11434/api/generate', 
                json={
                    'model': 'mistral',
                    'prompt': prompt,
                    'stream': False
                })
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            return f"[Mistral error]: {str(e)}"

    elif model_name == "openai_o1-mini":
        load_dotenv()
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=128,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI error]: {str(e)}"

    else:
        return "[Unknown model]: No valid call made."

def main():
    # Define two prompts
    prompt_fi = "Voisitko ystävällisesti ehdottaa tapoja, joilla keskituloinen opiskelija voi aloittaa sijoittamisen pienellä riskillä?"
    prompt_en = "Give me low-risk investment tips for a college student with moderate income."

    # New pair of models
    models = ["mistral_local", "openai_o1-mini"]
    
    # Ask each model both prompts
    for model in models:
        response_fi = ask_model(model, prompt_fi)
        response_en = ask_model(model, prompt_en)
        print(f"\nFI Answer from {model}:\n{response_fi}")
        print(f"\nEN Answer from {model}:\n{response_en}")
        print("-" * 80)

if __name__ == "__main__":
    main() 