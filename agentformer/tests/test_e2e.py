from playwright.sync_api import Page, expect


def test_chat_interaction(page: Page):
    # Avaa sivu
    page.goto("http://localhost:5001")

    # Kirjoita viesti
    page.fill("#message-input", "Test message")

    # Lähetä viesti
    page.click("#send-button")

    # Tarkista että viesti näkyy
    expect(page.locator(".user-message")).to_contain_text("Test message")

    # Odota vastausta
    expect(page.locator(".bot-message")).to_be_visible()
