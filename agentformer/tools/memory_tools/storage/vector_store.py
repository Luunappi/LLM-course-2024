"""Vector store implementation using FAISS."""

import logging
import numpy as np
import faiss
from typing import List, Dict, Optional, Any
from ..processing.embedder import TextEmbedder

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector database and semantic search."""

    def __init__(self, embedder: Optional[TextEmbedder] = None):
        """Initialize vector store.

        Args:
            embedder: Shared TextEmbedder instance

        Raises:
            ValueError: If embedder is not provided
        """
        if embedder is None:
            raise ValueError("TextEmbedder instance is required")

        self.embedder = embedder
        self.dimension = embedder.get_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts = []
        self.metadata = []

    def add_vectors(
        self,
        vectors: List[np.ndarray],
        metadata: Optional[List[Dict]] = None,
        texts: Optional[List[str]] = None,
    ) -> None:
        """Add vectors to the database.

        Args:
            vectors: List of vectors as numpy arrays
            metadata: Optional metadata for each vector
            texts: Optional original texts
        """
        if not vectors:
            return

        vectors_array = np.array(vectors)
        self.index.add(vectors_array)

        if texts:
            self.texts.extend(texts)
        if metadata:
            self.metadata.extend(metadata)

    def semantic_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for most similar vectors.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of dicts containing results with scores and metadata
        """
        # Get query embedding
        query_vector = self.embedder.embed_texts([query])[0]

        # Search index
        scores, indices = self.index.search(np.array([query_vector]), k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.texts):
                result = {
                    "score": float(score),
                    "content": self.texts[idx],
                }
                if idx < len(self.metadata):
                    result.update(self.metadata[idx])
                results.append(result)

        return results

    def reset(self) -> None:
        """Reset the vector store."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts = []
        self.metadata = []

    def count(self) -> int:
        """Get total number of vectors.

        Returns:
            int: Number of vectors in store
        """
        return self.index.ntotal

    def remove_vectors_by_metadata(self, metadata_filter: Dict[str, Any]) -> bool:
        """Remove vectors matching metadata filter.

        Args:
            metadata_filter: Filter for metadata (e.g. {"filename": "doc.txt"})

        Returns:
            bool: True if removal succeeded
        """
        try:
            # Find indices to remove
            indices_to_remove = []
            for i, meta in enumerate(self.metadata):
                if all(meta.get(k) == v for k, v in metadata_filter.items()):
                    indices_to_remove.append(i)

            if not indices_to_remove:
                return True  # Nothing to remove

            # Create new index and copy vectors to keep
            new_index = faiss.IndexFlatL2(self.dimension)
            new_metadata = []
            new_texts = []

            for i in range(len(self.metadata)):
                if i not in indices_to_remove:
                    vector = faiss.vector_to_array(self.index.reconstruct(i))
                    new_index.add(np.array([vector]))
                    new_metadata.append(self.metadata[i])
                    new_texts.append(self.texts[i])

            # Update data structures
            self.index = new_index
            self.metadata = new_metadata
            self.texts = new_texts

            return True

        except Exception as e:
            logger.error(f"Error removing vectors: {str(e)}")
            return False
