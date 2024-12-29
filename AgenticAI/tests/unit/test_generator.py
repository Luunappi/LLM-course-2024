"""Unit tests for Generator"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agentic.rag import Generator


@pytest.fixture
async def get_mock_generator():
    """Fixture for getting a mocked generator"""
    # Mock OpenAI client and response
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()

    # Mock response structure
    class MockChoice:
        def __init__(self):
            self.message = MagicMock(content="Test response")

    mock_response = MagicMock()
    mock_response.choices = [MockChoice()]
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        gen = Generator()
        await gen.initialize()
        return gen


@pytest.mark.unit
def test_build_prompt(get_mock_generator):
    """Test prompt building"""
    generator = get_mock_generator
    query = "What is the capital of France?"
    context = [
        {"chunk": "Paris is the capital of France."},
        {"chunk": "France is a country in Europe."},
    ]

    prompt = generator._build_prompt(query, context)
    assert query in prompt
    assert "Context 1" in prompt
    assert "Paris is the capital" in prompt


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generator_response(get_mock_generator):
    """Test response generation"""
    generator = get_mock_generator
    response = await generator.generate(
        query="test query", context=[{"chunk": "test context"}]
    )
    assert isinstance(response, str)
    assert response == "Test response"  # Tarkistetaan mockattu vastaus

    # Verify that OpenAI API was called with correct parameters
    generator.client.chat.completions.create.assert_called_once()
    call_args = generator.client.chat.completions.create.call_args[1]
    assert call_args["model"] == "gpt-3.5-turbo"
    assert len(call_args["messages"]) == 2
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][1]["role"] == "user"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generator_error_handling(get_mock_generator):
    """Test error handling in generation"""
    generator = get_mock_generator

    # Mock OpenAI error
    generator.client.chat.completions.create.side_effect = Exception("API Error")

    with pytest.raises(Exception) as exc_info:
        await generator.generate(query="test", context=[{"chunk": "test"}])
    assert "API Error" in str(exc_info.value)
