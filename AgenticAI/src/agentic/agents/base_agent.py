"""Base agent class that all agents inherit from"""

from typing import Dict, Any, Optional, Callable
from ..core.events import Event


class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.event_handlers: Dict[str, Callable] = {}

    async def initialize(self) -> None:
        """Initialize agent"""
        pass

    async def shutdown(self) -> None:
        """Shutdown agent"""
        pass

    async def handle_event(self, event: Event) -> Optional[Dict[str, Any]]:
        """Handle incoming event"""
        handler = self.event_handlers.get(event.type)
        if handler:
            return await handler(event)
        return None

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register event handler"""
        self.event_handlers[event_type] = handler
