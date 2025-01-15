"""Message bus implementation using Singleton pattern.

This module provides a centralized message bus for system-wide event handling:
1. Singleton pattern ensures single message bus instance
2. Publisher/Subscriber pattern for event handling
3. Type-safe event definitions
4. Automatic event logging
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Callable, Optional, ForwardRef
from time import time

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for system-wide messaging."""

    # General events
    CHAT_MESSAGE = "chat"
    ERROR = "error"
    SYSTEM_INFO = "system_info"

    # Indexing events
    INDEXING_STARTED = "indexing_started"
    INDEXING_PROGRESS = "indexing_progress"
    INDEXING_COMPLETE = "indexing_complete"
    INDEXING_ERROR = "indexing_error"

    # Document events
    FILE_ADDED = "file_added"
    FILE_REMOVED = "file_removed"
    FILE_UPDATED = "file_updated"

    # RAG events
    RAG_QUERY_STARTED = "rag_query_started"
    RAG_QUERY_COMPLETE = "rag_query_complete"
    RAG_QUERY_ERROR = "rag_query_error"


@dataclass
class Message:
    """Message structure for event bus."""

    type: EventType
    data: Dict[str, Any]
    timestamp: float = None
    error: Optional[str] = None

    def __post_init__(self):
        self.timestamp = self.timestamp or time()


class MessageBus:
    """Message bus using Singleton pattern.

    This class implements a centralized message bus that:
    1. Ensures single instance using Singleton pattern
    2. Provides type-safe event publishing and subscription
    3. Handles automatic event logging
    4. Manages subscriber callbacks safely
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.subscribers = {}
        self._initialized = True
        logger.info("MessageBus initialized")

    def subscribe(self, event: EventType, callback: Callable) -> bool:
        """Subscribe to an event.

        Args:
            event: Event type to subscribe to
            callback: Function to call when event occurs

        Returns:
            bool: True if subscription succeeded

        Raises:
            ValueError: If event type is invalid
        """
        if not isinstance(event, EventType):
            raise ValueError(f"Invalid event type: {event}")

        if event not in self.subscribers:
            self.subscribers[event] = []
        self.subscribers[event].append(callback)
        logger.debug(f"Subscribed to {event.name}: {callback.__name__}")
        return True

    def publish(self, event: EventType, data: Dict[str, Any]) -> None:
        """Publish an event.

        Args:
            event: Event type to publish
            data: Event data to pass to subscribers

        Raises:
            ValueError: If event type is invalid
        """
        if not isinstance(event, EventType):
            raise ValueError(f"Invalid event type: {event}")

        logger.debug(f"Publishing {event.name} with data: {data}")
        if event in self.subscribers:
            for callback in self.subscribers[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in subscriber {callback.__name__}: {str(e)}")
