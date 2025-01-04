from typing import List, Dict, Any, Optional
from pathlib import Path
from .modules.agentic_memory import AgenticMemory
from .modules.pubsub import EnhancedPubSub
from .modules.memory_operations import MemoryOperations
from .modules.memory_manager import MemoryManager
from .modules.context_manager import ContextManager
import time
import os
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np
from .modules.storage import StorageManager
from math import fabs
import torch
from .modules.model_manager import ModelManager


class RAGOrchestrator:
    """Kokoaa MemoryRAG-järjestelmän yhteen:
    - Lataa .env
    - Alustaa model_manager, context_manager, storage, memory_manager
    - Tarjoaa process_query, _store_memory ja muut julkiset metodit
    """

    @classmethod
    async def create(cls, model_name: str = "gpt-4o-mini"):
        # Lataa .env
        repo_root = Path(__file__).resolve().parents[2]
        load_dotenv(dotenv_path=repo_root / ".env")

        # Hakee avaimet
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY puuttuu .env tiedostosta!")

        azure_endpoint = os.getenv("AZURE_ENDPOINT", "")  # Valinnainen

        instance = cls(model_name, api_key, azure_endpoint)
        await instance._initialize()
        return instance

    def __init__(self, model_name: str, api_key: str, azure_endpoint: str = ""):
        # Aseta perusmuisti
        self.memory_types = {
            "core": [],
            "semantic": [],
            "episodic": [],
            "working": [],
        }
        self.model_name = model_name
        self.api_key = api_key
        self.azure_endpoint = azure_endpoint

        # Managerit
        self.storage = StorageManager(self.memory_types)
        self.context_manager = ContextManager(self)
        self.model_manager = ModelManager()
        self.memory_manager = MemoryManager(self)

    async def _initialize(self):
        """Alustaa järjestelmän."""
        # Lataa muistit
        await self.storage.load_memories()

        # Alusta embeddings-indeksi jos käytössä
        # TODO: Implementoi embedding-indeksin alustus

        # Testaa API-yhteys
        try:
            test_response = await self.model_manager._call_model(
                self.model_name, "Test connection", max_tokens=10, temperature=0.1
            )
            if not test_response.startswith("Virhe"):
                print("API-yhteys testattu onnistuneesti")
        except Exception as e:
            print(f"Varoitus: API-yhteyden testaus epäonnistui: {e}")

    async def process_query(self, query: str, query_type: str = "rag") -> str:
        """Käsittelee käyttäjän kyselyn asynkronisesti."""
        try:
            # Tallenna kysely working-muistiin
            await self._store_memory("working", query, importance=0.7)

            # Rakenna konteksti
            context = await self.context_manager.build_context(query)

            # Kutsu mallia asynkronisesti
            response = await self._run_llm_query(query, context)

            # Tallenna vastaukset episodic-muistiin
            await self._store_memory(
                "episodic", f"K: {query}\nV: {response}", importance=0.6
            )

            return response
        except Exception as e:
            print(f"Virhe kyselyn käsittelyssä: {e}")
            return f"Pahoittelen, mutta kyselyn käsittelyssä tapahtui virhe: {str(e)}"

    async def _store_memory(self, memory_type: str, content: str, importance: float):
        # Tallenna muistiin + laske embedding...
        item = {
            "content": content,
            "importance": importance,
            "metadata": {
                "timestamp": time.time(),
                # halutun embed-datan tms.
            },
        }
        self.memory_types.setdefault(memory_type, []).append(item)
        # (async) tallennus
        await self.storage.save_memories(self.memory_types)

    async def _run_llm_query(self, query: str, context: str) -> str:
        """Kutsuu model_manageria asynkronisesti."""
        prompt = f"Context:\n{context}\n\nQuestion: {query}"
        result = await self.model_manager._call_model(
            self.model_name, prompt, max_tokens=1000, temperature=0.7
        )
        return result

    async def _search_memories(self, query: str, memories: List[Dict]) -> List[Dict]:
        """Hakee relevantit muistit annetusta muistilistasta.

        Args:
            query: Hakukysely
            memories: Lista muisteja, joista haetaan

        Returns:
            Lista relevanteista muisteista järjestettynä tärkeyden mukaan
        """
        # Yksinkertainen toteutus - järjestä tärkeyden mukaan
        # TODO: Implementoi semanttinen haku embeddingeillä
        sorted_memories = sorted(
            memories, key=lambda x: x.get("importance", 0), reverse=True
        )

        # Palauta max 5 relevanteinta muistia
        return sorted_memories[:5]
