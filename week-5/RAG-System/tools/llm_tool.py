"""
LLM Tool

Handles direct language model interactions.
"""

import streamlit as st
from openai import OpenAI
import os
from datetime import datetime

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class LLMTool:
    """Tool for direct LLM operations"""

    def process(self, query: str) -> dict:
        """Process direct LLM request"""
        try:
            model_name = st.session_state.get("current_model", "gpt-4o-mini")
            max_words = st.session_state.get("max_words", 50)

            content = query
            if max_words > 0:
                content = f"Answer the following question in {max_words} words or less: {query}"

            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": content}],
                temperature=0.7,
                max_tokens=500,
            )

            # Update session state
            st.session_state["current_model"] = model_name
            st.session_state["input_tokens"] = response.usage.prompt_tokens
            st.session_state["output_tokens"] = response.usage.completion_tokens
            st.session_state["last_query_time"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            return {"type": "text", "content": response.choices[0].message.content}

        except Exception as e:
            st.session_state["system_warnings"].append(
                f"LLM processing error: {str(e)}"
            )
            return None
