"""
RAG Tool

Handles document retrieval and augmented generation functionality.
"""

import streamlit as st
from openai import OpenAI
import os
from sentence_transformers import SentenceTransformer
import torch

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class RAGTool:
    """Tool for RAG operations"""

    def __init__(self):
        self.embedding_model = SentenceTransformer(
            "sentence-transformers/all-mpnet-base-v2"
        )

    def process(self, query: str) -> dict:
        """Process RAG request"""
        try:
            if "chunks" not in st.session_state:
                return {
                    "type": "text",
                    "content": "Please load a document first",
                    "error": True,
                }

            relevant_chunks = self.semantic_search(query)
            answer = self.generate_answer(query, relevant_chunks)

            return {"type": "text", "content": answer, "chunks": relevant_chunks}
        except Exception as e:
            st.session_state["system_warnings"].append(
                f"RAG processing error: {str(e)}"
            )
            return None

    def semantic_search(self, query: str, top_k: int = 3) -> list:
        """Find most relevant chunks"""
        query_embedding = self.embedding_model.encode([query])
        query_embedding = torch.tensor(query_embedding).squeeze(0)
        query_embedding = query_embedding / query_embedding.norm()

        embeddings = st.session_state.embeddings
        embeddings = embeddings / embeddings.norm(dim=1, keepdim=True)

        similarities = torch.matmul(embeddings, query_embedding)
        top_indices = similarities.argsort(descending=True)[:top_k]

        return [st.session_state.chunks[idx] for idx in top_indices]

    def generate_answer(self, query: str, chunks: list) -> str:
        """Generate answer using context"""
        context = "\n".join(chunks)
        prompt = f"""Based on the following context, answer the question.
        If you cannot answer based on the context, say so.

        Context:
        {context}

        Question: {query}

        Answer:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided context.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        return response.choices[0].message.content
