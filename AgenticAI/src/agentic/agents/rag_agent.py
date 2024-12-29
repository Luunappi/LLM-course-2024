"""RAG Agent implementation"""

from typing import Dict, Any
from ..core.events import Event
from ..rag import RAGManager
from .base_agent import BaseAgent


class RAGAgent(BaseAgent):
    def __init__(self, name: str = "rag_agent"):
        super().__init__(name)
        self.rag_manager = RAGManager()

        # Register event handlers
        self.register_handler("query", self.handle_query)
        self.register_handler("add_document", self.handle_add_document)

    async def initialize(self) -> None:
        """Initialize RAG components"""
        await self.rag_manager.initialize()

    async def handle_query(self, event: Event) -> Dict[str, Any]:
        """Handle query event"""
        query = event.data.get("query")
        if not query:
            return {"error": "No query provided"}

        result = await self.rag_manager.query(query)
        return result

    async def handle_add_document(self, event: Event) -> Dict[str, Any]:
        """Handle document addition event"""
        content = event.data.get("content")
        doc_id = event.data.get("doc_id")
        metadata = event.data.get("metadata", {})

        if not all([content, doc_id]):
            return {"error": "Missing required fields"}

        await self.rag_manager.add_document(
            content=content, doc_id=doc_id, metadata=metadata
        )

        return {"status": "success", "doc_id": doc_id}
