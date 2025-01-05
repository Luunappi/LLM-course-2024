"""OpenAI API Tests"""

import pytest
from unittest.mock import Mock, patch
from ui_components.model_module import Models


@pytest.fixture
def mock_openai():
    with patch("openai.OpenAI") as mock:
        # Mock response structure
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Helsinki on Suomen pääkaupunki"))
        ]

        # Mock client
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response

        mock.return_value = mock_client
        yield mock


@pytest.fixture
def models():
    """Provide test models instance"""
    return Models()


def test_api_error_handling(mock_openai, models):
    """Test API error handling"""
    mock_openai.return_value.chat.completions.create.side_effect = Exception(
        "API Error"
    )
    response = models.generate_response("Test error")
    assert response == ""
