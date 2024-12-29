"""Test configuration and fixtures"""

import pytest
import asyncio
import streamlit as st
from pathlib import Path
import shutil
import os
from unittest.mock import patch


@pytest.fixture(scope="session", autouse=True)
def mock_openai_env():
    """Mock OpenAI API key for tests"""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        yield


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_streamlit():
    """Initialize Streamlit session state for all tests"""
    # Alusta session state
    if "rag_manager" not in st.session_state:
        st.session_state.rag_manager = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "processing_status" not in st.session_state:
        st.session_state.processing_status = None


@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Clean up test data before and after each test"""
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
