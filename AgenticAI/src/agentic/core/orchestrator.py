"""Orchestrator for coordinating agents"""

from typing import Dict, Any
from .events import EventBus, Event


class Orchestrator:
    def __init__(self):
        self.event_bus = EventBus()
        self.agents = {}

    def register_agent(self, name: str, agent: Any) -> None:
        """Register new agent"""
        self.agents[name] = agent

    async def handle_request(self, request_type: str, data: Dict[str, Any]) -> None:
        """Handle incoming request by publishing event"""
        event = Event(type=request_type, data=data, source="orchestrator")
        await self.event_bus.publish(event)

    async def initialize(self) -> None:
        """Initialize all registered agents"""
        for name, agent in self.agents.items():
            if hasattr(agent, "initialize"):
                await agent.initialize()

    async def shutdown(self) -> None:
        """Shutdown all registered agents"""
        for name, agent in self.agents.items():
            if hasattr(agent, "shutdown"):
                await agent.shutdown()
