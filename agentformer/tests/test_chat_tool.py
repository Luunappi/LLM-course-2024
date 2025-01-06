import pytest
from tools.chat_tool import ChatTool


def test_chat_tool_singleton():
    tool1 = ChatTool()
    tool2 = ChatTool()
    assert tool1 is tool2


def test_generate_response():
    chat_tool = ChatTool()
    response = chat_tool.generate_response("Test message")
    assert "response" in response
    assert "model_used" in response
    assert "token_usage" in response


def test_conversation_history():
    chat_tool = ChatTool()
    chat_tool.clear_history()

    response1 = chat_tool.generate_response("First message")
    response2 = chat_tool.generate_response("Second message")

    assert len(chat_tool.conversation_history) == 4  # 2 viestiparia
