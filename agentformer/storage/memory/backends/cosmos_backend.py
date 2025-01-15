"""CosmosDB backend for vector storage and retrieval"""

import os
import logging
from typing import List, Dict, Optional, Any
import numpy as np
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        ".env",
    )
)

logger = logging.getLogger(__name__)


class CosmosMemoryBackend:
    """CosmosDB backend for storing and retrieving vector embeddings"""

    def __init__(self):
        """Initialize CosmosDB connection"""
        try:
            # Get connection details from environment variables
            self.cosmos_uri = os.getenv("COSMOS_DB_URI")
            self.cosmos_key = os.getenv("COSMOS_DB_PRIMARY_KEY")
            self.database_name = os.getenv("COSMOS_DB_DATABASE")
            self.collection_name = os.getenv("COSMOS_DB_COLLECTION")

            if not all(
                [
                    self.cosmos_uri,
                    self.cosmos_key,
                    self.database_name,
                    self.collection_name,
                ]
            ):
                raise ValueError("Missing required CosmosDB environment variables")

            # Initialize CosmosDB client
            self.client = CosmosClient(self.cosmos_uri, credential=self.cosmos_key)
            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(self.collection_name)

            logger.info(f"Connected to CosmosDB database: {self.database_name}")

        except Exception as e:
            logger.error(f"Error initializing CosmosDB backend: {str(e)}")
            raise

    def store(
        self,
        content_id: str,
        text_content: str,
        embedding: np.ndarray,
        extra_meta: Dict = None,
    ) -> bool:
        """Store content with its embedding vector"""
        try:
            # Convert numpy array to list for JSON serialization
            embedding_list = (
                embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            )

            # Create document
            document = {
                "id": content_id,
                "content": text_content,
                "embedding": embedding_list,
                "metadata": extra_meta or {},
            }

            # Store in CosmosDB
            self.container.upsert_item(document)
            return True

        except Exception as e:
            logger.error(f"Error storing content in CosmosDB: {str(e)}")
            return False

    def semantic_search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """Perform semantic search using cosine similarity"""
        try:
            # Convert query embedding to list
            query_vector = (
                query_embedding.tolist()
                if isinstance(query_embedding, np.ndarray)
                else query_embedding
            )

            # Query to calculate cosine similarity
            query = {
                "query": f"""
                SELECT TOP {k} c.id, c.content, c.metadata,
                    (
                        SELECT VALUE dotProduct(c.embedding, @queryVector) / 
                        (SQRT(dotProduct(c.embedding, c.embedding)) * 
                         SQRT(dotProduct(@queryVector, @queryVector)))
                    ) AS similarity
                FROM c
                ORDER BY similarity DESC
                """,
                "parameters": [{"name": "@queryVector", "value": query_vector}],
            }

            results = list(
                self.container.query_items(
                    query=query["query"],
                    parameters=query["parameters"],
                    enable_cross_partition_query=True,
                )
            )

            # Format results
            formatted_results = []
            for item in results:
                formatted_results.append(
                    {
                        "content": item["content"],
                        "meta": item["metadata"],
                        "distance": 1
                        - item["similarity"],  # Convert similarity to distance
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []

    def get_saved_files(self) -> List[str]:
        """Get list of saved files"""
        try:
            query = "SELECT DISTINCT VALUE c.metadata.filename FROM c WHERE IS_DEFINED(c.metadata.filename)"
            results = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )
            return results

        except Exception as e:
            logger.error(f"Error getting saved files: {str(e)}")
            return []

    def save_file(self, content: bytes, filename: str) -> bool:
        """Save file metadata"""
        try:
            document = {
                "id": f"file_{filename}",
                "type": "file_metadata",
                "filename": filename,
                "size": len(content),
            }
            self.container.upsert_item(document)
            return True

        except Exception as e:
            logger.error(f"Error saving file metadata: {str(e)}")
            return False

    def load_file(self, filename: str) -> Optional[bytes]:
        """Load file from saved_files directory"""
        try:
            file_path = os.path.join("agentformer/saved_files", filename)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"Error loading file {filename}: {str(e)}")
            return None

    def reset_index(self):
        """Clear all documents from the container"""
        try:
            # Delete all documents except file metadata
            query = "SELECT c.id FROM c WHERE c.type != 'file_metadata'"
            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            for item in items:
                self.container.delete_item(item["id"], partition_key=item["id"])

            logger.info("Index reset successfully")

        except Exception as e:
            logger.error(f"Error resetting index: {str(e)}")
            raise
