"""Long-term memory management for conversations.

This module handles:
1. Conversation archival
2. Semantic search for relevant history
3. Automatic cleanup of old conversations
4. Memory optimization
"""

import os
import time
import json
import uuid
from typing import List, Optional, Dict
from dataclasses import asdict

from ..config import ArchiveConfig, ConversationWindow
from ..storage.vector_store import VectorStore
from ..processing.embedder import TextEmbedder


class LongTermMemory:
    """Manages long-term memory for archived conversations."""

    def __init__(self, config: ArchiveConfig):
        """Initialize long-term memory manager.

        Args:
            config: Archive configuration
        """
        self.config = config
        self._ensure_directories()
        self.vector_store = VectorStore()
        self.embedder = TextEmbedder()
        self.archive_index: Dict[str, dict] = self._load_index()

    def archive_conversation(self, conversation: ConversationWindow) -> str:
        """Archive a conversation for long-term storage.

        Args:
            conversation: Conversation window to archive

        Returns:
            Archive ID
        """
        # Generate unique ID
        archive_id = str(uuid.uuid4())

        # Prepare metadata
        metadata = {
            "created_at": conversation.created_at,
            "last_updated": conversation.last_updated,
            "summary": conversation.summary,
            "interaction_count": len(conversation.interactions),
        }

        # Save conversation data
        self._save_conversation(archive_id, conversation)

        # Update index
        self.archive_index[archive_id] = metadata
        self._save_index()

        # Add to vector store for semantic search
        if conversation.summary:
            embedding = self.embedder.embed_text(conversation.summary)
            self.vector_store.add_vector(archive_id, embedding, metadata)

        return archive_id

    def get_conversation(self, archive_id: str) -> Optional[ConversationWindow]:
        """Retrieve an archived conversation.

        Args:
            archive_id: ID of the archived conversation

        Returns:
            Retrieved conversation window or None if not found
        """
        if archive_id not in self.archive_index:
            return None

        archive_path = os.path.join(self.config.storage_path, f"{archive_id}.json")
        if not os.path.exists(archive_path):
            return None

        with open(archive_path, "r") as f:
            data = json.load(f)
            window = ConversationWindow()
            window.interactions = data["interactions"]
            window.summary = data["summary"]
            window.created_at = data["created_at"]
            window.last_updated = data["last_updated"]
            return window

    def find_relevant(self, query: str, limit: int = 5) -> List[str]:
        """Find relevant conversations using semantic search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of archive IDs
        """
        query_embedding = self.embedder.embed_text(query)
        results = self.vector_store.search(query_embedding, limit)
        return [result.id for result in results]

    def cleanup(self) -> None:
        """Clean up old conversations based on age and threshold."""
        current_time = time.time()
        max_age = self.config.max_age_days * 24 * 3600

        # Find old conversations
        old_ids = []
        for archive_id, metadata in self.archive_index.items():
            age = current_time - metadata["last_updated"]
            if age > max_age:
                old_ids.append(archive_id)

        # Remove old conversations
        for archive_id in old_ids:
            self._remove_conversation(archive_id)

        # Check total count
        if len(self.archive_index) > self.config.cleanup_threshold:
            self._cleanup_by_count()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        os.makedirs(self.config.storage_path, exist_ok=True)
        os.makedirs(self.config.index_path, exist_ok=True)

    def _load_index(self) -> Dict[str, dict]:
        """Load the archive index from disk."""
        index_path = os.path.join(self.config.index_path, "archive_index.json")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                return json.load(f)
        return {}

    def _save_index(self) -> None:
        """Save the archive index to disk."""
        index_path = os.path.join(self.config.index_path, "archive_index.json")
        with open(index_path, "w") as f:
            json.dump(self.archive_index, f)

    def _save_conversation(
        self, archive_id: str, conversation: ConversationWindow
    ) -> None:
        """Save a conversation to disk."""
        archive_path = os.path.join(self.config.storage_path, f"{archive_id}.json")
        with open(archive_path, "w") as f:
            json.dump(asdict(conversation), f)

    def _remove_conversation(self, archive_id: str) -> None:
        """Remove a conversation from storage."""
        # Remove from index
        if archive_id in self.archive_index:
            del self.archive_index[archive_id]

        # Remove from vector store
        self.vector_store.remove_vector(archive_id)

        # Remove file
        archive_path = os.path.join(self.config.storage_path, f"{archive_id}.json")
        if os.path.exists(archive_path):
            os.remove(archive_path)

    def _cleanup_by_count(self) -> None:
        """Clean up conversations when total count exceeds threshold."""
        # Sort by last updated time
        sorted_ids = sorted(
            self.archive_index.keys(),
            key=lambda x: self.archive_index[x]["last_updated"],
        )

        # Remove oldest conversations
        remove_count = len(sorted_ids) - self.config.cleanup_threshold
        for archive_id in sorted_ids[:remove_count]:
            self._remove_conversation(archive_id)
