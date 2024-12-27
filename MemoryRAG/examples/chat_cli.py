"""Komentorivi-käyttöliittymä MemoryRAG:n testaamiseen"""

import argparse
from pathlib import Path
from memoryrag import MemoryRAG
from memoryrag.file_handlers import read_document
import glob


def load_documents(rag: MemoryRAG, paths: list[str]) -> None:
    """Lataa dokumentit muistiin"""
    print("\nLataan dokumentteja...")

    # Tarkista ja luo data-hakemisto
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    for subdir in ["pdf", "txt", "docx", "csv", "xlsx", "html"]:
        (data_dir / subdir).mkdir(exist_ok=True)

    for path in paths:
        try:
            # Tarkista onko hakemisto
            path = Path(path)
            if path.is_dir():
                # Käsittele kaikki tuetut tiedostot hakemistosta
                for ext in [".pdf", ".txt", ".docx", ".csv", ".xlsx", ".html"]:
                    for file in path.glob(f"**/*{ext}"):
                        try:
                            paragraphs = read_document(str(file))
                            print(
                                f"Ladattu: {file.name} ({len(paragraphs)} kappaletta)"
                            )
                            for p in paragraphs:
                                rag._store_memory("semantic", p, importance=0.7)
                        except Exception as e:
                            print(f"Virhe ladattaessa {file}: {e}")
            else:
                # Käsittele yksittäinen tiedosto
                abs_path = path.resolve()
                if not abs_path.exists():
                    print(f"Tiedostoa ei löydy: {abs_path}")
                    continue

                paragraphs = read_document(str(abs_path))
                print(f"Ladattu: {abs_path.name} ({len(paragraphs)} kappaletta)")
                for p in paragraphs:
                    rag._store_memory("semantic", p, importance=0.7)
        except Exception as e:
            print(f"Virhe ladattaessa {path}: {e}")


def save_memory(rag: MemoryRAG, path: str) -> None:
    """Tallenna muisti tiedostoon"""
    try:
        rag.storage.save_memories(path)
        print(f"\nMuisti tallennettu: {path}")
    except Exception as e:
        print(f"Virhe tallennettaessa muistia: {e}")


def load_memory(rag: MemoryRAG, path: str) -> None:
    """Lataa muisti tiedostosta"""
    try:
        rag.storage.load_memories(path)
        print(f"\nMuisti ladattu: {path}")
        # Näytä tilastot
        stats = {k: len(v) for k, v in rag.memory_types.items()}
        print("Muistin tila:")
        for type_, count in stats.items():
            print(f"- {type_}: {count} muistia")
    except Exception as e:
        print(f"Virhe ladattaessa muistia: {e}")


def chat_loop(rag: MemoryRAG) -> None:
    """Keskustelusilmukka"""
    print("\nKomennot:")
    print("- /save <tiedosto> : Tallenna muisti")
    print("- /load <tiedosto> : Lataa muisti")
    print("- /stats : Näytä muistin tila")
    print("- /clear : Tyhjennä muisti")
    print("- /exit tai q : Lopeta")

    while True:
        try:
            query = input("\nKysymys: ").strip()

            # Käsittele komennot
            if query.startswith("/"):
                cmd = query.split()
                if cmd[0] == "/save" and len(cmd) > 1:
                    save_memory(rag, cmd[1])
                elif cmd[0] == "/load" and len(cmd) > 1:
                    load_memory(rag, cmd[1])
                elif cmd[0] == "/stats":
                    stats = {k: len(v) for k, v in rag.memory_types.items()}
                    print("\nMuistin tila:")
                    for type_, count in stats.items():
                        print(f"- {type_}: {count} muistia")
                elif cmd[0] == "/clear":
                    rag.clear_memories()
                    print("\nMuisti tyhjennetty")
                elif cmd[0] == "/exit":
                    break
                continue

            if query.lower() in ["exit", "q"]:
                break

            if not query:
                continue

            response = rag.process_query(query)
            print("\nVastaus:", response)

            # Näytä käytetyt muistit
            print("\nKäytetyt muistit:")
            context = rag.context_manager.get_last_context()
            for i, mem in enumerate(context.split("\n"), 1):
                if mem.strip():
                    print(f"{i}. {mem}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Virhe: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="MemoryRAG Chat CLI - Keskustele dokumenttien kanssa"
    )
    parser.add_argument(
        "files",
        nargs="*",  # Tiedostot ovat nyt valinnaisia
        help="Ladattavat dokumentit tai hakemistot. Tukee wildcardeja (esim. data/pdf/*.pdf)",
    )
    parser.add_argument(
        "--model",
        default="gpt-3.5-turbo",
        help="Käytettävä OpenAI malli (oletus: gpt-3.5-turbo)",
    )
    parser.add_argument("--load-memory", help="Lataa muisti tiedostosta")
    args = parser.parse_args()

    # Alusta RAG
    rag = MemoryRAG(model_name=args.model)

    # Lataa muisti jos annettu
    if args.load_memory:
        load_memory(rag, args.load_memory)

    # Laajenna wildcards
    expanded_files = []
    for pattern in args.files:
        expanded = glob.glob(pattern)
        if expanded:
            expanded_files.extend(expanded)
        else:
            print(f"Varoitus: Ei löytynyt tiedostoja haulla '{pattern}'")

    # Lataa dokumentit jos annettu
    if expanded_files:
        load_documents(rag, expanded_files)

    # Aloita keskustelu
    chat_loop(rag)


if __name__ == "__main__":
    main()
