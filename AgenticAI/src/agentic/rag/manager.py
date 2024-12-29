"""RAG Manager component"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from openai import OpenAI
import os
from dotenv import load_dotenv


class RAGManager:
    def __init__(self):
        self.config_path = Path("data/rag_config")
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.documents: Dict[str, Dict[str, Any]] = {}

        # Load OpenAI API key
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.token_pricing = {
            "o1-mini-2024-09-12": {
                "input": 0.50 / 1_000_000,  # $0.50 per 1M input tokens
                "output": 2.00 / 1_000_000,  # $2.00 per 1M output tokens
            },
            "gpt-4o": {
                "input": 2.50 / 1_000_000,  # $2.50 per 1M input tokens
                "output": 10.00 / 1_000_000,  # $10.00 per 1M output tokens
            },
        }

    def query(
        self,
        query: str,
        query_type: str = "rag",
        max_words: int = 100,
        system_prompt: str = None,
    ) -> Dict:
        """Query the RAG system"""
        try:
            # Yhdistä promptit user-viestiin
            full_prompt = f"{system_prompt}\n\nKysymys: {query}\n\nVastaa ytimekkäästi, noin {max_words} sanalla (+/- 5 sanaa)."

            if query_type == "direct":
                response = self.client.chat.completions.create(
                    model="o1-mini-2024-09-12",
                    messages=[{"role": "user", "content": full_prompt}],
                )
                pricing = self.token_pricing["o1-mini-2024-09-12"]
                cost = (
                    response.usage.prompt_tokens * pricing["input"]
                    + response.usage.completion_tokens * pricing["output"]
                )

                return {
                    "response": response.choices[0].message.content,
                    "context": [],
                    "metadata": {
                        "model": "o1-mini-2024-09-12",
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                        "cost_usd": cost,
                    },
                }

            elif query_type == "rag":
                # RAG käyttää GPT-4o mallia
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": query}],
                    max_tokens=max_words * 2,
                )
                pricing = self.token_pricing["gpt-4o"]
                cost = (
                    response.usage.prompt_tokens * pricing["input"]
                    + response.usage.completion_tokens * pricing["output"]
                )

                return {
                    "response": response.choices[0].message.content,
                    "context": [],
                    "metadata": {
                        "model": "gpt-4o",
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                        "cost_usd": cost,
                    },
                }

            else:  # summary
                # Yhteenvedot o1-mini mallilla
                response = self.client.chat.completions.create(
                    model="o1-mini-2024-09-12",
                    messages=[{"role": "user", "content": query}],
                    max_tokens=max_words * 2,
                )
                pricing = self.token_pricing["o1-mini-2024-09-12"]
                cost = (
                    response.usage.prompt_tokens * pricing["input"]
                    + response.usage.completion_tokens * pricing["output"]
                )

                return {
                    "response": response.choices[0].message.content,
                    "context": [],
                    "metadata": {
                        "model": "o1-mini-2024-09-12",
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                        "cost_usd": cost,
                    },
                }

        except Exception as e:
            print(f"Error in query: {str(e)}")
            raise

    def add_document(
        self, content: str, doc_id: str, metadata: Optional[Dict] = None
    ) -> None:
        """Add document to system"""
        # For now, just store the document
        self.documents[doc_id] = {
            "content": content,
            "metadata": metadata or {},
            "indexed": True,
        }
        self._save_document_index()

    def _save_document_index(self) -> None:
        """Save document index to disk"""
        index_path = self.config_path / "document_index.json"
        with open(index_path, "w") as f:
            json.dump(self.documents, f, indent=2)

    def _load_document_index(self) -> None:
        """Load document index from disk"""
        index_path = self.config_path / "document_index.json"
        if index_path.exists():
            with open(index_path) as f:
                self.documents = json.load(f)
