"""
Tool for creating diagrams and visualizations
"""

from typing import Dict, Any


class DiagramTool:
    def __init__(self):
        self.capabilities = ["create_diagram", "update_diagram"]
        self.current_diagram = None

    def handle_capability(self, message):
        """Handle incoming capability requests"""
        if message.data.get("type") == "create_diagram":
            return self.create_example_diagram(message.data)
        return "Unknown diagram operation"

    def create_example_diagram(self, data: Dict[str, Any]) -> str:
        """Create a simple example diagram"""
        # Tässä vaiheessa vain placeholder
        self.current_diagram = """
        +-------------+
        |   Example   |
        |   Diagram   |
        +-------------+
        """
        return self.current_diagram
