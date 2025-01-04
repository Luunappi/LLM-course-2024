import streamlit as st


def render_prompt_module():
    with st.expander("System Prompt (optional)"):
        # System prompt
        new_prompt = st.text_area("Prompt content", st.session_state["system_prompt"])
        if st.button("Update Prompt"):
            st.session_state["system_prompt"] = new_prompt
            st.success("System prompt updated!")

        st.write("---")

        # Max word limit slider
        if "max_words" not in st.session_state:
            st.session_state["max_words"] = 50  # Default value

        max_words = st.slider(
            "Max words in response:",
            min_value=0,
            max_value=250,
            value=st.session_state["max_words"],
            step=10,
            help="Limit the length of model responses (0 = no limit)",
        )

        if max_words != st.session_state["max_words"]:
            st.session_state["max_words"] = max_words
            st.success(f"Max words set to: {max_words}")
