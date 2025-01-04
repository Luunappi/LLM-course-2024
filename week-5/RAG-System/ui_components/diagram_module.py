"""
Diagram Module

Handles visualization requests from chat and generates appropriate diagrams.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re


def is_visualization_request(query: str) -> bool:
    """Check if the query is requesting a visualization"""
    viz_keywords = [
        r"näytä\s+(?:kuvaaja|diagrammi|kaavio|visualisointi)",
        r"piirrä\s+(?:kuvaaja|diagrammi|kaavio)",
        r"visualisoi",
        r"show\s+(?:chart|diagram|graph|visualization)",
        r"plot\s+(?:chart|diagram|graph)",
        r"visualize",
        r"draw\s+(?:chart|diagram|graph)",
    ]
    pattern = "|".join(viz_keywords)
    return bool(re.search(pattern, query.lower()))


def create_visualization(query: str, data: dict = None) -> go.Figure:
    """Create appropriate visualization based on the query"""
    # Esimerkki yksinkertaisesta lämpötiladatasta
    if "lämpötil" in query.lower() or "temperature" in query.lower():
        # Dummy data for demonstration
        df = pd.DataFrame(
            {
                "Year": ["2010", "2011", "2012", "2013", "2014", "2015"],
                "Temperature": [-8.5, -6.2, -7.8, -5.9, -4.2, -3.8],
            }
        )

        fig = px.line(
            df,
            x="Year",
            y="Temperature",
            title="Tammikuun keskilämpötilat Suomessa",
            labels={"Temperature": "Lämpötila (°C)", "Year": "Vuosi"},
        )
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(17, 19, 23, 0.8)",
            paper_bgcolor="rgba(17, 19, 23, 0.8)",
        )
        return fig

    return None


def render_diagram(query: str):
    """Render diagram based on chat query"""
    if is_visualization_request(query):
        fig = create_visualization(query)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            return True
    return False
