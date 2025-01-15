"""Tool Factory for lazy loading tools.

This module provides lazy loading functionality for system tools to avoid
circular imports and manage dependencies efficiently.

Classes:
    ToolFactory: Static factory methods for creating tool instances
"""

from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from agentformer.tools.memory_tools.rag_tool import RAGTool
    from agentformer.tools.core_tools.model_tool import ModelTool

T = TypeVar("T")


class ToolFactory:
    """Factory class for creating tool instances."""

    @staticmethod
    def create_rag_tool() -> "RAGTool":
        """Create and configure RAG tool."""
        from agentformer.tools.memory_tools.rag_tool import RAGTool
        from agentformer.tools.core_tools.model_tool import ModelTool

        rag_tool = RAGTool()
        rag_tool.model_tool = ModelTool()
        return rag_tool

    @staticmethod
    def create_model_tool() -> "ModelTool":
        """Create and return a ModelTool instance."""
        from agentformer.tools.core_tools.model_tool import ModelTool

        return ModelTool()
