"""
FaissMemoryBackend

Tämä tiedosto tarjoaa yksinkertaisen esimerkin siitä, miten
pitkäkestoista (tai keskipitkää) muistia voidaan hallita
vektorihakujärjestelmän kautta. Tällä demolla käytämme paikallista
Faiss-indeksiä, joka tallennetaan binääritiedostoon (faiss_index.bin).
Se mahdollistaa, että voimme hakea relevantteja muisteja
embeddings-pohjaisella vektorikyselyllä.

Modulaarinen rakenne sallii sen, että halutessamme voimme siirtyä
käyttämään toista tietokantaa (esim. Cosmos DB) tai erillistä Pinecone-
palvelua. Perusidea on, että vain store/persist/lookup -logiikka vaihtuu,
ylätason MemoryManager-luokan ja muun AgentFormerin ei välttämättä
tarvitse muuttua.

Käyttö:
1. Etsi/toteuta jostain embed-funktio (self._embed_text), joka palauttaa
   vektorin (list/ndarray).
2. Lisää store-funktiota kutsuttaessa tallennus niin, että
   a) Teksti + vektori tallentuu sisäiseen listaan (metadataan).
   b) Myös indeksin päivitys (faiss) tallentuu tiedostoon.

Laajennus: halutessasi siirry Cosmos DB:hen - toteutat vain samat
funktiot (store, search, clear, load/save) Cosmos-lausekkeilla. Voit
säilyttää query-embedding -logiikan identtisenä.

Huom: tämä filu vaatii, että pythonin puolelta on asennettu faiss
(esim. pip install faiss-cpu).
"""

import logging
import os
import json
import numpy as np
from typing import List, Dict, Optional, Any
import faiss

# Määritä tallennuskansio
VECTOR_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vector_database"
)
INDEX_FILE = os.path.join(VECTOR_DB_DIR, "faiss_index.bin")
METADATA_FILE = os.path.join(VECTOR_DB_DIR, "faiss_metadata.json")

# Varmista että kansio on olemassa
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


class FaissMemoryBackend:
    """FAISS-based memory backend for vector storage and retrieval"""

    def __init__(self):
        """Initialize FAISS backend"""
        self.index = None
        self.metadata = []
        self.dimension = 768  # Default dimension for SBERT
        self._load_metadata()
        self._load_index()

    def _init_index(self):
        """Initialize FAISS index with correct dimension"""
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dimension)
            logger.debug(f"Initialized new FAISS index with dimension {self.dimension}")

    def reset_index(self):
        """Reset the FAISS index and metadata"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        self._save_metadata()
        logger.info(f"Reset FAISS index with dimension {self.dimension}")

    def _load_metadata(self):
        """Load metadata from file"""
        try:
            if os.path.isfile(METADATA_FILE):
                logger.debug("Loading metadata from faiss_metadata.json")
                with open(METADATA_FILE, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            self.metadata = []

    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved metadata with {len(self.metadata)} records")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def _load_index(self):
        """Load FAISS index from file"""
        try:
            if os.path.isfile(INDEX_FILE):
                logger.debug("Loading existing FAISS index from faiss_index.bin")
                self.index = faiss.read_index(INDEX_FILE)
                logger.debug(f"Loaded FAISS index with {self.index.ntotal} vectors")
                # Update dimension if needed
                if self.index.d != self.dimension:
                    logger.warning(
                        f"Index dimension mismatch, reinitializing with dimension {self.dimension}"
                    )
                    self._init_index()
            else:
                self._init_index()
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            self._init_index()

    def _save_index(self):
        """Save FAISS index to file"""
        try:
            if self.index is not None:
                faiss.write_index(self.index, INDEX_FILE)
                logger.debug(f"Saved FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def store(
        self,
        content_id: str,
        text_content: str,
        embedding: np.ndarray,
        extra_meta: Dict = None,
    ):
        """Store content with its embedding"""
        try:
            # Ensure embedding is the right shape and type
            embedding = np.ascontiguousarray(embedding.reshape(1, -1), dtype=np.float32)

            # Add to FAISS index
            self.index.add(embedding)

            # Store metadata
            metadata = {
                "content_id": content_id,
                "content": text_content,
                "meta": extra_meta or {},
            }
            self.metadata.append(metadata)

            # Save changes
            self._save_metadata()
            self._save_index()

        except Exception as e:
            logger.error(f"Error storing content: {e}")
            raise

    def semantic_search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """Search for similar content"""
        try:
            # Ensure query embedding is the right shape
            query_embedding = np.ascontiguousarray(
                query_embedding.reshape(1, -1), dtype=np.float32
            )

            # Search
            D, I = self.index.search(query_embedding, k)

            # Get results
            results = []
            for score, idx in zip(D[0], I[0]):
                if idx >= len(self.metadata):
                    continue
                result = {
                    "content": self.metadata[idx]["content"],
                    "meta": self.metadata[idx]["meta"],
                    "distance": float(score),
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def get_saved_files(self) -> List[str]:
        """Get list of saved files in saved_files directory"""
        try:
            saved_files_dir = "agentformer/saved_files"
            if not os.path.exists(saved_files_dir):
                os.makedirs(saved_files_dir)
            return [
                f
                for f in os.listdir(saved_files_dir)
                if os.path.isfile(os.path.join(saved_files_dir, f))
            ]
        except Exception as e:
            logger.error(f"Error getting saved files: {str(e)}")
            return []

    def load_file(self, filename: str) -> Optional[bytes]:
        """Load file content from saved_files directory"""
        try:
            file_path = os.path.join("agentformer/saved_files", filename)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"Error loading file {filename}: {e}")
            return None

    def save_file(self, content: bytes, filename: str) -> bool:
        """Save file to saved_files directory"""
        try:
            saved_files_dir = "agentformer/saved_files"
            if not os.path.exists(saved_files_dir):
                os.makedirs(saved_files_dir)

            file_path = os.path.join(saved_files_dir, filename)
            with open(file_path, "wb") as f:
                f.write(content)

            logger.debug(f"File saved successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            return False
