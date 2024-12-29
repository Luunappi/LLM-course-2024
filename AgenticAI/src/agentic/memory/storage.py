"""
Storage implementation for AgenticAI memory system.
Handles persistent storage and retrieval of memories.
"""

from typing import Dict, List, Optional
import asyncio
import json
import aiofiles
from pathlib import Path


class MemoryStorage:
    def __init__(self):
        self.storage_path = Path("data/memories")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize storage"""
        pass

    async def save_memory(self, memory_type: str, memory: Dict):
        """Save memory to storage"""
        file_path = self.storage_path / f"{memory_type}.json"

        async with aiofiles.open(file_path, mode="a") as f:
            await f.write(json.dumps(memory) + "\n")

    async def search_memories(self, memory_type: str, query: str) -> List[Dict]:
        """Search memories from storage"""
        file_path = self.storage_path / f"{memory_type}.json"
        if not file_path.exists():
            return []

        memories = []
        async with aiofiles.open(file_path) as f:
            async for line in f:
                memory = json.loads(line)
                # Tässä vaiheessa yksinkertainen string-match
                if query.lower() in memory["content"].lower():
                    memories.append(memory)

        return memories
