import sys
from pathlib import Path

# Lisää projektin juurikansio Python-polkuun
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

import pytest
from src.memoryrag import MemoryRAG


@pytest.fixture
def rag():
    """Luo MemoryRAG-instanssi testeille"""
    return MemoryRAG()


def test_memory_hierarchy(rag):
    """Testaa muistihierarkian toimintaa"""
    # Tyhjennä ensin muisti
    rag.clear_memories()

    # Lisää muisteja eri tasoille
    rag._store_memory("core", "Tärkeä fakta", importance=1.0)
    rag._store_memory("semantic", "Yleistieto", importance=0.7)
    rag._store_memory("working", "Nykyinen konteksti", importance=0.8)

    # Tarkista että muistit ovat oikeilla tasoilla
    assert len(rag.memory_types["core"]) == 1
    assert len(rag.memory_types["semantic"]) == 1
    assert len(rag.memory_types["working"]) == 1


def test_memory_retrieval(rag):
    """Testaa muistin hakua"""
    # Tyhjennä ensin muisti
    rag.clear_memories()

    # Lisää testidataa
    rag._store_memory("semantic", "Python on ohjelmointikieli", importance=0.8)
    rag._store_memory("core", "Python soveltuu tekoälyyn", importance=1.0)

    # Hae muistit kyselyllä
    results = rag._search_memories("Python", rag.memory_types["semantic"])

    # Tarkista että tulokset ovat tärkeysjärjestyksessä
    assert len(results) == 1
    assert "Python" in results[0]["content"]


def test_context_building(rag):
    """Testaa kontekstin rakentamista"""
    # Lisää kontekstimateriaalia
    rag._store_memory("core", "Fakta 1", importance=1.0)
    rag._store_memory("semantic", "Tieto 1", importance=0.7)

    # Rakenna konteksti
    context = rag.context_manager.build_context("test")

    # Tarkista kontekstin rakenne
    assert "Core Memories" in context
    assert "Fakta 1" in context


def test_query_processing(rag):
    """Testaa kyselyn käsittelyä"""
    # Lisää taustatietoa
    rag._store_memory("core", "Tekoäly on älykästä", importance=1.0)

    # Suorita kysely
    response = rag.process_query("Mitä on tekoäly?")

    # Tarkista vastaus ja muistin päivitys
    assert response is not None
    assert len(rag.memory_types["episodic"]) == 1  # Kysely tallennettu


def test_semantic_search():
    """Testaa semanttista hakua"""
    rag = MemoryRAG()

    # Lisää testidataa
    rag._store_memory("semantic", "Python on ohjelmointikieli", 0.8)
    rag._store_memory("semantic", "Kissa on lemmikkieläin", 0.7)

    # Testaa semanttista hakua
    results = rag._search_memories(
        "Mikä ohjelmointikieli Python on?", rag.memory_types["semantic"]
    )

    # Tarkista että relevantti muisti löytyi
    assert "Python" in results[0]["content"]
    assert results[0]["similarity"] > 0.5


if __name__ == "__main__":
    pytest.main([__file__])
