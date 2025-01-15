"""Base class for RAG functionality"""

from typing import Dict, Any
from ..core_tools.model_tool import ModelTool


class RAGToolBase:
    """Base class for RAG implementations."""

    def __init__(self):
        """Initialize base RAG tool."""
        self.model_tool = ModelTool()

    def query(self, query: str) -> Dict[str, Any]:
        """Process a query using RAG.

        Args:
            query: User query

        Returns:
            Dict containing response and metadata
        """
        raise NotImplementedError("Subclasses must implement query method")
