"""Integraatiotestit muistin tallennukselle ja lataukselle"""

import pytest
import pytest_asyncio
import time
from memoryrag import MemoryRAG


@pytest_asyncio.fixture(scope="function")
async def rag():
    instance = await MemoryRAG.create()
    yield instance
    await instance.clear_memories()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_cleanup(rag):
    """Testaa vanhojen muistien siivousta"""
    # Testisisältö...
