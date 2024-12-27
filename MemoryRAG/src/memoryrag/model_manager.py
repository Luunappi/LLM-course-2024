"""Mallien hallinta ja optimointi"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any
from openai import AsyncOpenAI  # Lisää asynkroninen OpenAI client
import os
from dotenv import load_dotenv
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from pathlib import Path


class TaskType(Enum):
    PROCESS = "process"  # Tekstin prosessointi, jäsentely
    FACTCHECK = "factcheck"  # Faktojen tarkistus
    TECHNICAL = "technical"  # Tekninen analyysi
    ANALYSIS = "analysis"  # Syvällinen analyysi
    EVALUATION = "evaluation"  # Laadun arviointi


@dataclass
class ModelConfig:
    name: str
    input_cost: float  # USD per 1M tokenia
    output_cost: float
    max_tokens: int
    temperature: float


class ModelManager:
    def __init__(self):
        self.models = {
            TaskType.PROCESS: ModelConfig(
                name="gpt-4o-mini",  # Kevyt malli prosessointiin
                input_cost=0.15,
                output_cost=0.60,
                max_tokens=2000,
                temperature=0.3,
            ),
            TaskType.FACTCHECK: ModelConfig(
                name="o1-mini",  # Tarkka malli faktantarkistukseen
                input_cost=3.0,
                output_cost=12.0,
                max_tokens=1000,
                temperature=0.1,
            ),
            TaskType.ANALYSIS: ModelConfig(
                name="o1-preview",  # Tehokas malli analyysiin
                input_cost=15.0,
                output_cost=15.0,
                max_tokens=4000,  # Kasvatettu kontekstia
                temperature=0.7,
            ),
        }
        self.token_usage = {task: 0 for task in TaskType}
        self.costs = {task: 0.0 for task in TaskType}

        # Lataa API-avaimet repon juuresta
        repo_root = (
            Path(__file__).resolve().parents[3]
        )  # 3 tasoa ylös src/memoryrag/model_manager.py:stä
        load_dotenv(dotenv_path=repo_root / ".env")

        # Alusta Azure client
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT")

        # Azure clients per deployment
        self.azure_clients = {}
        for model_name in ["gpt-4o-mini", "o1-mini", "o1-preview"]:
            endpoint = self.azure_endpoint.rstrip("/")
            # Lisää api-version URL:iin
            base_url = f"{endpoint}/openai/deployments/{model_name}?api-version=2024-07-01-preview"

            print(f"Initializing {model_name} with URL: {base_url}")

            self.azure_clients[model_name] = AsyncOpenAI(
                api_key=os.getenv("AZURE_API_KEY"),
                base_url=base_url,
                default_headers={
                    "api-key": os.getenv("AZURE_API_KEY"),
                },
            )

        # Alusta OpenAI client fallbackia varten
        self.openai_client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            organization=os.getenv("OPENAI_ORG_ID"),  # Lisätty org ID jos tarpeen
        )

    async def _call_model(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Kutsuu ensin Azurea, fallback OpenAI:hin"""
        # Azure deployment nimet ja OpenAI fallback-mallit
        model_configs = {
            "gpt-4o-mini": {
                "azure": "gpt-4o-mini",
                "openai": "gpt-4o-mini",
                "fallback_temp": 0.3,
            },
            "o1-mini": {
                "azure": "o1-mini",
                "openai": "o1-mini",
                "fallback_temp": 0.1,
            },
            "o1-preview": {
                "azure": "o1-preview",
                "openai": "o1-preview",
                "fallback_temp": temperature,
            },
        }

        config = model_configs.get(model_name)
        if not config:
            raise ValueError(f"Mallia {model_name} ei tueta")

        try:
            # Yritä ensin Azurella
            print(f"Yritetään Azure-mallia: {config['azure']}")
            client = self.azure_clients[model_name]
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            print("Azure-kutsu onnistui")
            return response.choices[0].message.content

        except Exception as azure_error:
            print(f"Azure-kutsu epäonnistui: {str(azure_error)}")
            print(f"Yritetään OpenAI fallbackia: {config['openai']}")

            try:
                # Fallback OpenAI:hin
                response = await self.openai_client.chat.completions.create(
                    model=config["openai"],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=config["fallback_temp"],
                )
                print("OpenAI fallback onnistui")
                return response.choices[0].message.content

            except Exception as openai_error:
                error_msg = f"Sekä Azure ({str(azure_error)}) että OpenAI ({str(openai_error)}) epäonnistuivat"
                print(error_msg)
                return f"Virhe: {error_msg}"

    async def _evaluate_response(
        self, query: str, rag_response: str, context: str
    ) -> Dict:
        """Analysoi RAG-vastauksen laatua ja antaa parannusehdotuksia"""

        evaluation_prompt = f"""
        Analysoi RAG-vastauksen laatua ja anna kehitysehdotuksia:

        Kysymys: {query}

        RAG-vastaus: 
        {rag_response}

        Käytetty konteksti:
        {context}

        Arvioi seuraavat asiat:
        1. Kontekstin käyttö:
           - Hyödyntääkö vastaus kaikkea relevanttia tietoa kontekstista?
           - Onko vastaus uskollinen kontekstille vai sisältääkö se ylimääräisiä päätelmiä?
           
        2. Vastauksen tarkkuus:
           - Vastaako se suoraan kysymykseen?
           - Onko vastaus riittävän yksityiskohtainen?
           
        3. Parannusehdotukset:
           - Mitä tietoja kontekstista jäi käyttämättä?
           - Miten vastausta voisi tarkentaa kontekstin perusteella?
           
        Anna konkreettiset parannusehdotukset ja perustele ne kontekstin avulla.
        """

        try:
            # Käytä o1-preview mallia arviointiin
            analysis = await self._call_model(
                "o1-preview", evaluation_prompt, max_tokens=1000, temperature=0.1
            )

            return {
                "analysis": analysis,
                "context_length": len(context),
                "response_length": len(rag_response),
            }

        except Exception as e:
            print(f"Virhe vastauksen analysoinnissa: {e}")
            return {"analysis": "Analysointi epäonnistui", "error": str(e)}

    async def run_task(self, task_type: TaskType, prompt: str) -> Dict[str, Any]:
        """Suorittaa tehtävän ja arvioi vastauksen laadun"""
        config = self.models[task_type]

        # Laske tokenit ja kustannukset
        input_tokens = len(prompt.split())  # Yksinkertainen arvio
        estimated_cost = (
            input_tokens * config.input_cost + config.max_tokens * config.output_cost
        ) / 1_000_000

        print(f"\nTehtävä: {task_type.value}")
        print(f"Malli: {config.name}")
        print(f"Arvioitu kustannus: ${estimated_cost:.4f}")

        # Suorita tehtävä
        response = await self._call_model(
            config.name,
            prompt,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )

        # Arvioi vastauksen laatu
        evaluation = await self._evaluate_response(
            prompt, response, self.context_manager.get_last_context()
        )

        # Päivitä käyttötilastot
        self.token_usage[task_type] += input_tokens + len(response.split())
        self.costs[task_type] += estimated_cost

        return {
            "result": response,
            "model": config.name,
            "cost": estimated_cost,
            "task_type": task_type.value,
            "evaluation": evaluation,
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Palauttaa käyttötilastot"""
        return {
            "token_usage": self.token_usage,
            "costs": self.costs,
            "total_cost": sum(self.costs.values()),
        }
