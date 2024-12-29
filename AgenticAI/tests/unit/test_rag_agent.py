"""Unit tests for RAG Agent"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agentic.agents.rag_agent import RAGAgent
from agentic.core.events import Event


@pytest.fixture
async def rag_agent():
    """Fixture for RAGAgent testing"""
    agent = RAGAgent("test_agent")

    # Mock RAGManager
    agent.rag_manager = MagicMock()
    agent.rag_manager.initialize = AsyncMock()
    agent.rag_manager.query = AsyncMock(
        return_value={
            "response": "Test response",
            "context": [{"chunk": "test context"}],
            "metadata": {"used_documents": ["test.txt"]},
        }
    )
    agent.rag_manager.add_document = AsyncMock()

    await agent.initialize()
    return agent


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialization(rag_agent):
    """Test agent initialization"""
    rag_agent.rag_manager.initialize.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_handling(rag_agent):
    """Test query event handling"""
    event = Event("query", {"query": "test question"})
    result = await rag_agent.handle_query(event)

    rag_agent.rag_manager.query.assert_called_once_with("test question")
    assert result["response"] == "Test response"
    assert "context" in result
    assert "metadata" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_document_addition(rag_agent):
    """Test document addition handling"""
    event = Event(
        "add_document",
        {"content": "test content", "doc_id": "test.txt", "metadata": {"type": "text"}},
    )

    result = await rag_agent.handle_add_document(event)

    rag_agent.rag_manager.add_document.assert_called_once_with(
        content="test content", doc_id="test.txt", metadata={"type": "text"}
    )
    assert result["status"] == "success"
    assert result["doc_id"] == "test.txt"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_query(rag_agent):
    """Test handling invalid query event"""
    event = Event("query", {})  # Missing query field
    result = await rag_agent.handle_query(event)
    assert "error" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_document(rag_agent):
    """Test handling invalid document event"""
    event = Event("add_document", {})  # Missing required fields
    result = await rag_agent.handle_add_document(event)
    assert "error" in result
