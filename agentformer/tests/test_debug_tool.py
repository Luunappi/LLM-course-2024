import pytest
from agentformer.tools.debug_tool import DebugTool


def test_debug_tool_singleton():
    tool1 = DebugTool()
    tool2 = DebugTool()
    assert tool1 is tool2


def test_add_event():
    tool = DebugTool()
    tool.clear_events()
    tool.add_event("INFO", "test", "test message")
    info = tool.get_debug_info()
    assert len(info["events"]) == 1
    assert info["events"][0]["level"] == "INFO"
