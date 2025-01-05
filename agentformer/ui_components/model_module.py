"""
Model Management Module

Hallinnoi LLM-malleja ja niiden käyttöä:
- Mallien konfiguraatio ja valinta
- API-kutsujen käsittely
- Vastausten generointi
"""

import logging
from typing import Dict, Any, Optional
import openai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class Models:
    """Handles model selection and management"""

    def __init__(self):
        self.available_models = {
            "gpt-4o": {"name": "gpt-4", "max_tokens": 4000, "temperature": 0.7},
            "gpt-4o-mini": {
                "name": "gpt-3.5-turbo",
                "max_tokens": 2048,
                "temperature": 0.7,
            },
            "o1-mini": {
                "name": "gpt-3.5-turbo-16k",
                "max_tokens": 8000,
                "temperature": 0.7,
            },
        }
        self.current_model = "gpt-4o"  # Default model
        logger.info(f"Models initialized with default model: {self.current_model}")

    def set_model(self, model_name: str) -> bool:
        """
        Switch to a different model
        Returns True if successful, False otherwise
        """
        try:
            if model_name not in self.available_models:
                logger.error(f"Unknown model: {model_name}")
                return False

            self.current_model = model_name
            logger.info(f"Switched to model: {model_name}")
            return True

        except Exception as e:
            logger.error(f"Error switching model: {e}")
            return False

    def get_current_model(self) -> str:
        """Get current model name"""
        return self.current_model

    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using current model"""
        try:
            model_config = self.available_models[self.current_model]

            # Rakenna viestit
            messages = []

            # Lisää järjestelmäprompt
            messages.append(
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Maintain context of the conversation.",
                }
            )

            # Lisää konteksti jos on
            if context:
                messages.append({"role": "system", "content": context})

            # Hae aiemmat viestit muistista
            if hasattr(self, "conversation_history"):
                messages.extend(self.conversation_history)
            else:
                self.conversation_history = []

            # Lisää uusi viesti
            messages.append({"role": "user", "content": prompt})

            # Käytä OpenAI API:a
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=model_config["name"],
                messages=messages,
                temperature=model_config["temperature"],
                max_tokens=model_config["max_tokens"],
            )

            # Tallenna viestit muistiin
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )

            # Rajoita historian kokoa (esim. viimeiset 10 viestiä)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            # Palauta vastaus
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: {str(e)}"

    def get_model_info(self, model_name: Optional[str] = None) -> dict:
        """Get model configuration"""
        if model_name is None:
            model_name = self.current_model

        return self.available_models.get(model_name, {})

    def get_available_models(self) -> Dict:
        """Get all available models and their configurations"""
        return {"gpt-4o-mini": self.current_model}

    def get_model_for_task(self, task_type: str) -> str:
        """Get recommended model for specific task type"""
        return "gpt-4o-mini"

    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
