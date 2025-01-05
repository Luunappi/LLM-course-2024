"""Message bus and event types for AgentFormer"""

from enum import Enum
from typing import Any, Callable, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    CHAT_MESSAGE = "chat"
    RAG_QUERY = "rag"
    ERROR = "error"


class Message:
    def __init__(self, type: EventType, data: Dict[str, Any]):
        self.type = type
        self.data = data


class MessageBus:
    def __init__(self, orchestrator=None):
        self.handlers = {}
        self.orchestrator = orchestrator
        logger.debug("Initialized MessageBus")

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe handler to event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type}")

    def publish(self, event_type: str, data: dict) -> Any:
        """Publish event to message bus"""
        # Korjaa Message-luokan alustus
        if isinstance(event_type, str):
            if event_type == "chat":
                event_type = EventType.CHAT_MESSAGE
            elif event_type == "rag":
                event_type = EventType.RAG_QUERY
            elif event_type == "error":
                event_type = EventType.ERROR

        message = Message(type=event_type, data=data)  # Korjattu parametrin nimi

        # Tarkista sekä string että enum-muodossa
        if event_type not in self.handlers and (
            isinstance(event_type, EventType) and event_type.value not in self.handlers
        ):
            logger.warning(f"No handlers for {event_type}")
            return ""

        handlers = self.handlers.get(event_type) or self.handlers.get(
            event_type.value, []
        )
        for handler in handlers:
            try:
                result = handler(message)
                if result is not None:
                    return result
            except Exception as e:
                logger.error(f"Handler error: {e}")

        return ""
