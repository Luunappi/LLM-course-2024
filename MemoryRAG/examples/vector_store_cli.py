"""
Terminaalikäyttöliittymä MemoryRAG:n local vector store -toiminnallisuuden testaamiseen.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from memoryrag import MemoryRAG


def print_separator():
    print("\n" + "=" * 50 + "\n")


def main():
    # Varmista että API-avain on asetettu repon juuresta
    repo_root = Path(__file__).parent.parent.parent
    dotenv_path = repo_root / ".env"
    load_dotenv(dotenv_path=str(dotenv_path))

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY puuttuu! Tarkista että .env tiedosto on repon juuressa.")
        return

    # Alusta MemoryRAG
    rag = MemoryRAG()

    # Yritä ladata olemassa olevat embeddingit
    try:
        rag.load_vectorstore("local_memory_index.json")
        print("Ladattiin olemassa olevat embeddingit.")
    except Exception as e:
        print(f"Ei aiempia embeddingejä: {e}")

    while True:
        print_separator()
        print("MemoryRAG Vector Store Testaus")
        print("1. Lisää muisti")
        print("2. Tee kysely")
        print("3. Näytä muistit")
        print("4. Tallenna embeddingit")
        print("5. Lataa embeddingit")
        print("6. Lopeta")

        choice = input("\nValitse toiminto (1-6): ")

        if choice == "1":
            print_separator()
            content = input("Syötä muistin sisältö: ")
            importance = float(input("Syötä tärkeys (0.0-1.0): "))
            mem_type = input("Syötä muistityyppi (core/semantic/episodic/working): ")

            try:
                rag._store_memory(mem_type, content, importance)
                print(f"Muisti tallennettu tyyppiin '{mem_type}'")
            except Exception as e:
                print(f"Virhe tallennuksessa: {e}")

        elif choice == "2":
            print_separator()
            query = input("Syötä kysely: ")
            try:
                # Hae semanttisesti samankaltaiset muistit
                relevant = rag.semantic_search(query)
                print("\nLöydetyt relevantit muistit:")
                for i, mem in enumerate(relevant, 1):
                    print(f"{i}. {mem}")

                # Tee varsinainen kysely
                response = rag.process_query(query)
                print("\nVastaus:")
                print(response)
            except Exception as e:
                print(f"Virhe kyselyssä: {e}")

        elif choice == "3":
            print_separator()
            print("Tallennetut muistit:")
            for mem_type, memories in rag.memory_types.items():
                print(f"\n{mem_type.upper()}:")
                for mem in memories:
                    print(f"- [{mem['importance']:.1f}] {mem['content']}")

        elif choice == "4":
            print_separator()
            try:
                rag.save_vectorstore("local_memory_index.json")
                print("Embeddingit tallennettu onnistuneesti.")
            except Exception as e:
                print(f"Virhe tallennuksessa: {e}")

        elif choice == "5":
            print_separator()
            try:
                rag.load_vectorstore("local_memory_index.json")
                print("Embeddingit ladattu onnistuneesti.")
            except Exception as e:
                print(f"Virhe latauksessa: {e}")

        elif choice == "6":
            print("\nTallennetaan embeddingit ennen lopetusta...")
            try:
                rag.save_vectorstore("local_memory_index.json")
                print("Embeddingit tallennettu.")
            except Exception as e:
                print(f"Virhe lopputallennuksessa: {e}")
            print("\nKiitos käytöstä!")
            break


if __name__ == "__main__":
    main()
