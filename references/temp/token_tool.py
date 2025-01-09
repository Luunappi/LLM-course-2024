"""Token calculation and tracking tool"""

from typing import Dict, Any
import logging
import tiktoken

logger = logging.getLogger(__name__)


class TokenTool:
    def __init__(self):
        self._usage_stats = {"models": {}, "total_tokens": 0, "total_cost": 0.0}

    def calculate_tokens(self, text: str, model: str = "default") -> Dict[str, Any]:
        """Calculate tokens for given text"""
        try:
            # Muunna mallinimi tiktoken-yhteensopivaksi
            model_name = {
                "gpt-4o-mini": "gpt-4",  # Käytä GPT-4 tokenisaatiota
                "o1-mini": "gpt-4",
                "gpt-4o": "gpt-4",
                "o1": "gpt-4",
                "default": "gpt-4",
            }.get(model, "gpt-4")

            # Käytä tiktoken-kirjastoa token-laskentaan
            encoding = tiktoken.encoding_for_model(model_name)
            tokens = encoding.encode(text)
            token_count = len(tokens)

            cost = self._calculate_cost(token_count, model)

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

            self._usage_stats["models"].setdefault(model, {"tokens": 0, "cost": 0.0})
            self._usage_stats["models"][model]["tokens"] += tokens
            self._usage_stats["models"][model]["cost"] += cost
            self._usage_stats["total_tokens"] += tokens
            self._usage_stats["total_cost"] += cost
        except Exception as e:
            logger.error(f"Error updating usage stats: {e}")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return self._usage_stats

    def _calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost based on tokens and model"""
        # Tässä oikea hinnoittelumalli eri malleille
        rates = {"gpt-4": 0.03, "gpt-3.5-turbo": 0.002, "default": 0.002}
        rate = rates.get(model, rates["default"])
        return (tokens / 1000) * rate

    def update_pricing(self, rates: Dict[str, float]) -> None:
        """Update pricing rates"""
        self._rates = rates

    def get_message_stats(
        self, message: str, response: str, model: str
    ) -> Dict[str, Any]:
        """Get token statistics for a single message exchange"""
        try:
            # Laske input tokenit
            input_stats = self.calculate_tokens(message, model)
            input_tokens = input_stats["total_tokens"]

            # Laske output tokenit
            output_stats = self.calculate_tokens(response, model)
            output_tokens = output_stats["total_tokens"]

            # Laske kokonaistokenit ja kustannus
            total_tokens = input_tokens + output_tokens
            cost = self._calculate_cost(total_tokens, model)

            # Päivitä käyttötilastot
            self.update_usage(
                {"model": model, "total_tokens": total_tokens, "cost": cost}
            )

            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
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
