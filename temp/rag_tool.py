"""RAG Tool for document retrieval and querying"""

import logging
from typing import List, Optional, Dict, Any
from tools.model_tool import ModelTool

logger = logging.getLogger(__name__)


class RAGTool:
    def __init__(self):
        self.documents = []
        self.model_tool = ModelTool()  # Singleton instance
        logger.debug("Initialized RAGTool")

    def add_document(self, document: str) -> None:
        """Add document to RAG system"""
        self.documents.append(document)
        logger.debug(f"Added document: {document[:50]}...")

    def query(self, query: str) -> Dict[str, Any]:
        """Query documents and return relevant information"""
        if not self.documents:
            return {"response": "Ei dokumentteja saatavilla", "found_in_docs": False}

        # Hae sopiva malli hakuvaiheeseen RAG-spesifeillä asetuksilla
        retrieval_model = self.model_tool.get_model_for_task("rag_retrieval")
        retrieval_config = self.model_tool.get_model_config(
            retrieval_model, tool_name="rag_tool"
        )

        # Yksinkertainen haku - tuotannossa käyttäisi embeddingiä
        relevant_docs = []
        for doc in self.documents:
            if any(word.lower() in doc.lower() for word in query.split()):
                relevant_docs.append(doc)

        if not relevant_docs:
            return {
                "response": "Ei löytynyt relevanttia tietoa",
                "found_in_docs": False,
            }

        # Hae sopiva malli vastauksen generointiin RAG-spesifeillä asetuksilla
        generation_model = self.model_tool.get_model_for_task("rag_generation")
        generation_config = self.model_tool.get_model_config(
            generation_model, tool_name="rag_tool"
        )

        # Tässä käytettäisiin generation_modelia vastauksen muodostamiseen
        response = " ".join(relevant_docs)  # Placeholder, oikeasti käyttäisi mallia

        return {
            "response": response,
            "found_in_docs": True,
            "models_used": [
                f"{retrieval_model} (retrieval)",
                f"{generation_model} (generation)",
            ],
        }
