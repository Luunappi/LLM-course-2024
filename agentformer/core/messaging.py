"""Message bus for AgentFormer"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Callable


class EventType(Enum):
    CHAT_MESSAGE = "chat"
    RAG_QUERY = "rag"
    ERROR = "error"


@dataclass
class Message:
    type: EventType
    data: Dict[str, Any]


class MessageBus:
    def __init__(self, orchestrator=None):
        self.handlers = {}
        self.orchestrator = orchestrator

    def subscribe(self, event_type: EventType, handler: Callable):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def publish(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        event = EventType(event_type)
        message = Message(type=event, data=data)

        if event in self.handlers:
            for handler in self.handlers[event]:
                return handler(message)
        return {"error": f"No handler for event type: {event}"}
