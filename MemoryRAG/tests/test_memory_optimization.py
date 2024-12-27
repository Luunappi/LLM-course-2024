"""Testit muistin optimoinnille"""

import pytest
from memoryrag import MemoryRAG
import time


def test_memory_decay(rag):
    """Testaa muistin vanhenemista ja käyttöhistorian vaikutusta"""
    # Tyhjennä muisti
    rag.clear_memories()

    # Lisää muisti ja aseta vanha aikaleima
    old_time = time.time() - 3600  # tunti sitten
    memory = {
        "content": "Vanha muisti",
        "importance": 0.8,
        "timestamp": old_time,
        "use_count": 5,  # Paljon käyttöä
    }

    # Päivitä tärkeys
    new_importance = rag.memory_manager.update_importance(memory)

    # Tarkista että tärkeys on laskenut mutta käyttö nostaa sitä
    assert new_importance < 0.8  # Vanheneminen laskee
    assert new_importance > 0.4  # Käyttö nostaa


def test_memory_optimization(rag):
    """Testaa muistin automaattista optimointia"""
    # Tyhjennä muisti
    rag.clear_memories()

    # Lisää paljon muisteja
    for i in range(150):  # Yli max_memories
        rag._store_memory("semantic", f"Muisti {i}", importance=0.7 if i < 50 else 0.5)

    # Optimoi muisti
    rag.memory_manager.check_and_optimize_memory("semantic", max_memories=100)

    # Tarkista optimointi
    memories = rag.memory_types["semantic"]
    assert len(memories) <= 100
    assert memories[0]["importance"] > memories[-1]["importance"]  # Tärkeimmät ensin


def test_memory_clustering(rag):
    """Testaa muistien klusterointia"""
    # Tyhjennä muisti
    rag.clear_memories()

    # Lisää täysin erilaisia muisteja
    similar_memories = [
        {
            "content": "Python on suosittu ohjelmointikieli",
            "importance": 0.8,
            "timestamp": time.time(),
        },
        {
            "content": "Tekoäly mullistaa maailmaa",  # Täysin eri aihe
            "importance": 0.7,
            "timestamp": time.time(),
        },
        {
            "content": "Kissat ovat lemmikkieläimiä",  # Täysin eri aihe
            "importance": 0.8,
            "timestamp": time.time(),
        },
    ]

    # Klusteroi muistit erittäin matalalla kynnyksellä
    clusters = rag.memory_manager.cluster_memories(similar_memories, threshold=0.3)

    # Tarkista klusterointi
    assert len(clusters) >= 2  # Ainakin 2 klusteria


def test_memory_compression_quality(rag):
    """Testaa muistin tiivistyksen laatua"""
    # Tyhjennä muisti
    rag.clear_memories()

    # Lisää samankaltaisia muisteja
    memories = [
        {
            "content": "Python julkaistiin vuonna 1991",
            "importance": 0.8,
            "timestamp": time.time(),
        },
        {
            "content": "Python kehitettiin 1990-luvun alussa",
            "importance": 0.7,
            "timestamp": time.time(),
        },
        {
            "content": "Python on Guido van Rossumin luoma",
            "importance": 0.7,
            "timestamp": time.time(),
        },
    ]

    # Tiivistä muistit
    compressed = rag.memory_manager.compress_memories(memories)

    # Tarkista tiivistys
    assert len(compressed) < len(memories)
    assert any("Python" in m["content"] for m in compressed)
    assert any("1991" in m["content"] for m in compressed)  # Säilyttää tärkeät faktat
    assert compressed[0]["importance"] >= 0.8  # Säilyttää korkeimman tärkeyden


def test_memory_type_detection(rag):
    """Testaa muistin tyypin automaattista tunnistusta"""
    # Tyhjennä muisti
    rag.clear_memories()

    test_cases = [
        {
            "content": "Q: Mitä on Python?\nA: Ohjelmointikieli",
            "expected_type": "episodic",
        },
        {"content": "Python on ohjelmointikieli", "expected_type": "core"},
        {"content": "Python kehitettiin 1990-luvulla", "expected_type": "semantic"},
    ]

    for case in test_cases:
        memory = {
            "content": case["content"],
            "importance": 0.8,
            "timestamp": time.time(),
        }
        detected_type = rag.memory_manager._get_memory_type(memory)
        assert (
            detected_type == case["expected_type"]
        ), f"Expected {case['expected_type']} for '{case['content']}'"


def test_memory_usage_tracking(rag):
    """Testaa muistin käyttökertojen seurantaa"""
    # Tyhjennä muisti
    rag.clear_memories()

    # Lisää muisti
    rag._store_memory("semantic", "Testattava muisti", 0.7)

    # Hae muisti useita kertoja
    for _ in range(5):
        results = rag._search_memories("Testattava", rag.memory_types["semantic"])
        assert len(results) == 1

    # Tarkista että käyttökerrat on laskettu
    memory = rag.memory_types["semantic"][0]
    assert memory.get("use_count", 0) >= 5

    # Tarkista että käyttö nostaa tärkeyttä
    new_importance = rag.memory_manager.update_importance(memory)
    assert new_importance > 0.7  # Käyttö nostaa tärkeyttä
