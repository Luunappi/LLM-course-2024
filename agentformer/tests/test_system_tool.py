import pytest
from tools.system_tool import SystemTool
from time import sleep


def test_system_tool_singleton():
    tool1 = SystemTool()
    tool2 = SystemTool()
    assert tool1 is tool2


def test_timing_steps():
    tool = SystemTool()
    tool.start_timing()

    tool.add_step("Step 1", 1.5)
    tool.add_step("Step 2", 2.0)
    tool.set_model("test-model")

    stats = tool.get_timing_stats()
    assert len(stats["steps"]) == 2
    assert stats["model_used"] == "test-model"
    assert stats["steps"][0]["step"] == "Step 1"
