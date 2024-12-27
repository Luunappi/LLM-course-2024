import json
import time
from typing import List, Dict, Any, Union


class AgenticMemory:
    """
    AgenticRAG:n muistinhallintakomponentti, joka mahdollistaa:
    - Nimetyt muistiankkurit
    - Kontekstin hallinnan
    - Muistin päivitysten seurannan
    """

    def __init__(self):
        # Alustetaan muistiankkurit
        self.contents = {
            "query_history": [],  # Lista kyselyistä
            "context_chunks": [],  # Kontekstipalat
            "current_query": "",  # Nykyinen kysely
            "analysis_results": [],  # Analyysin tulokset
            "final_response": "",  # Lopullinen vastaus
            "chat_history": [],  # Keskusteluhistoria
        }

        # Muistin päivitysloki
        self.memory_log = []

    def update_memory(self, anchor: str, content: Any, metadata: Dict = None) -> None:
        """
        Päivittää muistin ankkuroidun sisällön

        Args:
            anchor: Muistiankkurin nimi
            content: Tallennettava sisältö
            metadata: Lisätiedot päivityksestä (optional)
        """
        if anchor not in self.contents:
            raise KeyError(f"Unknown memory anchor: {anchor}")

        # Tallennetaan päivitys lokiin
        update_record = {
            "timestamp": time.time(),
            "anchor": anchor,
            "content": content,
            "metadata": metadata or {},
        }
        self.memory_log.append(update_record)

        # Päivitetään sisältö tyypin mukaan
        if isinstance(self.contents[anchor], list):
            self.contents[anchor].append(content)
        else:
            self.contents[anchor] = content

    def get_context(self, anchors: List[str], limit: int = None) -> str:
        """
        Hakee kontekstin määritellyistä ankkureista

        Args:
            anchors: Lista ankkureista joista konteksti haetaan
            limit: Maksimimäärä palautettavia kohteita per ankkuri

        Returns:
            str: Yhdistetty konteksti annetuista ankkureista
        """
        context = []
        for anchor in anchors:
            if anchor in self.contents:
                content = self.contents[anchor]
                if isinstance(content, list) and limit:
                    content = content[-limit:]
                context.append(f"=== {anchor} ===")
                context.append(str(content))
        return "\n".join(context)

    def get_memory_state(self) -> Dict:
        """Palauttaa muistin nykyisen tilan"""
        return {
            "contents": self.contents,
            "update_count": len(self.memory_log),
            "last_update": self.memory_log[-1] if self.memory_log else None,
        }

    def clear_memory(self, anchor: str = None) -> None:
        """
        Tyhjentää muistin sisällön

        Args:
            anchor: Jos määritelty, tyhjentää vain kyseisen ankkurin
        """
        if anchor:
            if isinstance(self.contents[anchor], list):
                self.contents[anchor] = []
            else:
                self.contents[anchor] = ""
        else:
            for key in self.contents:
                if isinstance(self.contents[key], list):
                    self.contents[key] = []
                else:
                    self.contents[key] = ""
