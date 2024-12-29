"""Integration tests for RAG Chat UI"""

import pytest
import streamlit as st
from agentic.ui.rag_chat import RAGChatUI
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_ui_integration():
    """Test chat UI integration with RAG system"""
    # Mock OpenAI
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )

    with patch("openai.OpenAI", return_value=mock_client):
        # Initialize UI
        ui = RAGChatUI()
        await ui.initialize()

        # Verify session state
        assert "rag_manager" in st.session_state
        assert "messages" in st.session_state
        assert "processing_status" in st.session_state

        # Simulate document upload
        test_content = "This is a test document."
        await st.session_state.rag_manager.add_document(
            content=test_content, doc_id="test.txt", metadata={"type": "text"}
        )

        # Simulate chat interaction
        query = "What is in the test document?"
        result = await st.session_state.rag_manager.query(query)

        # Add to chat history
        st.session_state.messages.extend(
            [
                {"role": "user", "content": query},
                {
                    "role": "assistant",
                    "content": result["response"],
                    "context": result["context"],
                    "metadata": result["metadata"],
                },
            ]
        )

        # Verify chat history
        assert len(st.session_state.messages) == 2
        assert st.session_state.messages[0]["role"] == "user"
        assert st.session_state.messages[1]["role"] == "assistant"
        assert "context" in st.session_state.messages[1]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_ui_file_handling():
    """Test file upload handling in chat UI"""
    ui = RAGChatUI()
    await ui.initialize()

    # Mock file with invalid encoding
    mock_file = MagicMock()
    mock_file.read.return_value = b"\x80\x81\x82"  # Invalid UTF-8
    mock_file.name = "test.txt"
    mock_file.type = "text/plain"
    mock_file.size = 100

    # Test with invalid UTF-8
    with patch("streamlit.file_uploader", return_value=mock_file):
        await ui.render_sidebar()
        assert "merkistökoodausta ei tueta" in st.error.mock_calls[0].args[0]

    # Test with file read error
    mock_file.read.side_effect = Exception("Read error")
    with patch("streamlit.file_uploader", return_value=mock_file):
        await ui.render_sidebar()
        assert "Virhe tiedoston käsittelyssä" in st.error.mock_calls[1].args[0]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_summary_generation():
    """Test document summary generation"""
    ui = RAGChatUI()
    await ui.initialize()

    # Mock OpenAI
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test summary response"))]
    )

    # Mock file content
    test_files = {
        "doc1.txt": "This is test document 1 content.",
        "doc2.txt": "This is test document 2 content.",
    }

    # Korjattu mock Path.read_text
    def mock_read_text(path):
        return test_files[path.name]

    with (
        patch("openai.OpenAI", return_value=mock_client),
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "read_text", side_effect=mock_read_text),
    ):
        # Add test documents to file manager
        for name, content in test_files.items():
            await ui.file_manager.save_file(
                MagicMock(name=name, type="text/plain", size=len(content)),
                {"indexed": True},
            )

        # Generate summary
        result = await ui._generate_summary()

        # Verify response structure
        assert isinstance(result, dict)
        assert "response" in result
        assert "context" in result
        assert "metadata" in result

        # Verify metadata
        metadata = result["metadata"]
        assert metadata["document_count"] == 2
        assert "total_tokens" in metadata
        assert "estimated_cost" in metadata

        # Verify context contains all documents
        context_docs = {ctx["doc_id"] for ctx in result["context"]}
        assert context_docs == set(test_files.keys())

        # Verify process tracking
        assert "Test summary response" in result["response"]
