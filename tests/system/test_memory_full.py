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
async def test_full_query_cycle(rag):
    """Testaa koko kysely-vastaus-sykliä"""
    # Lisää kontekstitietoa
    await rag._store_memory(
        "core", "Python on ohjelmointikieli, joka julkaistiin vuonna 1991.", 1.0
    )

    # Tee kysely
    response = await rag.process_query("Milloin Python julkaistiin?")

    # Tarkista vastaus
    assert response is not None
    assert "1991" in response

    # Tarkista että kysely tallentui työmuistiin
    assert len(rag.memory_types["working"]) > 0
    assert "Python" in rag.memory_types["working"][-1]["content"]


@pytest.mark.system
@pytest.mark.asyncio
async def test_memory_hierarchy(rag):
    """Testaa muistihierarkian toimintaa"""
    # Lisää eri tyyppistä dataa
    await rag._store_memory("core", "Tärkeä fakta", 1.0)
    await rag._store_memory("semantic", "Yleistieto", 0.7)
    await rag._store_memory("episodic", "Keskusteluhistoria", 0.5)
    await rag._store_memory("working", "Nykyinen konteksti", 0.8)

    # Tee kysely joka vaatii eri muistityyppien tietoa
    response = await rag.process_query("Kerro kaikki mitä tiedät tästä aiheesta.")

    # Tarkista että vastaus sisältää tietoa eri muistityypeistä
    assert "Tärkeä fakta" in response
    assert "Yleistieto" in response


@pytest.mark.system
@pytest.mark.asyncio
async def test_context_building(rag):
    """Testaa kontekstin rakentamista"""
    # Lisää erilaista kontekstidataa
    await rag._store_memory("core", "Tärkeä periaate", 1.0)
    await rag._store_memory("semantic", "Aiheeseen liittyvä tieto", 0.8)
    await rag._store_memory("episodic", "Aiempi keskustelu", 0.6)

    # Rakenna konteksti kyselylle
    context = await rag.context_manager.build_context("Testikysely")

    # Tarkista että konteksti sisältää dataa eri muistityypeistä
    assert context is not None
    assert len(context) > 0
    assert "Tärkeä periaate" in context
