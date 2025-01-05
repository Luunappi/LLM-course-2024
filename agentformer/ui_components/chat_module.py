"""
Chat module for Flask UI
"""

from flask import render_template
from core.messaging import EventType, Message
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def render_chat_module(message_bus):
    """Render chat interface"""
    return render_template(
        "chat.html",
        model_name="gpt-4o-mini",  # Käytetään oletusmallia
    )


def handle_chat_message(message_bus, message: str) -> str:
    """Handle incoming chat message"""
    try:
        logger.debug(f"Processing chat message: {message}")

        # Julkaistaan viesti ja odotetaan vastausta
        response = message_bus.handle_message(
            Message(EventType.CHAT_MESSAGE, {"message": message})
        )

        # Varmistetaan että vastaus on oikeassa muodossa
        if response:
            logger.debug(f"Got response: {response}")
            return response  # Palautetaan suoraan tekstivastaus
        else:
            return "No response available"

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return f"Error: {str(e)}"
