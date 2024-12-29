import pytest
from agentic.ui.rag_chat import RAGChatUI
import streamlit as st


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_chat_flow():
    """Test complete chat flow from file upload to response"""
    ui = RAGChatUI()
    await ui.initialize()

    # Test file upload
    with open("test_data/sample.pdf", "rb") as f:
        await ui.handle_file_upload(f)

    # Test query and response
    await ui.handle_query("What is in the document?")

    # Verify chat history and context
    assert len(st.session_state.messages) > 0
    assert "context" in st.session_state.messages[-1]


@pytest.mark.integration
async def test_multiple_document_handling():
    """Test handling multiple document uploads and queries"""
    ui = RAGChatUI()
    await ui.initialize()

    # Upload multiple documents
    test_files = ["doc1.pdf", "doc2.pdf", "doc3.txt"]
    for file in test_files:
        with open(f"test_data/{file}", "rb") as f:
            await ui.handle_file_upload(f)

    # Verify documents are searchable
    await ui.handle_query("Find information from all documents")
    assert len(st.session_state.messages[-1]["context"]) > 0
