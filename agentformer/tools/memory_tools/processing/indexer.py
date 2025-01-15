"""Document indexer for chunking and preprocessing.

This module handles:
1. Document chunking into suitable sizes
2. Text preprocessing
3. Metadata extraction
"""

import logging
from typing import List, Dict, Any
from .chunker import DocumentChunker
from ..config import ChunkConfig

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Handles document preprocessing and chunking."""

    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()
        self.chunker = DocumentChunker(self.config)

    def process_document(
        self, content: str, metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Process document into chunks with metadata.

        Args:
            content: Document content
            metadata: Optional metadata

        Returns:
            List of chunks with metadata
        """
        try:
            # Split into chunks
            chunks = self.chunker.split_text(content)

            # Add metadata to each chunk
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_data = {
                    "content": chunk,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                if metadata:
                    chunk_data["metadata"] = metadata

                processed_chunks.append(chunk_data)

            return processed_chunks

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return []
