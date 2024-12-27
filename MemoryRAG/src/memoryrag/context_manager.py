from typing import List, Dict, Tuple
import tiktoken
import re


class ContextManager:
    def __init__(self, memory_rag):
        self.memory_rag = memory_rag
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.query_types = {
            "what": "definition",  # Määrittelykysymykset
            "how": "process",  # Prosessikysymykset
            "when": "temporal",  # Aikaan liittyvät
            "why": "causal",  # Syy-seuraus
            "where": "location",  # Sijainti
            "who": "entity",  # Henkilöt/entiteetit
        }
        self.last_context = ""  # Lisätään muuttuja viimeisimmälle kontekstille

    def _analyze_query_type(self, query: str) -> str:
        """Analysoi kyselyn tyypin"""
        query = query.lower()
        for keyword, qtype in self.query_types.items():
            if query.startswith(keyword):
                return qtype
        return "general"

    def _get_dynamic_budget(self, query_type: str, max_tokens: int) -> Dict[str, int]:
        """Määrittää token-budjetin kyselyn tyypin mukaan"""
        budgets = {
            "definition": {
                "core": 0.5,  # Määritelmät core-muistista
                "semantic": 0.3,
                "episodic": 0.1,
                "working": 0.1,
            },
            "process": {
                "core": 0.3,
                "semantic": 0.4,  # Prosessit semantic-muistista
                "episodic": 0.2,
                "working": 0.1,
            },
            "temporal": {
                "core": 0.2,
                "semantic": 0.3,
                "episodic": 0.4,  # Historia episodic-muistista
                "working": 0.1,
            },
            "general": {"core": 0.4, "semantic": 0.2, "episodic": 0.3, "working": 0.1},
        }

        budget = budgets.get(query_type, budgets["general"])
        return {k: int(v * max_tokens) for k, v in budget.items()}

    def _get_relevant_memories(self, query: str) -> Dict[str, List[Dict]]:
        """Hakee relevantit muistit kaikista muistityypeistä"""
        memories = {}
        for memory_type in self.memory_rag.memory_types:
            results = self.memory_rag._search_memories(
                query, self.memory_rag.memory_types[memory_type]
            )
            memories[memory_type] = results
        return memories

    def _format_context(
        self, memories: Dict[str, List[Dict]], token_budget: Dict[str, int]
    ) -> str:
        """Muotoilee kontekstin token-budjetin mukaan"""
        context_parts = []

        for memory_type, budget in token_budget.items():
            if memory_type in memories and memories[memory_type]:
                context_parts.append(f"\n=== {memory_type.title()} Memories ===")
                memory_text = self._format_memories(memories[memory_type])
                truncated = self._truncate_context(memory_text, budget)
                context_parts.append(truncated)

        return "\n".join(context_parts)

    def build_context(self, query: str) -> str:
        """Rakentaa kontekstin kyselyä varten"""
        max_context_length = 8000  # Kasvatettu kontekstin kokoa

        context_parts = []

        # 1. Lisää aiemmat relevantit kysymykset ja vastaukset
        recent_qa = self.memory_rag.memory_types.get("episodic", [])[-3:]  # Viimeiset 3
        if recent_qa:
            context_parts.append("Recent Q&A:")
            for qa in recent_qa:
                context_parts.append(qa["content"])

        # 2. Hae relevantit muistit semanttisesta muistista
        semantic_memories = self.memory_rag._search_memories(
            query, self.memory_rag.memory_types.get("semantic", [])
        )

        # Rajoita muistien määrää top_k:n mukaan
        semantic_memories = semantic_memories[:5]  # Ota 5 relevanteinta

        # 3. Järjestä muistit tärkeyden mukaan
        semantic_memories = sorted(
            semantic_memories,
            key=lambda x: x.get("importance", 0) * 0.7 + x.get("similarity", 0) * 0.3,
            reverse=True,
        )

        # 4. Lisää muistit kontekstiin
        total_length = len("\n".join(context_parts))
        for mem in semantic_memories:
            mem_text = f"- {mem['content']}"
            if total_length + len(mem_text) < max_context_length:
                context_parts.append(mem_text)
                total_length += len(mem_text)

        self.last_context = "\n".join(context_parts)  # Tallenna viimeisin konteksti
        return self.last_context

    def get_last_context(self) -> str:
        """Palauttaa viimeisimmän käytetyn kontekstin"""
        return self.last_context

    def _truncate_context(self, text: str, max_tokens: int) -> str:
        """Rajoittaa kontekstin pituutta merkkeinä"""
        # Käytä suoraan merkkimäärää
        if len(text) > max_tokens:
            text = text[:max_tokens]
            # Varmista että viimeinen lause on kokonainen
            if "." in text:
                text = text.rsplit(".", 1)[0] + "."
        return text

    def _format_memories(self, memories: List[Dict]) -> str:
        """Muotoilee muistit luettavaksi tekstiksi"""
        formatted = []
        for mem in memories:
            formatted.append(f"[{mem['importance']:.1f}] {mem['content']}")
        return "\n".join(formatted)
