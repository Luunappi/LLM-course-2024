import pytest
import asyncio
from agentic.memory import MemoryManager
from pathlib import Path
import shutil


@pytest.fixture
async def memory_manager():
    """Fixture memory managerin testaukseen"""
    manager = MemoryManager()
    await manager.initialize()
    yield manager
    # Siivoa testidatat
    if Path("data/memories").exists():
        shutil.rmtree("data/memories")


@pytest.mark.asyncio
async def test_store_and_search_memory(memory_manager):
    """Testaa muistin tallennuksen ja haun"""
    # Tallenna testimuisti
    test_content = "Tämä on testitekstiä"
    await memory_manager.store_memory("episodic", test_content, 1.0)

    # Hae muistista
    memories = await memory_manager.search_memories("testitekstiä", "episodic")

    assert len(memories) == 1
    assert memories[0]["content"] == test_content
    assert memories[0]["importance"] == 1.0
    assert "timestamp" in memories[0]


@pytest.mark.asyncio
async def test_invalid_memory_type(memory_manager):
    """Testaa virheellisen muistityypin käsittelyn"""
    with pytest.raises(ValueError):
        await memory_manager.store_memory("invalid_type", "test", 1.0)

    with pytest.raises(ValueError):
        await memory_manager.search_memories("test", "invalid_type")


@pytest.mark.asyncio
async def test_multiple_memories(memory_manager):
    """Testaa useiden muistien tallennuksen ja haun"""
    # Tallenna useita muisteja
    await memory_manager.store_memory("semantic", "ensimmäinen muisti", 0.5)
    await memory_manager.store_memory("semantic", "toinen muisti", 0.7)
    await memory_manager.store_memory("semantic", "kolmas muisti", 0.9)

    # Hae muisteja
    memories = await memory_manager.search_memories("muisti", "semantic")
    assert len(memories) == 3
