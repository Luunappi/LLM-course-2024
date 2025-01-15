"""Tests for memory management components.

This module contains tests for:
1. Short-term memory management
2. Long-term memory archival and retrieval
3. Memory chain coordination
4. Integration between components
"""

import pytest
from agentformer.tools.memory_tools import (
    MemoryChain,
    MemoryChainConfig,
    ShortTermMemory,
    ConversationWindow,
    LongTermMemory,
    ArchiveConfig,
)


@pytest.fixture
def memory_chain():
    """Create a memory chain instance for testing."""
    config = MemoryChainConfig(
        max_window_size=5, summary_threshold=3, archive_after_hours=24
    )
    return MemoryChain(config)


def test_short_term_memory_add_interaction(memory_chain):
    """Test adding interactions to short-term memory."""
    memory = memory_chain.short_term

    # Add test interactions
    memory.add_interaction("user", "What is the capital of France?")
    memory.add_interaction("assistant", "The capital of France is Paris.")

    # Verify window contents
    window = memory.get_current_window()
    assert len(window.interactions) == 2
    assert window.interactions[0].role == "user"
    assert window.interactions[1].role == "assistant"


def test_short_term_memory_summarization(memory_chain):
    """Test automatic summarization of conversations."""
    memory = memory_chain.short_term

    # Add interactions to trigger summarization
    for i in range(4):
        memory.add_interaction("user", f"Test question {i}")
        memory.add_interaction("assistant", f"Test answer {i}")

    # Verify summary was created
    window = memory.get_current_window()
    assert window.summary is not None
    assert len(window.summary) > 0


def test_long_term_memory_archival(memory_chain):
    """Test archiving conversations to long-term memory."""
    memory = memory_chain.long_term

    # Create test conversation
    conversation = ConversationWindow()
    conversation.add_interaction("user", "Test question")
    conversation.add_interaction("assistant", "Test answer")

    # Archive conversation
    archive_id = memory.archive_conversation(conversation)

    # Verify retrieval
    archived = memory.get_conversation(archive_id)
    assert archived is not None
    assert len(archived.interactions) == 2


def test_memory_chain_context_retrieval(memory_chain):
    """Test retrieving context for ongoing conversations."""
    # Add some interactions
    memory_chain.process_interaction("user", "What is Python?")
    memory_chain.process_interaction("assistant", "Python is a programming language.")
    memory_chain.process_interaction("user", "What can I do with it?")

    # Get context for next interaction
    context = memory_chain.get_context()

    # Verify context includes relevant history
    assert len(context.interactions) > 0
    assert "Python" in str(context)


def test_memory_chain_cleanup(memory_chain):
    """Test cleanup of old conversations."""
    # Add test interactions
    for i in range(10):
        memory_chain.process_interaction("user", f"Old message {i}")
        memory_chain.process_interaction("assistant", f"Old response {i}")

    # Trigger cleanup
    memory_chain.cleanup()

    # Verify cleanup results
    window = memory_chain.short_term.get_current_window()
    assert len(window.interactions) <= memory_chain.config.max_window_size


if __name__ == "__main__":
    pytest.main([__file__])
