"""
Info Module

Displays general system information and notifications.
Shows warnings, errors and other important system messages.
"""

import streamlit as st


def render_info_module():
    """Render system information and notifications"""
    with st.expander("System Info"):
        # System warnings and notifications
        if st.session_state.get("system_warnings"):
            for warning in st.session_state["system_warnings"]:
                st.warning(warning)

        # API and connection status
        st.markdown("### System Status")
        if "api_key_loaded" in st.session_state:
            st.success("✓ OpenAI API key loaded")
        else:
            st.error("✗ OpenAI API key not found")

        # Show callback warnings if any
        if st.session_state.get("callback_warnings"):
            st.warning("Callback warnings:")
            for warning in st.session_state["callback_warnings"]:
                st.write(f"- {warning}")
        else:
            st.success("✓ No callback warnings")
