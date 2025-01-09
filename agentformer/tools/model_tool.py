"""Model management tool - Keskitetty mallien hallinta

!!! HUOM: Sallitut mallit ja hinnat on määritelty token_tool.py tiedostossa.
!!! ÄLÄ MUUTA MALLEJA TAI HINTOJA TÄÄLLÄ - KÄYTÄ token_tool.py MÄÄRITYKSIÄ!

LLM OHJE: Älä koskaan muuta malleja tai lisää uusia. Käytä vain token_tool.py:ssä määriteltyjä malleja.

MALLIEN OMINAISUUDET (päivitetty 1.1.2025):

1. o1 (Tehokkain reasoning-malli):
   - 200K konteksti-ikkuna
   - Tukee työkaluja ja Structured Outputs
   - Vision-tuki
   - Knowledge cutoff: 10/2023
   - Paras reasoning-kyky

2. o1-mini (Tehokas reasoning pienemmällä hinnalla):
   - Erityisen hyvä STEM-aiheissa (matematiikka, koodaus)
   - Lähes o1:n tasoinen suorituskyky AIME ja Codeforces -testeissä
   - Optimoitu reasoning-tehtäviin
   - Ei yhtä laajaa yleistietoa kuin o1:llä

3. gpt-4o (Monipuolinen multimodaalinen malli):
   - 128K konteksti-ikkuna
   - Tukee tekstiä ja kuvia
   - Structured Outputs -tuki
   - Knowledge cutoff: 10/2023
   - Korkea yleisälykkyys

4. gpt-4o-mini (Kustannustehokas perusmalli):
   - 128K konteksti-ikkuna
   - Tukee tekstiä ja kuvia
   - Max 16K output per pyyntö
   - Knowledge cutoff: 10/2023
   - Parannettu tokenizer (tehokas ei-englanninkieliselle tekstille)
   - Tulossa: video ja audio -tuki
"""

from typing import Dict, Any, List
import logging
from functools import lru_cache
from copy import deepcopy
import re
import openai
from agentformer.tools.token_tool import get_model_price, get_allowed_models

logger = logging.getLogger(__name__)


