from typing import List, Dict, Any, Optional
import time


class AgenticMemory:
    """
    AgenticRAG:n muistinhallintakomponentti, joka mahdollistaa:
    - Nimetyt muistiankkurit
    - Kontekstin hallinnan
    - Muistin päivitysten seurannan
    """

    def __init__(self):
        self.contents = {
            "query_history": [],  # Lista kyselyistä
            "context_chunks": [],  # Kontekstipalat
            "current_query": "",  # Nykyinen kysely
            "final_response": "",  # Lopullinen vastaus
        }
        self.update_count = 0
        self.last_update = None

    def update_memory(self, anchor: str, content: Any, metadata: Dict = None) -> None:
        """Päivittää muistin sisältöä"""
        if isinstance(self.contents[anchor], list):
            self.contents[anchor].append(content)
        else:
            self.contents[anchor] = content

        self.update_count += 1
        self.last_update = time.time()

    def get_context(self, anchors: List[str], limit: int = None) -> str:
        """Hakee kontekstin annetuista ankkureista"""
        context_parts = []
        for anchor in anchors:
            if isinstance(self.contents[anchor], list):
                items = (
                    self.contents[anchor][-limit:] if limit else self.contents[anchor]
                )
                context_parts.extend(items)
            else:
                context_parts.append(self.contents[anchor])
        return "\n".join(str(part) for part in context_parts if part)

    def get_memory_state(self) -> Dict:
        """Palauttaa muistin tilan"""
        return {
            "contents": self.contents,
            "update_count": self.update_count,
            "last_update": self.last_update,
        }
