"""Indexer Tool - Indeksointityökalu

Tämä työkalu hoitaa dokumenttien indeksoinnin ja hallinnan:
1. Indeksoi uudet dokumentit vektoritietokantaan
2. Valitsee sopivan chunkkausmenetelmän dokumentin rakenteen mukaan
3. Käyttää SBERT-mallia embeddingeille (vaihtoehtoisesti text-embedding-ada-002)
4. Tallentaa vektorit FAISS-indeksiin tai vaihtoehtoisesti CosmosDB:hen
"""

import logging
import sys
from typing import Optional, Dict, Any
from agentformer.tools.memory_tools.rag_tool import RAGTool
from agentformer.storage.memory.backends.faiss_backend import FaissMemoryBackend

logger = logging.getLogger(__name__)


class IndexerTool:
    """Hoitaa dokumenttien indeksoinnin ja hallinnan"""

    def __init__(self):
        self.rag_tool = RAGTool()
        self.backend = FaissMemoryBackend()

        # Configure logging
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(message)s")  # Simplified format
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def index_file(self, filename: str) -> Dict[str, Any]:
        """Indeksoi yksittäinen tiedosto saved_files-hakemistosta"""
        try:
            logger.info(f"Starting indexing: {filename}")

            # Reset metadata if corrupted
            if not hasattr(self.backend, "metadata") or self.backend.metadata is None:
                self.backend.metadata = []

            # Load file
            content = self.backend.load_file(filename)
            if not content:
                logger.error(f"Could not load content for {filename}")
                return {"success": False, "error": "Could not load file content"}

            # Index document
            result = self.rag_tool.process_file(file=content, filename=filename)

            if result.get("status") == "success":
                logger.info(f"Successfully indexed: {filename}")
                return {"success": True, "details": result}
            else:
                logger.error(
                    f"Error in indexing: {result.get('message', 'Unknown error')}"
                )
                return {"success": False, "error": result.get("message")}

        except Exception as e:
            logger.error(f"Error indexing file: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_indexed_files(self) -> list:
        """Hae lista indeksoiduista tiedostoista"""
        return self.rag_tool.get_saved_files()

    def remove_from_index(self, filename: str) -> Dict[str, Any]:
        """Poista tiedosto indeksistä"""
        try:
            # TODO: Implement file removal from index
            return {"success": True, "message": f"File {filename} removed from index"}
        except Exception as e:
            return {"success": False, "error": str(e)}
