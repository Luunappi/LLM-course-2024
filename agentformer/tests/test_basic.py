"""Basic functionality tests"""

import pytest
from core.orchestrator import AgentFormerOrchestrator
from ui_components.model_module import Models


def test_model_config(models):
    """Test model configuration"""
    current = models.get_current_model()
    assert current["name"] == "gpt-4o-mini"
    assert current["type"] == "chat"
    assert current["context_length"] == 8192
    assert current["temperature"] == 0.7
    assert current["max_tokens"] == 500


def test_memory_state():
    """Test memory state initialization"""
    orchestrator = AgentFormerOrchestrator()
    state = orchestrator.get_memory_state()

    assert state is not None
    assert "status" in state

    # Tarkista että tila on joko aktiivinen tai ei-alustettu
    if state["status"] == "active":
        assert "state" in state
        memory_state = state["state"]
        # Tarkista muistin rakenne
        assert all(
            k in memory_state for k in ["core", "semantic", "episodic", "working"]
        )
    else:
        # Jos ei alustettu tai virhe, tarkista viesti
        assert "message" in state or state["status"] == "not_initialized"
