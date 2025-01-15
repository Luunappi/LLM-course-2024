import pytest
import time
import numpy as np
from memoryrag import MemoryRAG


@pytest.fixture(scope="function")
async def rag():
    """Create fresh MemoryRAG instance for each test."""
    rag = await MemoryRAG.create()
    yield rag
    await rag.clear_memories()


@pytest.mark.asyncio
async def test_memory_decay(rag):
    """Testaa muistin vanhenemista"""
    # Lisää testidataa
    await rag._store_memory("semantic", "Test content", 0.8)

    # Aseta vanha aikaleima
    old_time = time.time() - (rag.max_age_days + 1) * 24 * 60 * 60
    rag.memory_types["semantic"][-1]["timestamp"] = old_time

    # Suorita puhdistus
    await rag.cleanup_old_embeddings()

    # Tarkista että vanha muisti poistettiin
    assert len(rag.memory_types["semantic"]) == 0


@pytest.mark.asyncio
async def test_memory_clustering(rag):
    """Testaa muistien klusterointia"""
    # Lisää samankaltaista dataa
    test_data = [
        "Python on ohjelmointikieli",
        "Python kielessä on hyvä syntaksi",
        "Python soveltuu datatieteeseen",
    ]

    for content in test_data:
        await rag._store_memory("semantic", content, 0.8)

    # Suorita klusterointi
    clusters = await rag.memory_manager.cluster_memories(rag.memory_types["semantic"])

    # Tarkista klusterit
    assert len(clusters) > 0
    assert all("Python" in cluster[0]["content"] for cluster in clusters)


@pytest.mark.asyncio
async def test_memory_compression_quality(rag):
    """Testaa muistin tiivistyksen laatua"""
    # Lisää toistuvaa dataa
    original_data = [
        "Python versio 3.8 julkaistiin",
        "Python 3.8 tuli saataville",
        "Python 3.8 release tapahtui",
        "Täysin eri aihe tässä",
    ]

    for content in original_data:
        await rag._store_memory("semantic", content, 0.7)

    # Tiivistä muistit
    compressed = await rag.memory_manager.compress_memories(
        rag.memory_types["semantic"]
    )

    # Tarkista laatu
    assert len(compressed) < len(original_data)
    assert any("Python 3.8" in m["content"] for m in compressed)
    assert any("eri aihe" in m["content"] for m in compressed)


@pytest.mark.asyncio
async def test_memory_usage_tracking(rag):
    """Testaa muistin käytön seurantaa"""
    # Lisää dataa
    for i in range(10):
        await rag._store_memory("semantic", f"Test content {i}", 0.8)

    # Tarkista muistin käyttö
    usage = await rag.memory_manager.get_memory_usage()
    assert usage["total_memories"] >= 10
    assert usage["embeddings_size"] > 0
    assert "memory_types" in usage
