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

    def __init__(self):
        self.storage_path = None
        self.memories = {"core": [], "semantic": [], "episodic": [], "working": []}

    async def save_memories(self) -> bool:
        """Tallentaa muistit tiedostoon"""
        try:
            if not self.storage_path:
                print("Virhe: storage_path ei ole asetettu")
                return False

            import json

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Virhe tallennettaessa muisteja: {e}")
            return False

    async def load_memories(self) -> dict:
        """Lataa muistit tiedostosta"""
        try:
            if not self.storage_path or not self.storage_path.exists():
                print("Virhe: storage_path ei ole asetettu tai tiedostoa ei löydy")
                return self.memories

            import json

            with open(self.storage_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                self.memories = loaded_data
                return loaded_data
        except Exception as e:
            print(f"Virhe ladattaessa muisteja: {e}")
            return self.memories

    async def store_memory(self, memory_type: str, memory_item: dict):
        """Tallentaa yksittäisen muistin"""
        if memory_type not in self.memories:
            self.memories[memory_type] = []
        self.memories[memory_type].append(memory_item)

    async def clear_memories(self):
        """Tyhjentää kaikki muistit"""
        self.memories = {"core": [], "semantic": [], "episodic": [], "working": []}
