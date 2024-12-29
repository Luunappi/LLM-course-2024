"""Event system for agent communication"""

from typing import Dict, List, Callable, Any
from collections import defaultdict
import asyncio


class Event:
    def __init__(self, type: str, data: Dict[str, Any], source: str = None):
        self.type = type
        self.data = data
        self.source = source
        self.timestamp = asyncio.get_event_loop().time()


class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.history = []

    async def publish(self, event: Event) -> None:
        """Publish event to all subscribers"""
        self.history.append(event)
        for handler in self.subscribers[event.type]:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error handling event {event.type}: {e}")

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to event type"""
        self.subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type"""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
