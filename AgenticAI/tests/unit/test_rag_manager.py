"""Unit tests for RAG Manager"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import json
from agentic.rag import RAGManager


@pytest.fixture
async def rag_manager():
    """Fixture for RAGManager testing with mocked components"""
    manager = RAGManager()

    # Mock Retriever
    manager.retriever = MagicMock()
    manager.retriever.initialize = AsyncMock()
    manager.retriever.add_text = AsyncMock()
    manager.retriever.search = AsyncMock(
        return_value=[{"doc_id": "test.txt", "chunk": "test content", "score": 0.9}]
    )

    # Mock Generator
    manager.generator = MagicMock()
    manager.generator.initialize = AsyncMock()
    manager.generator.generate = AsyncMock(return_value="Generated response")

    await manager.initialize()
    return manager


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialization(rag_manager):
    """Test RAGManager initialization"""
    # Verify that components were initialized
    rag_manager.retriever.initialize.assert_called_once()
    rag_manager.generator.initialize.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_document(rag_manager):
    """Test document addition"""
    doc_id = "test.txt"
    content = "Test content"
    metadata = {"type": "text"}

    await rag_manager.add_document(content, doc_id, metadata)

    # Verify document was added to retriever
    rag_manager.retriever.add_text.assert_called_once_with(content, doc_id)

    # Verify metadata was stored
    assert doc_id in rag_manager.documents
    assert rag_manager.documents[doc_id]["metadata"] == metadata
    assert rag_manager.documents[doc_id]["indexed"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query(rag_manager):
    """Test query processing"""
    query = "test query"
    result = await rag_manager.query(query)

    # Verify retriever was called
    rag_manager.retriever.search.assert_called_once_with(query, top_k=3)

    # Verify generator was called with correct context
    context = rag_manager.retriever.search.return_value
    rag_manager.generator.generate.assert_called_once_with(query=query, context=context)

    # Verify response structure
    assert result["response"] == "Generated response"
    assert result["context"] == context
    assert result["metadata"]["used_documents"] == ["test.txt"]
    assert result["metadata"]["context_count"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_document_persistence(tmp_path):
    """Test document index persistence"""
    # Luo mock komponentit
    mock_retriever = MagicMock()
    mock_retriever.initialize = AsyncMock()
    mock_retriever.add_text = AsyncMock()

    mock_generator = MagicMock()
    mock_generator.initialize = AsyncMock()

    # Luo manager ja aseta mockit
    with (
        patch("agentic.rag.manager.Retriever", return_value=mock_retriever),
        patch("agentic.rag.manager.Generator", return_value=mock_generator),
    ):
        # Ensimmäinen manager
        manager = RAGManager()
        manager.config_path = tmp_path  # Käytä pytest:in tmp_path
        await manager.initialize()

        # Lisää dokumentti
        doc_id = "test.txt"
        metadata = {"type": "text"}
        await manager.add_document("content", doc_id, metadata)

        # Tarkista että indeksi tallennettiin
        index_path = tmp_path / "document_index.json"
        assert index_path.exists()

        # Toinen manager
        new_manager = RAGManager()
        new_manager.config_path = tmp_path
        await new_manager.initialize()

        # Tarkista että dokumentin tiedot ladattiin
        assert doc_id in new_manager.documents
        assert new_manager.documents[doc_id]["metadata"] == metadata


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_document_info(rag_manager):
    """Test document info retrieval"""
    # Add test documents
    rag_manager.documents = {
        "doc1": {"metadata": {"type": "text"}, "indexed": True},
        "doc2": {"metadata": {"type": "pdf"}, "indexed": True},
    }

    info = await rag_manager.get_document_info()

    assert len(info) == 2
    assert all("id" in doc for doc in info)
    assert all("metadata" in doc for doc in info)
    assert all("indexed" in doc for doc in info)
