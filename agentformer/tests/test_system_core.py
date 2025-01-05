"""
System Core Tests

Testaa järjestelmän ydinkomponentteja:
- Muistin alustus ja toiminta
- Mallien konfiguraatiot
- Orkestraattorin toiminta
"""

import pytest
from core.orchestrator import AgentFormerOrchestrator
from ui_components.model_module import Models


def test_model_configuration():
    """Test model configurations and defaults"""
    models = Models()

    # Tarkista oletusmallin asetukset
    config = models.get_current_model()
    assert config["name"] == "gpt-4o-mini"
    assert config["temperature"] == 0.7
    assert config["max_tokens"] == 500

    # Älä testaa mallin vaihtoa, koska vain yksi malli käytössä
    assert models.get_available_models()["gpt-4o-mini"] == config


def test_memory_initialization():
    """Test memory system initialization"""
    orchestrator = AgentFormerOrchestrator()
    state = orchestrator.get_memory_state()

    assert state is not None
    assert "status" in state

    if state["status"] == "active":
        assert "state" in state
        memory_state = state["state"]
        assert all(
            k in memory_state for k in ["core", "semantic", "episodic", "working"]
        )
    else:
        assert "message" in state or state["status"] == "not_initialized"


def test_orchestrator_initialization():
    """Test orchestrator initialization and tools"""
    orchestrator = AgentFormerOrchestrator()
    state = orchestrator.get_current_state()

    assert "memory_state" in state
    assert "active_tools" in state
    assert "current_model" in state
    assert "diagram" in state["active_tools"]
