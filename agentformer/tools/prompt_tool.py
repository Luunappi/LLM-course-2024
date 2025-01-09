"""Prompt management tool"""

from typing import Dict, Optional


class PromptTool:
    def __init__(self):
        self._prompts = {
            "system": {
                "default": "You are a helpful AI assistant...",
                "rag": "You are an AI assistant with access to specific documents...",
                "diagram": "You are an AI assistant specialized in creating diagrams...",
            },
            "tool": {
                "default": "Analyze the following request and choose appropriate tools...",
                "rag": "Search through the provided documents to find relevant information...",
                "diagram": "Create a diagram based on the following specifications...",
            },
            "custom": {},  # User defined prompts
        }
        self._active_prompts = {"system": "default", "tool": "default"}

    def get_prompt(self, prompt_type: str) -> str:
        """Get currently active prompt for given type"""
        active = self._active_prompts.get(prompt_type)
        if active:
            return self._prompts[prompt_type].get(
                active, self._prompts[prompt_type]["default"]
            )
        return ""

    def set_prompt(
        self, prompt_type: str, content: str, name: Optional[str] = "custom"
    ) -> bool:
        """Set new prompt content"""
        try:
            if name == "custom":
                self._prompts["custom"][prompt_type] = content
                self._active_prompts[prompt_type] = "custom"
            else:
                self._prompts[prompt_type][name] = content
                self._active_prompts[prompt_type] = name
            return True
        except Exception:
            return False

    def list_prompts(self) -> Dict[str, Dict[str, str]]:
        """Get all available prompts"""
        return self._prompts

    def get_active_prompts(self) -> Dict[str, str]:
        """Get currently active prompts"""
        return {
            prompt_type: self.get_prompt(prompt_type)
            for prompt_type in self._active_prompts
        }
