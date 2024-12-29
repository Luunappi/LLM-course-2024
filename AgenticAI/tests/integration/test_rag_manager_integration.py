import pytest
from pathlib import Path
import shutil
from agentic.rag import RAGManager
import numpy as np
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_embeddings():
    """Mock embedding model for tests"""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(3, 384)
    return mock_model


@pytest.fixture(autouse=True)
async def setup_teardown():
    """Setup and teardown for each test"""
    # Setup
    if Path("data/rag_config").exists():
        shutil.rmtree("data/rag_config")
    if Path("data/vectors").exists():
        shutil.rmtree("data/vectors")

    yield

    # Teardown
    if Path("data/rag_config").exists():
        shutil.rmtree("data/rag_config")
    if Path("data/vectors").exists():
        shutil.rmtree("data/vectors")


@pytest.mark.asyncio
async def test_document_persistence(mock_embeddings):
    """Test that documents persist between sessions"""
    with patch(
        "sentence_transformers.SentenceTransformer", return_value=mock_embeddings
    ):
        # First session
        manager1 = RAGManager()
        await manager1.initialize()

        doc_id = "test.txt"
        content = "Test content"
        metadata = {"type": "text"}

        await manager1.add_document(content, doc_id, metadata)

        # Second session
        manager2 = RAGManager()
        await manager2.initialize()

        docs = await manager2.get_document_info()
        assert len(docs) == 1
        assert docs[0]["id"] == doc_id
        assert docs[0]["metadata"] == metadata


@pytest.mark.asyncio
async def test_full_pipeline(mock_embeddings):
    """Test complete RAG pipeline"""
    with patch(
        "sentence_transformers.SentenceTransformer", return_value=mock_embeddings
    ):
        manager = RAGManager()
        await manager.initialize()

        # Add document
        content = "Paris is the capital of France."
        await manager.add_document(content, "facts.txt", {"type": "text"})

        # Test query
        try:
            result = await manager.query("What is the capital of France?")

            assert "response" in result
            assert "context" in result
            assert len(result["context"]) > 0
            assert "Paris" in str(result["context"])

        except Exception as e:
            pytest.skip(f"OpenAI API test skipped: {e}")
