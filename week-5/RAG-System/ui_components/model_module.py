"""
Model Module

Manages model selection and configuration.
Provides model-specific information and settings.
"""

import streamlit as st
from enum import Enum
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Model configuration"""

    name: str
    input_cost: float
    output_cost: float
    max_tokens: int
    description: str


class Models:
    """Available models and their configurations"""

    CONFIGS = {
        "gpt-4o-mini": ModelConfig(
            name="gpt-4o-mini",
            input_cost=0.15,
            output_cost=0.60,
            max_tokens=2000,
            description="Kevyt yleiskäyttöinen malli",
        ),
        "o1-mini": ModelConfig(
            name="o1-mini",
            input_cost=3.0,
            output_cost=12.0,
            max_tokens=1000,
            description="Tarkka malli faktantarkistukseen",
        ),
        "o1": ModelConfig(
            name="o1",
            input_cost=15.0,
            output_cost=15.0,
            max_tokens=4000,
            description="Tehokas malli monimutkaiseen analyysiin",
        ),
    }

    @staticmethod
    def get_default_model() -> str:
        """Get default model name"""
        return "gpt-4o-mini"

    @staticmethod
    def get_model_config(model_name: str) -> ModelConfig:
        """Get model configuration"""
        return Models.CONFIGS.get(model_name)


def render_model_selector():
    """Render model selection in sidebar"""
    with st.expander("Model Selection", expanded=False):
        # Initialize model in session state if not exists
        if "current_model" not in st.session_state:
            st.session_state["current_model"] = Models.get_default_model()

        # Model selection
        selected_model = st.selectbox(
            "Select Model:",
            options=list(Models.CONFIGS.keys()),
            index=list(Models.CONFIGS.keys()).index(st.session_state["current_model"]),
            format_func=lambda x: f"{x} ({Models.CONFIGS[x].description})",
        )

        # Show token details
        model_config = Models.get_model_config(selected_model)
        st.write("#### Token Info:")
        st.write(f"- Max tokens: {model_config.max_tokens:,}")
        st.write(f"- Input cost: ${model_config.input_cost}/1M tokens")
        st.write(f"- Output cost: ${model_config.output_cost}/1M tokens")

        # Update current model if changed
        if selected_model != st.session_state["current_model"]:
            st.session_state["current_model"] = selected_model
            st.success(f"Model changed to {selected_model}")
