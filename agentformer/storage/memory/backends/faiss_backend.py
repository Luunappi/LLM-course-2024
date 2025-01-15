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

logger = logging.getLogger(__name__)


class FaissMemoryBackend:
    """FAISS-based memory backend for vector storage and retrieval"""

    def __init__(self):
        """Initialize FAISS backend"""
        # Määritä projektin juurihakemisto
        project_root = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),  # backends/
                "..",  # memory/
                "..",  # storage/
                "..",  # agentformer/
            )
        )

        # Määritä polut suhteessa projektin juureen
        self.storage_dir = os.path.join(project_root, "storage", "memory")
        self.vector_db_dir = os.path.join(self.storage_dir, "vector_database")
        self.saved_files_dir = os.path.join(self.storage_dir, "saved_files")

        logger.info("\n=== Initializing FAISS Backend ===")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Storage directory: {self.storage_dir}")
        logger.info(f"Vector DB directory: {self.vector_db_dir}")
        logger.info(f"Saved files directory: {self.saved_files_dir}")

        # Varmista että kansiot ovat olemassa
        os.makedirs(self.vector_db_dir, exist_ok=True)
        os.makedirs(self.saved_files_dir, exist_ok=True)

        # Indeksin ja metadatan polut
        self.index_path = os.path.join(self.vector_db_dir, "faiss_index.bin")
        self.metadata_path = os.path.join(self.vector_db_dir, "faiss_metadata.json")

        self.dimension = 384  # SBERT embedding dimension
        self.index = None
        self.metadata = []

        self._load_or_create_index()
        logger.info("=== FAISS Backend Initialized ===\n")

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
            if os.path.isfile(self.metadata_path):
                logger.debug("Loading metadata from faiss_metadata.json")
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            self.metadata = []

    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved metadata with {len(self.metadata)} records")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def _load_index(self):
        """Load FAISS index from file"""
        try:
            if os.path.isfile(self.index_path):
                logger.debug("Loading existing FAISS index from faiss_index.bin")
                self.index = faiss.read_index(self.index_path)
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
                faiss.write_index(self.index, self.index_path)
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
            # Ensure query embedding is numpy array and right shape
            if isinstance(query_embedding, str):
                logger.error("Expected numpy array for embedding, got string")
                return []

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
            if not os.path.exists(self.saved_files_dir):
                os.makedirs(self.saved_files_dir)

            return [
                f
                for f in os.listdir(self.saved_files_dir)
                if os.path.isfile(os.path.join(self.saved_files_dir, f))
            ]
        except Exception as e:
            logger.error(f"Error listing saved files: {e}")
            return []

    def load_file(self, filename: str) -> Optional[str]:
        """Load file content from saved_files directory"""
        try:
            file_path = os.path.join(self.saved_files_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading file {filename}: {e}")
            return None

    def save_file(self, filename: str, content: str) -> bool:
        """Save file to saved_files directory"""
        try:
            if not os.path.exists(self.saved_files_dir):
                os.makedirs(self.saved_files_dir)

            file_path = os.path.join(self.saved_files_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            return False
