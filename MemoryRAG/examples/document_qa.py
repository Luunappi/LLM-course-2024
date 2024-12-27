"""Esimerkki dokumenttien käsittelystä MemoryRAG:lla"""

from memoryrag import MemoryRAG
from pathlib import Path


def process_document(file_path: str, query: str):
    """Käsittelee dokumentin ja vastaa kyselyyn"""
    rag = MemoryRAG()

    # Lue dokumentti
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Jaa dokumentti kappaleisiin
    paragraphs = text.split("\n\n")

    # Tallenna kappaleet semanttiseen muistiin
    for i, para in enumerate(paragraphs):
        # Ensimmäinen kappale on usein tärkein
        importance = 0.9 if i == 0 else 0.7
        rag._store_memory("semantic", para, importance)

    # Tee kysely
    response = rag.process_query(query)
    return response


def main():
    # Esimerkki käytöstä
    doc_path = "docs/example.txt"

    # Luo esimerkkidokumentti jos ei ole
    if not Path(doc_path).exists():
        text = """
        Python on monipuolinen ohjelmointikieli, joka julkaistiin vuonna 1991.
        Se on tunnettu selkeästä syntaksistaan ja laajasta kirjastostaan.
        
        Python soveltuu erityisen hyvin data-analyysiin ja tekoälyn kehitykseen.
        Sen ekosysteemi sisältää useita tekoälykirjastoja kuten TensorFlow ja PyTorch.
        """
        Path(doc_path).parent.mkdir(exist_ok=True)
        with open(doc_path, "w") as f:
            f.write(text)

    # Tee kyselyitä
    queries = [
        "Milloin Python julkaistiin?",
        "Mihin Python soveltuu?",
        "Mitä tekoälykirjastoja Python tukee?",
    ]

    for query in queries:
        print(f"\nKysymys: {query}")
        answer = process_document(doc_path, query)
        print(f"Vastaus: {answer}")


if __name__ == "__main__":
    main()
