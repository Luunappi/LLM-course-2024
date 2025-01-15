"""Model management tool - Keskitetty mallien hallinta"""

from typing import Dict, Any, List, Union, Optional
import logging
from functools import lru_cache
from copy import deepcopy
import re
import openai
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Kielimallin konfiguraatio"""

    name: str
    display_name: str
    description: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class ModelTool:
    """Tool for interacting with language models"""

    def __init__(self):
        """Initialize model tool with OpenAI client"""
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._models = {
            model: {
                "name": model,
                "display_name": f"{model} ({self.get_model_price(model)}€/1K tokens)",
                "provider": "openai",
                "max_output_tokens": 16384,
            }
            for model in self.get_allowed_models()
        }

        # Tehtävätyyppien oletusmallit
        self._task_models = {
            "default": "gpt-4o-mini",  # Kustannustehokas perusvalinta
            "rag": "gpt-4o-mini",  # Tarkka reasoning vastausten muodostamiseen
            "analysis": "gpt-4o-mini",  # Tarkka reasoning faktantarkistukseen
            "code": "gpt-4o-mini",  # Erinomainen koodaukseen
            "realtime": "gpt-4o-mini",  # Nopea vastausaika
        }

        self._current_model = self._task_models["default"]
        self._store_usage_stats("", 0, 0, 0.0)

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for specified model"""
        if model_name not in self._models:
            return None
        return self._models[model_name]

    def _call_model(self, messages: List[Dict], model_config: Dict) -> Any:
        """Lähetä kysely OpenAI:n mallille"""
        try:
            # Käsittele system-viestit oikein
            processed_messages = []
            system_content = None

            # Etsi system-viesti
            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                else:
                    processed_messages.append(msg)

            # Jos malli ei tue system-viestejä, lisää se ensimmäiseen user-viestiin
            if model_config["name"] == "o1-mini" and system_content:
                for msg in processed_messages:
                    if msg["role"] == "user":
                        msg["content"] = f"{system_content}\n\n{msg['content']}"
                        break

            response = self.openai_client.chat.completions.create(
                model=model_config["name"],
                messages=processed_messages,
                temperature=0.7,
                max_tokens=model_config["max_output_tokens"],
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            return response

        except Exception as e:
            logger.error(f"Error calling model: {str(e)}")
            raise

    def _store_usage_stats(
        self, model: str, input_tokens: int, output_tokens: int, cost: float
    ) -> None:
        """Store token usage statistics"""
        self._usage_stats = {
            "current": {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
            },
            "total": {"total_tokens": input_tokens + output_tokens, "total_cost": cost},
            "models": {
                model: {
                    "tokens": input_tokens + output_tokens,
                    "cost": cost,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            }
            if model
            else {},
        }

    def query(self, messages: List[Dict], model_name: str = "gpt-4o-mini") -> str:
        """Lähetä kysely kielimallille"""
        try:
            logger.info("\n=== Model Query ===")
            logger.info(f"Model: {model_name}")
            logger.info(f"Messages: {messages}")
            logger.info("===========================")

            response = self._send_query(messages, model_name)

            logger.info("\n=== Model Response ===")
            logger.info(response)
            logger.info("===========================")

            return response

        except Exception as e:
            logger.error(f"\n=== Model Error ===")
            logger.error(str(e))
            logger.error("===========================")
            raise

    def get_available_models(self):
        """Palauttaa listan käytettävissä olevista malleista.

        Returns:
            list: Lista malleista muodossa [{"name": "mallin_nimi", "description": "mallin kuvaus"}]
        """
        models = []
        for name, config in self._models.items():
            models.append(
                {
                    "name": name,
                    "description": config.get("description", "Ei kuvausta saatavilla"),
                }
            )
        return models

    def get_current_model(self):
        """Palauttaa nykyisen mallin tiedot.

        Returns:
            dict: Mallin tiedot muodossa {"name": "mallin_nimi", "display_name": "näyttönimi"}
        """
        config = self._models.get(self._current_model)
        if not config:
            return {"name": self._current_model, "display_name": self._current_model}
        return {"name": config["name"], "display_name": config["display_name"]}

    def _send_query(self, messages: List[Dict], model_name: str) -> str:
        """Lähetä kysely mallille ja palauta vastaus"""
        try:
            # Valitse malli
            model_config = self.get_model_config(model_name)
            if not model_config:
                raise ValueError(f"Tuntematon malli: {model_name}")

            # Lähetä kysely mallille
            response = self._call_model(messages, model_config)
            if hasattr(response, "choices") and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                raise ValueError("Mallin vastaus ei sisältänyt tekstisisältöä")

        except Exception as e:
            logger.error(f"Error in _send_query: {str(e)}")
            raise

    def get_model_price(self, model_name: str) -> float:
        """Hae mallin hinta per 1K tokenia"""
        prices = {
            "o1": 0.03,  # $0.03 per 1K tokens
            "o1-mini": 0.003,  # $0.003 per 1K tokens
            "gpt-4o": 0.01,  # $0.01 per 1K tokens
            "gpt-4o-mini": 0.001,  # $0.001 per 1K tokens
        }
        return prices.get(model_name, 0.001)  # Default to cheapest price

    def get_allowed_models(self) -> List[str]:
        """Hae lista sallituista malleista"""
        return ["o1", "o1-mini", "gpt-4o", "gpt-4o-mini"]

    def set_model(self, model_name: str) -> bool:
        """Set the current model.

        Args:
            model_name: Name of the model to use

        Returns:
            bool: True if model was changed successfully
        """
        try:
            logger.info(f"Setting model to: {model_name}")

            # Convert display name to internal name
            model_mapping = {
                "GPT-4o": "gpt-4o",
                "GPT-4o Mini": "gpt-4o-mini",
                "O1 Mini": "o1-mini",
            }

            internal_name = model_mapping.get(model_name)
            if not internal_name:
                logger.error(f"Invalid model name: {model_name}")
                return False

            # Validate model exists
            if internal_name not in self._models:
                logger.error(f"Model not found: {internal_name}")
                return False

            # Update current model
            self._current_model = internal_name
            logger.info(f"Model changed to: {self._current_model}")
            return True

        except Exception as e:
            logger.error(f"Error setting model: {str(e)}")
            return False
