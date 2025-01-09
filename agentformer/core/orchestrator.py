"""Orchestrator Module

This module coordinates the use of different tools and manages the overall flow of the application.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from agentformer.tools.model_tool import ModelTool
from agentformer.tools.rag_tool import RAGTool
from agentformer.memory.memory_manager import MemoryManager
from agentformer.tools.system_tool import SystemTool
from agentformer.tools.prompt_tool import PromptTool
from agentformer.tools.token_tool import TokenTool

logger = logging.getLogger(__name__)


class AgentFormerOrchestrator:
    """Coordinates tool selection and task execution"""

    TASK_ANALYSIS_PROMPT = """Analyze the query and determine the best way to respond:

    1. Context Analysis
    - Identify key information and requirements
    - Determine query type and complexity
    - Assess available context and history

    2. Response Strategy
    - Choose appropriate memory types to query
    - Determine response format and structure
    - Plan necessary data processing steps

    3. Execution Plan
    - List required operations in sequence
    - Identify potential challenges
    - Prepare fallback options if needed

    4. Quality Criteria
    - Ensure response completeness
    - Verify accuracy and relevance
    - Check for consistency with context

    This structured analysis ensures comprehensive and accurate responses.
    """

    def __init__(self):
        self.model_tool = ModelTool()
        self.rag_tool = RAGTool()
        self.memory_manager = MemoryManager()
        self.system_tool = SystemTool()
        self.prompt_tool = PromptTool()
        self.token_tool = TokenTool()

        self.tools = {
            "model": self.model_tool,
            "rag": self.rag_tool,
            "llm": self.model_tool,  # Add model_tool as llm for compatibility
            "system": self.system_tool,
            "prompt": self.prompt_tool,
            "token": self.token_tool,
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query using appropriate tools"""
        try:
            # Retrieve recent conversations from memory
            recent_conversations = self.memory_manager.retrieve_memories(
                "type:conversation", limit=10
            )
            conversation_context = "\n".join(
                [
                    f"User: {conv.get('query', '')}\nAssistant: {conv.get('response', '')}"
                    for conv in recent_conversations
                ]
            )

            # Store the current query in memory immediately
            current_memory = {
                "query": query,
                "timestamp": time.time(),
                "type": "conversation",
            }

            # Try to find answer from documents first
            rag_result = self.tools["rag"].query(query)

            # If no documents found or answer not in docs, use language model with conversation history
            if not rag_result.get("found_in_docs", False):
                # Create prompt with conversation history
                prompt = f"""Previous conversation:
{conversation_context}

Current question: {query}

Answer the question based on the previous conversation. If you can't find the answer in the conversation history, clearly state that."""

                # Use language model
                response = self.tools["llm"].process(prompt)

                # Update and store memory with response
                current_memory["response"] = response
                self.memory_manager.store_memory(current_memory)

                return {
                    "response": response,
                    "source": "language_model",
                    "found_in_docs": False,
                }

            # If answer found in documents, store it in memory
            current_memory["response"] = rag_result["response"]
            self.memory_manager.store_memory(current_memory)

            return rag_result

        except Exception as e:
            logger.error(f"Error in query processing: {e}")
            return {"error": str(e)}

    def add_document(self, document: bytes, filename: str) -> Dict[str, Any]:
        """Add document to system memory"""
        try:
            # 1. Prosessoi dokumentti RAG-työkalulla
            rag_result = self.rag_tool.process_file(document, filename)

            # 2. Tallenna dokumentin metadata muistiin
            doc_memory = {
                "filename": filename,
                "type": "document",
                "timestamp": self._get_timestamp(),
                "metadata": rag_result,
            }
            self.memory_manager.store_memory(doc_memory, "semantic")

            return rag_result
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return {"error": str(e)}

    def get_documents_info(self) -> List[Dict[str, Any]]:
        """Get information about stored documents"""
        # Hae dokumenttien tiedot muistista
        memories = self.memory_manager.retrieve_memories("type:document")
        return [mem for mem in memories if mem.get("type") == "document"]

    def get_saved_files(self) -> List[str]:
        """Get list of saved files"""
        # Hae tiedostojen nimet muistista
        memories = self.memory_manager.retrieve_memories("type:document")
        return [mem.get("filename") for mem in memories if mem.get("filename")]

    def load_saved_file(self, filename: str) -> bytes:
        """Load previously saved file using memory manager"""
        memories = self.memory_manager.retrieve_memories(f"filename:{filename}")
        if memories:
            return self.rag_tool.load_saved_file(filename)
        return None

    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time

        return time.time()
