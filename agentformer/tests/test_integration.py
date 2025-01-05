"""
Integration Tests

Testaa komponenttien yhteistoimintaa:
- Orkestraattori + Muisti
- Orkestraattori + Mallit
- Muisti + RAG
- Web + Orkestraattori
"""

import pytest
from core.orchestrator import AgentFormerOrchestrator
from memory.memory_manager import MemoryManager
from ui_components.model_module import Models
from tools.rag_tool import RAGTool
from unittest.mock import patch, Mock


@pytest.fixture(autouse=True)
def mock_openai():
    """Mock OpenAI API for all tests"""
    with patch("openai.OpenAI") as mock:
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Helsinki on pääkaupunki"))]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def system():
    """Create full system with all components"""
    orchestrator = AgentFormerOrchestrator()
    return {
        "orchestrator": orchestrator,
        "memory": orchestrator.memory,
        "models": orchestrator.models,
    }


def test_memory_model_integration(system):
    """Test memory and model interaction"""
    # Tallenna muistiin
    system["memory"].store_memory(
        {"content": "Helsinki on Suomen pääkaupunki"}, memory_type="core"
    )

    # Hae konteksti ja generoi vastaus
    memories = system["memory"].retrieve_memories("pääkaupunki")
    context = memories[0]["content"] if memories else None
    response = system["models"].generate_response(
        "Mikä on pääkaupunki?", context=context
    )

    assert "Helsinki" in response
    assert "pääkaupunki" in response


def test_orchestrator_memory_integration(system):
    """Test orchestrator and memory interaction"""
    # Lähetä viesti orkestraattorin kautta
    message = "Muista että Helsinki on pääkaupunki"
    response = system["orchestrator"].process_request("chat", {"message": message})
    assert response is not None

    # Tallenna vastaus muistiin
    system["memory"].store_memory(
        {"content": f"{message} -> {response}"}, memory_type="episodic"
    )

    # Tarkista että tieto tallentui muistiin
    memories = system["memory"].retrieve_memories("Helsinki")
    assert len(memories) > 0
    assert "Helsinki" in str(memories[0]["content"])


def test_rag_memory_integration(system):
    """Test RAG and memory integration"""
    # Lisää dokumentti RAG-työkaluun
    rag_tool = RAGTool()
    document = "Helsinki on Suomen pääkaupunki."
    rag_tool.add_document(document)

    # Tee RAG-haku ja tallenna muistiin
    result = rag_tool.query("Kerro Helsingistä")
    system["memory"].store_memory(
        {"content": document},
        memory_type="core",  # Tallenna alkuperäinen dokumentti
    )
    system["memory"].store_memory({"content": f"RAG: {result}"}, memory_type="episodic")

    # Tarkista muisti
    memories = system["memory"].retrieve_memories("Helsinki")
    assert len(memories) > 0
    assert "Helsinki" in str(memories[0]["content"])


def test_full_conversation_flow(system):
    """Test full conversation flow through system"""
    # Ensimmäinen viesti
    message1 = "Muista että Helsinki on pääkaupunki"
    response1 = system["orchestrator"].process_request("chat", {"message": message1})
    assert response1 is not None

    # Tallenna ensimmäinen viesti muistiin
    system["memory"].store_memory(
        {"content": f"{message1} -> {response1}"}, memory_type="episodic"
    )

    # Toinen viesti hyödyntää muistia
    response2 = system["orchestrator"].process_request(
        "chat", {"message": "Mikä oli se pääkaupunki?"}
    )
    assert "Helsinki" in response2

    # Tarkista muistin tila
    state = system["orchestrator"].get_memory_state()
    assert state["status"] == "active"
    memory_state = state["state"]
    assert "episodic" in memory_state
    assert memory_state["episodic"]["count"] >= 2  # Kaksi viestiä tallennettu


def test_error_recovery(system):
    """Test error handling and recovery"""
    # Aiheuta virhe mallissa
    system["models"].set_model("non_existent_model")

    # Järjestelmän pitäisi palautua virheestä
    response = system["orchestrator"].process_request(
        "chat", {"message": "Testikysymys"}
    )

    assert response is not None
    assert (
        system["models"].get_current_model()["name"] == "gpt-4o-mini"
    )  # Palautunut oletukseen
