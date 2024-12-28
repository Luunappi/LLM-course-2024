from typing import List, Dict, Any, Optional, Tuple
from MemoryRAG.src.memoryrag.agentic_memory import AgenticMemory
from MemoryRAG.src.memoryrag.pubsub import EnhancedPubSub
from MemoryRAG.src.memoryrag.memory_operations import MemoryOperations
from MemoryRAG.src.memoryrag.memory_manager import MemoryManager
from MemoryRAG.src.memoryrag.context_manager import ContextManager
from MemoryRAG.src.memoryrag.storage import StorageManager
import time
import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import torch
from concurrent.futures import ThreadPoolExecutor
import math
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiofiles
from openai import AsyncOpenAI


@dataclass
class IndexConfig:
    """Indeksin konfiguraatio eri datamäärille."""

    dim: int
    nlist: int  # Voronoi-solujen määrä
    nprobe: int  # Haettavien solujen määrä
    use_pq: bool = False  # Product Quantization
    pq_m: int = 8  # Määrä alikvantisaattoreita PQ:lle
    pq_bits: int = 8  # Bittejä per alikvantisaattori


class IndexType(Enum):
    FLAT = "flat"
    IVF = "ivf"
    IVF_PQ = "ivf_pq"


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

        # Initialize vectors and memory
        self.pending_embeddings = []
        self.pending_ids = []
        self.embeddings_index = {}
        self.index_loaded = False

        # Initialize memory types
        self.memory_types = {"core": [], "semantic": [], "episodic": [], "working": []}

        # Initialize components
        self.memory = AgenticMemory()
        self.pubsub = EnhancedPubSub()
        self.model_name = model_name
        self.memory_manager = MemoryManager()
        self.context_manager = ContextManager(self)

        # Embedding model initialization
        self.embedding_model = SentenceTransformer(
            "sentence-transformers/all-mpnet-base-v2"
        )
        self.embedding_dim = 768

        # Move model to MPS if available
        if self.use_mps:
            print("Using Apple Silicon MPS acceleration")
            self.embedding_model = self.embedding_model.to("mps")

        # Initialize Faiss index
        self._init_index()

    @classmethod
    async def create(cls, model_name: str = "gpt-3.5-turbo"):
        """Asynkroninen tehdasmetodi MemoryRAG:n luomiseen"""
        instance = cls(model_name)
        await instance._load_memories()
        return instance

    def _init_index(self):
        """Alustaa Faiss-indeksin."""
        n = len(self.embeddings_index)
        config = self._get_index_config(n)

        # Apple Silicon optimointi
        if (
            hasattr(faiss, "supported_cpu_features")
            and "neon" in faiss.supported_cpu_features()
        ):
            print("Using ARM NEON optimizations for Faiss")
            faiss.cvar.CPU_FEATURE_NEON = True
            faiss.cvar.CPU_FEATURE_AVX2 = False

        # Alusta indeksi konfiguraation mukaan
        if config.use_pq:
            quantizer = faiss.IndexFlatL2(config.dim)
            self.index = faiss.IndexIVFPQ(
                quantizer, config.dim, config.nlist, config.pq_m, config.pq_bits
            )
        else:
            quantizer = faiss.IndexFlatL2(config.dim)
            self.index = faiss.IndexIVFFlat(
                quantizer, config.dim, config.nlist, faiss.METRIC_L2
            )

        self.index.nprobe = config.nprobe
        self.is_trained = False

    async def process_query(self, query: str) -> str:
        """
        Käsittelee kyselyn ja rakentaa kontekstin älykkäästi.
        """
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
        """
        Päivitetty haku, joka huomioi chunk-naapurit.
        """
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

            final_score = sim * 0.6 + keyword_score * 0.4
            scored_memories.append({**memory, "score": final_score})

        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        return scored_memories[:top_k]

    async def _run_llm_query(self, query: str, context: str) -> str:
        """Suorittaa LLM-kyselyn."""
        try:
            client = AsyncOpenAI()

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

            response = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=800,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Virhe LLM-kyselyssä: {e}")
            return "Pahoittelen, mutta vastauksen muodostamisessa tapahtui virhe."

    async def clear_memories(self):
        """Tyhjentää kaikki muistit"""
        await self.storage.clear_memories()
        self.memory_types = self.storage.memories

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

    def _format_memories(self, memories: List[Dict]) -> str:
        """Muotoilee muistit kontekstiksi"""
        return "\n".join([m["content"] for m in memories])

    def get_memory_state(self) -> Dict:
        """Palauttaa muistin tilan"""
        return self.memory.get_memory_state()

    async def _train_index_if_needed(self, embeddings: np.ndarray):
        """Train the IVF index if not already trained."""
        if not self.is_trained:
            config = self._get_index_config(len(embeddings))  # Hae konfiguraatio
            if len(embeddings) < config.nlist:
                # Not enough data to train, fall back to flat index
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                return

            print("Training IVF index...")
            await self._train_index_async(embeddings)
            self.is_trained = True

    async def _train_index_async(self, embeddings: np.ndarray):
        """Asynkroninen indeksin koulutus"""
        # Suorita raskas koulutus asynkronisesti ThreadPoolissa
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.index.train, embeddings)

    async def _add_to_batch(self, mem_id: str, embedding: np.ndarray):
        """Add embedding to batch for processing."""
        self.pending_embeddings.append(embedding)
        self.pending_ids.append(mem_id)

        if len(self.pending_embeddings) >= self.batch_size:
            await self._process_batch()

    async def _process_batch(self):
        """Process accumulated embeddings in batch."""
        if not self.pending_embeddings:
            return

        embeddings_array = np.vstack(self.pending_embeddings)

        # Train index if needed
        await self._train_index_if_needed(embeddings_array)

        # Add embeddings to index asynchronously
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.index.add, embeddings_array)

        # Update embeddings_index
        for mem_id, emb in zip(self.pending_ids, self.pending_embeddings):
            self.embeddings_index[mem_id] = {
                "embedding": emb,
                "timestamp": time.time(),
            }

        # Clear pending lists
        self.pending_embeddings = []
        self.pending_ids = []

    async def cleanup_old_embeddings(self):
        """Poistaa vanhat embeddingit ja optimoi muistinkäyttöä."""
        current_time = time.time()

        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        self.last_cleanup = current_time
        max_age = self.max_age_days * 24 * 60 * 60

        # Find old embeddings
        old_ids = []
        for mem_id, data in self.embeddings_index.items():
            if current_time - data["timestamp"] > max_age:
                old_ids.append(mem_id)

        if not old_ids:
            return

        # Remove old embeddings
        print(f"Removing {len(old_ids)} old embeddings...")

        # Create new index without old embeddings
        new_embeddings = []
        new_ids = []

        for mem_id, data in self.embeddings_index.items():
            if mem_id not in old_ids:
                new_embeddings.append(data["embedding"])
                new_ids.append(mem_id)

        # Recreate index with remaining embeddings
        if new_embeddings:
            embeddings_array = np.vstack(new_embeddings)
            config = self._get_index_config(len(new_embeddings))  # Hae konfiguraatio
            self.index = faiss.IndexIVFFlat(
                faiss.IndexFlatL2(config.dim), config.dim, config.nlist, faiss.METRIC_L2
            )
            await self._train_index_if_needed(embeddings_array)
            self.index.add(embeddings_array)
        else:
            # No embeddings left, reset everything
            config = self._get_index_config(0)  # Hae oletuskonfiguraatio
            self.index = faiss.IndexIVFFlat(
                faiss.IndexFlatL2(config.dim), config.dim, config.nlist, faiss.METRIC_L2
            )
            self.embeddings_index = {}
            self.is_trained = False

    async def _store_memory(self, memory_type: str, content: str, importance: float):
        """Store memory asynchronously."""
        memory_item = {
            "content": content,
            "importance": importance,
            "timestamp": time.time(),
        }
        await self.storage.store_memory(memory_type, memory_item)
        self.memory_types[memory_type].append(memory_item)

        # Prepare embedding
        mem_id = f"{memory_type}_{len(self.memory_types[memory_type])-1}"
        embedding = await self._compute_embedding(content)

        # Add to batch
        await self._add_to_batch(mem_id, embedding)

        # Run cleanup if needed
        await self.cleanup_old_embeddings()

        # Check if index needs optimization
        if len(self.embeddings_index) > 0 and len(self.embeddings_index) % 100_000 == 0:
            self._optimize_index()

    async def load_vectorstore(self, path: str = "local_memory_index.json") -> None:
        """Lataa tallennetut embeddingit ja rakenna Faiss-indeksi."""
        if os.path.exists(path):
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())

            # Alusta uusi indeksi
            self.index = faiss.IndexFlatL2(self.embedding_dim)

            # Muunna JSON-listat takaisin NumPy-taulukoiksi ja lisää Faiss-indeksiin
            embeddings = []
            for mem_id, emb_list in data.items():
                embedding = np.array(emb_list, dtype=np.float32)
                self.embeddings_index[mem_id] = embedding
                embeddings.append(embedding)

            if embeddings:
                embeddings_array = np.vstack(embeddings)
                # Add embeddings asynchronously
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.index.add, embeddings_array)

            self.index_loaded = True
            print(f"[MemoryRAG] Ladattiin {len(self.embeddings_index)} embeddingiä.")
        else:
            print(f"[MemoryRAG] Ei löydetty aiempia embeddingejä: {path}")

    async def save_vectorstore(self, path: str = "local_memory_index.json") -> None:
        """Tallenna embeddingit ja indeksi."""
        # Tallenna embeddingit JSON-muodossa
        data = {mem_id: emb.tolist() for mem_id, emb in self.embeddings_index.items()}
        os.makedirs(os.path.dirname(path), exist_ok=True)

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))

        # Tallenna Faiss-indeksi binäärimuodossa
        faiss_path = path.replace(".json", ".faiss")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, faiss.write_index, self.index, faiss_path)

        print(f"[MemoryRAG] Tallennettu {len(self.embeddings_index)} embeddingiä.")

    async def _compute_embedding(self, text: str) -> np.ndarray:
        """Laske embedding tekstille käyttäen all-mpnet-base-v2 mallia."""
        # Käytä MPS:ää jos saatavilla
        if self.use_mps:
            with torch.no_grad():
                embedding = await self.embedding_model.encode(
                    text, convert_to_numpy=False, normalize_embeddings=True
                )
                # Siirrä CPU:lle ja muunna NumPy:ksi
                embedding = embedding.cpu().numpy()
        else:
            embedding = await self.embedding_model.encode(text, convert_to_numpy=True)

        return embedding.astype(np.float32)

    async def semantic_search(self, query: str, top_k: int = 3) -> List[str]:
        """Hae semanttisesti samankaltaiset muistit Faiss-indeksillä."""
        if not self.embeddings_index:
            print("[MemoryRAG] Ei embeddingejä - palautetaan tyhjä lista.")
            return []

        # Laske kyselyn embedding
        query_emb = await self._compute_embedding(query)

        # Hae lähimmät naapurit Faiss-indeksistä
        D, I = self.index.search(query_emb.reshape(1, -1), top_k)

        # Muunna indeksit takaisin muisti-id:iksi
        mem_ids = list(self.embeddings_index.keys())
        results = []
        for idx in I[0]:
            if idx < len(mem_ids):
                mid = mem_ids[idx]
                mtype, idx_str = mid.rsplit("_", maxsplit=1)
                idx = int(idx_str)
                if idx < len(self.memory_types[mtype]):
                    results.append(self.memory_types[mtype][idx]["content"])

        return results

    def _get_index_config(self, n_vectors: int) -> IndexConfig:
        """Määrittää optimaalisen indeksikonfiguraation."""
        if n_vectors > 1_000_000:
            nlist = int(math.sqrt(n_vectors) * 4)
            return IndexConfig(
                dim=self.embedding_dim,
                nlist=nlist,
                nprobe=min(nlist // 4, 2048),
                use_pq=True,
            )
        elif n_vectors > 100_000:
            nlist = int(math.sqrt(n_vectors))
            return IndexConfig(
                dim=self.embedding_dim,
                nlist=nlist,
                nprobe=min(nlist // 4, 256),
                use_pq=False,
            )
        else:
            return IndexConfig(
                dim=self.embedding_dim, nlist=100, nprobe=10, use_pq=False
            )

    def _process_chunk(self, chunk: List[np.ndarray]) -> np.ndarray:
        """Prosessoi yhden batch-palan."""
        if not chunk:
            return None
        return np.vstack(chunk)

    async def _parallel_process_batch(self):
        """Prosessoi batch rinnakkaisesti."""
        if len(self.pending_embeddings) < self.batch_size:
            return

        # Määritä työntekijöiden määrä
        chunk_size = max(
            self.min_chunk_size, len(self.pending_embeddings) // self.max_workers
        )
        n_workers = min(self.max_workers, len(self.pending_embeddings) // chunk_size)

        # Jaa batch sopiviin paloihin
        chunks = [
            self.pending_embeddings[i : i + chunk_size]
            for i in range(0, len(self.pending_embeddings), chunk_size)
        ]

        # Prosessoi rinnakkain asynkronisesti
        tasks = [self._process_chunk(chunk) for chunk in chunks]
        processed_chunks = await asyncio.gather(*tasks)
        processed_chunks = [c for c in processed_chunks if c is not None]

        # Yhdistä tulokset
        if processed_chunks:
            embeddings_array = np.vstack(processed_chunks)
            await self._train_index_if_needed(embeddings_array)

            # Add to index asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.index.add, embeddings_array)

            # Update embeddings_index
            for mem_id, emb in zip(self.pending_ids, self.pending_embeddings):
                self.embeddings_index[mem_id] = {
                    "embedding": emb,
                    "timestamp": time.time(),
                }

        # Clear pending lists
        self.pending_embeddings = []
        self.pending_ids = []

    def _optimize_index(self):
        """Optimoi indeksin datamäärän mukaan."""
        # Tämä metodi on tällä hetkellä tyhjä, koska optimointi on tällä hetkellä toteutettu
        # automaattisesti kun uusia embeddingeja lisätään.
        pass

    async def _load_memories(self):
        """Lataa muistit"""
        self.memory_types = await self.storage.load_memories()

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Laske vektorien välinen kosinisamankaltaisuus."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
