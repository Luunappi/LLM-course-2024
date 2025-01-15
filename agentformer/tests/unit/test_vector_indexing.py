import pytest
import numpy as np
import faiss
import torch
import asyncio
from memoryrag import MemoryRAG


@pytest.fixture(scope="function")
async def rag():
    """Create fresh MemoryRAG instance for each test."""
    rag = await MemoryRAG.create()
    yield rag
    await rag.clear_memories()


@pytest.mark.asyncio
async def test_index_initialization(rag):
    """Testaa indeksin alustuksen eri datamäärille"""
    # Testaa pienen datamäärän indeksi
    n_vectors = 50_000
    embeddings = np.random.randn(n_vectors, rag.embedding_dim).astype(np.float32)

    # Alusta ja kouluta indeksi
    await rag._train_index_if_needed(embeddings)

    # Tarkista indeksin tyyppi ja parametrit
    assert isinstance(rag.index, faiss.IndexIVFFlat)
    assert rag.index.nlist == 100
    assert rag.index.nprobe == 10


@pytest.mark.asyncio
async def test_batch_processing(rag):
    """Testaa batch-prosessoinnin toiminta"""
    # Lisää testidataa
    test_data = [
        ("semantic", f"Test content {i}", 0.8) for i in range(rag.batch_size + 10)
    ]

    # Lisää muistit
    for mem_type, content, importance in test_data:
        await rag._store_memory(mem_type, content, importance)

    # Tarkista että batch on prosessoitu
    assert len(rag.pending_embeddings) < rag.batch_size
    assert len(rag.embeddings_index) >= rag.batch_size


@pytest.mark.asyncio
async def test_parallel_processing(rag):
    """Testaa rinnakkaista prosessointia"""
    # Luo testidataa
    n_items = rag.batch_size * 2
    embeddings = [
        np.random.randn(rag.embedding_dim).astype(np.float32) for _ in range(n_items)
    ]

    # Jaa batcheihin ja prosessoi
    chunks = [
        embeddings[i : i + rag.min_chunk_size]
        for i in range(0, len(embeddings), rag.min_chunk_size)
    ]

    # Prosessoi rinnakkain
    tasks = [rag._process_chunk(chunk) for chunk in chunks]
    processed = await asyncio.gather(*tasks)

    # Tarkista tulokset
    assert all(p is not None for p in processed)
    assert all(isinstance(p, np.ndarray) for p in processed)


@pytest.mark.asyncio
async def test_apple_silicon_optimization(rag):
    """Testaa Apple Silicon -optimoinnit"""
    if torch.backends.mps.is_available():
        assert rag.use_mps == True
        # Tarkista että embedding-malli on MPS-laitteella
        assert str(rag.embedding_model.device).startswith("mps")

        # Tarkista NEON-optimoinnit
        if hasattr(faiss, "supported_cpu_features"):
            features = faiss.supported_cpu_features()
            if "neon" in features:
                assert faiss.cvar.CPU_FEATURE_NEON == True
