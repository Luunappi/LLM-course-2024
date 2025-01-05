"""RAG Tool for document retrieval and querying"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class RAGTool:
    def __init__(self):
        self.documents = []
        logger.debug("Initialized RAGTool")

    def add_document(self, document: str) -> None:
        """Add document to RAG system"""
        self.documents.append(document)
        logger.debug(f"Added document: {document[:50]}...")

    def query(self, query: str) -> str:
        """Query documents and return relevant information"""
        if not self.documents:
            return "Ei dokumentteja saatavilla"

        # Yksinkertainen haku - tuotannossa käyttäisi embeddingiä
        relevant_docs = []
        for doc in self.documents:
            if any(word.lower() in doc.lower() for word in query.split()):
                relevant_docs.append(doc)

        if not relevant_docs:
            return "Ei löytynyt relevanttia tietoa"

        return " ".join(relevant_docs)
