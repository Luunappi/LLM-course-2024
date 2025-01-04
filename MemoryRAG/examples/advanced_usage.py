# Tämä esimerkki näyttää:
"""
1. Hierarkkisen muistin toiminnan
- Eri muistityyppien käyttö
- Tiedon priorisointi tärkeyden mukaan

2. Semanttisen haun
- Relevantin tiedon löytäminen
- Tietojen yhdistäminen vastaukseksi

3. Kontekstin hallinnan
- Aiemman keskustelun hyödyntäminen
- Työmuistin päivittyminen

4. Muistin tilan seurannan
- Muistin sisällön tarkastelu
- Prioriteettien vaikutus

Kun ajat esimerkin, näet miten:
- Muisti rakentuu vaiheittain
- Vastaukset hyödyntävät kontekstia
- Muisti päivittyy kyselyiden myötä
"""

import sys
from pathlib import Path

# Lisää projektin juurikansio Python-polkuun
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from dotenv import load_dotenv
from src.modules import MemoryRAG


def demonstrate_memory_features():
    """Demonstroi MemoryRAG:n ominaisuuksia käytännössä"""
    # Alusta MemoryRAG
    repo_root = Path(__file__).parent.parent.parent
    dotenv_path = repo_root / ".env"
    load_dotenv(dotenv_path=str(dotenv_path))

    rag = MemoryRAG()

    print("\n=== 1. Hierarkkisen muistin demonstraatio ===")

    # Lisää tietoa eri muistityyppeihin
    print("\nLisätään tietoa muistiin...")

    # Core memory - tärkein tieto
    rag._store_memory(
        "core",
        "Tekoäly on tietokoneiden kyky simuloida älykästä toimintaa ja oppia datasta.",
        importance=1.0,
    )

    # Semantic memory - taustatiedot
    rag._store_memory(
        "semantic",
        "Tekoälyn kehitys alkoi 1950-luvulla Turingin testin myötä.",
        importance=0.8,
    )
    rag._store_memory(
        "semantic",
        "Nykyaikainen tekoäly perustuu usein koneoppimiseen ja neuroverkkoihin.",
        importance=0.7,
    )

    print("\n=== 2. Semanttisen haun demonstraatio ===")

    # Tee kysely joka vaatii tietojen yhdistämistä
    query = "Miten tekoäly on kehittynyt vuosien varrella?"
    print(f"\nKysely: {query}")

    response = rag.process_query(query)
    print(f"Vastaus: {response}")

    # Näytä miten episodinen muisti tallentaa keskustelun
    print("\nEpisodinen muisti kyselyn jälkeen:")
    for mem in rag.memory_types["episodic"]:
        print(f"- [{mem['importance']:.1f}] {mem['content']}")

    print("\n=== 3. Kontekstin hallinnan demonstraatio ===")

    # Lisää uusi kysely joka hyödyntää aiempaa kontekstia
    query2 = "Mitä erityistä tapahtui 1950-luvulla tekoälyn kehityksessä?"
    print(f"\nKysely: {query2}")

    response2 = rag.process_query(query2)
    print(f"Vastaus: {response2}")

    # Näytä miten työmuisti päivittyy
    print("\nTyömuisti toisen kyselyn jälkeen:")
    for mem in rag.memory_types["working"]:
        print(f"- [{mem['importance']:.1f}] {mem['content']}")

    print("\n=== 4. Muistin tila ===")
    print("\nMuistin lopullinen tila:")
    for memory_type, memories in rag.memory_types.items():
        if memories:
            print(f"\n{memory_type.upper()}:")
            for mem in memories:
                print(f"- [{mem['importance']:.1f}] {mem['content']}")


if __name__ == "__main__":
    demonstrate_memory_features()
