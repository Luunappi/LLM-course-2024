"""
Web Interface Tests

Testaa web-käyttöliittymän:
- HTTP endpointit
- Viestien käsittely
- Tilanhallinnan
- Virhetilanteet
"""

import pytest
from flask.testing import FlaskClient
from agentformer_web import app


@pytest.fixture
def client() -> FlaskClient:
    """Create test client"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """Test main page load"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"chat.html" in response.data


def test_chat_endpoint(client):
    """Test chat message handling"""
    # Testaa tyhjä viesti
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 400
    assert b"Empty message" in response.data

    # Testaa normaali viesti
    response = client.post("/chat", json={"message": "Testikysymys"})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert "response" in data
    assert isinstance(data["response"], str)
    assert "state" in data
    assert isinstance(data["state"], dict)


def test_state_endpoint(client):
    """Test state retrieval"""
    response = client.get("/state")
    assert response.status_code == 200
    data = response.get_json()

    # Tarkista tilan rakenne
    assert "memory_state" in data
    assert "active_tools" in data
    assert "current_model" in data


def test_error_handling(client):
    """Test error handling"""
    # Testaa virheellinen JSON
    response = client.post(
        "/chat", data="invalid json", content_type="application/json"
    )
    assert response.status_code == 400

    # Testaa puuttuva viesti
    response = client.post("/chat", json={})
    assert response.status_code == 400


def test_chat_integration(client):
    """Test chat integration with orchestrator"""
    response = client.post("/chat", json={"message": "Testikysymys"})
    assert response.status_code == 200
    data = response.get_json()

    # Tarkista vastauksen rakenne
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0  # Tarkista vain että vastaus ei ole tyhjä

    # Tarkista tilan päivitys
    assert "state" in data
    assert isinstance(data["state"], dict)


@pytest.mark.skip(reason="Rinnakkaisuustestit vaativat erillisen konfiguraation")
def test_concurrent_requests(client):
    """Test handling multiple requests"""
    # Ohitetaan testi toistaiseksi
    pass
