"""Document chunking tool - Dokumenttien pilkkominen"""

from typing import List, Dict, Any
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    """Configuration for document chunking"""

    chunk_size: int = 1000
    overlap: int = 200
    min_chunk_size: int = 100


class DocumentChunker:
    """Pilkkoo dokumentit sopivan kokoisiksi palasiksi"""

    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()
        self.chunk_size = self.config.chunk_size
        self.overlap = self.config.overlap

    def chunk_text(self, text: str) -> List[str]:
        """Pilko teksti sopivan kokoisiin palasiin"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end > len(text):
                end = len(text)
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.overlap
        return chunks
