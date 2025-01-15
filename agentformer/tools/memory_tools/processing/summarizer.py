"""Document summarization with multiple strategies.

This module provides:
1. Fast clustering-based summarization
2. Hierarchical multi-level summarization
3. Summary optimization
4. Length control
"""

import os
import json
import hashlib
import numpy as np
from typing import List, Dict, Optional, Union
from sklearn.cluster import KMeans
from transformers import pipeline, AutoTokenizer
from transformers.utils import logging

from ..config import SummaryConfig
from .embedder import TextEmbedder, EmbedderConfig

# Reduce verbosity of transformers
logging.set_verbosity_error()


class DocumentSummarizer:
    """Handles document summarization with multiple strategies."""

    def __init__(self, config: SummaryConfig):
        """Initialize document summarizer.

        Args:
            config: Summarizer configuration
        """
        self.config = config
        self.embedder = TextEmbedder(EmbedderConfig())
        self._init_summarizer()
        self._ensure_cache_dir()

    def summarize(self, text: Union[str, List[str]]) -> str:
        """Generate summary for text.

        Args:
            text: Text or list of texts to summarize

        Returns:
            Generated summary
        """
        if not text:
            return ""

        if isinstance(text, list):
            text = " ".join(text)

        # For very short text, return as is
        if len(text.split()) < self.config.min_length:
            return text

        # Check cache
        cache_key = self._get_cache_key(text)
        cached = self._load_from_cache(cache_key)
        if cached:
            return cached

        try:
            # Generate summary
            summary = self.summarizer(
                text,
                max_length=self.config.max_length,
                min_length=self.config.min_length,
                do_sample=False,
            )[0]["summary_text"]

            # Cache result
            self._save_to_cache(cache_key, summary)

            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            return text[: self.config.max_length]  # Fallback to truncation

    def summarize_hierarchical(self, text: str) -> Dict[str, Union[str, List[str]]]:
        """Generate hierarchical summary.

        Args:
            text: Text to summarize

        Returns:
            Dictionary with main summary and section summaries
        """
        if not text:
            return {"main": "", "sections": []}

        try:
            # Split into sections
            sections = self._split_into_sections(text)

            # Generate section summaries with progress tracking
            section_summaries = []
            total_sections = len(sections)

            for i, section in enumerate(sections, 1):
                summary = self.summarize(section)
                section_summaries.append(summary)
                print(f"Summarized section {i}/{total_sections}")

            # Generate main summary
            main_summary = self.summarize(section_summaries)

            return {"main": main_summary, "sections": section_summaries}
        except Exception as e:
            print(f"Error in hierarchical summarization: {e}")
            return {"main": text[: self.config.max_length], "sections": []}

    def summarize_by_clustering(self, texts: List[str]) -> str:
        """Generate summary using clustering.

        Args:
            texts: List of texts to summarize

        Returns:
            Generated summary
        """
        if not texts:
            return ""

        try:
            # Get embeddings
            embeddings = self.embedder.embed_texts(texts)

            # Perform clustering
            n_clusters = min(self.config.num_clusters, len(texts))
            kmeans = KMeans(n_clusters=n_clusters)
            clusters = kmeans.fit_predict(embeddings)

            # Get central sentences from each cluster
            central_texts = []
            for i in range(n_clusters):
                cluster_texts = [t for t, c in zip(texts, clusters) if c == i]
                if cluster_texts:
                    # Get most central text
                    cluster_embeddings = [
                        e for e, c in zip(embeddings, clusters) if c == i
                    ]
                    centroid = np.mean(cluster_embeddings, axis=0)
                    distances = [
                        np.linalg.norm(e - centroid) for e in cluster_embeddings
                    ]
                    central_idx = np.argmin(distances)
                    central_texts.append(cluster_texts[central_idx])

            # Combine and summarize central texts
            combined = " ".join(central_texts)
            return self.summarize(combined)
        except Exception as e:
            print(f"Error in clustering summarization: {e}")
            return texts[0] if texts else ""  # Fallback to first text

    def _split_into_sections(self, text: str) -> List[str]:
        """Split text into sections.

        Args:
            text: Text to split

        Returns:
            List of sections
        """
        if not text:
            return []

        try:
            # Simple section splitting by newlines
            sections = [s.strip() for s in text.split("\n\n") if s.strip()]

            # Merge short sections
            merged = []
            current = []
            current_length = 0

            for section in sections:
                section_length = len(section.split())
                if current_length + section_length < self.config.min_length:
                    current.append(section)
                    current_length += section_length
                else:
                    if current:
                        merged.append("\n".join(current))
                    current = [section]
                    current_length = section_length

            if current:
                merged.append("\n".join(current))

            return merged
        except Exception as e:
            print(f"Error splitting sections: {e}")
            return [text]  # Fallback to single section

    def _init_summarizer(self) -> None:
        """Initialize the summarization model."""
        try:
            self.summarizer = pipeline(
                "summarization",
                model=self.config.model_name or "facebook/bart-large-cnn",
                device=-1,  # Use CPU by default
            )
        except Exception as e:
            print(f"Error loading summarizer model: {e}")
            raise

    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        os.makedirs(self.config.cache_dir, exist_ok=True)

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        text_bytes = text.encode("utf-8")
        return hashlib.sha256(text_bytes).hexdigest()

    def _get_cache_path(self, cache_key: str) -> str:
        """Get cache file path."""
        return os.path.join(self.config.cache_dir, f"{cache_key}.txt")

    def _load_from_cache(self, cache_key: str) -> Optional[str]:
        """Load summary from cache."""
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    return f.read()
            except Exception:
                return None
        return None

    def _save_to_cache(self, cache_key: str, summary: str) -> None:
        """Save summary to cache."""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, "w") as f:
                f.write(summary)
        except Exception:
            pass  # Ignore cache write errors
