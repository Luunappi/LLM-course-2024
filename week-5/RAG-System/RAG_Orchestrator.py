"""
RAG Orchestrator

Core component that coordinates tool selection and usage. Acts as the brain of the system by:
1. Analyzing queries using a fixed GPT-4-Turbo model for consistent tool selection
2. Determining which tools are needed for each query
3. Coordinating tool execution and combining results

Tool selection is centralized here to ensure consistent decision making across the system.
Individual tools focus only on their specific tasks, not on deciding when they should be used.
"""

import streamlit as st
import json
from openai import OpenAI
import os
from tools.diagram_tool import DiagramTool
from tools.rag_tool import RAGTool
from tools.llm_tool import LLMTool

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Fixed model for all tool selection decisions to ensure consistency
TOOL_EVALUATOR_MODEL = "gpt-4-turbo-preview"


class RAGOrchestrator:
    """Coordinates tool selection and execution"""

    # Tool selection prompt as class variable for access from prompt module
    TOOL_SELECTION_PROMPT = """Analyze what tools are needed to answer this query.
    Available tools:
    - visualization: For creating charts, graphs and visual data presentations
    - rag: For finding and extracting information from loaded documents
    - llm: For direct language model responses and general knowledge
    
    Guidelines:
    1. Only suggest RAG if documents are explicitly mentioned or referenced
    2. For numerical data or trends, prefer visualization
    3. If the request is unclear, return "needs_clarification": true and "clarification_question"
    4. For data presentation requests, ask for preference if not specified
    
    Return format: {
        "tools": ["tool1", "tool2"],
        "reason": "explanation",
        "visualization_type": "line/bar/scatter", # if visualization in tools
        "needs_clarification": false,
        "clarification_question": null # e.g. "Would you prefer to see the data as a visualization or as text?"
    }
    """

    def __init__(self):
        # Available tools - each tool handles a specific type of task
        self.tools = {
            "visualization": DiagramTool(),  # For charts and graphs
            "rag": RAGTool(),  # For document-based answers
            "llm": LLMTool(),  # For direct LLM responses
        }

    def analyze_query(self, query: str) -> dict:
        """
        Analyze query to determine required tools.
        Uses a fixed model (TOOL_EVALUATOR_MODEL) for consistent evaluation.
        """
        try:
            response = client.chat.completions.create(
                model=TOOL_EVALUATOR_MODEL,
                messages=[
                    {"role": "system", "content": self.TOOL_SELECTION_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            st.session_state["system_warnings"].append(
                f"Query analysis error: {str(e)}"
            )
            return {"tools": ["llm"], "reason": "Fallback to basic LLM due to error"}

    def process_query(self, query: str) -> dict:
        """
        Process query using appropriate tools and combine results.
        Returns a single dict containing all results.
        """
        # Get and store analysis
        analysis = self.analyze_query(query)
        st.session_state["last_tool_analysis"] = {
            "query": query,
            "tools": analysis.get("tools", []),
            "reason": analysis.get("reason", "No reason provided"),
            "visualization_type": analysis.get("visualization_type", None),
        }

        results = []

        # Process with each required tool
        for tool_name in analysis["tools"]:
            tool = self.tools[tool_name]
            try:
                if tool_name == "visualization":
                    result = tool.process(query, analysis.get("visualization_type"))
                    if result:
                        # Add visualization result
                        results.append(result)
                        # Also create text explanation
                        results.append({"type": "text", "content": result["message"]})
                else:
                    result = tool.process(query)
                    if result:
                        results.append(result)
            except Exception as e:
                st.session_state["system_warnings"].append(
                    f"Error with {tool_name}: {str(e)}"
                )

        # Combine and return results
        return self.combine_results(results)

    def combine_results(self, results: list) -> dict:
        """
        Combine results from different tools into a single response.
        Ensures visualizations are properly included.
        """
        combined = {"text": "", "visualizations": [], "data": {}}

        for result in results:
            if result["type"] == "visualization":
                combined["visualizations"].append(
                    {"figure": result["content"], "summary": result["message"]}
                )
            elif result["type"] == "text":
                if combined["text"]:
                    combined["text"] += "\n\n"
                combined["text"] += result["content"]
            elif result["type"] == "data":
                combined["data"].update(result["content"])

        return combined
