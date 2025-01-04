"""
Token Module

Displays token usage information and cost calculations.
Shows model details and usage statistics.
"""

import streamlit as st


def calculate_token_cost(input_tokens, output_tokens, model):
    """Calculate cost based on token usage and model"""
    costs = {
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},  # per 1M tokens
        "o1-mini": {"input": 3.00, "output": 12.00},  # per 1M tokens
        "o1": {"input": 15.00, "output": 60.00},  # per 1M tokens
    }

    if model not in costs:
        return 0.0

    cost = (
        input_tokens * costs[model]["input"] + output_tokens * costs[model]["output"]
    ) / 1_000_000
    return cost


def render_token_module():  # Muutettu funktion nimi
    with st.expander("Token Info"):
        # Get current model and token counts from session state
        current_model = st.session_state.get("current_model", "Not used yet")
        input_tokens = st.session_state.get("input_tokens", 0)
        output_tokens = st.session_state.get("output_tokens", 0)
        embedding_model = "sentence-transformers/all-mpnet-base-v2"

        # Calculate cost
        cost = calculate_token_cost(input_tokens, output_tokens, current_model)

        # Display model info
        st.markdown("### Models Used")
        st.write("**Last Response:**")
        if current_model != "Not used yet":
            st.write(f"- LLM Model: {current_model} (for answer generation)")
        else:
            st.write("- LLM Model: Not used yet")
        st.write(f"- Embedding Model: {embedding_model} (for semantic search)")

        # Display token usage with columns
        st.markdown("### Token Usage")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Counts:")
            st.write(f"• Input: {input_tokens:,}")
            st.write(f"• Output: {output_tokens:,}")
            st.write(f"• Total: {input_tokens + output_tokens:,}")
        with col2:
            st.write("Estimated Cost:")
            st.write(f"${cost:.6f}")

        # Add last update timestamp if available
        if "last_query_time" in st.session_state:
            st.markdown("---")
            st.write("Last query:", st.session_state.get("last_query_time"))
            if current_model != "Not used yet":
                st.write("Response generated using:", current_model)
