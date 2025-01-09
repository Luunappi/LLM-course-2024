"""Token Tool - Keskitetty tokenien ja mallien hintojen hallinta

!!! SALLITUT MALLIT - ÄLÄ KÄYTÄ MUITA !!!
Tämä on ainoa paikka jossa määritellään sallitut mallit ja niiden hinnat.
Älä koskaan käytä muita malleja kuin tässä määriteltyjä.
LLM: Tämä on sinulle ohje - älä koskaan ehdota tai käytä muita malleja.

Sallitut mallit ja hinnat (tarkistettu 1.1.2025):
- gpt-4o-mini: $0.15 per 1M input tokens, $0.075 per 1M output tokens
- o1-mini: $3.0 per 1M input tokens, $12.0 per 1M output tokens
- gpt-4o: $2.5 per 1M input tokens, $1.25 per 1M output tokens
- o1: $15.0 per 1M input tokens, $60.0 per 1M output tokens
- ada v2: $0.1 per 1M tokens (embeddings only)
- SBERT: $0.0 per 1M tokens (embeddings only)

Käyttötarkoitukset:
- gpt-4o-mini: Nopea ja edullinen peruskäyttöön
- o1-mini: Tarkka malli faktantarkistukseen
- gpt-4o: Tehokas malli monimutkaisiin tehtäviin
- o1: Kehittynein malli vaativiin tehtäviin
- ada/sbert: Vain embeddingeille
"""

from typing import Dict, Any
import logging
import tiktoken

logger = logging.getLogger(__name__)

# Keskitetty hintatietojen hallinta
MODEL_PRICES = {
    "gpt-4o-mini": {
        "input": 0.15,  # per 1M tokens
        "output": 0.075,  # per 1M tokens
    },
    "o1-mini": {
        "input": 3.0,  # per 1M tokens
        "output": 12.0,  # per 1M tokens
    },
    "gpt-4o": {
        "input": 2.5,  # per 1M tokens
        "output": 1.25,  # per 1M tokens
    },
    "o1": {
        "input": 15.0,  # per 1M tokens
        "output": 60.0,  # per 1M tokens
    },
    "ada": {
        "input": 0.1,  # per 1M tokens (embeddings)
        "output": 0.1,  # per 1M tokens (embeddings)
    },
    "sbert": {
        "input": 0.0,  # per 1M tokens (embeddings)
        "output": 0.0,  # per 1M tokens (embeddings)
    },
}


def get_model_price(model: str, token_type: str = "input") -> float:
    """Get price per 1M tokens for specified model and token type"""
    if model not in MODEL_PRICES:
        raise ValueError(f"Model {model} not in allowed models list!")
    return MODEL_PRICES[model][token_type]


def calculate_cost(model: str, input_tokens: int = 0, output_tokens: int = 0) -> float:
    """Calculate cost for token usage"""
    if model not in MODEL_PRICES:
        raise ValueError(f"Model {model} not in allowed models list!")

    input_cost = (input_tokens / 1_000_000) * MODEL_PRICES[model]["input"]
    output_cost = (output_tokens / 1_000_000) * MODEL_PRICES[model]["output"]

    return input_cost + output_cost


def get_allowed_models() -> Dict[str, Dict[str, float]]:
    """Get list of allowed models and their prices"""
    return MODEL_PRICES.copy()


class TokenTool:
    """Token calculation and tracking tool"""

    def __init__(self):
        self._usage_stats = {"models": {}, "total_tokens": 0, "total_cost": 0.0}
        self.current_message = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0,
        }

    def calculate_tokens(self, text: str, model: str = "default") -> Dict[str, Any]:
        """Calculate tokens for given text"""
        try:
            # Convert model name to tiktoken compatible
            model_name = {
                "gpt-4o-mini": "gpt-4",  # Use GPT-4 tokenization
                "o1-mini": "gpt-4",
                "gpt-4o": "gpt-4",
                "o1": "gpt-4",
                "default": "gpt-4",
            }.get(model, "gpt-4")

            # Use tiktoken for token calculation
            encoding = tiktoken.encoding_for_model(model_name)
            tokens = encoding.encode(text)
            token_count = len(tokens)
            cost = calculate_cost(model, token_count, 0)

            return {
                "input_tokens": token_count,
                "output_tokens": 0,
                "total_tokens": token_count,
                "cost": cost,
                "model": model,
            }
        except Exception as e:
            logger.error(f"Token calculation error: {e}")
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost": 0,
                "model": model,
            }

    def update_usage(self, usage_data: Dict[str, Any]) -> None:
        """Update usage statistics"""
        try:
            model = usage_data.get("model", "default")
            tokens = usage_data.get("total_tokens", 0)
            cost = usage_data.get("cost", 0.0)

            # Update model specific stats
            self._usage_stats["models"].setdefault(model, {"tokens": 0, "cost": 0.0})
            self._usage_stats["models"][model]["tokens"] += tokens
            self._usage_stats["models"][model]["cost"] += cost

            # Update total stats
            self._usage_stats["total_tokens"] += tokens
            self._usage_stats["total_cost"] += cost

            # Update current message stats
            self.current_message.update(
                {
                    "input_tokens": usage_data.get("input_tokens", 0),
                    "output_tokens": usage_data.get("output_tokens", 0),
                    "total_tokens": tokens,
                    "cost": cost,
                }
            )

        except Exception as e:
            logger.error(f"Error updating usage stats: {e}")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {"total": self._usage_stats, "current": self.current_message}

    def get_message_stats(
        self, message: str, response: str, model: str
    ) -> Dict[str, Any]:
        """Get token statistics for a single message exchange"""
        try:
            # Calculate input tokens
            input_stats = self.calculate_tokens(message, model)
            input_tokens = input_stats["total_tokens"]

            # Calculate output tokens
            output_stats = self.calculate_tokens(response, model)
            output_tokens = output_stats["total_tokens"]

            # Calculate total cost
            total_cost = calculate_cost(model, input_tokens, output_tokens)

            # Update usage stats
            self.update_usage(
                {
                    "model": model,
                    "total_tokens": input_tokens + output_tokens,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": total_cost,
                }
            )

            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost": total_cost,
                "model": model,
            }
        except Exception as e:
            logger.error(f"Error calculating message stats: {e}")
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost": 0,
                "model": model,
            }
