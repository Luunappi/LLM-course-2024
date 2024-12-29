import pytest
from unittest.mock import MagicMock, AsyncMock
from agentic.core.orchestrator import Orchestrator
from agentic.agents.base_agent import BaseAgent


@pytest.fixture
async def orchestrator():
    return Orchestrator()


@pytest.fixture
def mock_agent():
    agent = MagicMock(spec=BaseAgent)
    agent.initialize = AsyncMock()
    agent.shutdown = AsyncMock()
    agent.handle_event = AsyncMock()
    return agent


@pytest.mark.asyncio
async def test_agent_registration(orchestrator, mock_agent):
    """Test agent registration"""
    orchestrator.register_agent("test_agent", mock_agent)
    assert "test_agent" in orchestrator.agents
    assert orchestrator.agents["test_agent"] == mock_agent


@pytest.mark.asyncio
async def test_agent_initialization(orchestrator, mock_agent):
    """Test agent initialization"""
    orchestrator.register_agent("test_agent", mock_agent)
    await orchestrator.initialize()
    mock_agent.initialize.assert_called_once()


@pytest.mark.asyncio
async def test_agent_shutdown(orchestrator, mock_agent):
    """Test agent shutdown"""
    orchestrator.register_agent("test_agent", mock_agent)
    await orchestrator.shutdown()
    mock_agent.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_request_handling(orchestrator, mock_agent):
    """Test request handling and event publishing"""
    orchestrator.register_agent("test_agent", mock_agent)

    received_events = []

    async def handle_test_event(event):
        received_events.append(event)
        assert event.type == "test_request"
        assert event.data == {"key": "value"}

    orchestrator.event_bus.subscribe("test_request", handle_test_event)

    # Handle request
    await orchestrator.handle_request("test_request", {"key": "value"})

    # Varmista että event käsiteltiin
    assert len(received_events) == 1
    assert received_events[0].type == "test_request"
    assert received_events[0].data == {"key": "value"}
