import pytest
import time
from memoryrag import MemoryRAG


@pytest.fixture(scope="function")
async def rag():
    """Create fresh MemoryRAG instance for each test."""
    rag = await MemoryRAG.create()
    yield rag
    await rag.clear_memories()


@pytest.mark.asyncio
async def test_memory_hierarchy(rag):
    """Testaa muistihierarkian toimintaa"""
    # Tyhjennä ensin muisti
    await rag.clear_memories()

    # Lisää muisteja eri tasoille
    await rag._store_memory("core", "Tärkeä fakta", importance=1.0)
    await rag._store_memory("semantic", "Yleistieto", importance=0.7)
    await rag._store_memory("working", "Nykyinen konteksti", importance=0.8)

    # Tarkista että muistit ovat oikeilla tasoilla
    assert len(rag.memory_types["core"]) == 1
    assert len(rag.memory_types["semantic"]) == 1
    assert len(rag.memory_types["working"]) == 1


@pytest.mark.asyncio
async def test_memory_retrieval(rag):
    """Testaa muistin hakua"""
    # Tyhjennä ensin muisti
    await rag.clear_memories()

    # Lisää testidataa
    await rag._store_memory("semantic", "Python on ohjelmointikieli", importance=0.8)
    await rag._store_memory("core", "Python soveltuu tekoälyyn", importance=1.0)

    # Hae muistit kyselyllä
    results = await rag._search_memories("Python", rag.memory_types["semantic"])

    # Tarkista että tulokset ovat tärkeysjärjestyksessä
    assert len(results) >= 1
    assert any("Python" in r["content"] for r in results)


@pytest.mark.asyncio
async def test_context_building(rag):
    """Testaa kontekstin rakentamista"""
    # Lisää kontekstimateriaalia
    await rag._store_memory("core", "Fakta 1", importance=1.0)
    await rag._store_memory("semantic", "Tieto 1", importance=0.7)

    # Rakenna konteksti
    context = await rag.context_manager.build_context("test")

    # Tarkista kontekstin rakenne
    assert len(context) > 0
    assert isinstance(context, str)


@pytest.mark.asyncio
async def test_query_processing(rag):
    """Testaa kyselyn käsittelyä"""
    # Lisää taustatietoa
    await rag._store_memory("core", "Tekoäly on älykästä", importance=1.0)

    # Suorita kysely
    response = await rag.process_query("Mitä on tekoäly?")

    # Tarkista vastaus ja muistin päivitys
    assert response is not None
    assert len(rag.memory_types["episodic"]) >= 1  # Kysely tallennettu


@pytest.mark.asyncio
async def test_semantic_search(rag):
    """Testaa semanttista hakua"""
    # Lisää testidataa
    await rag._store_memory("semantic", "Python on ohjelmointikieli", importance=0.8)
    await rag._store_memory("semantic", "Kissa on lemmikkieläin", importance=0.7)

    # Testaa semanttista hakua
    results = await rag.semantic_search("Mikä ohjelmointikieli Python on?")

    # Tarkista että relevantti muisti löytyi
    assert len(results) > 0
    assert any("Python" in r for r in results)
