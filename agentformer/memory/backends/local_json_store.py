import json
import os
from typing import List, Dict, Any


class LocalJsonMemoryBackend:
    def __init__(self, filepath: str = "local_memory.json"):
        self.filepath = filepath
        # Luodaan tiedosto, jos sitä ei ole
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump([], f)

    def store(self, data: Dict[str, Any]) -> None:
        # Lue
        records = self._read_all()
        # Lisää
        records.append(data)
        # Kirjoita
        self._write_all(records)

    def retrieve_all(self) -> List[Dict[str, Any]]:
        return self._read_all()

    def clear(self):
        self._write_all([])

    def _read_all(self) -> List[Dict[str, Any]]:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_all(self, records: List[Dict[str, Any]]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
