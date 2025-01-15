"""Tests for memory chain functionality.

This module tests:
1. Memory chain coordination
2. Context management
3. Conversation archival
4. Memory cleanup
"""

import pytest
import time
from agentformer.tools.memory_tools import (
    MemoryChain,
    MemoryChainConfig,
    ConversationWindow,
)


@pytest.fixture
def memory_chain():
    """Create a memory chain instance for testing."""
    config = MemoryChainConfig(
        max_window_size=5,
        summary_threshold=3,
        archive_after_hours=24,
        cleanup_interval=3600,
    )
    return MemoryChain(config)


def test_process_interaction(memory_chain):
    """Test processing new interactions."""
    # Add test interactions
    memory_chain.process_interaction("user", "What is Python?")
    memory_chain.process_interaction("assistant", "Python is a programming language.")

    # Verify interactions were added
    context = memory_chain.get_context()
    assert len(context.interactions) == 2
    assert context.interactions[0]["content"] == "What is Python?"


def test_context_retrieval(memory_chain):
    """Test context retrieval with query."""
    # Add some interactions
    memory_chain.process_interaction("user", "Tell me about machine learning.")
    memory_chain.process_interaction("assistant", "Machine learning is a field of AI.")
    memory_chain.process_interaction("user", "What are neural networks?")

    # Get context with query
    context = memory_chain.get_context("machine learning")

    # Verify context includes relevant information
    assert len(context.interactions) > 0
    assert any(
        "machine learning" in str(interaction) for interaction in context.interactions
    )


def test_conversation_archival(memory_chain):
    """Test conversation archival."""
    # Add interactions
    memory_chain.process_interaction("user", "What is Python?")
    memory_chain.process_interaction("assistant", "Python is a programming language.")

    # End conversation
    memory_chain.end_conversation()

    # Verify short-term memory was cleared
    context = memory_chain.get_context()
    assert len(context.interactions) == 0

    # Add new interaction and check context
    memory_chain.process_interaction("user", "Tell me more about Python")
    context = memory_chain.get_context("Python")

    # Should include summary from archived conversation
    assert any("Python" in str(interaction) for interaction in context.interactions)


def test_memory_cleanup(memory_chain):
    """Test memory cleanup."""
    # Add many interactions
    for i in range(10):
        memory_chain.process_interaction("user", f"Test message {i}")
        memory_chain.process_interaction("assistant", f"Test response {i}")

    # Force cleanup
    memory_chain.cleanup()

    # Verify cleanup results
    context = memory_chain.get_context()
    assert len(context.interactions) <= memory_chain.config.max_window_size


def test_automatic_archival(memory_chain):
    """Test automatic archival of old conversations."""
    # Add test interaction
    memory_chain.process_interaction("user", "Old message")
    memory_chain.process_interaction("assistant", "Old response")

    # Simulate time passing
    memory_chain.short_term.get_current_window().last_updated -= 25 * 3600  # 25 hours

    # Add new interaction to trigger check
    memory_chain.process_interaction("user", "New message")

    # Verify old conversation was archived
    context = memory_chain.get_context()
    assert len(context.interactions) == 1
    assert context.interactions[0]["content"] == "New message"


if __name__ == "__main__":
    pytest.main([__file__])
