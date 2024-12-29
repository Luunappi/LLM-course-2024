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
