"""Kattavat testit MemoryRAG-järjestelmälle"""

import pytest
from memoryrag import MemoryRAG
from pathlib import Path
import json
import time


@pytest.fixture
def rag():
    """Fixture MemoryRAG:n alustukseen"""
    return MemoryRAG()


def test_memory_persistence(rag):
    """Testaa muistin pysyvyyttä"""
    # Tyhjennä ensin muisti
    rag.clear_memories()

    # Lisää testidataa
    rag._store_memory("core", "Testitieto", 1.0)

    # Tarkista muistin tila
    assert len(rag.memory_types["core"]) == 1
    assert rag.memory_types["core"][0]["content"] == "Testitieto"


def test_memory_decay(rag):
    """Testaa muistin vanhenemista"""
    # Lisää muisti menneisyydessä
    old_time = time.time() - 3600  # tunti sitten
    rag._store_memory("episodic", "Vanha muisti", 0.8)
    rag.memory_types["episodic"][-1]["timestamp"] = old_time

    # Päivitä tärkeys
    new_importance = rag.memory_manager.update_importance(
        rag.memory_types["episodic"][-1]
    )

    # Tarkista että tärkeys on laskenut
    assert new_importance < 0.8


def test_context_building(rag):
    """Testaa kontekstin rakentamista"""
    # Lisää erilaista dataa
    rag._store_memory("core", "Määritelmä", 1.0)
    rag._store_memory("semantic", "Taustatieto", 0.8)
    rag._store_memory("episodic", "Historia", 0.6)

    # Testaa eri kysymystyyppejä
    what_context = rag.context_manager.build_context("Mitä tämä on?")
    how_context = rag.context_manager.build_context("Miten tämä toimii?")
    when_context = rag.context_manager.build_context("Milloin tämä tapahtui?")

    # Tarkista että konteksti painottuu oikein
    assert "Määritelmä" in what_context  # määritelmäkysymys -> core
    assert "Taustatieto" in how_context  # prosessikysymys -> semantic
    assert "Historia" in when_context  # aikakysymys -> episodic


def test_memory_optimization(rag):
    """Testaa muistin optimointia"""
    # Lisää samankaltaista dataa
    similar_data = [
        "Python versio 3.8 julkaistiin",
        "Python 3.8 tuli saataville",
        "Python 3.8 release tapahtui",
    ]

    for data in similar_data:
        rag._store_memory("semantic", data, 0.7)

    # Tiivistä muisti
    original_count = len(rag.memory_types["semantic"])
    compressed = rag.memory_manager.compress_memories(rag.memory_types["semantic"])

    # Tarkista tiivistys
    assert len(compressed) < original_count
    assert any("Python" in m["content"] for m in compressed)


def test_error_handling(rag):
    """Testaa virheenkäsittelyä"""
    # Testaa virheellistä muistityyppiä
    with pytest.raises(KeyError):
        rag._store_memory("invalid_type", "test", 1.0)

    # Testaa liian pitkää kontekstia
    huge_text = "x" * 1000
    truncated = rag.context_manager._truncate_context(huge_text, 50)
    # Tarkista että teksti on lyhentynyt merkittävästi
    assert len(truncated) < len(huge_text)

    # Testaa puuttuvaa API-avainta
    original_client = rag.client
    rag.client = None
    try:
        response = rag.process_query("test")
        assert "virhe" in response.lower()
    finally:
        rag.client = original_client


def test_semantic_search(rag):
    """Testaa semanttista hakua"""
    # Lisää testidataa
    rag._store_memory("semantic", "Kissa on kotieläin", 0.8)
    rag._store_memory("semantic", "Koira on lemmikki", 0.8)

    # Hae semanttisesti
    results = rag._search_memories("Kerro lemmikeistä", rag.memory_types["semantic"])

    # Tarkista tulokset
    assert len(results) > 0
    assert all("similarity" in r for r in results)
    assert sorted(results, key=lambda x: x["similarity"], reverse=True)


def test_integration(rag):
    """Testaa kokonaisuuden toimintaa"""
    # Lisää dataa eri muistityyppeihin
    rag._store_memory("core", "AI on tekoäly", 1.0)
    rag._store_memory("semantic", "AI kehitettiin 1950", 0.8)

    # Tee useita kyselyitä
    queries = [
        "Mitä AI tarkoittaa?",
        "Milloin AI kehitettiin?",
        "Miten AI liittyy aiempaan?",
    ]

    responses = []
    for query in queries:
        response = rag.process_query(query)
        responses.append(response)

    # Tarkista vastaukset ja muistin tila
    assert len(responses) == len(queries)
    assert len(rag.memory_types["episodic"]) >= len(queries)
    assert len(rag.memory_types["working"]) > 0
