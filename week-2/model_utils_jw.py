from typing import List, Optional, Union, Dict, Tuple
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
import requests


class LLMInterface:
    """Base interface for language models"""

    def generate_content(self, messages: Union[str, List[str]]) -> Tuple[str, Dict]:
        """Returns tuple of (response_text, metrics)"""
        raise NotImplementedError


class GeminiModel(LLMInterface):
    """Wrapper for Gemini API"""

    def __init__(self, model_name: str = "gemini-1.5-pro"):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Please set GOOGLE_API_KEY in .env file")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        self.current_language = "en"

        self.system_prompts = {
            "en": "You are a helpful AI assistant.",
            "fi": "Olet avulias tekoälyassistentti.",
        }

    def set_language(self, language: str):
        if language not in self.system_prompts:
            raise ValueError(f"Unsupported language: {language}")
        self.current_language = language

    def generate_content(self, messages: Union[str, List[str]]) -> Tuple[str, Dict]:
        start_time = time.time()

        if isinstance(messages, list):
            text = " ".join(messages)
        else:
            text = messages

        prompt = f"{self.system_prompts[self.current_language]}\n\nUser: {text}"
        response = self.model.generate_content(prompt)

        duration = time.time() - start_time
        metrics = {
            "model_name": self.model_name,
            "duration": duration,
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(response.text.split()),
            "total_tokens": len(prompt.split()) + len(response.text.split()),
            "cost": 0.0001 * (len(prompt.split()) + len(response.text.split())),
        }

        return response.text, metrics


# Mistral implementation (commented out but ready to use)
"""
class MistralModel(LLMInterface):
    def __init__(self):
        self.current_language = "fi"
        self.model_name = "mistral-fi"
        
        # System prompts for different languages
        self.system_prompts = {
            "en": "You are a helpful AI assistant.",
            "fi": "Olet suomenkielinen tekoälyassistentti. Vastaat kysymyksiin selkeällä suomen kielellä."
        }
        
    def set_language(self, language: str):
        if language not in self.system_prompts:
            raise ValueError(f"Unsupported language: {language}")
        self.current_language = language
        
    def generate_content(self, messages: Union[str, List[str]]) -> Tuple[str, Dict]:
        start_time = time.time()
        
        if isinstance(messages, list):
            text = " ".join(messages)
        else:
            text = messages
            
        prompt = f"{self.system_prompts[self.current_language]}\n\nUser: {text}"
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model_name, "prompt": prompt},
                timeout=30
            )
            response.raise_for_status()
            response_text = response.json()["response"]
            
            duration = time.time() - start_time
            metrics = {
                "model_name": self.model_name,
                "duration": duration,
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split()),
                "cost": 0.0  # Local model, no cost
            }
            
            return response_text, metrics
            
        except Exception as e:
            raise Exception(f"Error calling Mistral API: {str(e)}")
"""


# Factory function to get the right model (commented out but ready to use)
"""
def get_model(model_type: str) -> LLMInterface:
    if model_type.lower() == "gemini":
        return GeminiModel()
    elif model_type.lower() == "mistral":
        return MistralModel()
    else:
        raise ValueError(f"Unknown model type: {model_type}")
"""
