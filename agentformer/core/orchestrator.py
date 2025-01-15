"""Orchestrator Tool - Orkestraattori työkalu

Tämä moduuli toteuttaa järjestelmän pääkoordinaattorin, joka:
1. Analysoi käyttäjän kysymykset ja valitsee sopivat työkalut
2. Hallinnoi työkalujen elinkaarta ja tilanvaihtoja
3. Koordinoi RAG vs. suora LLM -käyttö
4. Integroi muistinhallinnan ja mallien valinnan
5. Ohjaa dokumenttien indeksoinnin ja haun

Arkkitehtuurin keskeinen komponentti:
- Käyttää ToolFactory:a työkalujen luomiseen (lazy loading)
- Toteuttaa Singleton-mallin MessageBus:in kautta
- Mahdollistaa modulaarisen laajennettavuuden
- Hallinnoi järjestelmän tilaa ja moodeja

Käyttö:
    orchestrator = AgentFormerOrchestrator()

    # RAG-moodi (oletus)
    result = orchestrator.process_query("Mitä dokumentissa kerrotaan?")

    # Suora LLM-moodi
    orchestrator.set_mode("llm")
    result = orchestrator.process_query("Kerro yleistietoa aiheesta.")
"""

import logging
import time
from typing import Dict, Any, List, Optional

# Core tools
from agentformer.tools.core_tools.token_tool import TokenTool
from agentformer.tools.core_tools.system_tool import SystemTool
from agentformer.tools.core_tools.prompt_tool import PromptTool

# Analysis tools
from agentformer.tools.analysis_tools.analyzer_tool import AnalyzerTool

from agentformer.storage.memory.memory_manager import MemoryManager
import json
from agentformer.core.messaging import MessageBus, EventType
from agentformer.core.tool_factory import ToolFactory

logger = logging.getLogger(__name__)


