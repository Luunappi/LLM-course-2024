"""Text embedding generation and caching."""

import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from ..config import EmbedderConfig

logger = logging.getLogger(__name__)


class TextEmbedder:
    """Handles text embedding generation and caching."""

    def __init__(self, config: EmbedderConfig):
        """Initialize text embedder.

        Args:
            config: Embedder configuration
        """
        self.config = config
        self.model = self._load_model()
        logger.info(f"Initialized TextEmbedder with model: {config.model_name}")

    def _load_model(self) -> SentenceTransformer:
        """Load the embedding model."""
        return SentenceTransformer(
            self.config.model_name, device=self.config.model_device
        )

    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=self.config.normalize_embeddings,
                batch_size=self.config.batch_size,
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def get_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            int: Dimension of embeddings
        """
        return self.model.get_sentence_embedding_dimension()
