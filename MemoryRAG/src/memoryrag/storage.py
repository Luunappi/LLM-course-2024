import json
from pathlib import Path
from typing import Dict, List
import time


class StorageManager:
    """Hallinnoi muistin pysyvää tallennusta"""

    def __init__(self, storage_path: str = "data/memories/history.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Luo tai lataa muisti
        if self.storage_path.exists():
            self.memories = self._load_memories()
        else:
            self.memories = {"working": [], "episodic": [], "semantic": [], "core": []}
            self._save_memories()

        # Automaattinen tallennus
        self.auto_save_interval = 60  # Tallenna minuutin välein
        self.last_save = time.time()

    def _load_memories(self) -> Dict[str, List[Dict]]:
        """Lataa muistit tiedostosta"""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Virhe muistin latauksessa: {e}")
            return {"working": [], "episodic": [], "semantic": [], "core": []}

    def _save_memories(self):
        """Tallentaa muistit tiedostoon"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Virhe muistin tallennuksessa: {e}")

    def store_memory(self, memory_type: str, content: str, importance: float):
        """Tallentaa muistin ja tekee automaattisen tallennuksen"""
        # Rajoita muistien kokoa
        max_content_length = 1000  # Maksimi merkkimäärä per muisti
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        # Tarkista duplikaatit
        if memory_type in self.memories:
            # Älä tallenna jos sama sisältö on jo olemassa
            if any(m["content"] == content for m in self.memories[memory_type]):
                return

        # Tallenna muisti
        memory = {
            "content": content,
            "importance": importance,
            "timestamp": time.time(),
        }

        if memory_type not in self.memories:
            self.memories[memory_type] = []
        self.memories[memory_type].append(memory)

        # Automaattinen tallennus
        if time.time() - self.last_save > self.auto_save_interval:
            self._save_memories()
            self.last_save = time.time()

    def get_memories(self, memory_type: str) -> List[Dict]:
        """Hakee tietyn tyypin muistit"""
        return self.memories.get(memory_type, [])

    def update_memories(self, memory_type: str, memories: List[Dict]):
        """Päivittää tietyn tyypin muistit"""
        self.memories[memory_type] = memories
        self._save_memories()

    def clear_memories(self):
        """Tyhjentää kaikki muistit"""
        self.memories = {"working": [], "episodic": [], "semantic": [], "core": []}
        self._save_memories()

    def update_memory(self, memory_type: str, memory_index: int, updates: Dict):
        """Päivittää olemassa olevaa muistia"""
        if memory_type in self.memories and 0 <= memory_index < len(
            self.memories[memory_type]
        ):
            self.memories[memory_type][memory_index].update(updates)
            self._save_memories()
