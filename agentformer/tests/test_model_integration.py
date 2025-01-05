"""
Model Integration Tests

Testaa mallien integraation:
- OpenAI API -kutsut
- Mallien konfiguraatiot
- Virhetilanteiden käsittely
"""

import pytest
from unittest.mock import Mock, patch
from ui_components.model_module import Models


@pytest.fixture
def mock_openai():
    with patch("openai.OpenAI") as mock:
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Helsinki on Suomen pääkaupunki"))
        ]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock


def test_openai_api_parameters(mock_openai, models):
    """Test OpenAI API call parameters"""
    response = models.generate_response("Test message")

    # Tarkista API-kutsun parametrit
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Test message"}],
        temperature=0.7,
        max_tokens=500,
    )

    # Tarkista vastaus
    assert response == "Helsinki on Suomen pääkaupunki"


def test_model_switching(models):
    """Test model switching"""
    # Tarkista oletusmallin asetukset
    current = models.get_current_model()
    assert current["name"] == "gpt-4o-mini"

    # Tarkista virheellisen mallin käsittely
    assert models.set_model("non_existent_model") == False
    current = models.get_current_model()
    assert current["name"] == "gpt-4o-mini"  # Pysyy oletuksessa

    # Tarkista saatavilla olevat mallit
    available = models.get_available_models()
    assert "gpt-4o-mini" in available
    assert len(available) == 1  # Vain yksi malli käytössä


def test_api_error_handling(mock_openai, models):
    """Test API error handling"""
    mock_openai.return_value.chat.completions.create.side_effect = Exception(
        "API Error"
    )
    response = models.generate_response("Test error")
    assert response == ""  # Tyhjä vastaus virhetilanteessa
