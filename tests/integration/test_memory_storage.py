"""Integraatiotestit muistin ja tallennuksen yhteistoiminnalle"""

import pytest
import pytest_asyncio
from memoryrag import MemoryRAG
import time


@pytest_asyncio.fixture(scope="function")
async def rag():
    instance = await MemoryRAG.create()
    yield instance
    await instance.clear_memories()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_persistence(rag):
    """Testaa muistin pysyvyyttä"""
    # Tallenna muistiin
    await rag._store_memory("core", "Test persistence", 1.0)

    # Tarkista että muisti on tallennettu
    loaded = await rag.storage.load_memories()
    assert len(loaded["core"]) == 1
    assert loaded["core"][0]["content"] == "Test persistence"

    # Tyhjennä muisti
    await rag.clear_memories()

    # Tarkista että muisti on tyhjennetty sekä muistista että levyltä
    loaded = await rag.storage.load_memories()
    assert len(loaded["core"]) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_manager_cleanup(rag):
    """Testaa muistinhallinnan siivousta"""
    # Lisää vanha muisti
    old_time = time.time() - (rag.max_age_days + 1) * 24 * 60 * 60
    await rag._store_memory(
        "episodic", "Old memory", 0.5, metadata={"timestamp": old_time}
    )

    # Lisää tuore muisti
    await rag._store_memory("episodic", "Fresh memory", 0.5)

    # Suorita siivous
    await rag.cleanup_old_embeddings()

    # Tarkista että vain tuore muisti jäi
    assert len(rag.memory_types["episodic"]) == 1
    assert rag.memory_types["episodic"][0]["content"] == "Fresh memory"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_search(rag):
    """Testaa muistin semanttista hakua"""
    await rag._store_memory(
        "semantic", "Tekoäly on tietokoneiden kyky simuloida älykästä toimintaa", 0.8
    )
    await rag._store_memory("semantic", "Kissat ovat suosittuja lemmikkieläimiä", 0.7)

    results = await rag._search_memories(
        "Mitä on tekoäly?", rag.memory_types["semantic"]
    )
    assert len(results) > 0
    assert "tekoäly" in results[0]["content"].lower()
