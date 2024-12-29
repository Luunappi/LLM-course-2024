"""
Retrieval component for RAG operations.
Handles text chunking, embedding and vector search.
"""

from typing import List, Dict, Optional
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from pathlib import Path


class Retriever:
    def __init__(self):
        # Käytetään E5-mallia, joka on optimoitu hakutehtäviin
        self.tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-base-v2")
        self.model = AutoModel.from_pretrained("intfloat/e5-base-v2")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)
        self.vectors_path = Path("data/vectors")
        self.vectors_path.mkdir(parents=True, exist_ok=True)
        self.embeddings = {}

    async def initialize(self):
        """Initialize retriever"""
        pass

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using E5"""
        # E5 käyttää "query: " ja "passage: " etuliitteitä
        if "query:" not in text and "passage:" not in text:
            text = f"passage: {text}"  # Lisätään etuliite dokumenteille

        # Tokenize and get model output
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=512
        )
        # Move inputs to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        # E5 käyttää mean pooling
        attention_mask = inputs["attention_mask"]
        embeddings = outputs.last_hidden_state
        mask = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
        masked_embeddings = embeddings * mask
        summed = torch.sum(masked_embeddings, dim=1)
        counts = torch.clamp(torch.sum(attention_mask, dim=1, keepdims=True), min=1e-9)
        mean_pooled = summed / counts

        # Move back to CPU for numpy conversion
        return mean_pooled.cpu().numpy()[0]  # Return as 1D array

    async def add_text(self, text: str, doc_id: str):
        """Add text to retriever"""
        # Chunk text
        chunks = self._chunk_text(text)

        # Create embeddings
        embeddings = np.array([self._get_embedding(chunk) for chunk in chunks])

        # Store embeddings
        self.embeddings[doc_id] = {"chunks": chunks, "vectors": embeddings}

    async def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant text chunks"""
        # E5 käyttää "query: " etuliitettä kyselyille
        query = f"query: {query}"

        # Create query embedding
        query_embedding = self._get_embedding(query)

        results = []
        for doc_id, doc_data in self.embeddings.items():
            # Calculate similarities
            similarities = np.dot(doc_data["vectors"], query_embedding)

            # Get top matches
            top_indices = np.argsort(similarities)[-top_k:]

            for idx in top_indices:
                results.append(
                    {
                        "doc_id": doc_id,
                        "chunk": doc_data["chunks"][idx],
                        "score": float(similarities[idx]),
                    }
                )

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    def _chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        """Split text into chunks"""
        # Yksinkertainen chunkkaus aluksi
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
