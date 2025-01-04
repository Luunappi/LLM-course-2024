"""
Info Module

Displays general system information and notifications.
Shows warnings, errors and other important system messages.
"""

import streamlit as st


def render_info_module():
    """Render system information and notifications"""

    # Tool Analysis Section
    st.markdown(
        '<div style="color: #666; font-size: 1em; font-weight: 600; margin-bottom: 0.8rem;">'
        "Question evaluation for choosing the right tools"
        "</div>",
        unsafe_allow_html=True,
    )

    if st.session_state.get("last_tool_analysis"):
        with st.container():
            st.markdown(
                '<div style="color: #888; font-size: 0.9em;">Query:</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="color: #666; font-size: 0.9em; margin-bottom: 0.5rem; padding-left: 1rem;">{st.session_state["last_tool_analysis"]["query"]}</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div style="color: #888; font-size: 0.9em;">Selected tools:</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="color: #666; font-size: 0.9em; margin-bottom: 0.5rem; padding-left: 1rem;">{", ".join(st.session_state["last_tool_analysis"]["tools"])}</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div style="color: #888; font-size: 0.9em;">Reasoning:</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="color: #666; font-size: 0.9em; margin-bottom: 0.5rem; padding-left: 1rem;">{st.session_state["last_tool_analysis"]["reason"]}</div>',
                unsafe_allow_html=True,
            )

            if st.session_state["last_tool_analysis"].get("visualization_type"):
                st.markdown(
                    '<div style="color: #888; font-size: 0.9em;">Visualization type:</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="color: #666; font-size: 0.9em; margin-bottom: 0.5rem; padding-left: 1rem;">{st.session_state["last_tool_analysis"]["visualization_type"]}</div>',
                    unsafe_allow_html=True,
                )

    # Lisätty tyhjä rivi ja viiva arvioinnin jälkeen
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # System Status Section
    st.markdown(
        '<div style="color: #666; font-size: 1em; font-weight: 500; margin-bottom: 0.5rem;">'
        "System Status"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.session_state.get("api_key_loaded"):
        st.markdown(
            '<div style="color: #4CAF50; font-size: 0.9em;">✓ API connection active</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="color: #f44336; font-size: 0.9em;">✗ API connection error</div>',
            unsafe_allow_html=True,
        )

    # Session Information Section
    st.markdown("---")
    st.markdown(
        '<div style="color: #666; font-size: 1em; font-weight: 500; margin-bottom: 0.5rem;">'
        "Session Information"
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            '<div style="color: #888; font-size: 0.9em;">Started:</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="color: #888; font-size: 0.9em;">Model:</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="color: #888; font-size: 0.9em;">Word limit:</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div style="color: #666; font-size: 0.9em;">{st.session_state.get("init_time", "Not set")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="color: #666; font-size: 0.9em;">{st.session_state.get("current_model", "Not set")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="color: #666; font-size: 0.9em;">{str(st.session_state.get("max_words", 50))}</div>',
            unsafe_allow_html=True,
        )
