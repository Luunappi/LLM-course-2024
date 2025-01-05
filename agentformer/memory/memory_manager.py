"""
Memory Manager Module

Keskitetty muistinhallinta, joka:
- Koordinoi eri muistityyppien käyttöä
- Tarjoaa yhtenäisen rajapinnan muistin käyttöön
- Hallinnoi muistin elinkaarta
- Mahdollistaa muistityypin valinnan käyttötarkoituksen mukaan

Toimii rajapintana muun järjestelmän ja muistikomponenttien välillä.
"""

from typing import Dict, List, Any, Optional
import logging
from .base_memory import BaseMemory
from .hierarchical import HierarchicalMemory

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

    def retrieve_memories(
        self, query: str, memory_type: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve relevant memories"""
        return self.memory.retrieve(query, memory_type)

    def cleanup_old_memories(self) -> None:
        """Clean old memories"""
        self.memory.cleanup()

    def get_memory_state(self) -> Dict:
        """Get current memory state"""
        return self.memory.get_state()
