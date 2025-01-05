"""Base Memory Interface"""

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
