"""Chat tool for handling message generation and conversation history"""

import logging
from typing import Dict, Any, Optional, List
import openai
from tools.model_tool import ModelTool

logger = logging.getLogger(__name__)


class ChatTool:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatTool, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self.model_tool = ModelTool()
            self.conversation_history = []
            logger.debug("ChatTool initialized")

    def generate_response(
        self, prompt: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using current model"""
        try:
            logger.debug(f"[CHAT] Generating response for prompt: {prompt}")

            model_name = self.model_tool.get_model_for_task("chat")
            model_config = self.model_tool.get_model_config(
                model_name, tool_name="chat_tool"
            )
            logger.debug(f"[CHAT] Using model: {model_name}")

            messages = self._build_messages(prompt, context)
            logger.debug(f"[CHAT] Built messages: {messages}")

            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=model_config["name"],
                messages=messages,
                temperature=model_config["temperature"],
                max_tokens=model_config["max_tokens"],
            )
            logger.debug(f"[CHAT] Got OpenAI response: {response}")

            raw_response = response.choices[0].message.content
            formatted_response = self._format_response(raw_response)
            logger.debug(f"[CHAT] Formatted response: {formatted_response}")

            self._update_history(prompt, raw_response)

            return {
                "response": formatted_response,
                "model_used": model_name,
                "token_usage": {
                    "input_tokens": len(prompt),
                    "output_tokens": len(raw_response),
                },
            }
        except Exception as e:
            logger.error(f"[CHAT] Error generating response: {e}", exc_info=True)
            return {"error": str(e)}

    def _format_response(self, text: str) -> str:
        """Format response text to HTML"""
        lines = text.split("\n")
        formatted_lines = []
        has_title = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Tarkista onko otsikko
            if line.lower().startswith("title:") or (
                not formatted_lines and ":" in line
            ):
                title = line.replace("Title:", "").strip()
                formatted_lines.append(f"<h3>{title}</h3>")
                has_title = True
                continue

            # Käsittele lihavoinnit vain jos on otsikko
            if has_title:
                line = line.replace("**", "<b>", 1)
                while "**" in line:
                    line = line.replace("**", "</b>", 1)

            # Bulletpoint
            if line.startswith("- "):
                formatted_lines.append(f"• {line[2:]}")

            # Numeroitu kohta
            elif line[0].isdigit() and ". " in line[:4]:
                formatted_lines.append(line)

            # Tavallinen teksti
            else:
                formatted_lines.append(line)

        return "<br>".join(formatted_lines)

    def _update_history(self, prompt: str, response: str) -> None:
        """Update conversation history"""
        message_id = (
            len(self.conversation_history) // 2
        )  # Generate unique ID for message pair
        self.conversation_history.append(
            {"role": "user", "content": prompt, "message_id": message_id}
        )
        self.conversation_history.append(
            {"role": "assistant", "content": response, "message_id": message_id}
        )

        # Rajoita historian kokoa
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    def delete_message(self, message_id: int) -> bool:
        """Delete specific message pair from history

        Args:
            message_id: ID of the message pair to delete

        Returns:
            bool: True if message was deleted, False if not found
        """
        try:
            # Find and remove both user and assistant messages with matching ID
            self.conversation_history = [
                msg
                for msg in self.conversation_history
                if msg.get("message_id") != message_id
            ]
            return True
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")
            return False

    def clear_history(self) -> bool:
        """Clear conversation history

        Returns:
            bool: True if history was cleared successfully
        """
        try:
            self.conversation_history = []
            return True
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return False

    def _build_messages(
        self, prompt: str, context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build message list for API call"""
        messages = []

        # Lisää järjestelmäprompt
        messages.append(
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Maintain context of the conversation.",
            }
        )

        # Lisää konteksti jos on
        if context:
            messages.append({"role": "system", "content": context})

        # Lisää keskusteluhistoria
        messages.extend(self.conversation_history)

        # Lisää uusi viesti
        messages.append({"role": "user", "content": prompt})

        return messages
