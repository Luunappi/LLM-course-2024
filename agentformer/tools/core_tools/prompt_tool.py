"""Prompt Tool - Kehotetyökalu

Tämä työkalu hallinnoi kehotteiden luontia ja optimointia:
1. Luo kehotteet eri tehtäville
2. Optimoi kehotteet mallin mukaan
3. Hallinnoi kehotekontekstia
4. Seuraa kehotteiden tehokkuutta
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PromptTool:
    """Hallinnoi kehotteiden luontia ja optimointia"""

    def __init__(self):
        self.system_prompts = {
            "default": "You are a helpful AI assistant. Answer the question directly using your knowledge.",
            "rag": """You are a helpful AI assistant. Answer based on the provided context. 
            If the context doesn't contain relevant information, say so clearly.""",
            "analysis": """You are an analysis assistant. Analyze the provided data and give clear insights.
            Support your analysis with specific examples from the data.""",
            "code": """You are a coding assistant. Help with programming tasks and explain your solutions clearly.
            Follow best practices and provide comments for complex code.""",
        }

        self.task_templates = {
            "question": "{system_prompt}\n\nQuestion: {query}\n\nAnswer: ",
            "analysis": "{system_prompt}\n\nData to analyze: {data}\n\nAnalysis: ",
            "code": "{system_prompt}\n\nTask: {task}\n\nSolution: ",
        }

    def get_system_prompt(self, task_type: str = "default") -> str:
        """Hae järjestelmäkehote tehtävätyypin mukaan"""
        return self.system_prompts.get(task_type, self.system_prompts["default"])

    def format_prompt(self, task_type: str, **kwargs) -> str:
        """Muotoile kehote annettujen parametrien mukaan"""
        template = self.task_templates.get(task_type, self.task_templates["question"])
        system_prompt = self.get_system_prompt(task_type)
        return template.format(system_prompt=system_prompt, **kwargs)

    def add_system_prompt(self, name: str, prompt: str) -> None:
        """Lisää uusi järjestelmäkehote"""
        self.system_prompts[name] = prompt
        logger.info(f"Added new system prompt: {name}")

    def add_task_template(self, name: str, template: str) -> None:
        """Lisää uusi tehtäväpohja"""
        self.task_templates[name] = template
        logger.info(f"Added new task template: {name}")

    def optimize_prompt(self, prompt: str, model: str) -> str:
        """Optimoi kehote tietylle mallille"""
        # TODO: Implement model-specific prompt optimization
        return prompt

    def get_context_window(self, model: str) -> int:
        """Hae mallin konteksti-ikkunan koko"""
        context_windows = {
            "gpt-4o": 8192,
            "gpt-4o-mini": 4096,
            "o1": 200000,
            "o1-mini": 128000,
        }
        return context_windows.get(model, 4096)

    def truncate_prompt(self, prompt: str, model: str) -> str:
        """Lyhennä kehote mallin konteksti-ikkunaan sopivaksi"""
        max_length = self.get_context_window(model)
        if len(prompt) > max_length:
            return prompt[:max_length]
        return prompt
