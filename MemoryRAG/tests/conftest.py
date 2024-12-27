import pytest
from memoryrag import MemoryRAG
from pathlib import Path
import tempfile


@pytest.fixture(autouse=True)
def rag():
    """Fixture joka alustaa puhtaan MemoryRAG-instanssin joka testille"""
    # Käytä väliaikaista tiedostoa testeissä
    with tempfile.NamedTemporaryFile() as tmp:
        # Alusta MemoryRAG väliaikaisella tallennuspolulla
        rag = MemoryRAG()
        rag.storage.storage_path = Path(tmp.name)
        rag.clear_memories()
        yield rag
