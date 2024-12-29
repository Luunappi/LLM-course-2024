import pytest
from agentic.core.events import Event, EventBus


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.mark.asyncio
async def test_event_creation():
    """Test event creation and properties"""
    event = Event("test", {"key": "value"}, "test_source")
    assert event.type == "test"
    assert event.data == {"key": "value"}
    assert event.source == "test_source"
    assert event.timestamp is not None


@pytest.mark.asyncio
async def test_event_subscription(event_bus):
    """Test event subscription and publishing"""
    received_events = []

    async def handler(event):
        received_events.append(event)

    # Subscribe to event
    event_bus.subscribe("test_event", handler)

    # Publish event
    test_event = Event("test_event", {"data": "test"})
    await event_bus.publish(test_event)

    assert len(received_events) == 1
    assert received_events[0].type == "test_event"
    assert received_events[0].data == {"data": "test"}


@pytest.mark.asyncio
async def test_multiple_subscribers(event_bus):
    """Test multiple subscribers for same event"""
    results = []

    async def handler1(event):
        results.append("handler1")

    async def handler2(event):
        results.append("handler2")

    event_bus.subscribe("test", handler1)
    event_bus.subscribe("test", handler2)

    await event_bus.publish(Event("test", {}))

    assert len(results) == 2
    assert "handler1" in results
    assert "handler2" in results


@pytest.mark.asyncio
async def test_unsubscribe(event_bus):
    """Test unsubscribing from events"""
    received = []

    async def handler(event):
        received.append(event)

    event_bus.subscribe("test", handler)
    event_bus.unsubscribe("test", handler)

    await event_bus.publish(Event("test", {}))

    assert len(received) == 0
