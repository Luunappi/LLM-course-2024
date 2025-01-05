"""
Orchestrator for AgentFormer
Handles tool selection and coordination
"""

import logging
import time
from pathlib import Path
from typing import Any, Optional, Dict
from memory.memory_manager import MemoryManager
from tools.diagram_tool import DiagramTool
from core.messaging import MessageBus, EventType, Message
from ui_components.model_module import Models

# DEBUG: Konfiguroi debug-loggaus
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# DEBUG: Lisää file handler debug.log tiedostoon
debug_handler = logging.FileHandler("debug.log")
debug_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
debug_handler.setFormatter(formatter)
logger.addHandler(debug_handler)


class AgentFormerOrchestrator:
    def __init__(self):
        # DEBUG: Luo instanssi ja alusta komponentit
        logger.debug("Initializing AgentFormerOrchestrator")
        try:
            self.message_bus = MessageBus(orchestrator=self)
            self.memory = MemoryManager()
            self.tools = {}
            self.current_state = {}
            self.models = Models()

            # Rekisteröi perusviestien käsittelijät
            self._register_message_handlers()

            # Rekisteröi työkalut
            self._register_default_tools()

            # DEBUG: Tarkista alustuksen tila
            logger.debug(f"Initialization complete. State: {self.get_current_state()}")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
            raise RuntimeError(f"Orchestrator initialization failed: {str(e)}")

    def _register_message_handlers(self):
        """Register all message handlers"""
        handlers = {
            EventType.CHAT_MESSAGE: self._handle_chat,
            EventType.RAG_QUERY: self._handle_rag,
            EventType.ERROR: self._handle_error,
        }
        for event_type, handler in handlers.items():
            self.message_bus.subscribe(event_type, handler)
            logger.debug(f"Registered handler for {event_type}")

    def _register_default_tools(self):
        """Register default system tools"""
        try:
            self.register_tool("diagram", DiagramTool())
            logger.info("Registered default tools")
        except Exception as e:
            logger.error(f"Failed to register default tools: {e}")

    def register_tool(self, name: str, tool: Any):
        """Register tool and its message handlers"""
        self.tools[name] = tool
        # Subscribe tool's handlers
        for capability in tool.capabilities:
            self.message_bus.subscribe(f"{name}_{capability}", tool.handle_capability)

    def process_request(self, request_type: str, data: dict) -> dict:
        """Process request and return response dictionary"""
        try:
            response = self.message_bus.publish(request_type, data)
            if isinstance(response, str):
                return {
                    "response": response,
                    "input_tokens": len(data.get("message", "")),
                    "output_tokens": len(response),
                    "total_tokens": len(data.get("message", "")) + len(response),
                }
            return response
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {"error": str(e)}

    def _handle_chat(self, message: Message):
        """Handle chat requests"""
        try:
            user_input = message.data.get("message", "")
            if not user_input:
                return {"response": "Tyhjä viesti, kirjoita jotain"}

            # Hae konteksti muistista
            context = None
            try:
                memories = self.memory.retrieve_memories(user_input)
                if memories:
                    context = "\n".join(str(m["content"]) for m in memories)
            except Exception as mem_error:
                logger.error(f"Error retrieving context: {mem_error}")

            # Generoi vastaus
            response = self.models.generate_response(user_input, context)

            # Tallenna vastaus muistiin
            try:
                self.memory.store_memory(
                    {"content": f"{user_input} -> {response}"}, memory_type="episodic"
                )
            except Exception as mem_error:
                logger.error(f"Error storing response: {mem_error}")

            # Palauta vastaus sanakirjana
            return {
                "response": response,
                "input_tokens": len(user_input),
                "output_tokens": len(response),
                "total_tokens": len(user_input) + len(response),
            }

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {"error": f"Virhe viestin käsittelyssä: {str(e)}"}

    def _handle_rag(self, message: Message):
        """Handle RAG requests"""
        query = message.data.get("query", "")
        context = message.data.get("context", [])
        # RAG-specific logic here
        return {"response": "RAG response placeholder"}

    def _handle_diagram(self, message: Message):
        """Handle diagram generation requests"""
        if "diagram" not in self.tools:
            raise ValueError("Diagram tool not registered")
        return self.tools["diagram"].create_example_diagram(message.data)

    def _handle_error(self, message: Message):
        """Keskitetty virheenkäsittely"""
        error_data = message.data
        logging.error(f"Error in {error_data['source']}: {error_data['error']}")
        # Voidaan lisätä automaattista virheestä toipumista

    def initialize_memory(self, instruction_text, contents_text) -> None:
        """Initialize memory with instructions"""
        try:
            logger.debug(f"Initializing memory with instructions: {instruction_text}")
            # Käytä uutta MemoryManager-luokkaa
            self.memory = MemoryManager()

            # Tallenna alkutiedot muistiin
            self.memory.store_memory(
                {"instructions": instruction_text, "contents": contents_text},
                memory_type="core",  # Tallenna ydinmuistiin
            )

            logger.info("Memory initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize memory: {e}")
            raise RuntimeError(f"Memory initialization failed: {str(e)}")

    def get_current_state(self):
        """Get current orchestrator state"""
        return {
            "memory_state": self.memory.get_memory_state() if self.memory else None,
            "active_tools": list(self.tools.keys()),
            "current_state": self.current_state,
            "current_model": self.models.get_current_model(),
        }

    def get_memory_state(self) -> Dict:
        """Get detailed memory state for debugging"""
        try:
            if not self.memory:
                return {"status": "not_initialized"}

            return {
                "status": "active",
                "state": self.memory.get_memory_state(),
            }
        except Exception as e:
            logger.error(f"Error getting memory state: {e}")
            return {"status": "error", "message": str(e)}

    # DEBUG: Apufunktio virhetilanteen tallentamiseen
    def _log_error_state(self, error: Exception) -> None:
        """Log detailed error state for debugging"""
        try:
            error_state = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "memory_state": self.get_memory_state(),
                "current_state": self.current_state,
                "active_tools": list(self.tools.keys()),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            logger.debug(f"Error state: {error_state}")
        except Exception as e:
            logger.error(f"Failed to log error state: {e}")

    def process_document(self, file):
        """Process uploaded document using RAG components"""
        # Implement document processing using SBERT+FAISS
        # This is just a skeleton - actual implementation depends on your RAG components
        try:
            # 1. Extract text from document
            text = self.extract_text(file)

            # 2. Split into chunks
            chunks = self.split_text(text)

            # 3. Create embeddings
            embeddings = self.create_embeddings(chunks)

            # 4. Store in FAISS index
            self.store_embeddings(embeddings)

            return True

        except Exception as e:
            logger.error(f"Document processing error: {e}")
            raise

    def set_model(self, model: str) -> bool:
        """Switch to a different model"""
        try:
            success = self.models.set_model(model)
            if success:
                # Päivitä tila
                self.current_state["current_model"] = self.models.get_current_model()
                logger.debug(f"Switched to model: {model}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to switch model: {e}")
            return False
