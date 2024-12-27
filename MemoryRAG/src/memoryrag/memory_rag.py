from typing import List, Dict, Any, Optional
from pathlib import Path
from .agentic_memory import AgenticMemory
from .pubsub import EnhancedPubSub
from .memory_operations import MemoryOperations
from .memory_manager import MemoryManager
from .context_manager import ContextManager
import time
import os
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np
from .storage import StorageManager
from math import fabs


class MemoryRAG(MemoryOperations):
    """
    RAG (Retrieval-Augmented Generation) toteutus muistinhallinnalla.

    Muistihierarkia:
    - working: Työmuisti nykyiselle kontekstille
    - episodic: Keskusteluhistoria
    - semantic: Yleistieto ja faktat
    - core: Kriittiset muistettavat asiat

    Muistin hallinta:
    - Automaattinen priorisointi tärkeyden mukaan
    - Kontekstin älykäs rakentaminen
    - Muistin vanheneminen ajan myötä
    """

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.memory = AgenticMemory()
        self.pubsub = EnhancedPubSub()
        self.model_name = model_name
        self.storage = StorageManager()
        self.memory_types = self.storage.memories

        # Alusta memory_manager ja context_manager
        self.memory_manager = MemoryManager(memory_rag=self)
        self.context_manager = ContextManager(self)

        # Lataa API-avain repon juuresta (.env on aina repon juuressa)
        repo_root = (
            Path(__file__).resolve().parents[3]
        )  # 3 tasoa ylös src/memoryrag/memory_rag.py:stä
        dotenv_path = repo_root / ".env"

        if not dotenv_path.exists():
            raise ValueError(
                f"API-avainta ei löydy! Varmista että .env tiedosto on repon juuressa: {repo_root}"
            )

        load_dotenv(dotenv_path=str(dotenv_path))
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY puuttuu .env tiedostosta! Lisää se muodossa: OPENAI_API_KEY=your-key-here"
            )

        self.client = OpenAI(api_key=api_key)

        # Testaa API-avaimen toimivuus
        try:
            print("Testataan OpenAI API-yhteyttä...")
            test_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
            )
            print("OpenAI API-yhteys toimii!")
        except Exception as e:
            raise ValueError(f"OpenAI API-avain ei toimi: {e}")

        # Rekisteröidään käsittelijät
        self.pubsub.subscribe("query", self._handle_query)
        self.pubsub.subscribe("context_update", self._handle_context_update)

    def process_query(self, query: str) -> str:
        """
        Käsittelee kyselyn ja rakentaa kontekstin älykkäästi.

        Prosessi:
        1. Tallenna kysely työmuistiin
        2. Rakenna relevantti konteksti
        3. Suorita LLM-kysely
        4. Tallenna vastaus episodiseen muistiin
        """
        # Tallenna kysely työmuistiin
        self._store_memory("working", query, importance=0.8)

        # Rakenna konteksti
        context = self.context_manager.build_context(query)

        # Suorita kysely
        response = self._run_llm_query(query, context)

        # Tallenna vastaus episodiseen muistiin
        self._store_memory("episodic", f"Q: {query}\nA: {response}", importance=0.6)

        return response

    def _search_memories(
        self, query: str, memories: List[Dict], top_k: int = 5
    ) -> List[Dict]:
        """
        Päivitetty haku, joka huomioi chunk-naapurit (esim. chunk_id +/- 1).
        """
        query_embedding = self.client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        query_vec = query_embedding.data[0].embedding

        scored_memories = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        for memory in memories:
            mem_emb = memory.get("metadata", {}).get("embedding")
            if not mem_emb:
                continue
            sim = self._cosine_similarity(query_vec, mem_emb)

            content_lower = memory["content"].lower()
            keyword_hits = sum(term in content_lower for term in query_terms)
            keyword_score = keyword_hits / len(query_terms) if query_terms else 0

            # Etsi chunk-id
            c_id = memory.get("metadata", {}).get("chunk_id", None)
            # Bonus jos muistilla on vierekkäisiä chunkkeja
            neighbor_bonus = 1.0
            if c_id is not None:
                # Etsi chunkit, joilla chunk_id on lähellä
                neighbors = [
                    m
                    for m in memories
                    if "chunk_id" in m.get("metadata", {})
                    and fabs(m["metadata"]["chunk_id"] - c_id) <= 1
                ]
                if len(neighbors) > 1:
                    neighbor_bonus = 1.1

            final_score = sim * 0.6 + keyword_score * 0.3 + neighbor_bonus * 0.1
            scored_memories.append({**memory, "score": final_score})

        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        return scored_memories[:top_k]

    def _format_memories(self, memories: List[Dict]) -> str:
        """Muotoilee muistit kontekstiksi"""
        return "\n".join([m["content"] for m in memories])

    def _handle_query(self, query: str):
        """Sisäinen kyselyn käsittelijä"""
        # Hae relevantti konteksti
        context = self.memory.get_context(["query_history", "context_chunks"], limit=5)

        # Julkaise konteksti päivitettäväksi
        self.pubsub.publish("context_update", context)

    def _handle_context_update(self, context: str):
        """
        Rakennetaan vastauskonteksti inline-viitteillä
        """
        # Suorita LLM-kysely kontekstilla
        # -> Lisätään linkit, jos memoryssa on "source"-metadata
        enhanced_context_lines = []
        # Koostetaan rivit suoraan chunkin sisällön, chunk_id:n ja sivunumeron perusteella

        # Jos haluamme käyttää jo formatointia, muotoillaan ne muistot.
        # TAI voimme olettaa, että context on jo pelkkää tekstiä.
        # Jotta chunk-tiedot eivät katoa, voidaan muotoilla ne build_context-metodia muokaten.
        # Nämä rivit esimerkinomaisesti havainnollistavat chunk-viitat:

        lines = context.split("\n")
        for line in lines:
            # Etsi mahdolliset chunk-id-linjat
            # Esim. jos build_context() tuottaa "chunk #3 (page 5): Teksti..."
            # Tässä vain varovainen esimerkki
            if "chunk #:" in line.lower() or "page #:" in line.lower():
                # Insert link
                # LISÄ-ESIMERKKI: chunk_id = 3 => [chunk 3]
                enhanced_context_lines.append(f"{line} [link to chunk metadata?]")
            else:
                enhanced_context_lines.append(line)

        new_context = "\n".join(enhanced_context_lines)

        response = self._run_llm_query(
            self.memory.contents["current_query"], new_context
        )
        self.memory.update_memory("final_response", response)

    def _run_llm_query(self, query: str, context: str) -> str:
        """Suorittaa LLM-kyselyn paremmalla kontekstin käytöllä"""
        messages = [
            {
                "role": "system",
                "content": """Olet tutkimusassistentti, joka analysoi tieteellisiä artikkeleita.
                Tehtäväsi on:
                1. Analysoi annettu konteksti huolellisesti
                2. Tunnista tärkeimmät kohdat jotka vastaavat kysymykseen
                3. Muodosta selkeä ja tarkka vastaus perustuen VAIN kontekstiin
                4. Viittaa suoraan dokumentin tekstiin käyttäen lainauksia
                5. Jos vastaus on epävarma tai puutteellinen, kerro se selkeästi
                
                Älä koskaan tee oletuksia kontekstin ulkopuolelta.""",
            },
            {
                "role": "user",
                "content": f"""
                Kysymys: {query}
                
                Relevantti konteksti dokumentista:
                {context}
                
                Vastaa seuraavasti:
                1. Analysoi ensin mitä tietoja konteksti tarjoaa kysymykseen
                2. Muodosta vastaus käyttäen suoria lainauksia
                3. Kerro selkeästi jos jokin osa vastauksesta on puutteellinen
                """,
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,  # Matalampi lämpötila tarkempaa vastausta varten
                max_tokens=800,  # Enemmän tilaa analyysille
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Virhe LLM-kyselyssä: {e}")
            return "Pahoittelen, mutta vastauksen muodostamisessa tapahtui virhe."

    def get_memory_state(self) -> Dict:
        """Palauttaa muistin tilan"""
        return self.memory.get_memory_state()

    def _store_memory(self, memory_type: str, content: str, importance: float):
        """Tallentaa muistin pysyvästi"""
        self.storage.store_memory(memory_type, content, importance)
        self.memory_types = self.storage.memories  # Päivitä muisti

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Laskee kahden vektorin välisen kosinisamankaltaisuuden"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        # Laske kosinisamankaltaisuus
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def clear_memories(self):
        """Tyhjentää kaikki muistit"""
        self.storage.clear_memories()
        self.memory_types = self.storage.memories

    def load_document(self, file_path: str):
        """Lataa dokumentin ja luo embeddingt älykkäällä chunking-logiikalla"""
        from .file_handlers.pdf_handler import read_pdf

        print(f"\nLadataan dokumenttia: {file_path}")
        # Oletus: read_pdf palauttaa listan (page_number, text). Jos ei, korvaa “page=?”
        pages_and_paragraphs = read_pdf(file_path)
        print(f"Luettu {len(pages_and_paragraphs)} kappaletta/sivua")

        # Yhdistä lyhyet kappaleet ja jaa pitkät
        chunks = []
        current_chunk = []
        current_length = 0
        page_info = []  # Tallennetaan sivunumerot chunk-kertymiä varten

        for page_num, paragraph in pages_and_paragraphs:
            # Poista ylimääräiset whitespacet
            text = " ".join(paragraph.split())
            words = text.split()

            # Seurataan sivunumeroa. Käytetään alkusivua chunkin “dlottiin”.
            # Jos chunk-keräykselle ei ole sivunumero vielä tallennettu, otetaan se tästä kappaleesta
            if not page_info:
                page_info.append(page_num)

            # Jos kappale on liian pitkä, jaa se
            if len(words) > 300:  # ~750 tokenia
                for i in range(0, len(words), 250):  # 250 sanan chunkit
                    chunk = " ".join(words[i : i + 250])
                    chunks.append(chunk)
            else:
                # Yhdistä lyhyet kappaleet
                if current_length + len(words) < 300:
                    current_chunk.append(text)
                    current_length += len(words)
                else:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [text]
                    current_length = len(words)
                    page_info = [page_num]

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        print(f"Luotu {len(chunks)} chunkkia")

        # Luo embeddingt chunkeille
        embeddings = self.client.embeddings.create(
            model="text-embedding-ada-002", input=chunks
        )

        # Tallenna chunkit ja embeddingt
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings.data)):
            # page num on se “page_info[0]” jos halutaan tallentaa chunkin sivu
            # (oletuksella että chunk pysyy samalla sivulla)
            # jos haluat keskiarvoa tms., voit muokata logiikkaa.
            page_number = page_info[0] if page_info else 0

            self._store_memory(
                "semantic",
                chunk,
                importance=0.8,
                metadata={
                    "embedding": embedding.embedding,
                    "chunk_id": i,
                    "page_number": page_number,
                    "source": file_path,
                },
            )
        print(f"Tallennettu {len(chunks)} chunkkia muistiin")
