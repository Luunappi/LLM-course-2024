"""
Generator component for RAG operations.
Handles prompt construction and text generation.
"""

from typing import List, Dict, Any
import openai
from ..config.model_config import ModelType, get_model_config
import os
from openai import AsyncOpenAI
import streamlit as st


class Generator:
    def __init__(self):
        """Initialize generator with model configuration"""
        self.model_config = get_model_config(ModelType.STANDARD)
        self.client = AsyncOpenAI()

    async def initialize(self) -> None:
        """Initialize generator"""
        pass

    def _build_prompt(self, query: str, context: List[Dict]) -> str:
        """Build prompt from query and context"""
        context_text = "\n\n".join(
            f"Context {i+1}:\n{item['chunk']}" for i, item in enumerate(context)
        )

        return f"""Based on the following context:

{context_text}

Answer the question: {query}

Use only the information provided in the context. If you cannot find relevant information, say so."""

    async def generate(self, query: str, context: List[Dict]) -> str:
        """Generate response based on query and context"""
        try:
            # Haetaan käyttäjän määrittelemä sanaraja
            max_words = st.session_state.get("max_words", 200)

            # Lisätään ohje sanarajasta system promptiin
            word_limit_instruction = f"\nVastaa {max_words} sanalla (±10 sanaa). Vastauksen tulee olla kokonainen ja looginen."

            if not context:  # Suora kysely LLM:lle
                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": st.session_state.get(
                                "direct_prompt", "Olet avulias tekoälyassistentti..."
                            )
                            + word_limit_instruction,
                        },
                        {"role": "user", "content": query},
                    ],
                    temperature=0.7,
                )
                return response.choices[0].message.content

            # RAG-kysely dokumenteista
            prompt = self._build_prompt(query, context)
            response = await self.client.chat.completions.create(
                model=self.model_config.model_id,
                messages=[
                    {
                        "role": "system",
                        "content": st.session_state.get(
                            "rag_prompt", "Olet tutkimusassistentti..."
                        )
                        + word_limit_instruction,
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"Virhe kyselyn käsittelyssä: {str(e)}"
