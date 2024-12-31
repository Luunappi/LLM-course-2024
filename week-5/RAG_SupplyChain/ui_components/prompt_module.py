import streamlit as st


def render_prompt_module():
    with st.expander("System Prompt (optional)"):
        new_prompt = st.text_area("Prompt content", st.session_state["system_prompt"])
        if st.button("Update Prompt"):
            st.session_state["system_prompt"] = new_prompt
            st.success("System prompt updated!")
