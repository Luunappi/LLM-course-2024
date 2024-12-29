"""Unit tests for RAG Chat UI"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import streamlit as st
from agentic.ui.rag_chat import RAGChatUI


@pytest.fixture
def mock_streamlit():
    """Mock all relevant Streamlit functions"""
    with (
        patch("streamlit.set_page_config") as mock_config,
        patch("streamlit.sidebar") as mock_sidebar,
        patch("streamlit.file_uploader") as mock_uploader,
        patch("streamlit.chat_message") as mock_chat_message,
        patch("streamlit.chat_input") as mock_chat_input,
    ):
        mock_uploader.return_value = None
        mock_chat_input.return_value = None
        yield {
            "config": mock_config,
            "sidebar": mock_sidebar,
            "uploader": mock_uploader,
            "chat_message": mock_chat_message,
            "chat_input": mock_chat_input,
        }


@pytest.fixture
async def chat_ui(mock_streamlit):
    """Fixture for RAGChatUI with mocked dependencies"""
    ui = RAGChatUI()
    st.session_state.rag_manager = MagicMock()
    st.session_state.rag_manager.initialize = AsyncMock()
    st.session_state.rag_manager.query = AsyncMock(
        return_value={
            "response": "Test response",
            "context": [{"chunk": "test context", "doc_id": "test.txt"}],
            "metadata": {"used_documents": ["test.txt"]},
        }
    )
    await ui.initialize()
    return ui


@pytest.mark.asyncio
async def test_file_upload_handling(chat_ui, mock_streamlit):
    """Test file upload functionality"""
    mock_file = MagicMock()
    mock_file.name = "test.pdf"
    mock_file.read.return_value = b"test content"

    mock_streamlit["uploader"].return_value = mock_file

    await chat_ui.handle_file_upload(mock_file)

    # Verify file was processed
    st.session_state.rag_manager.add_document.assert_called_once()


@pytest.mark.asyncio
async def test_query_processing(chat_ui):
    """Test query processing and response handling"""
    test_query = "test question"

    # Simulate query processing
    await chat_ui.handle_query(test_query)

    # Verify query was processed
    st.session_state.rag_manager.query.assert_called_once_with(
        test_query, query_type=chat_ui.query_type
    )

    # Verify messages were added to chat history
    assert len(st.session_state.messages) == 2
    assert st.session_state.messages[0]["content"] == test_query
    assert st.session_state.messages[1]["content"] == "Test response"


@pytest.mark.asyncio
async def test_query_type_switching(chat_ui):
    """Test switching between different query types"""
    # Test RAG query
    chat_ui.query_type = "rag"
    await chat_ui.handle_query("test rag query")
    assert st.session_state.rag_manager.query.call_args[1]["query_type"] == "rag"

    # Test direct query
    chat_ui.query_type = "direct"
    await chat_ui.handle_query("test direct query")
    assert st.session_state.rag_manager.query.call_args[1]["query_type"] == "direct"


@pytest.mark.asyncio
async def test_error_handling(chat_ui):
    """Test error handling in UI"""
    # Simulate error in RAG manager
    st.session_state.rag_manager.query.side_effect = Exception("Test error")

    with pytest.raises(Exception):
        await chat_ui.handle_query("test query")
