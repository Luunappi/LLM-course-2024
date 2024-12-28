"""Yksikkötestit perusominaisuuksille"""

import pytest
import pytest_asyncio
from memoryrag import MemoryRAG


@pytest_asyncio.fixture(scope="function")
async def rag():
    """Create fresh MemoryRAG instance for each test."""
    instance = await MemoryRAG.create()
    yield instance
    await instance.clear_memories()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_memory_types_init(rag):
    """Testaa että muistityypit alustetaan oikein."""
    assert isinstance(rag.memory_types, dict)
    assert all(
        k in rag.memory_types for k in ["core", "semantic", "episodic", "working"]
    )
