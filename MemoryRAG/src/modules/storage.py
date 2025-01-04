import asyncio
import aiofiles
import json
from pathlib import Path
from typing import Dict, List
import time
import numpy as np
import shutil


class StorageManager:
    """Hallinnoi muistin pysyvää tallennusta"""

    def __init__(self, memory_types: dict):
        """Alustaa StorageManagerin.

        Args:
            memory_types: Viittaus MemoryRAG:n memory_types-sanakirjaan
        """
        self.memory_types = memory_types

        # Korjaa storage_path määrittely
        self.storage_path = Path("test_data")  # Määritellään Path-objektina
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Tiedostopolut
        self.memories_file = self.storage_path / "memories.json"
        self.embeddings_file = self.storage_path / "embeddings.json"
        self.faiss_index_file = self.storage_path / "faiss_index.bin"

    async def save_memories(self, memories: dict = None):
        """Tallentaa muistit tiedostoon."""
        try:
            if memories is None:
                memories = self.memory_types

            async with aiofiles.open(self.memories_file, "w") as f:
                await f.write(json.dumps(memories, indent=2))

        except Exception as e:
            print(f"ERROR: Virhe muistien tallennuksessa: {e}")

    async def load_memories(self) -> dict:
        """Lataa muistit tiedostosta."""
        try:
            if self.memories_file.exists():
                async with aiofiles.open(self.memories_file, "r") as f:
                    content = await f.read()
                    loaded = json.loads(content)
                    print(f"DEBUG: Loaded content: {loaded}")
                    # Päivitä memory_types viittaus
                    self.memory_types.clear()
                    self.memory_types.update(loaded)
                    return loaded

            print("DEBUG: File does not exist")
            return self.get_empty_memories()

        except Exception as e:
            print(f"ERROR: Virhe muistien latauksessa: {e}")
            return self.get_empty_memories()

    def get_empty_memories(self):
        """Palauttaa tyhjän muistirakenteen"""
        return {"core": [], "semantic": [], "episodic": [], "working": []}
