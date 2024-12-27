from typing import List, Dict, List
import time
from datetime import datetime, timedelta
import numpy as np
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os
import math


class MemoryManager:
    """Hallinnoi muistin priorisointia ja rajoja"""

    def __init__(self, memory_rag=None, max_memories: int = 100):
        self.memory_rag = memory_rag
        self.max_memories = max_memories
        self.decay_rates = {
            "working": timedelta(minutes=5),
            "episodic": timedelta(days=1),
            "semantic": timedelta(days=30),
            "core": timedelta(days=365),
        }

        # Alusta OpenAI client
        repo_root = Path(__file__).parent.parent.parent.parent
        dotenv_path = repo_root / ".env"
        load_dotenv(dotenv_path=str(dotenv_path))
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def prioritize_memories(self, memories: List[Dict]) -> List[Dict]:
        """Priorisoi muistit tärkeyden ja ajankohdan mukaan"""
        # Laske prioriteetti jokaiselle muistille
        for memory in memories:
            age = time.time() - memory["timestamp"]
            memory["priority"] = memory["importance"] * (1.0 / (1.0 + age / 3600))

        # Järjestä ja rajoita määrää
        memories.sort(key=lambda x: x["priority"], reverse=True)
        return memories[: self.max_memories]

    def update_importance(self, memory_item: Dict) -> float:
        """Päivittää muistin tärkeyden ajan ja käytön mukaan"""
        age = time.time() - memory_item["timestamp"]
        memory_type = self._get_memory_type(memory_item)

        # Perusvanheneminen
        decay_rate = self.decay_rates[memory_type].total_seconds()
        base_decay = 1.0 / (1.0 + age / (decay_rate / 24))  # Lineaarinen vanheneminen

        # Huomioi käyttöhistoria
        uses = memory_item.get("use_count", 0)
        use_boost = min(0.05, uses * 0.005)  # Vielä pienempi boost

        # Yhdistä tekijät
        new_importance = memory_item["importance"] * base_decay * (1 + use_boost)

        return min(1.0, max(0.1, new_importance))

    def compress_memories(self, memories: List[Dict]) -> List[Dict]:
        """Tiivistää muistit käyttäen LLM:ää"""
        try:
            # Ryhmittele samankaltaiset muistit
            groups = self._cluster_memories(memories)

            # Tiivistä jokainen ryhmä
            compressed = []
            for group in groups:
                summary = self._summarize_group(group)
                compressed.append(
                    {
                        "content": summary,
                        "importance": max(m["importance"] for m in group),
                        "timestamp": max(m["timestamp"] for m in group),
                    }
                )
            return compressed
        except Exception as e:
            print(f"Virhe muistin tiivistyksessä: {e}")
            return memories

    def _cluster_memories(
        self, memories: List[Dict], similarity_threshold: float = 0.7
    ) -> List[List[Dict]]:
        """Ryhmittelee samankaltaiset muistit"""
        if not memories:
            return []

        # Luo embeddings kaikille muisteille
        embeddings = []
        for memory in memories:
            embedding = (
                self.client.embeddings.create(
                    model="text-embedding-ada-002", input=memory["content"]
                )
                .data[0]
                .embedding
            )
            embeddings.append(embedding)

        # Muodosta ryhmät samankaltaisuuden perusteella
        groups = []
        used = set()

        for i, mem1 in enumerate(memories):
            if i in used:
                continue

            current_group = [mem1]
            used.add(i)

            # Etsi samankaltaiset muistit
            for j, mem2 in enumerate(memories):
                if j in used:
                    continue

                # Laske samankaltaisuus
                similarity = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )

                if similarity > similarity_threshold:
                    current_group.append(mem2)
                    used.add(j)

            groups.append(current_group)

        return groups

    def _summarize_group(self, group: List[Dict]) -> str:
        """Tiivistää muistiryhmän sisällön käyttäen LLM:ää"""
        if not group:
            return ""

        # Yhdistä ryhmän sisältö
        combined_content = "\n".join(m["content"] for m in group)

        try:
            # Käytä LLM:ää tiivistämiseen
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Tiivistä annetut muistit yhdeksi 
                    johdonmukaiseksi tekstiksi. S��ilytä olennaiset faktat ja yksityiskohdat.""",
                    },
                    {
                        "role": "user",
                        "content": f"Tiivistä seuraavat muistit:\n{combined_content}",
                    },
                ],
                temperature=0.3,
                max_tokens=150,
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Virhe tiivistyksessä: {e}")
            # Jos tiivistys epäonnistuu, palauta ensimmäinen muisti
            return group[0]["content"]

    def check_and_optimize_memory(self, memory_type: str, max_memories: int = 100):
        """Tarkistaa ja optimoi muistin tarvittaessa"""
        memories = self.memory_rag.memory_types[memory_type]

        if len(memories) > max_memories:
            # Järjestä muistit tärkeyden mukaan
            memories.sort(key=lambda x: x["importance"], reverse=True)

            # Jaa muistit ryhmiin
            top_memories = memories[: max_memories // 2]  # Säilytä tärkeimmät
            to_compress = memories[max_memories // 2 :]  # Tiivistä loput

            # Tiivistä vähemmän tärkeät muistit
            compressed = self.compress_memories(to_compress)

            # Yhdistä ja päivitä
            self.memory_rag.memory_types[memory_type] = top_memories + compressed

    def cluster_memories(
        self, memories: List[Dict], threshold: float = 0.3
    ) -> List[List[Dict]]:
        """Ryhmittelee samankaltaiset muistit klustereihin"""
        if not memories:
            return []

        # Luo embeddings
        embeddings = []
        for memory in memories:
            embedding = (
                self.memory_rag.client.embeddings.create(
                    model="text-embedding-ada-002", input=memory["content"]
                )
                .data[0]
                .embedding
            )
            embeddings.append(embedding)

        # Luo samankaltaisuusmatriisi
        n = len(memories)
        similarity_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Laske samankaltaisuus
                    similarity = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
                    # Laske yhteiset sanat
                    words_i = set(memories[i]["content"].lower().split())
                    words_j = set(memories[j]["content"].lower().split())
                    common_words = len(words_i & words_j)

                    # Yhdistä metriikka
                    similarity_matrix[i, j] = similarity * (
                        1.0 - min(1.0, common_words / 3)
                    )

        # Muodosta klusterit
        clusters = []
        used = set()

        for i in range(n):
            if i in used:
                continue

            # Etsi kaikki muistit jotka ovat tarpeeksi erilaisia
            cluster = [memories[i]]
            used.add(i)

            for j in range(n):
                if j not in used and similarity_matrix[i, j] < threshold:
                    cluster.append(memories[j])
                    used.add(j)

            clusters.append(cluster)

        return clusters

    def _get_memory_type(self, memory_item: Dict) -> str:
        """Päättelee muistin tyypin sen sisällöstä"""
        # Tarkista ensin suora tyyppi
        if "type" in memory_item:
            return memory_item["type"]

        # Päättele sisällöstä
        content = memory_item["content"].lower()

        # Kysymys-vastaus pari -> episodic
        if content.startswith("q:") or "?\na:" in content:
            return "episodic"

        # Historia -> semantic
        if any(
            word in content
            for word in ["kehitettiin", "julkaistiin", "luotiin", "vuonna"]
        ):
            return "semantic"

        # Määritelmä -> core
        if any(word in content for word in ["on", "tarkoittaa", "määritellään"]):
            return "core"

        # Oletuksena semantic
        return "semantic"
