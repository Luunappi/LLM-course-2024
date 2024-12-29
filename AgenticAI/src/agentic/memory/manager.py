"""
Memory management module for AgenticAI.
Handles different types of memory (core, semantic, episodic, working).
"""

from typing import Dict, List, Optional
import asyncio
from .storage import MemoryStorage


class MemoryManager:
    def __init__(self):
        self.storage = MemoryStorage()
        self.memory_types = {"core": [], "semantic": [], "episodic": [], "working": []}

    async def initialize(self):
        """Initialize memory storage"""
        await self.storage.initialize()

    async def store_memory(self, memory_type: str, content: str, importance: float):
        """Store a memory of given type"""
        if memory_type not in self.memory_types:
            raise ValueError(f"Invalid memory type: {memory_type}")

        memory = {
            "content": content,
            "importance": importance,
            "timestamp": asyncio.get_event_loop().time(),
        }

        self.memory_types[memory_type].append(memory)
        await self.storage.save_memory(memory_type, memory)

    async def search_memories(self, query: str, memory_type: str) -> List[Dict]:
        """Search memories of given type"""
        if memory_type not in self.memory_types:
            raise ValueError(f"Invalid memory type: {memory_type}")

        return await self.storage.search_memories(memory_type, query)
