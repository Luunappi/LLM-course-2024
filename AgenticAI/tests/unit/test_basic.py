"""Basic unit tests for core functionality"""

import pytest
from agentic.core.events import Event, EventBus
from agentic.core.orchestrator import Orchestrator
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.unit
def test_event_creation():
    """Test Event object creation"""
    event = Event("test", {"key": "value"}, "test_source")
    assert event.type == "test"
    assert event.data == {"key": "value"}
    assert event.source == "test_source"
    assert event.timestamp is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus():
    """Test EventBus functionality"""
    bus = EventBus()
    received = []

    async def handler(event):
        received.append(event)

    # Subscribe and publish
    bus.subscribe("test", handler)
    event = Event("test", {"data": "test"})
    await bus.publish(event)

    assert len(received) == 1
    assert received[0].type == "test"
    assert received[0].data == {"data": "test"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrator():
    """Test Orchestrator functionality"""
    orchestrator = Orchestrator()

    # Mock agent
    mock_agent = MagicMock()
    mock_agent.initialize = AsyncMock()
    mock_agent.handle_event = AsyncMock()

    # Register agent
    orchestrator.register_agent("test_agent", mock_agent)

    # Initialize
    await orchestrator.initialize()
    mock_agent.initialize.assert_called_once()

    # Handle request
    await orchestrator.handle_request("test", {"data": "test"})
    assert len(orchestrator.event_bus.history) == 1
