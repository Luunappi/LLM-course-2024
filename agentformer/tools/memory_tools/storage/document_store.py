"""Document store for managing text documents.

This module provides:
1. Document storage and retrieval
2. Version control
3. Metadata management
4. Storage optimization
"""

import os
import json
import time
import shutil
import logging
from typing import List, Dict, Optional, NamedTuple, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A document with metadata and version information."""

    id: str
    content: str
    metadata: Optional[Dict] = None
    version: int = 1
    created_at: float = None
    updated_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class DocumentVersion:
    """A specific version of a document."""

    content: str
    metadata: Optional[Dict]
    version: int
    timestamp: float


class DocumentStore:
    """Manages document storage with versioning."""

    def __init__(self, storage_dir: str = "memory/storage/documents"):
        """Initialize document store.

        Args:
            storage_dir: Directory for document storage
        """
        self.storage_dir = storage_dir
        self.docs_dir = os.path.join(storage_dir, "docs")
        self.versions_dir = os.path.join(storage_dir, "versions")
        self.index_path = os.path.join(storage_dir, "index.json")
        self.index: Dict[str, Document] = {}

        self._ensure_directories()
        self._load_index()

    def _ensure_directories(self):
        """Varmista että tarvittavat hakemistot ovat olemassa."""
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        os.makedirs(self.versions_dir, exist_ok=True)

    def _load_index(self):
        """Lataa dokumentti-indeksi tiedostosta."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.index = {k: Document(**v) for k, v in data.items()}
            except Exception as e:
                logger.error(f"Virhe indeksin lataamisessa: {str(e)}")
                self.index = {}
        else:
            self.index = {}

    def _save_index(self):
        """Tallenna dokumentti-indeksi tiedostoon."""
        try:
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(
                    {k: asdict(v) for k, v in self.index.items()},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Virhe indeksin tallennuksessa: {str(e)}")

    def add_document(self, filename: str, content: str, metadata: Dict[str, Any]):
        """Lisää dokumentti varastoon"""
        doc = Document(id=filename, content=content, metadata=metadata)
        self.index[filename] = doc
        self._save_index()

    def get_all_documents(self) -> Dict[str, Any]:
        """Hae kaikki dokumentit"""
        return self.index

    # ... muut metodit kuten aiemmin ...
