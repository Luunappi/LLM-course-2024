"""
Memory Manager Module

This module provides centralized memory management for the system, acting as the main
interface between the application and various memory implementations.

Key Responsibilities:
- Coordinates usage of different memory types
- Provides a unified interface for memory operations
- Manages memory lifecycle and cleanup
- Enables selection of appropriate memory type based on use case
- Handles memory initialization and configuration

Usage:
    manager = MemoryManager(memory_type="hierarchical")
    manager.store_memory({"content": "data"}, "episodic")
    memories = manager.retrieve_memories("query")

The manager abstracts away the complexity of different memory implementations,
providing a clean and consistent interface for memory operations.
"""

from typing import Dict, List, Any, Optional
import logging
from .memory_base import BaseMemory
from .memory_hierarchical import HierarchicalMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self, memory_type: str = "hierarchical"):
        self.memory: BaseMemory
        if memory_type == "hierarchical":
            self.memory = HierarchicalMemory()
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")

        logger.info(f"Initialized MemoryManager with {memory_type} memory")

    def store_memory(self, data: Dict, memory_type: str = "episodic") -> None:
        """Store memory with type"""
        # Delegoi tallennus muistille
        self.memory.store(data, memory_type)

    def retrieve_memories(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """Retrieve memories based on query"""
        try:
            # Delegate to memory backend
            memories = self.memory.retrieve(query)

            # Apply limit if specified
            if limit is not None:
                memories = memories[:limit]

            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []

    def cleanup_old_memories(self) -> None:
        """Clean old memories"""
        self.memory.cleanup()

    def get_memory_state(self) -> Dict:
        """Get current memory state"""
        return self.memory.get_state()