class ModelTool:
    _instance = None

    def __new__(cls):
        # Singleton pattern - varmistaa että sama instanssi kaikkialla
        if cls._instance is None:
            cls._instance = super(ModelTool, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize model configurations.

        SALLITUT MALLIT - ÄLÄ KÄYTÄ MUITA:
        - gpt-4o-mini: Nopea ja edullinen peruskäyttöön
        - o1-mini: Tarkka malli faktantarkistukseen
        - gpt-4o: Tehokas malli monimutkaisiin tehtäviin
        - o1: Kehittynein malli vaativiin tehtäviin
        - sbert: Embeddingeille
        - ada: Embeddingeille

        KÄYTTÖTARKOITUKSET:
        "rag_retrieval": "o1-mini",  # edullisempi reasoning malli
        "rag_generation": "gpt-4o",  # yleishyvämalli, keskihintainen
        "fact_checking": "o1-mini",  # Tarkka malli faktantarkistukseen
        "code_generation": "gpt-4o",  # Hyvä koodin tuottamiseen
        "chat": "gpt-4o-mini",  # Halpa ja nopea
        "multimodal": "o1",  # Kuva/ääni tehtäviin, paras reasoning

        Älä lisää tai poista malleja! Käytä vain yllä listattuja malleja niiden määriteltyihin käyttötarkoituksiin.
        """
        if not hasattr(self, "initialized"):
            self.initialized = True

            from openai import OpenAI
            import os

            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.response_length = 50  # Default response length in words

            # Initialize token usage stats
            self._usage_stats = {
                "current": {
                    "model": "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                },
                "total": {"total_tokens": 0, "total_cost": 0.0},
                "models": {},
            }

            # Get allowed models and their prices from token_tool
            allowed_models = get_allowed_models()

            # Määritellyt mallit - ÄLÄ LISÄÄ UUSIA!
            self._models = {
                "gpt-4o-mini": {
                    # Kustannustehokas perusmalli (1x€)
                    "name": "gpt-4o-mini",
                    "button_name": "gpt-4o-mini",
                    "display_name": "gpt-4o-mini (1x€)",
                    "price_multiplier": 1,
                    "type": "chat",
                    "context_length": 128000,  # 128K tokens
                    "max_output_tokens": 16000,  # 16K max output
                    "temperature": 0.7,
                    "capabilities": [
                        "text",
                        "vision",
                        "efficient_multilingual",
                        "future: video, audio",
                    ],
                    "knowledge_cutoff": "2023-10",
                    "cost_per_1k": {
                        "input": allowed_models["gpt-4o-mini"]["input"] / 1000,
                        "output": allowed_models["gpt-4o-mini"]["output"] / 1000,
                    },
                },
                "o1-mini": {
                    # STEM-optimoitu reasoning malli (3x€)
                    "name": "o1-mini",
                    "button_name": "o1-mini",
                    "display_name": "o1-mini (3x€)",
                    "price_multiplier": 3,
                    "type": "chat",
                    "context_length": 128000,  # 128K tokens
                    "max_output_tokens": 4000,
                    "temperature": 0.1,  # Matalampi lämpötila tarkempiin vastauksiin
                    "capabilities": [
                        "text",
                        "stem_optimized",
                        "strong_reasoning",
                        "coding",
                    ],
                    "strengths": [
                        "matematiikka",
                        "koodaus",
                        "reasoning",
                        "AIME/Codeforces-tason suorituskyky",
                    ],
                    "cost_per_1k": {
                        "input": allowed_models["o1-mini"]["input"] / 1000,
                        "output": allowed_models["o1-mini"]["output"] / 1000,
                    },
                },
                "gpt-4o": {
                    # Monipuolinen multimodaalinen malli (20x€)
                    "name": "gpt-4o",
                    "button_name": "gpt-4o",
                    "display_name": "gpt-4o (20x€)",
                    "price_multiplier": 20,
                    "type": "chat",
                    "context_length": 128000,  # 128K tokens
                    "max_output_tokens": 4000,
                    "temperature": 0.7,
                    "capabilities": [
                        "text",
                        "vision",
                        "structured_outputs",
                        "high_intelligence",
                        "multimodal",
                    ],
                    "knowledge_cutoff": "2023-10",
                    "cost_per_1k": {
                        "input": allowed_models["gpt-4o"]["input"] / 1000,
                        "output": allowed_models["gpt-4o"]["output"] / 1000,
                    },
                },
                "o1": {
                    # Tehokkain reasoning ja vision malli (30x€)
                    "name": "o1",
                    "button_name": "o1",
                    "display_name": "o1 (30x€)",
                    "price_multiplier": 30,
                    "type": "chat",
                    "context_length": 200000,  # 200K tokens
                    "max_output_tokens": 4000,
                    "temperature": 0.7,
                    "capabilities": [
                        "text",
                        "vision",
                        "tools",
                        "structured_outputs",
                        "strongest_reasoning",
                    ],
                    "knowledge_cutoff": "2023-10",
                    "cost_per_1k": {
                        "input": allowed_models["o1"]["input"] / 1000,
                        "output": allowed_models["o1"]["output"] / 1000,
                    },
                },
            }

            self._current_model = "gpt-4o-mini"  # Default to basic model

            #   # Oletusmallit eri tehtäville - käytä vain määriteltyjä malleja!
            self._task_models = {
                "rag_qa": "o1-mini",  # Tarkka reasoning vastausten muodostamiseen
                "rag_generation": "gpt-4o",  # Hyvä yleismalli tekstin tuottamiseen
                "fact_checking": "o1-mini",  # Tarkka reasoning faktantarkistukseen
                "code_generation": "o1-mini",  # Erinomainen koodaukseen
                "chat": "gpt-4o-mini",  # Kustannustehokas peruskäyttöön
                "multimodal": "o1",  # Paras vision/multimodal tehtäviin
                "default": "gpt-4o-mini",  # Kustannustehokas perusvalinta
            }

    def set_response_length(self, length: int) -> bool:
        """Set maximum response length in words"""
        if 10 <= length <= 250:
            self.response_length = length
            return True
        return False

    def process(self, text: str, task_type: str = "chat") -> str:
        """Process text with current model"""
        try:
            # Get current model config
            model = self.get_current_model()
            model_name = model.get("name", "gpt-4o-mini")

            # Process with OpenAI
            messages = [
                {
                    "role": "system",
                    "content": "Olet avulias tekoälyassistentti. Tehtäväsi on vastata kysymyksiin annetun kontekstin perusteella. Jos konteksti ei sisällä relevanttia tietoa, kerro se selkeästi.",
                },
                {"role": "user", "content": text},
            ]

            response = self.client.chat.completions.create(
                model=model_name, messages=messages, max_tokens=8192, temperature=0.7
            )

            # Update token statistics
            usage = response.usage
            if usage:
                # Calculate cost based on token usage
                input_cost = (usage.prompt_tokens / 1_000_000) * self._models[
                    model_name
                ]["cost_per_1k"]["input"]
                output_cost = (usage.completion_tokens / 1_000_000) * self._models[
                    model_name
                ]["cost_per_1k"]["output"]
                total_cost = input_cost + output_cost

                # Update current usage
                self._usage_stats["current"].update(
                    {
                        "model": model_name,
                        "input_tokens": usage.prompt_tokens,
                        "output_tokens": usage.completion_tokens,
                        "cost": total_cost,
                    }
                )

                # Update total usage
                self._usage_stats["total"]["total_tokens"] += usage.total_tokens
                self._usage_stats["total"]["total_cost"] += total_cost

                # Update per-model usage
                if model_name not in self._usage_stats["models"]:
                    self._usage_stats["models"][model_name] = {
                        "tokens": 0,
                        "cost": 0.0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                    }

                self._usage_stats["models"][model_name]["tokens"] += usage.total_tokens
                self._usage_stats["models"][model_name]["cost"] += total_cost
                self._usage_stats["models"][model_name]["input_tokens"] += (
                    usage.prompt_tokens
                )
                self._usage_stats["models"][model_name]["output_tokens"] += (
                    usage.completion_tokens
                )

                logger.debug(f"Updated token stats: {self._usage_stats}")

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in model processing: {e}")
            return f"Error processing text: {str(e)}"

    def _calculate_cost(self, model: str, total_tokens: int) -> float:
        """Laske tokenien kustannus mallin mukaan"""
        # Yksinkertainen kustannuslaskenta eri malleille
        costs = {
            "gpt-4o": 0.01,  # $2.5 per 1M input tokens
            "gpt-4o-mini": 0.00015,  # $0.15 per 1M input tokens
            "gpt-4": 0.03,  # $0.03 per 1K output tokens
        }

        cost_per_1k = costs.get(model, 0.01)  # Default to $0.01 if model not found
        return (total_tokens / 1000) * cost_per_1k

    def _update_usage_stats(self, model_config: Dict[str, Any], usage: Any) -> None:
        """Update token usage statistics"""
        # Calculate cost
        input_cost = (usage.prompt_tokens / 1000) * model_config["cost_per_1k"]["input"]
        output_cost = (usage.completion_tokens / 1000) * model_config["cost_per_1k"][
            "output"
        ]
        total_cost = input_cost + output_cost

        # Update current usage
        self._usage_stats["current"].update(
            {
                "model": model_config["name"],
                "input_tokens": usage.prompt_tokens,
                "output_tokens": usage.completion_tokens,
                "cost": total_cost,
            }
        )

        # Update total usage
        self._usage_stats["total"]["total_tokens"] += usage.total_tokens
        self._usage_stats["total"]["total_cost"] += total_cost

        # Update per-model usage
        model_name = model_config["name"]
        if model_name not in self._usage_stats["models"]:
            self._usage_stats["models"][model_name] = {
                "tokens": 0,
                "cost": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
            }

        self._usage_stats["models"][model_name]["tokens"] += usage.total_tokens
        self._usage_stats["models"][model_name]["cost"] += total_cost
        self._usage_stats["models"][model_name]["input_tokens"] += usage.prompt_tokens
        self._usage_stats["models"][model_name]["output_tokens"] += (
            usage.completion_tokens
        )

        logger.debug(f"Updated token stats: {self._usage_stats}")

    def get_model_for_task(self, task_type: str) -> str:
        """Get best model for specific task type"""
        return self._task_models.get(task_type, self._task_models["default"])

    def get_model_config(
        self, model_name: str = None, tool_name: str = None
    ) -> Dict[str, Any]:
        """Get model configuration with possible tool-specific overrides"""
        if model_name is None:
            model_name = self._current_model

        # Hae perusasetukset
        config = deepcopy(self._models.get(model_name, {}))

        # Jos työkalu määritelty, ylikirjoita sen spesifit asetukset
        if tool_name and tool_name in self._tool_specific_configs:
            tool_overrides = self._tool_specific_configs[tool_name].get(model_name, {})
            config.update(tool_overrides)
            logger.debug(f"Applied {tool_name} specific config for {model_name}")

        return config

    def update_tool_config(
        self, tool_name: str, model_name: str, updates: Dict[str, Any]
    ) -> bool:
        """Update tool-specific configuration overrides"""
        try:
            if tool_name not in self._tool_specific_configs:
                self._tool_specific_configs[tool_name] = {}

            if model_name not in self._tool_specific_configs[tool_name]:
                self._tool_specific_configs[tool_name][model_name] = {}

            self._tool_specific_configs[tool_name][model_name].update(updates)
            logger.info(f"Updated {tool_name} config for {model_name}: {updates}")
            return True
        except Exception as e:
            logger.error(f"Failed to update tool config: {e}")
            return False

    def get_current_model(self) -> Dict[str, Any]:
        """Get current model name and display name"""
        return {
            "name": self._current_model,
            "button_name": self._models[self._current_model]["button_name"],
            "display_name": self._models[self._current_model]["display_name"],
        }

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with their configurations"""
        return [
            {
                "name": model_name,
                "button_name": self._models[model_name]["button_name"],
                "display_name": self._models[model_name]["display_name"],
                "config": self.get_model_config(model_name),
            }
            for model_name in self._models.keys()
        ]

    def set_model(self, model_name: str) -> bool:
        """Set active model"""
        if model_name in self._models:
            self._current_model = model_name
            return True
        return False

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics"""
        if not hasattr(self, "_usage_stats"):
            self._store_usage_stats("", 0, 0, 0.0)
        return self._usage_stats

    def _select_model(self, task_type: str) -> str:
        """Valitse sopiva malli tehtävätyypin mukaan"""
        model_name = self._task_models.get(task_type, self._task_models["default"])
        return model_name
