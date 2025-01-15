"""Configuration classes for memory management components.

This module contains configuration classes for:
1. Memory chain settings
2. Short-term memory settings
3. Long-term memory settings
4. Processing settings
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryChainConfig:
    """Configuration for the memory chain."""

    max_window_size: int = 10
    summary_threshold: int = 5
    archive_after_hours: int = 24
    cleanup_interval: int = 3600  # seconds
    max_context_length: int = 2000


@dataclass
class ConversationWindow:
    """Configuration for conversation windows."""

    interactions: list = None
    summary: Optional[str] = None
    created_at: Optional[float] = None
    last_updated: Optional[float] = None

    def __post_init__(self):
        self.interactions = self.interactions or []


@dataclass
class ArchiveConfig:
    """Configuration for long-term memory archival."""

    max_age_days: int = 30
    cleanup_threshold: int = 1000
    storage_path: str = "memory/archives"
    index_path: str = "memory/indices"


@dataclass
class ChunkConfig:
    """Configuration for document chunking."""

    chunk_size: int = 500
    chunk_overlap: int = 50
    min_chunk_size: int = 100


@dataclass
class EmbedderConfig:
    """Configuration for text embedding."""

    model_name: str = "all-MiniLM-L6-v2"
    cache_dir: str = "memory/cache/embeddings"
    batch_size: int = 32


@dataclass
class SummaryConfig:
    """Configuration for document summarization."""

    max_length: int = 200
    min_length: int = 50
    num_clusters: int = 3
    hierarchical_levels: int = 2
    model_name: Optional[str] = None  # Default to facebook/bart-large-cnn if None
    cache_dir: str = "memory/cache/summaries"
    use_gpu: bool = False  # Whether to use GPU for summarization
    show_progress: bool = True  # Whether to show progress during summarization
    fallback_strategy: str = (
        "truncate"  # Strategy when summarization fails: truncate/original
    )
