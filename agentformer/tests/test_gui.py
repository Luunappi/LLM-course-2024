import pytest
from agentformer_web import app
from bs4 import BeautifulSoup


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """Test that index page loads with all required elements"""
    rv = client.get("/")
    assert rv.status_code == 200

    soup = BeautifulSoup(rv.data, "html.parser")

    # Test that all required elements exist
    assert soup.find("img", {"class": "hy-logo"}) is not None
    assert soup.find("div", {"id": "chat-messages"}) is not None
    assert soup.find("input", {"id": "message-input"}) is not None
    assert soup.find("button", {"id": "send-button"}) is not None

    # Test that all tool buttons exist
    buttons = soup.find_all("button", {"class": "btn"})
    icons = ["bi-upload", "bi-globe", "bi-mic", "bi-send"]
    found_icons = [
        any(button.find("i", {"class": icon}) is not None for button in buttons)
        for icon in icons
    ]
    assert all(found_icons)


def test_chat_endpoint(client):
    """Test chat endpoint functionality"""
    test_message = "Hello, test message"
    rv = client.post(
        "/chat", json={"message": test_message}, content_type="application/json"
    )

    assert rv.status_code == 200
    json_data = rv.get_json()
    assert "response" in json_data
    assert "state" in json_data


def test_empty_message(client):
    """Test handling of empty messages"""
    rv = client.post("/chat", json={"message": ""}, content_type="application/json")

    assert rv.status_code == 400
    json_data = rv.get_json()
    assert "error" in json_data


def test_invalid_json(client):
    """Test handling of invalid JSON"""
    rv = client.post("/chat", data="not json", content_type="application/json")

    assert rv.status_code == 400
    json_data = rv.get_json()
    assert "error" in json_data


@pytest.mark.parametrize(
    "viewport_size",
    [
        (320, 568),  # iPhone SE
        (768, 1024),  # iPad
        (1920, 1080),  # Desktop
    ],
)
def test_responsive_layout(client, viewport_size):
    """Test responsive layout at different viewport sizes"""
    width, height = viewport_size

    # Tämä testi vaatii Selenium/Playwright-tyyppisen työkalun
    # tässä vain esimerkki miten voisi testata
    pass
