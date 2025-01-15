"""
HybridMemoryBackend

Hybridiratkaisu, joka yhdistää FAISS-vektorihaun ja CosmosDB:n metadatavaraston.
FAISS hoitaa tehokkaan vektorihaun paikallisesti, kun taas CosmosDB toimii
skaalautuvana metadatavarastona ja mahdollistaa hajautetun käytön.

Edut:
1. FAISS:n nopea vektorihaku
2. CosmosDB:n skaalautuva metadatan tallennus
3. Hajautettu käyttö mahdollista
4. Varmuuskopiointi ja replikointi CosmosDB:n kautta

Käyttö:
1. Alusta backend omilla Azure Cosmos DB tunnuksilla
2. Käytä store()-metodia dokumenttien tallentamiseen
3. Käytä semantic_search()-metodia hakuihin

Huom: Tämä backend vaatii sekä faiss-cpu että azure-cosmos paketit.
"""

import logging
import os
import json
import numpy as np
from typing import List, Dict, Optional, Any
import faiss
from azure.cosmos import CosmosClient
from datetime import datetime

logger = logging.getLogger(__name__)

# FAISS configuration
VECTOR_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vector_database"
)
INDEX_FILE = os.path.join(VECTOR_DB_DIR, "faiss_index.bin")

# Ensure directory exists
os.makedirs(VECTOR_DB_DIR, exist_ok=True)


class HybridMemoryBackend:
    """Hybrid backend using FAISS for vector search and CosmosDB for metadata"""

    def __init__(self):
        """Initialize hybrid backend with FAISS and CosmosDB"""
        # Initialize FAISS
        self.index = None
        self.dimension = 768  # Default dimension for SBERT
        self._init_faiss()

        # Initialize CosmosDB
        self._init_cosmos()

    def _init_faiss(self):
        """Initialize FAISS index"""
        try:
            if os.path.isfile(INDEX_FILE):
                logger.debug("Loading existing FAISS index")
                self.index = faiss.read_index(INDEX_FILE)
                if self.index.d != self.dimension:
                    logger.warning(f"Index dimension mismatch, reinitializing")
                    self.index = faiss.IndexFlatIP(self.dimension)
            else:
                logger.debug("Creating new FAISS index")
                self.index = faiss.IndexFlatIP(self.dimension)
        except Exception as e:
            logger.error(f"Error initializing FAISS: {e}")
            self.index = faiss.IndexFlatIP(self.dimension)

    def _init_cosmos(self):
        """Initialize CosmosDB connection"""
        try:
            # Get CosmosDB configuration from environment
            endpoint = os.getenv("COSMOS_DB_URI")
            key = os.getenv("COSMOS_DB_PRIMARY_KEY")
            database_name = os.getenv("COSMOS_DB_DATABASE")
            container_name = os.getenv("COSMOS_DB_COLLECTION")

            if not all([endpoint, key, database_name, container_name]):
                raise ValueError("Missing CosmosDB configuration")

            # Initialize CosmosDB client
            self.cosmos_client = CosmosClient(endpoint, key)
            self.database = self.cosmos_client.get_database_client(database_name)
            self.container = self.database.get_container_client(container_name)

            logger.info("Successfully connected to CosmosDB")

        except Exception as e:
            logger.error(f"Error connecting to CosmosDB: {e}")
            raise

    def _save_faiss_index(self):
        """Save FAISS index to file"""
        try:
            if self.index is not None:
                faiss.write_index(self.index, INDEX_FILE)
                logger.debug(f"Saved FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")

    def store(
        self,
        content_id: str,
        text_content: str,
        embedding: np.ndarray,
        extra_meta: Dict = None,
    ):
        """Store content with FAISS handling vectors and CosmosDB handling metadata"""
        try:
            # Prepare embedding for FAISS
            embedding = np.ascontiguousarray(embedding.reshape(1, -1), dtype=np.float32)

            # Add to FAISS index and get the index
            self.index.add(embedding)
            vector_id = self.index.ntotal - 1

            # Prepare metadata for CosmosDB
            metadata = {
                "id": content_id,
                "content": text_content,
                "vector_id": vector_id,
                "timestamp": datetime.utcnow().isoformat(),
                "meta": extra_meta or {},
            }

            # Store metadata in CosmosDB
            self.container.upsert_item(metadata)

            # Save FAISS index
            self._save_faiss_index()

            logger.debug(f"Stored content {content_id} with vector_id {vector_id}")

        except Exception as e:
            logger.error(f"Error storing content: {e}")
            raise

    def semantic_search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """Search using FAISS and fetch metadata from CosmosDB"""
        try:
            # Ensure query embedding is numpy array and right shape
            if isinstance(query_embedding, str):
                logger.error("Expected numpy array for embedding, got string")
                return []

            query_embedding = np.ascontiguousarray(
                query_embedding.reshape(1, -1), dtype=np.float32
            )

            # Search with FAISS
            D, I = self.index.search(query_embedding, k)

            # Get results with metadata from CosmosDB
            results = []
            for score, vector_id in zip(D[0], I[0]):
                try:
                    # Query CosmosDB for metadata using vector_id
                    query = f"SELECT * FROM c WHERE c.vector_id = {vector_id}"
                    items = list(
                        self.container.query_items(
                            query=query, enable_cross_partition_query=True
                        )
                    )

                    if items:
                        metadata = items[0]
                        result = {
                            "content": metadata["content"],
                            "meta": metadata["meta"],
                            "distance": float(score),
                            "vector_id": vector_id,
                            "timestamp": metadata["timestamp"],
                        }
                        results.append(result)

                except Exception as e:
                    logger.error(
                        f"Error fetching metadata for vector_id {vector_id}: {e}"
                    )
                    continue

            return results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def get_saved_files(self) -> List[str]:
        """Get list of unique filenames from CosmosDB"""
        try:
            query = "SELECT DISTINCT VALUE c.meta.filename FROM c WHERE IS_DEFINED(c.meta.filename)"
            files = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )
            return files
        except Exception as e:
            logger.error(f"Error getting saved files: {e}")
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

    def reset_index(self):
        """Reset both FAISS index and CosmosDB container"""
        try:
            # Reset FAISS
            self.index = faiss.IndexFlatIP(self.dimension)
            self._save_faiss_index()

            # Reset CosmosDB (delete all items)
            query = "SELECT c.id FROM c"
            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            for item in items:
                self.container.delete_item(item["id"], partition_key=item["id"])

            logger.info("Reset both FAISS index and CosmosDB container")

        except Exception as e:
            logger.error(f"Error resetting indexes: {e}")
            raise
