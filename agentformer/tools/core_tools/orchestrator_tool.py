"""Orchestrator Tool - Orkestraattori työkalu

Tämä työkalu koordinoi eri työkalujen käyttöä ja hallinnoi sovelluksen kokonaisvirtausta.
Orkestraattori:
1. Analysoi käyttäjän kysymykset
2. Valitsee sopivat työkalut vastauksen muodostamiseen
3. Ohjaa prosessin kulkua ja työkalujen yhteistoimintaa
4. Hallinnoi dokumenttien lisäämistä ja hakua
"""

import logging
import time
from typing import Dict, Any, List, Optional

# Core tools
from agentformer.tools.core_tools.model_tool import ModelTool
from agentformer.tools.core_tools.token_tool import TokenTool
from agentformer.tools.core_tools.system_tool import SystemTool

# Memory tools
from agentformer.tools.memory_tools.rag_tool import RAGTool

# Analysis tools
from agentformer.tools.analysis_tools.analyzer_tool import AnalyzerTool

# UI tools
from agentformer.tools.core_tools.prompt_tool import PromptTool

from agentformer.storage.memory.memory_manager import MemoryManager
import json
from agentformer.core.messaging import MessageBus, EventType

logger = logging.getLogger(__name__)


class OrchestratorTool:
    """Koordinoi työkalujen valintaa ja tehtävien suoritusta"""

    def __init__(self):
        self.model_tool = ModelTool()
        self.rag_tool = RAGTool()
        self.memory_manager = MemoryManager()
        self.system_tool = SystemTool()
        self.prompt_tool = PromptTool()
        self.token_tool = TokenTool()
        self.analyzer = AnalyzerTool()
        self.document_summaries = {}
        self.mode = "rag"  # Default to RAG mode
        self.message_bus = MessageBus()

        self.tools = {
            "model": self.model_tool,
            "rag": self.rag_tool,
            "llm": self.model_tool,
            "system": self.system_tool,
            "prompt": self.prompt_tool,
            "token": self.token_tool,
        }

        # Tehtävätyyppien oletusmallit
        self._task_models = {
            "default": "gpt-4o-mini",  # Kustannustehokas perusvalinta
            "rag": "gpt-4o-mini",  # Hyvä reasoning ja monikielisyys
            "analysis": "gpt-4o-mini",  # Riittävä useimpiin analyyseihin
            "code": "gpt-4o",  # Parempi koodaukseen
            "complex": "gpt-4o",  # Monimutkaisiin tehtäviin
        }

    def set_mode(self, mode: str):
        """Aseta toimintatila (llm/rag)"""
        if mode in ["llm", "rag"]:
            self.mode = mode
            logger.info(f"Switched to {mode.upper()} mode")

    def process_query(self, query: str, current_model: str = None) -> Dict[str, Any]:
        """Käsittele käyttäjän kysely käyttäen sopivia työkaluja tilan mukaan"""
        try:
            logger.info("\n=== Question ===")
            logger.info(query)
            logger.info("===========================")

            result = {}
            analysis = {}

            if self.mode == "llm":
                # Direct LLM mode
                model_name = current_model or "gpt-4o-mini"
                messages = [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant. Answer the question directly using your knowledge.",
                    },
                    {"role": "user", "content": query},
                ]
                response = self.model_tool.query(messages, model_name=model_name)

                logger.info("\n=== Answer ===")
                logger.info(response)
                logger.info("===========================")

                result = {
                    "response": response,
                    "source": "language_model",
                    "model": model_name,
                    "found_in_docs": False,
                }
                analysis = {
                    "mode": "llm",
                    "explanation": "Direct LLM response without RAG",
                    "model": model_name,
                    "should_use_rag": False,
                }
            else:
                # RAG mode
                analysis = self.analyze_query(query)
                logger.info(f"Query analysis: {analysis}")
                result = self._get_response(query, analysis)

                # Lisää tieto vastauksen lähteestä
                if result.get("found_in_docs", False):
                    result["response"] = (
                        f"{result['response']}\n\n[Vastaus perustuu dokumentteihin (RAG)]"
                    )
                else:
                    result["response"] = (
                        f"{result['response']}\n\n[Vastaus tulee suoraan kielimallilta (LLM)]"
                    )

                analysis["mode"] = "rag"

            # Always analyze the interaction
            analysis_result = self.analyzer.analyze_interaction(
                query=query,
                analysis=analysis,
                response=result,
            )

            if analysis_result and analysis_result.get("feedback_message"):
                result["analyzer_feedback"] = analysis_result["feedback_message"]
                result["analyzer_model"] = "o1-mini"

            return result

        except Exception as e:
            logger.error(f"Error in query processing: {e}")
            return {"error": str(e)}

    def _get_response(self, query: str, analysis: Dict) -> Dict:
        """Hae vastaus käyttäen sopivaa työkalua analyysin perusteella"""
        try:
            # RAG-moodi
            if self.mode == "rag":
                logger.info("Using RAG for response")
                return self.tools["rag"].query(query)

            # LLM-moodi
            model_name = analysis.get("model", "gpt-4o-mini")
            messages = [
                {
                    "role": "user",
                    "content": "You are a helpful AI assistant. Answer based on your knowledge.",
                },
                {"role": "user", "content": query},
            ]
            response = self.model_tool.query(messages, model_name=model_name)
            return {
                "response": response,
                "source": "language_model",
                "model": model_name,
                "found_in_docs": False,
            }

        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            return {
                "response": f"Error: {str(e)}",
                "source": "error",
                "model": "unknown",
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

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analysoi kysely ja päätä sopiva käsittelytapa"""
        try:
            logger.info("\n=== Analyzing Query ===")
            logger.info(query)
            logger.info("===========================")

            # Tunnista dokumentteihin liittyvät kysymykset
            doc_keywords = [
                "mitä",
                "mikä",
                "kuka",
                "missä",
                "milloin",
                "miten",
                "miksi",
                "kerro",
                "selitä",
                "kuvaile",
                "määrittele",
                "tarkoittaa",
            ]

            # Jos kysymys sisältää avainsanoja, käytä aina RAG:ia
            should_use_rag = any(keyword in query.lower() for keyword in doc_keywords)

            analysis = {
                "explanation": "Searching document database for relevant information"
                if should_use_rag
                else "Using direct LLM response",
                "model": "gpt-4o-mini",
                "should_use_rag": should_use_rag,
                "tools": ["rag"] if should_use_rag else ["llm"],
            }

            logger.info("\n=== Analysis Result ===")
            logger.info(f"Should use RAG: {should_use_rag}")
            logger.info(f"Selected model: {analysis['model']}")
            logger.info("===========================")

            return analysis

        except Exception as e:
            logger.error(f"Error in query analysis: {str(e)}")
            return {
                "explanation": "Error in analysis",
                "model": "gpt-4o-mini",
                "should_use_rag": False,
                "tools": ["llm"],
            }

    def list_saved_files(self):
        """Välitä kutsu RAGTool:in list_saved_files metodille."""
        try:
            if "rag" not in self.tools:
                logger.error("RAG tool not initialized")
                return []

            # Hae tiedostot RAGTool:ilta
            files = self.tools["rag"].list_saved_files()

            # Varmista että palautetaan lista
            if not isinstance(files, list):
                logger.error(f"RAGTool returned invalid type: {type(files)}")
                return []

            return files

        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
