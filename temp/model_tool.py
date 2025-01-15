"""Model management tool - Keskitetty mallien hallinta"""

from typing import Dict, Any, List
import logging
from functools import lru_cache
from copy import deepcopy

logger = logging.getLogger(__name__)


class ModelTool:
    _instance = None

    def __new__(cls):
        # Singleton pattern - varmistaa että sama instanssi kaikkialla
        if cls._instance is None:
            cls._instance = super(ModelTool, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            # Alustetaan vain kerran
            self.initialized = True
            self._models = {
                "gpt-4o-mini": {
                    # Nopea ja edullinen malli peruskäyttöön (1x€)
                    # - Hyvä yleiskäyttöinen malli yksinkertaisiin tehtäviin
                    # - Nopea vasteaika, matala kustannus
                    # - Soveltuu: chat, perustason tekstintuotanto, yksinkertaiset analyysit
                    # - Ei: monimutkaiset päättelyt, multimodaalisuus
                    #
                    # max_tokens: 8192 (n. 6000 sanaa)
                    # - Sallitaan pitkät vastaukset koska malli on edullinen
                    # - Voidaan säätää välillä 1-8192 kustannusten mukaan
                    "name": "gpt-4o-mini",
                    "button_name": "gpt-4o-mini",
                    "display_name": "gpt-4o-mini (1x€)",
                    "price_multiplier": 1,
                    "type": "chat",
                    "context_length": 8192,
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "cost_per_1k": {
                        "input": 0.5,
                        "output": 1.5,
                    },
                },
                "o1-mini": {
                    # Tarkka ja nopea malli faktantarkistukseen (3x€)
                    # - Optimoitu tarkkuuteen matalalla lämpötilalla
                    # - Nopea suorituskyky, keskitason kustannus
                    # - Soveltuu: faktantarkistus, tiedon validointi, täsmälliset vastaukset
                    # - Ei: luova sisältö, vapaamuotoinen keskustelu
                    #
                    # max_tokens: 2048 (n. 1500 sanaa)
                    # - Keskipitkät vastaukset faktantarkistukseen
                    # - Voidaan säätää välillä 1-4096 tarpeen mukaan
                    "name": "o1-mini",
                    "button_name": "o1-mini",
                    "display_name": "o1-mini (3x€)",
                    "price_multiplier": 3,
                    "type": "chat",
                    "context_length": 8192,
                    "temperature": 0.1,
                    "max_tokens": 2048,
                    "cost_per_1k": {
                        "input": 2.0,
                        "output": 6.0,
                    },
                },
                "gpt-4o": {
                    # Tehokas malli monimutkaisiin tehtäviin (20x€)
                    # - Erinomainen reasoning-kyky ja kontekstin ymmärrys
                    # - Hitaampi, korkeampi kustannus
                    # - Soveltuu: monimutkainen päättely, koodaus, analyysit
                    # - Ei: kun tarvitaan nopeaa vasteaikaa tai kustannustehokkuutta
                    #
                    # max_tokens: 1024 (n. 750 sanaa)
                    # - Rajoitettu vastausten pituus kustannusten hallitsemiseksi
                    # - Voidaan säätää välillä 1-32768 jos pidempiä vastauksia tarvitaan
                    "name": "gpt-4o",
                    "button_name": "gpt-4o",
                    "display_name": "gpt-4o (20x€)",
                    "price_multiplier": 20,
                    "type": "chat",
                    "context_length": 32768,
                    "temperature": 0.7,
                    "max_tokens": 1024,
                    "cost_per_1k": {
                        "input": 15.0,
                        "output": 40.0,
                    },
                },
                "o1": {
                    # Kehittynein malli vaativiin tehtäviin (30x€)
                    # - Tukee multimodaalista sisältöä (kuvat, ääni)
                    # - Paras reasoning-kyky, korkein kustannus
                    # - Soveltuu: multimodaaliset tehtävät, monimutkaiset analyysit
                    # - Ei: yksinkertaiset tehtävät, kustannustehokkuutta vaativat käyttötapaukset
                    #
                    # max_tokens: 512 (n. 400 sanaa)
                    # - Tiukasti rajoitettu vastausten pituus korkeiden kustannusten vuoksi
                    # - Voidaan säätää välillä 1-16384 jos pidempiä vastauksia tarvitaan
                    "name": "o1",
                    "button_name": "o1",
                    "display_name": "o1 (30x€)",
                    "price_multiplier": 30,
                    "type": "chat",
                    "context_length": 16384,
                    "temperature": 0.7,
                    "max_tokens": 512,
                    "cost_per_1k": {
                        "input": 20.0,
                        "output": 60.0,
                    },
                },
            }
            self._current_model = "gpt-4o-mini"

            # Työkalukohtaiset konfiguraatio-overridet
            self._tool_specific_configs = {
                "rag_tool": {
                    "o1-mini": {
                        "temperature": 0.1,  # Tarkempi haku
                        "max_tokens": 4096,  # Pidempi konteksti haulle
                    },
                    "gpt-4o": {
                        "temperature": 0.8,  # Luovempi vastausten generointi
                        "max_tokens": 2048,  # Pidemmät vastaukset
                    },
                },
                "code_tool": {
                    "gpt-4o": {
                        "temperature": 0.2,  # Tarkempi koodin generointi
                        "max_tokens": 8192,  # Pitkät koodivastaukset
                    }
                },
            }

    @lru_cache(maxsize=None)
    def get_model_for_task(self, task_type: str) -> str:
        """Get best model for specific task type"""
        task_model_mapping = {
            "rag_retrieval": "o1-mini",  # Tarkka malli hakuun
            "rag_generation": "gpt-4o",  # Hyvä reasoning vastauksen muodostamiseen
            "fact_checking": "o1-mini",  # Tarkka malli faktantarkistukseen
            "code_generation": "gpt-4o",  # Hyvä koodin tuottamiseen
            "chat": "gpt-4o-mini",  # Perus keskusteluun
            "multimodal": "o1",  # Kuva/ääni tehtäviin
            "default": "gpt-4o-mini",
        }
        return task_model_mapping.get(task_type, task_model_mapping["default"])

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
