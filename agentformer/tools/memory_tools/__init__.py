"""Memory Tools Package

This package provides tools for memory management in the chat system:
1. Conversation memory management (short-term and long-term)
2. Vector storage and retrieval
3. Document processing and summarization

The tools are organized into submodules:
- conversation: Memory chain and conversation management
- storage: Vector and document storage
- processing: Text processing and embedding
"""

from .conversation.memory_chain import MemoryChain, MemoryChainConfig
from .conversation.short_term import ShortTermMemory, ConversationWindow
from .conversation.long_term import LongTermMemory, ArchiveConfig
from .storage.vector_store import VectorStore
from .storage.document_store import DocumentStore
from .processing.chunker import DocumentChunker, ChunkConfig
from .processing.embedder import TextEmbedder, EmbedderConfig
from .processing.summarizer import DocumentSummarizer, SummaryConfig

__all__ = [
    "MemoryChain",
    "MemoryChainConfig",
    "ShortTermMemory",
    "ConversationWindow",
    "LongTermMemory",
    "ArchiveConfig",
    "VectorStore",
    "DocumentStore",
    "DocumentChunker",
    "ChunkConfig",
    "TextEmbedder",
    "EmbedderConfig",
    "DocumentSummarizer",
    "SummaryConfig",
]
