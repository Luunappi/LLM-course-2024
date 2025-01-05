"""Test configuration for AgentFormer"""

import pytest
import logging
from unittest.mock import patch, Mock

# Konfiguroi testien lokitus
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def orchestrator():
    """Provide configured orchestrator for tests"""
    from core.orchestrator import AgentFormerOrchestrator

    return AgentFormerOrchestrator()


@pytest.fixture
def models():
    """Provide configured models for tests"""
    from ui_components.model_module import Models

    return Models()


@pytest.fixture(autouse=True)
def mock_openai():
    """Mock OpenAI API for all tests"""
    with patch("openai.OpenAI") as mock:
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Helsinki on Suomen pääkaupunki"))
        ]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock
