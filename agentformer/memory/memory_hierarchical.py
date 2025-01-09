"""
Hierarchical Memory Implementation

This module implements a hierarchical memory structure that organizes information
in distinct layers based on their type and importance:

Memory Types:
- Core: Essential system knowledge and configurations
- Semantic: General knowledge and facts
- Episodic: Specific experiences and interactions
- Working: Temporary, active information being processed

Key Features:
- Structured memory organization in layers
- Type-based memory storage and retrieval
- Memory state tracking for each layer
- Efficient cleanup of outdated information

This implementation is ideal for systems requiring organized, layered memory storage
with clear separation between different types of information.
"""

import logging
from typing import Dict, List, Optional
from .memory_base import BaseMemory

logger = logging.getLogger(__name__)


class HierarchicalMemory(BaseMemory):
    def __init__(self):
        self.memory_state = {
            "core": {"count": 0, "oldest": None, "newest": None},
            "semantic": {"count": 0, "oldest": None, "newest": None},
            "episodic": {"count": 0, "oldest": None, "newest": None},
            "working": {"count": 0, "oldest": None, "newest": None},
        }
        self.memories = {"core": [], "semantic": [], "episodic": [], "working": []}
        logger.debug("Initialized HierarchicalMemory")

    def store(self, data: Dict, memory_type: str) -> None:
        """Store memory"""
        if memory_type not in self.memory_state:
            raise ValueError(f"Invalid memory type: {memory_type}")

        self.memories[memory_type].append(data)
        self.memory_state[memory_type]["count"] += 1
        logger.debug(f"Stored memory in {memory_type}: {data}")

    def retrieve(self, query: str, memory_type: Optional[str] = None) -> List[Dict]:
        """Retrieve memories"""
        results = []
        memory_types = [memory_type] if memory_type else self.memories.keys()

        for mtype in memory_types:
            for memory in self.memories[mtype]:
                content = memory.get("content", "")
                response = memory.get("response", "")
                if (
                    query.lower() in str(content).lower()
                    or query.lower() in str(response).lower()
                ):
                    results.append(memory)

        return results

    def cleanup(self) -> None:
        """Clean old memories"""
        # Implement cleanup logic here
        pass

    def get_state(self) -> Dict:
        """Get memory state"""
        return self.memory_state
