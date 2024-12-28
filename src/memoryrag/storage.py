import json
import aiofiles
from pathlib import Path


class StorageManager:
    def __init__(self, memory_types):
        """Alustaa StorageManagerin.

        Args:
            memory_types: Viittaus MemoryRAG:n memory_types-sanakirjaan
        """
        # Käytetään samaa rakennetta kuin Sasun koodissa
        self.storage_path = Path("test_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Tiedostopolut
        self.memory_file = self.storage_path / "memories.json"
        self.embedding_file = self.storage_path / "embeddings.json"
        self.index_file = self.storage_path / "faiss_index.bin"

        self.memory_types = memory_types

    async def initialize(self):
        """Asynkroninen alustus"""
        await self.load_memories()

    async def save_memories(self, memories=None):
        """Tallentaa muistit tiedostoon."""
        try:
            memories_to_save = memories if memories is not None else self.memory_types
            print(f"DEBUG: Trying to save memories to {self.memory_file}")

            async with aiofiles.open(self.memory_file, "w", encoding="utf-8") as f:
                json_str = json.dumps(memories_to_save, indent=2, ensure_ascii=False)
                print(f"DEBUG: Writing JSON: {json_str}")
                await f.write(json_str)
                return True

        except Exception as e:
            print(f"ERROR: Virhe muistien tallennuksessa: {e}")
            return False

    async def load_memories(self):
        """Lataa muistit tiedostosta."""
        try:
            if self.memory_file.exists():
                print(f"DEBUG: Loading from: {self.memory_file}")
                async with aiofiles.open(self.memory_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                    if not content.strip():
                        print("DEBUG: File is empty")
                        return self.get_empty_memories()

                    loaded = json.loads(content)
                    print(f"DEBUG: Loaded content: {loaded}")
                    # Päivitä memory_types viittaus
                    self.memory_types.clear()
                    self.memory_types.update(loaded)
                    return loaded

            print("DEBUG: File does not exist")
            return self.get_empty_memories()

        except Exception as e:
            print(f"ERROR: Virhe muistien latauksessa: {e}")
            return self.get_empty_memories()

    def get_empty_memories(self):
        """Palauttaa tyhjän muistirakenteen"""
        return {"core": [], "semantic": [], "episodic": [], "working": []}
