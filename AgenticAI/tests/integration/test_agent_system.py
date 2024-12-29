"""Integration tests for complete agent system"""

import pytest
from agentic.core.orchestrator import Orchestrator
from agentic.agents.rag_agent import RAGAgent
from agentic.core.events import Event
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_system_integration():
    """Test complete agent system with RAG functionality"""
    # Mock OpenAI
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )

    with patch("openai.OpenAI", return_value=mock_client):
        # Initialize system
        orchestrator = Orchestrator()
        rag_agent = RAGAgent("rag_agent")

        # Register agent
        orchestrator.register_agent("rag", rag_agent)
        await orchestrator.initialize()

        # Add test document
        doc_event = Event(
            "add_document",
            {
                "content": "This is a test document.",
                "doc_id": "test.txt",
                "metadata": {"type": "text"},
            },
        )
        await orchestrator.handle_request("add_document", doc_event.data)

        # Test query
        query_event = Event("query", {"query": "What is in the document?"})
        await orchestrator.handle_request("query", query_event.data)

        # Verify event history
        assert len(orchestrator.event_bus.history) == 2
        assert orchestrator.event_bus.history[0].type == "add_document"
        assert orchestrator.event_bus.history[1].type == "query"

        # Verify agent responses
        assert rag_agent.rag_manager is not None
        docs = await rag_agent.rag_manager.get_document_info()
        assert len(docs) == 1
        assert docs[0]["id"] == "test.txt"
