"""Short-term memory management for conversations.

This module handles:
1. Active conversation tracking
2. Automatic summarization
3. Window size management
4. Memory overflow prevention
"""

import time
from typing import List, Optional
from dataclasses import dataclass

from ..config import MemoryChainConfig, ConversationWindow
from ..processing.summarizer import DocumentSummarizer


@dataclass
class Interaction:
    """A single interaction in the conversation."""

    role: str
    content: str
    timestamp: float = None

    def __post_init__(self):
        self.timestamp = self.timestamp or time.time()


class ShortTermMemory:
    """Manages short-term memory for active conversations."""

    def __init__(self, config: MemoryChainConfig):
        """Initialize short-term memory manager.

        Args:
            config: Memory chain configuration
        """
        self.config = config
        self.current_window = ConversationWindow()
        self.summarizer = DocumentSummarizer()
        self.current_window.created_at = time.time()
        self.current_window.last_updated = time.time()

    def add_interaction(self, role: str, content: str) -> None:
        """Add a new interaction to the current window.

        Args:
            role: Role of the participant (user/assistant)
            content: Content of the interaction
        """
        interaction = Interaction(role=role, content=content)
        self.current_window.interactions.append(interaction)
        self.current_window.last_updated = time.time()

        # Check if summarization is needed
        if len(self.current_window.interactions) >= self.config.summary_threshold:
            self._update_summary()

        # Check if window cleanup is needed
        if len(self.current_window.interactions) > self.config.max_window_size:
            self._cleanup_window()

    def get_current_window(self) -> ConversationWindow:
        """Get the current conversation window.

        Returns:
            Current conversation window
        """
        return self.current_window

    def clear_memory(self) -> None:
        """Clear the current conversation window."""
        self.current_window = ConversationWindow()
        self.current_window.created_at = time.time()
        self.current_window.last_updated = time.time()

    def _update_summary(self) -> None:
        """Update the summary of the current window."""
        texts = [
            f"{interaction.role}: {interaction.content}"
            for interaction in self.current_window.interactions
        ]
        self.current_window.summary = self.summarizer.summarize(texts)

    def _cleanup_window(self) -> None:
        """Clean up the conversation window when it exceeds max size."""
        # Keep the most recent interactions
        keep_count = self.config.max_window_size // 2
        self.current_window.interactions = self.current_window.interactions[
            -keep_count:
        ]
        self._update_summary()
