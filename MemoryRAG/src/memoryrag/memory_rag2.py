from typing import List, Dict, Any, Optional
from pathlib import Path
from .memory_operations import MemoryOperations
from .storage import StorageManager
import time
import os
import numpy as np
from openai import AsyncOpenAI
from dotenv import load_dotenv


class MemoryRAG(MemoryOperations):
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Alustaa MemoryRAG:n."""
        super().__init__()
        self.model_name = model_name

        # Initialize memory types first
        self.memory_types = {"core": [], "semantic": [], "episodic": [], "working": []}

        # Then create storage with reference to memory_types
        self.storage = StorageManager(self.memory_types)

        # Memory settings
        self.max_age_days = 30
        self.batch_size = 1000
        self.min_chunk_size = 250
        self.max_workers = 4
        self.cleanup_interval = 24 * 60 * 60  # 24 hours
        self.last_cleanup = time.time()

        # Initialize OpenAI client
        repo_root = Path(__file__).resolve().parents[3]
        dotenv_path = repo_root / ".env"

        if not dotenv_path.exists():
            raise ValueError(
                f"API-avainta ei löydy! Varmista että .env tiedosto on repon juuressa: {repo_root}"
            )

        load_dotenv(dotenv_path=str(dotenv_path))
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY puuttuu .env tiedostosta! Lisää se muodossa: OPENAI_API_KEY=your-key-here"
            )

        self.client = AsyncOpenAI(api_key=api_key)

    @classmethod
    async def create(cls, model_name: str = "gpt-3.5-turbo"):
        """Luo uuden MemoryRAG-instanssin asynkronisesti."""
        instance = cls(model_name)
        await instance._test_api_connection()
        await instance.storage.initialize()
        return instance

    async def _test_api_connection(self):
        """Testaa API-yhteyden toimivuuden."""
        try:
            print("Testataan OpenAI API-yhteyttä...")
            test_response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
            )
            print("OpenAI API-yhteys toimii!")
        except Exception as e:
            raise ValueError(f"OpenAI API-avain ei toimi: {e}")

    async def cleanup_old_embeddings(self):
        """Poistaa vanhat muistit."""
        current_time = time.time()
        for memory_type in self.memory_types:
            self.memory_types[memory_type] = [
                mem
                for mem in self.memory_types[memory_type]
                if current_time - mem["timestamp"] <= self.max_age_days * 24 * 60 * 60
            ]
