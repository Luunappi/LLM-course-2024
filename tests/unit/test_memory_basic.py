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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_memory_store(rag):
    """Testaa muistin tallennusta"""
    await rag._store_memory("core", "Test content", 1.0)
    assert len(rag.memory_types["core"]) == 1
    assert rag.memory_types["core"][0]["content"] == "Test content"
    assert rag.memory_types["core"][0]["importance"] == 1.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_memory_clear(rag):
    """Testaa muistin tyhjennystä"""
    await rag._store_memory("semantic", "Test content", 0.8)
    await rag.clear_memories()
    assert len(rag.memory_types["semantic"]) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_api_connection(rag):
    """Testaa API-yhteyden toimivuutta"""
    await rag._test_api_connection()  # Should not raise exception


@pytest.mark.unit
@pytest.mark.asyncio
async def test_memory_importance(rag):
    """Testaa muistin tärkeysjärjestystä"""
    await rag._store_memory("semantic", "Less important", 0.5)
    await rag._store_memory("semantic", "Very important", 1.0)

    memories = rag.memory_types["semantic"]
    assert memories[1]["importance"] > memories[0]["importance"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_memory_type(rag):
    """Testaa virheellisen muistityypin käsittelyä"""
    with pytest.raises(KeyError):
        await rag._store_memory("invalid_type", "Test content", 1.0)