class AgentFormerOrchestrator:
    """Koordinoi työkalujen valintaa ja tehtävien suoritusta"""

    def __init__(self):
        self.rag_tool = ToolFactory.create_rag_tool()
        self.model_tool = ToolFactory.create_model_tool()
        self.memory_manager = MemoryManager()
        self.system_tool = SystemTool()
        self.prompt_tool = PromptTool()
        self.token_tool = TokenTool()
        self.analyzer = AnalyzerTool()
        self.document_summaries = {}
        self.mode = "rag"  # Default to RAG mode

        self.tools = {
            "model": self.model_tool,
            "rag": self.rag_tool,
            "llm": self.model_tool,
            "system": self.system_tool,
            "prompt": self.prompt_tool,
            "token": self.token_tool,
        }

    def set_mode(self, mode: str):
        """Aseta toimintatila (llm/rag)"""
        if mode in ["llm", "rag"]:
            self.mode = mode
            logger.info(f"Switched to {mode.upper()} mode")

    def process_query(self, query: str, current_model: str = None) -> Dict[str, Any]:
        """Käsittele käyttäjän kysely käyttäen sopivia työkaluja tilan mukaan"""
        try:
            if self.mode == "llm":
                # Direct LLM mode - bypass analysis and RAG
                model_name = current_model or "gpt-4o-mini"
                response = self.model_tool.query(
                    [{"role": "user", "content": query}],
                    model_name=model_name,
                )
                result = {
                    "response": response,
                    "source": "llm",
                    "model": model_name,
                    "found_in_docs": False,
                }
            else:
                # RAG mode - use full orchestration
                analysis = self.analyze_query(query)
                result = self._get_response(query, analysis)
                result["source"] = "rag" if result.get("found_in_docs") else "llm"

            # Always analyze the interaction
            analysis_result = self.analyzer.analyze_interaction(
                query=query, analysis={"mode": self.mode}, response=result
            )

            if analysis_result.get("feedback_message"):
                result["analyzer_feedback"] = analysis_result["feedback_message"]

            return result

        except Exception as e:
            logger.error(f"Error in query processing: {e}")
            return {"error": str(e), "source": "error", "found_in_docs": False}

    def _get_response(self, query: str, analysis: Dict) -> Dict:
        """Hae vastaus käyttäen sopivaa työkalua analyysin perusteella"""
        if analysis.get("should_use_rag"):
            rag_result = self.tools["rag"].query(query)
            if rag_result.get("found_in_docs", False) and rag_result.get("response"):
                return rag_result

        model_name = analysis.get("model", "gpt-4o")
        response = self.model_tool.query(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant..."},
                {"role": "user", "content": query},
            ]
        )

        return {
            "response": response,
            "source": "language_model",
            "model": model_name,
            "found_in_docs": False,
        }

    def _store_analysis(
        self, query: str, analysis: Dict, response: Dict, analysis_result: Dict
    ):
        """Tallenna vuorovaikutuksen analyysi tulevia parannuksia varten"""
        analysis_data = {
            "timestamp": self._get_timestamp(),
            "query": query,
            "analysis": analysis,
            "response": response,
            "analyzer_feedback": analysis_result,
        }
        self.memory_manager.store_memory(analysis_data, "interaction_analysis")

    def add_document(self, document: bytes, filename: str) -> Dict[str, Any]:
        """Lisää dokumentti järjestelmän muistiin ja luo tiivistelmä"""
        try:
            # Process document with RAG
            rag_result = self.rag_tool.process_file(document, filename)

            # Generate document summary
            summary = self.model_tool.query(
                "gpt-4o",
                system_prompt="Create a concise summary of the document's key topics and content.",
                user_message=rag_result.get("content", ""),
            )

            # Store document summary
            self.document_summaries[filename] = summary

            # Store document metadata
            doc_memory = {
                "filename": filename,
                "type": "document",
                "timestamp": self._get_timestamp(),
                "metadata": rag_result,
                "summary": summary,
            }
            self.memory_manager.store_memory(doc_memory, "semantic")

            return rag_result
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return {"error": str(e)}

    def get_documents_info(self) -> List[Dict[str, Any]]:
        """Hae tiedot tallennetuista dokumenteista"""
        memories = self.memory_manager.retrieve_memories("type:document")
        return [mem for mem in memories if mem.get("type") == "document"]

    def get_saved_files(self) -> List[str]:
        """Hae lista tallennetuista tiedostoista"""
        memories = self.memory_manager.retrieve_memories("type:document")
        return [mem.get("filename") for mem in memories if mem.get("filename")]

    def load_saved_file(self, filename: str) -> bytes:
        """Lataa aiemmin tallennettu tiedosto muistinhallinnasta"""
        memories = self.memory_manager.retrieve_memories(f"filename:{filename}")
        if memories:
            return self.rag_tool.load_saved_file(filename)
        return None

    def _get_timestamp(self) -> float:
        """Hae nykyinen aikaleima"""
        return time.time()

    def analyze_query(self, query: str) -> dict:
        """Analysoi kysely dokumenttikontekstin kanssa"""
        try:
            # Include document summaries in analysis context
            summaries_context = "\n".join(
                [
                    f"Document '{filename}': {summary}"
                    for filename, summary in self.document_summaries.items()
                ]
            )

            # Use o1-mini for fast analysis
            response = self.model_tool.query(
                "o1-mini",
                system_prompt=f"""You are a helpful coordinator guiding your AI colleague. Analyze the question and provide clear, professional guidance.

Available documents and their summaries:
{summaries_context}

Guidelines for providing instructions to your colleague:

1. For document/file related queries (e.g. "what documents do you have", "show articles", "list files"):
   - These are ONLY queries about the documents themselves, not general questions
   - Response: "Let's use RAG to check our document database for this information"
   - Set should_use_rag: true

2. For document content queries (e.g. "what does document X say about Y"):
   - Response: "We should search our document database for relevant information"
   - Set should_use_rag: true

3. For general questions (e.g. "how are you", "what's new", general greetings):
   - Response: "This is a general question - let's handle it directly"
   - Set should_use_rag: false
   - Set model: "o1-mini"

4. For complex analysis:
   - Response: "This requires deeper analysis - please use gpt-4o for a comprehensive response"
   - Set should_use_rag: false

Return a JSON object with:
{{
    "explanation": "Your professional guidance to your colleague",
    "model": "model_name",
    "should_use_rag": true/false,
    "tools": ["tool1", "tool2"]
}}""",
                user_message=query,
            )

            # Parse the response
            try:
                analysis = json.loads(response)
            except:
                analysis = {
                    "explanation": "Let's check our document database for this information",
                    "model": "gpt-4o",
                    "should_use_rag": True,
                    "tools": ["rag"],
                }

            return analysis
        except Exception as e:
            logger.error(f"Error in query analysis: {str(e)}")
            return {
                "explanation": "Let's check our document database for this information",
                "model": "gpt-4o",
                "should_use_rag": True,
                "tools": ["rag"],
            }
