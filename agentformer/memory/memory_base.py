"""
Base Memory Interface

This module defines the core interface for all memory implementations in the system.
It provides the essential contract that all memory types must fulfill:

Key Features:
- Abstract base class for memory implementations
- Defines standard methods for storing and retrieving memories
- Ensures consistent memory management across different implementations
- Provides memory state tracking and cleanup capabilities

This interface is used by concrete memory implementations like HierarchicalMemory
and DistributedMemory to ensure consistent behavior across the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseMemory(ABC):
    @abstractmethod
    def store(self, data: Dict, memory_type: str) -> None:
        """Store memory"""
        pass

    @abstractmethod
    def retrieve(self, query: str, memory_type: Optional[str] = None) -> List[Dict]:
        """Retrieve memories"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean old memories"""
        pass

    @abstractmethod
    def get_state(self) -> Dict:
        """Get memory state"""
        pass
