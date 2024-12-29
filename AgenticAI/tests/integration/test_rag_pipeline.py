"""Integration tests for complete RAG pipeline"""

import pytest
from pathlib import Path
import shutil
from agentic.rag import RAGManager
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
async def setup_test_env():
    """Setup test environment"""
    # Cleanup before tests
    if Path("data/rag_config").exists():
        shutil.rmtree("data/rag_config")
    if Path("data/vectors").exists():
        shutil.rmtree("data/vectors")

    yield

    # Cleanup after tests
    if Path("data/rag_config").exists():
        shutil.rmtree("data/rag_config")
    if Path("data/vectors").exists():
        shutil.rmtree("data/vectors")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_rag_pipeline():
    """Test complete RAG pipeline with real E5 embeddings and mocked OpenAI"""
    # Mock OpenAI response
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()

    class MockChoice:
        def __init__(self):
            self.message = MagicMock(content="Python was created by Guido van Rossum.")

    mock_response = MagicMock()
    mock_response.choices = [MockChoice()]
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        # Initialize RAG system
        manager = RAGManager()
        await manager.initialize()

        # Add test documents
        docs = {
            "python_history.txt": """
            Python was created by Guido van Rossum and was first released in 1991.
            The language emphasizes code readability and uses significant whitespace.
            """,
            "python_features.txt": """
            Python supports multiple programming paradigms, including procedural,
            object-oriented, and functional programming.
            """,
        }

        for doc_id, content in docs.items():
            await manager.add_document(content, doc_id)

        # Test query
        result = await manager.query("Who created Python?")

        # Verify response
        assert "response" in result
        assert "context" in result
        assert "metadata" in result
        assert len(result["context"]) > 0
        assert "Guido" in str(result["context"])  # Relevantti konteksti löytyi
        assert "Python was created" in result["response"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_document_management():
    """Test document management functionality"""
    manager = RAGManager()
    await manager.initialize()

    # Add document with metadata
    doc_id = "test.txt"
    content = "This is a test document."
    metadata = {"type": "text", "author": "Test User"}

    await manager.add_document(content, doc_id, metadata)

    # Verify document was indexed
    docs = await manager.get_document_info()
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id
    assert docs[0]["metadata"] == metadata
    assert docs[0]["indexed"] is True

    # Verify persistence
    new_manager = RAGManager()
    await new_manager.initialize()

    loaded_docs = await new_manager.get_document_info()
    assert len(loaded_docs) == 1
    assert loaded_docs[0]["id"] == doc_id
    assert loaded_docs[0]["metadata"] == metadata
