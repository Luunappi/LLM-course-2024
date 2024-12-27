from typing import List, Dict


class MemoryOperations:
    """MemGPT-tyylinen muistinhallinta"""

    def recall(self, query: str, memory_type: str = "all") -> List[Dict]:
        """Hakee relevantin muistin annetulla kyselyllä"""
        memories = []
        if memory_type == "all":
            # Hae kaikista muistityypeistä
            for type_memories in self.memory_types.values():
                relevant = self._search_memories(query, type_memories)
                memories.extend(relevant)
        else:
            # Hae vain tietystä muistityypistä
            memories = self._search_memories(query, self.memory_types[memory_type])

        return sorted(memories, key=lambda x: x["importance"], reverse=True)

    def core_memory_append(self, content: str):
        """Lisää kriittisen muistin"""
        self.memory.update_memory("core_memories", content, {"importance": 1.0})

    def archival_memory_search(self, query: str) -> List[str]:
        """Hakee arkistoidusta muistista"""
        return self._search_memories(query, self.memory_types["episodic"])
