"""
Diagram Tool

Handles visualization creation and data presentation. This tool:
1. Creates visualizations based on query and specified type
2. Generates data for visualizations using selected model
3. Provides summaries of visualizations

Note: Tool selection is handled by the RAGOrchestrator, not this tool.
This tool focuses solely on creating visualizations when requested.
"""

import streamlit as st
import json
from openai import OpenAI
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
from ui_components.model_module import Models

# Fixed model for visualization need evaluation
VISUALIZATION_EVALUATOR_MODEL = "gpt-4-turbo-preview"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class DiagramTool:
    """Creates and manages data visualizations"""

    def process(self, query: str, viz_type: str = None) -> dict:
        """
        Process visualization request.
        Visualization type is determined by the orchestrator, not this tool.
        """
        if not viz_type:
            return None

        fig = self.create_visualization(query, viz_type)
        if fig:
            summary = self.generate_summary(query, viz_type)
            return {
                "type": "visualization",
                "content": fig,
                "message": summary,
            }
        return None

    def create_visualization(self, query: str, viz_type: str) -> go.Figure:
        """Create appropriate visualization based on query and type"""
        try:
            # Get data from LLM using selected model
            model_name = st.session_state.get(
                "current_model", Models.get_default_model()
            )
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """Extract or generate relevant data for visualization.
                        For temperature data, use realistic values.
                        Return format: {
                            "data": {
                                "x": ["2010", "2011", "2012", "2013", "2014", "2015"],
                                "y": [-8.2, -7.5, -9.1, -6.8, -7.9, -8.3]
                            },
                            "title": "Tammikuun keskilämpötilat Suomessa 2010-2015",
                            "labels": {
                                "x": "Vuosi",
                                "y": "Lämpötila (°C)"
                            }
                        }
                        """,
                    },
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
            )
            data_spec = json.loads(response.choices[0].message.content)

            # Create DataFrame
            df = pd.DataFrame(data_spec["data"])

            # Create visualization based on type
            if viz_type == "line":
                fig = px.line(
                    df,
                    x=df.columns[0],
                    y=df.columns[1],
                    title=data_spec["title"],
                    labels=data_spec["labels"],
                )
            elif viz_type == "bar":
                fig = px.bar(
                    df,
                    x=df.columns[0],
                    y=df.columns[1],
                    title=data_spec["title"],
                    labels=data_spec["labels"],
                )
            else:
                fig = px.scatter(
                    df,
                    x=df.columns[0],
                    y=df.columns[1],
                    title=data_spec["title"],
                    labels=data_spec["labels"],
                )

            # Apply dark theme
            fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(17, 19, 23, 0.8)",
                paper_bgcolor="rgba(17, 19, 23, 0.8)",
            )

            return fig

        except Exception as e:
            st.session_state["system_warnings"].append(
                f"Visualization creation error: {str(e)}"
            )
            return None

    def generate_summary(self, query: str, viz_type: str) -> str:
        """Generate a summary of the visualization"""
        try:
            model_name = st.session_state.get(
                "current_model", Models.get_default_model()
            )
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """Generate a brief summary of the visualization.
                        Focus on key trends, patterns, and insights.
                        Keep it concise (2-3 sentences).
                        """,
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\nVisualization type: {viz_type}",
                    },
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return "Generated visualization based on request"
