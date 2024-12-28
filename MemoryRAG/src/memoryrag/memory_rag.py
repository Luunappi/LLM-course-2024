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
import torch


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
        super().__init__()

        # Storage
        self.storage = StorageManager()

        # Memory settings
        self.max_age_days = 30
        self.batch_size = 1000
        self.min_chunk_size = 250
        self.max_workers = 4
        self.cleanup_interval = 24 * 60 * 60  # 24 hours
        self.last_cleanup = time.time()

        # Apple Silicon optimizations
        self.use_mps = torch.backends.mps.is_available()
        if self.use_mps:
            print("Using Apple Silicon MPS acceleration")

        # Initialize vectors and memory
        self.pending_embeddings = []
        self.pending_ids = []
        self.embeddings_index = {}
        self.index_loaded = False

        # Initialize memory types
        self.memory_types = {"core": [], "semantic": [], "episodic": [], "working": []}

        self.memory = AgenticMemory()
        self.pubsub = EnhancedPubSub()
        self.model_name = model_name

        # Lataa API-avain
        repo_root = Path(__file__).resolve().parents[3]
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

        # Alusta OpenAI client
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key)

        # Rekisteröidään käsittelijät
        self.pubsub.subscribe("query", self._handle_query)
        self.pubsub.subscribe("context_update", self._handle_context_update)

        # Instantiate memory_manager and context_manager so tests can call e.g. rag.memory_manager.compress_memories()
        self.memory_manager = MemoryManager(self)
        self.context_manager = ContextManager(self)

        # Initialize embedding model
        try:
            from sentence_transformers import SentenceTransformer

            # Käytetään monikielistä mallia koska meillä on suomenkielistä tekstiä
            self.embedding_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )
        except ImportError:
            raise ImportError(
                "sentence-transformers kirjasto puuttuu! Asenna se: pip install sentence-transformers"
            )

    async def process_query(self, query: str) -> str:
        """Käsittelee kyselyn ja rakentaa kontekstin älykkäästi."""
        # Tallenna kysely työmuistiin
        await self._store_memory("working", query, importance=0.8)

        # Rakenna konteksti
        context = await self.context_manager.build_context(query)

        # Suorita kysely
        response = await self._run_llm_query(query, context)

        # Tallenna vastaus episodiseen muistiin
        await self._store_memory(
            "episodic", f"Q: {query}\nA: {response}", importance=0.6
        )

        return response

    async def _search_memories(
        self, query: str, memories: List[Dict], top_k: int = 5
    ) -> List[Dict]:
        """Päivitetty haku, joka huomioi chunk-naapurit."""
        # Laske kyselyn embedding
        query_emb = await self._compute_embedding(query)

        scored_memories = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        for memory in memories:
            mem_emb = memory.get("metadata", {}).get("embedding")
            if not mem_emb:
                continue
            sim = self._cosine_similarity(query_emb, mem_emb)

            content_lower = memory["content"].lower()
            keyword_hits = sum(term in content_lower for term in query_terms)
            keyword_score = keyword_hits / len(query_terms) if query_terms else 0

            # Etsi chunk-id
            c_id = memory.get("metadata", {}).get("chunk_id", None)
            # Bonus jos muistilla on vierekkäisiä chunkkeja
            neighbor_bonus = 1.0
            if c_id is not None:
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

    async def _handle_query(self, query: str):
        """Sisäinen kyselyn käsittelijä"""
        # Hae relevantti konteksti
        context = await self.memory.get_context(
            ["query_history", "context_chunks"], limit=5
        )

        # Julkaise konteksti päivitettäväksi
        await self.pubsub.publish("context_update", context)

    async def _handle_context_update(self, context: str):
        """Sisäinen kontekstin käsittelijä"""
        # Suorita LLM-kysely kontekstilla
        response = await self._run_llm_query(
            self.memory.contents["current_query"], context
        )

        # Tallenna vastaus
        await self.memory.update_memory("final_response", response)

    async def _run_llm_query(self, query: str, context: str) -> str:
        """Suorittaa LLM-kyselyn."""
        try:
            # Käytetään olemassa olevaa clientia
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
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
                ],
                temperature=0.3,
                max_tokens=800,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Virhe LLM-kyselyssä: {e}")
            return "Pahoittelen, mutta vastauksen muodostamisessa tapahtui virhe."

    def get_memory_state(self) -> Dict:
        """Palauttaa muistin tilan"""
        return self.memory.get_memory_state()

    async def _store_memory(
        self, memory_type: str, content: str, importance: float, metadata: Dict = None
    ):
        """Store memory asynchronously."""
        memory_item = {
            "content": content,
            "importance": importance,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        await self.storage.store_memory(memory_type, memory_item)
        self.memory_types[memory_type].append(memory_item)

        # Prepare embedding
        mem_id = f"{memory_type}_{len(self.memory_types[memory_type])-1}"
        embedding = await self._compute_embedding(content)

        # Add to batch
        await self._add_to_batch(mem_id, embedding)

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

    async def clear_memories(self):
        """Tyhjentää kaikki muistit"""
        await self.storage.clear_memories()
        self.memory_types = self.storage.memories

    async def load_document(self, file_path: str):
        """Lataa dokumentin ja luo embeddingt älykkäällä chunking-logiikalla"""
        from .file_handlers.pdf_handler import read_pdf

        print(f"\nLadataan dokumenttia: {file_path}")
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
        embeddings = []
        for chunk in chunks:
            embedding = await self._compute_embedding(chunk)
            embeddings.append(embedding)

        # Tallenna chunkit ja embeddingt
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            page_number = page_info[0] if page_info else 0

            await self._store_memory(
                "semantic",
                chunk,
                importance=0.8,
                metadata={
                    "embedding": embedding,
                    "chunk_id": i,
                    "page_number": page_number,
                    "source": file_path,
                },
            )
        print(f"Tallennettu {len(chunks)} chunkkia muistiin")

    async def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text using the embedding model."""
        if self.use_mps:
            with torch.no_grad():
                embedding = await self.embedding_model.encode(
                    text, convert_to_numpy=False, normalize_embeddings=True
                )
                # Move to CPU and convert to NumPy
                embedding = embedding.cpu().numpy()
        else:
            embedding = await self.embedding_model.encode(text, convert_to_numpy=True)

        return embedding.astype(np.float32)

    async def _add_to_batch(self, mem_id: str, embedding: np.ndarray):
        """Add embedding to batch for processing."""
        self.pending_embeddings.append(embedding)
        self.pending_ids.append(mem_id)

        if len(self.pending_embeddings) >= self.batch_size:
            await self._parallel_process_batch()

    async def _test_api_connection(self):
        """Testaa API-yhteyden toimivuuden."""
        try:
            print("Testataan OpenAI API-yhteyttä...")
            test_response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
            )
            print("OpenAI API-yhteys toimii!")
        except Exception as e:
            raise ValueError(f"OpenAI API-avain ei toimi: {e}")

    @classmethod
    async def create(cls, model_name: str = "gpt-3.5-turbo"):
        """Asynkroninen tehdasmetodi MemoryRAG:n luomiseen"""
        instance = cls(model_name)
        await instance._test_api_connection()
        await instance._load_memories()
        return instance

    async def _load_memories(self):
        """Lataa muistit tiedostosta"""
        try:
            await self.storage.load_memories()
        except Exception as e:
            print(f"Virhe muistien lataamisessa: {e}")
            # Alustetaan tyhjät muistit jos lataus epäonnistuu
            self.memory_types = {
                "core": [],
                "semantic": [],
                "episodic": [],
                "working": [],
            }
