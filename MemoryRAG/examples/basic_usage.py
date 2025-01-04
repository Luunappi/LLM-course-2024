import os
from pathlib import Path
from dotenv import load_dotenv
from src.modules import MemoryRAG


def test_memory_types():
    """Testaa eri muistityyppien toimintaa"""
    # Varmista että API-avain on asetettu repon juuresta
    repo_root = Path(__file__).parent.parent.parent
    dotenv_path = repo_root / ".env"
    load_dotenv(dotenv_path=str(dotenv_path))

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY puuttuu! Tarkista että .env tiedosto on repon juuressa.")
        return

    rag = MemoryRAG()

    # 1. Lisää tietoa eri muistityyppeihin
    print("\nLisätään tietoa muistiin...")

    # Ydinmuisti (tärkeimmät faktat)
    rag._store_memory(
        "core",
        "Tekoäly on tietokoneiden kyky simuloida älykästä toimintaa ja oppia datasta.",
        importance=1.0,
    )

    # Semanttinen muisti (yleistieto)
    rag._store_memory(
        "semantic",
        """Tekoäly kehitettiin 1950-luvulla. Alan Turing kehitti Turingin testin 
        vuonna 1950 mittaamaan koneen älykkyyttä.""",
        importance=0.7,
    )

    # 2. Testaa kyselyä
    print("\nTestataan kyselyä...")
    query = "Mitä on tekoäly, milloin se kehitettiin ja kuka kehitti Turingin testin?"
    response = rag.process_query(query)
    print(f"\nKysely: {query}")
    print(f"Vastaus: {response}")

    # 3. Tarkista muistin tila
    print("\nMuistin tila:")
    for memory_type, memories in rag.memory_types.items():
        if memories:
            print(f"\n{memory_type.upper()}:")
            for mem in memories:
                print(f"- [{mem['importance']:.1f}] {mem['content']}")


if __name__ == "__main__":
    test_memory_types()
