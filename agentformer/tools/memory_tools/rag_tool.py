"""RAG Tool - Retrieval Augmented Generation implementation"""

import logging
from typing import Dict, Any, Optional, List
from .rag_base import RAGToolBase
from .processing.indexer import DocumentIndexer
from .storage.vector_store import VectorStore
from .processing.embedder import TextEmbedder
from .processing.embedder import EmbedderConfig
import os

logger = logging.getLogger(__name__)


class RAGTool(RAGToolBase):
    """RAG (Retrieval Augmented Generation) implementation."""

    def __init__(self):
        """Initialize RAG tool with indexer and vector store."""
        super().__init__()

        # Set storage directory
        self.storage_dir = os.path.join(
            os.path.dirname(__file__), "../../storage/memory"
        )
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

        # Create saved_files directory
        self.saved_files_dir = os.path.join(self.storage_dir, "saved_files")
        if not os.path.exists(self.saved_files_dir):
            os.makedirs(self.saved_files_dir)

        # Initialize components
        self.indexer = DocumentIndexer()
        self.embedder = TextEmbedder(config=EmbedderConfig())
        self.vector_store = VectorStore(embedder=self.embedder)

        # Load existing index
        self._load_index()

    def _load_index(self):
        """Load existing index from files"""
        try:
            # Read each file and add to vector store
            for filename in self.list_saved_files():
                try:
                    file_path = os.path.join(self.saved_files_dir, filename)

                    # Handle PDF files
                    if filename.lower().endswith(".pdf"):
                        from pypdf import PdfReader

                        reader = PdfReader(file_path)
                        content = ""
                        for page in reader.pages:
                            content += page.extract_text()
                    else:
                        # Handle text files
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                    # Add to vector store
                    self.vector_store.add_texts([content], [filename])
                    logger.info(f"Indexed file: {filename}")

                except Exception as e:
                    logger.error(f"Error indexing file {filename}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")

    def query(self, query: str) -> Dict[str, Any]:
        """Process a query using RAG.

        Args:
            query: User query to process

        Returns:
            Dict containing:
                response: Generated response or None if failed
                found_in_docs: Whether relevant documents were found
                source: Source of response (rag/no_results/error)
                context: Retrieved context if found
                error: Error message if failed
        """
        try:
            logger.info(f"Processing query: {query[:50]}...")

            # Find relevant documents
            results = self.vector_store.semantic_search(query)
            logger.debug(f"Found {len(results)} relevant documents")

            if not results:
                logger.info("No relevant documents found")
                return {
                    "response": "Indeksistä ei löytynyt tietoa. Kokeile ensin lisätä dokumentteja Data-työkalun kautta.",
                    "found_in_docs": False,
                    "source": "no_results",
                    "message": "Indeksistä ei löytynyt tietoa. Suosittelen lisäämään dokumentteja ensin.",
                }

            # Format context from results
            context = "\n".join([r.get("content", "") for r in results])
            logger.debug(f"Created context of length {len(context)}")

            # Generate response using model
            response = self.model_tool.query(
                messages=[
                    {"role": "system", "content": f"Context:\n{context}"},
                    {"role": "user", "content": query},
                ]
            )
            logger.info("Generated response successfully")

            return {
                "response": response,
                "found_in_docs": True,
                "source": "rag",
                "context": context,
            }

        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            return {
                "response": None,
                "found_in_docs": False,
                "source": "error",
                "error": str(e),
            }

    def list_saved_files(self) -> List[str]:
        """List all saved files in the saved_files directory.

        Returns:
            List[str]: List of filenames
        """
        try:
            if not os.path.exists(self.saved_files_dir):
                return []

            files = [
                f
                for f in os.listdir(self.saved_files_dir)
                if os.path.isfile(os.path.join(self.saved_files_dir, f))
            ]
            return files

        except Exception as e:
            logger.error(f"Error listing saved files: {str(e)}")
            return []

    def get_indexed_files(self) -> List[str]:
        """Get list of indexed files.

        Returns:
            List[str]: List of filenames that are indexed in vector store
        """
        return self.list_saved_files()
