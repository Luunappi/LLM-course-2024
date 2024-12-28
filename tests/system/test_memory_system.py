"""Järjestelmätason testit koko MemoryRAG:lle"""

import pytest
import pytest_asyncio
from memoryrag import MemoryRAG


@pytest_asyncio.fixture(scope="function")
async def rag():
    instance = await MemoryRAG.create()
    yield instance
    await instance.clear_memories()


@pytest.mark.system
@pytest.mark.asyncio
async def test_full_memory_cycle(rag):
    """Testaa muistin koko elinkaari"""
    # Testisisältö...
