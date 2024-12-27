"""Esimerkki muistin käytöstä ja tarkastelusta"""

from memoryrag import MemoryRAG
from pathlib import Path
import json


def inspect_memories():
    # Alusta MemoryRAG
    rag = MemoryRAG()

    # Lisää testidataa
    print("\nLisätään testidataa muistiin...")

    rag._store_memory(
        "core", "Python on ohjelmointikieli, joka julkaistiin 1991", importance=1.0
    )

    rag._store_memory(
        "semantic",
        "Python 3.12 toi merkittäviä suorituskykyparannuksia",
        importance=0.8,
    )

    # Tee kysely
    print("\nTehdään kysely...")
    response = rag.process_query("Milloin Python julkaistiin?")
    print(f"Vastaus: {response}")

    # Tarkastele tallennettua muistia
    print("\nTarkastellaan tallennettua muistia:")
    memory_file = Path("data/memories.json")

    if memory_file.exists():
        with open(memory_file, "r", encoding="utf-8") as f:
            memories = json.load(f)

        # Näytä muistit tyypeittäin
        for memory_type, items in memories.items():
            if items:
                print(f"\n{memory_type.upper()}:")
                for item in items:
                    print(f"- [{item['importance']:.1f}] {item['content']}")
    else:
        print("Muistitiedostoa ei löydy!")


if __name__ == "__main__":
    inspect_memories()
