"""Test model configuration and API connectivity"""

import pytest
from agentic.config.model_config import ModelType, get_model_config
from agentic.rag.generator import Generator
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def load_env():
    """Load environment variables"""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.fail("OPENAI_API_KEY puuttuu .env tiedostosta")
    elif api_key == "your-openai-key-here":
        pytest.fail("OPENAI_API_KEY on oletusarvo, aseta oikea avain")


@pytest.mark.asyncio
async def test_openai_models_individually():
    """Test each OpenAI model separately"""
    logger.info("Testing OpenAI models individually...")

    test_query = "What is the capital of Finland?"
    test_context = [{"chunk": "Helsinki is the capital city of Finland."}]

    # Test each model type
    for model_type in ModelType:
        logger.info(f"\nTesting {model_type.value} model...")
        generator = Generator()
        config = generator.model_config

        logger.info(f"Model: {config.model_id}")
        logger.info(f"Context length: {config.context_length}")
        logger.info(
            f"Costs per 1M tokens: Input=${config.input_cost}, Output=${config.output_cost}"
        )

        try:
            response = await generator.generate(query=test_query, context=test_context)
            logger.info(f"Response: {response[:100]}...")

            assert isinstance(response, str)
            assert len(response) > 0
            assert "Helsinki" in response

            logger.info(f"{model_type.value} model test: SUCCESS")

        except Exception as e:
            logger.error(f"{model_type.value} model test failed: {str(e)}")
            pytest.fail(f"{model_type.value} model test failed: {str(e)}")


@pytest.mark.asyncio
async def test_model_selection():
    """Test model selection logic"""
    logger.info("Testing model selection...")

    # Verify model configurations
    fast_config = get_model_config(ModelType.FAST)
    assert fast_config.model_id == "gpt-3.5-turbo"
    assert fast_config.context_length == 4096

    std_config = get_model_config(ModelType.STANDARD)
    assert std_config.model_id == "gpt-4"
    assert std_config.context_length == 8192

    adv_config = get_model_config(ModelType.ADVANCED)
    assert adv_config.model_id == "gpt-4-turbo"
    assert adv_config.context_length == 128000
