"""Configuration for document chunking"""

from dataclasses import dataclass


@dataclass
class ChunkConfig:
    """Chunking configuration"""

    chunk_size: int = 1000
    overlap: int = 200
    min_chunk_size: int = 100
