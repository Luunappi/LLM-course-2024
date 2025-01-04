"""
• Kuvaus: Hallinnoi muistien elinkaarta ja priorisointia.
• Rooli: Tärkeä, jos halutaan tehokkaasti poistaa vanhat muistit tai järjestää muistit tärkeyden mukaan.
• Tarpeellisuus: “Avustava” mutta melko keskeinen – memory_rag.py kutsuu usein memory_manageria muistien puhdistukseen ja priorisoinnille.
"""

from typing import List, Dict, Any
import time
from datetime import datetime, timedelta
import numpy as np
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os
import math


class MemoryManager:
    """Hallinnoi muistien elinkaarta ja priorisointia"""

    def __init__(self, rag):
        self.rag = rag

    async def cleanup_old_memories(self, max_age_days: int = None):
        """Poistaa vanhat muistit"""
        if max_age_days is None:
            max_age_days = self.rag.max_age_days

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        for memory_type in self.rag.memory_types:
            # Suodata pois liian vanhat muistit
            self.rag.memory_types[memory_type] = [
                memory
                for memory in self.rag.memory_types[memory_type]
                if current_time
                - memory.get("metadata", {}).get("timestamp", current_time)
                < max_age_seconds
            ]

    async def get_important_memories(
        self, memory_type: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Hakee tärkeimmät muistit tietystä muistityypistä"""
        memories = self.rag.memory_types.get(memory_type, [])

        # Järjestä tärkeyden mukaan
        sorted_memories = sorted(
            memories, key=lambda x: x.get("importance", 0), reverse=True
        )

        return sorted_memories[:limit]

    async def compress_memories(self, memory_type: str):
        """Tiivistää muisteja yhdistämällä samankaltaisia"""
        # TODO: Implement memory compression logic
        pass
