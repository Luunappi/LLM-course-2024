"""Memory chain for coordinating short-term and long-term memory.

This module handles:
1. Coordination between memory components
2. Context management for conversations
3. Automatic archival of old conversations
4. Memory cleanup and optimization
"""

import time
from typing import Optional, List

from ..config import MemoryChainConfig, ConversationWindow, ArchiveConfig
from .short_term import ShortTermMemory
from .long_term import LongTermMemory


class MemoryChain:
    """Coordinates memory components for conversation management."""

    def __init__(self, config: MemoryChainConfig):
        """Initialize memory chain.

        Args:
            config: Memory chain configuration
        """
        self.config = config
        self.short_term = ShortTermMemory(config)
        self.long_term = LongTermMemory(ArchiveConfig())
        self.last_cleanup = time.time()

    def process_interaction(self, role: str, content: str) -> None:
        """Process a new interaction.

        Args:
            role: Role of the participant (user/assistant)
            content: Content of the interaction
        """
        # Add to short-term memory
        self.short_term.add_interaction(role, content)

        # Check if cleanup needed
        self._check_cleanup()

        # Check if archival needed
        self._check_archival()

    def get_context(self, query: Optional[str] = None) -> ConversationWindow:
        """Get context for the current conversation.

        Args:
            query: Optional query to find relevant history

        Returns:
            Conversation window with context
        """
        # Get current window
        context = self.short_term.get_current_window()

        # If query provided, find relevant history
        if query:
            archive_ids = self.long_term.find_relevant(query)
            for archive_id in archive_ids:
                archived = self.long_term.get_conversation(archive_id)
                if archived and archived.summary:
                    # Add summary to context
                    context.interactions.append(
                        {
                            "role": "system",
                            "content": f"Related history: {archived.summary}",
                        }
                    )

        return context

    def end_conversation(self) -> None:
        """End the current conversation and archive it."""
        window = self.short_term.get_current_window()
        if window.interactions:
            self.long_term.archive_conversation(window)
            self.short_term.clear_memory()

    def cleanup(self) -> None:
        """Perform cleanup of memory components."""
        self.short_term._cleanup_window()
        self.long_term.cleanup()
        self.last_cleanup = time.time()

    def _check_cleanup(self) -> None:
        """Check if cleanup is needed."""
        current_time = time.time()
        if current_time - self.last_cleanup > self.config.cleanup_interval:
            self.cleanup()

    def _check_archival(self) -> None:
        """Check if conversation should be archived."""
        window = self.short_term.get_current_window()
        if window.last_updated:
            age = time.time() - window.last_updated
            if age > self.config.archive_after_hours * 3600:
                self.end_conversation()
