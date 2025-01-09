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
        """Format response text to HTML with improved markdown support"""
        lines = text.split("\n")
        formatted_lines = []
        in_list = False
        in_code_block = False

        for line in lines:
            line = line.strip()
            if not line:
                if in_list:
                    formatted_lines.append("</ul>")
                    in_list = False
                formatted_lines.append("<br>")
                continue

            # Code blocks
            if line.startswith("```"):
                if in_code_block:
                    formatted_lines.append("</code></pre>")
                    in_code_block = False
                else:
                    language = line[3:].strip()
                    formatted_lines.append(f'<pre><code class="language-{language}">')
                    in_code_block = True
                continue

            if in_code_block:
                formatted_lines.append(line)
                continue

            # Headers
            if line.startswith("#"):
                level = len(line.split()[0])  # Count #'s
                title = line[level:].strip()
                formatted_lines.append(f"<h{level}>{title}</h{level}>")
                continue

            # Lists
            if line.startswith("- ") or line.startswith("* "):
                if not in_list:
                    formatted_lines.append("<ul>")
                    in_list = True
                formatted_lines.append(f"<li>{line[2:]}</li>")
                continue
            elif line[0].isdigit() and ". " in line[:4]:
                num, content = line.split(". ", 1)
                formatted_lines.append(
                    f"<div class='numbered-item'>{num}. {content}</div>"
                )
                continue
            elif in_list:
                formatted_lines.append("</ul>")
                in_list = False

            # Inline formatting
            line = line.replace("**", "<strong>", 1)
            while "**" in line:
                line = line.replace("**", "</strong>", 1)

            line = line.replace("*", "<em>", 1)
            while "*" in line:
                line = line.replace("*", "</em>", 1)

            line = line.replace("`", "<code>", 1)
            while "`" in line:
                line = line.replace("`", "</code>", 1)

            # Links
            while "[" in line and "](" in line and ")" in line:
                start = line.find("[")
                mid = line.find("](")
                end = line.find(")", mid)
                if start != -1 and mid != -1 and end != -1:
                    text = line[start + 1 : mid]
                    url = line[mid + 2 : end]
                    line = (
                        line[:start] + f'<a href="{url}">{text}</a>' + line[end + 1 :]
                    )
                else:
                    break

            formatted_lines.append(f"<p>{line}</p>")

        if in_list:
            formatted_lines.append("</ul>")

        return "\n".join(formatted_lines)

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
