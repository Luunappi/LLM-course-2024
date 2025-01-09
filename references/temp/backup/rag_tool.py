"""RAG Tool for document retrieval and querying"""

import logging
from typing import List, Optional, Dict, Any, Tuple, Callable
from agentformer.tools.model_tool import ModelTool
from agentformer.memory.backends.faiss_backend import FaissMemoryBackend
import numpy as np
from pypdf import PdfReader
import io
import time
from sentence_transformers import SentenceTransformer
from agentformer.tools import debug_tool
import torch
import re
import faiss
import fitz
import os

logger = logging.getLogger(__name__)


class RAGTool:
    """Tool for RAG operations"""

    def __init__(self, embedding_model="sbert"):
        """Initialize RAG tool with chosen embedding model and FAISS backend

        Args:
            embedding_model (str): Choice of embedding model: 'sbert' or 'ada'
        """
        self.embedding_model_choice = embedding_model
        self.last_indexed_files = set()  # Track indexed files

        # Initialize embedding model based on choice
        try:
            if embedding_model == "sbert":
                logger.info("\n=== Ladataan SBERT-mallia Hugging Face:sta ===")
                self.embedding_model = SentenceTransformer(
                    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
                )
                logger.info("=== SBERT-malli ladattu onnistuneesti ===\n")
                self.embedding_dimension = 768  # SBERT dimension

            elif embedding_model == "ada":
                logger.info("\n=== Käytetään OpenAI Ada -mallia embeddingeille ===")
                # Check for OpenAI API key
                if not os.getenv("OPENAI_API_KEY"):
                    raise ValueError(
                        "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
                    )
                import openai

                self.embedding_model = openai
                self.embedding_dimension = 1536  # Ada dimension
                logger.info("=== OpenAI Ada -malli käytettävissä ===\n")

            else:
                raise ValueError(
                    f"Invalid embedding model choice: {embedding_model}. Use 'sbert' or 'ada'"
                )

        except Exception as e:
            error_msg = f"""
VIRHE: Embedding-mallin alustus epäonnistui ({embedding_model}).
Syy voi olla:
1. Ei internet-yhteyttä
2. Palvelu ei vastaa (Hugging Face/OpenAI)
3. Mallia ei löydy
4. OpenAI API key puuttuu (jos valittu 'ada')

Tekninen virheilmoitus: {str(e)}
"""
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Set up device for SBERT if using it
        if embedding_model == "sbert":
            self.device = torch.device(
                "mps" if torch.backends.mps.is_available() else "cpu"
            )
            self.embedding_model.to(self.device)

        # Initialize memory backend with correct dimension
        self.backend = FaissMemoryBackend()
        self.backend.dimension = (
            self.embedding_dimension
        )  # Set dimension after initialization

        # Configuration
        self.chunk_size = 500
        self.chunk_overlap = 50
        self.min_chunk_size = 100
        self.max_chunks_per_query = 3
        self.batch_size = 32  # Add batch size configuration

        logger.debug("Initialized RAGTool with multilingual SBERT and FAISS backend")

        self.model_tool = ModelTool()  # Initialize ModelTool for summaries

    def add_document(
        self,
        document: str,
        doc_id: str = None,
        file_type: str = "text",
        extra_meta: Dict[str, Any] = None,
    ):
        """Add document to index with chunking"""
        try:
            logger.debug("=== STARTING DOCUMENT PROCESSING ===")
            logger.debug(f"File type: {file_type}")

            if file_type == "pdf":
                logger.debug("1/5: Reading and cleaning PDF")
                try:
                    document = self._process_pdf(document)
                    logger.debug("✓ PDF processed to text")
                except Exception as e:
                    logger.error(f"Error processing PDF: {str(e)}")
                    raise

            # Split document into chunks
            logger.debug("2/5: Text chunking")
            try:
                chunks = self._split_into_chunks(document, chunk_size=500)
                if not chunks:
                    raise ValueError("Chunking produced no chunks")
                logger.debug(f"✓ Text split into {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Error in chunking: {str(e)}")
                raise

            # Calculate embeddings
            logger.debug("3/5: Computing SBERT embeddings")
            try:
                embeddings = []
                for chunk in chunks:
                    chunk_embedding = self.embedding_model.encode([chunk])[0]
                    embeddings.append(chunk_embedding)
                logger.debug(f"✓ Computed embeddings for {len(embeddings)} chunks")
            except Exception as e:
                logger.error(f"Error computing embeddings: {str(e)}")
                raise

            # Add to FAISS index
            logger.debug("4/5: FAISS indexing")
            try:
                logger.debug(f"Starting FAISS indexing for {len(chunks)} chunks")
                logger.debug(
                    f"First chunk length: {len(chunks[0]) if chunks else 'N/A'}"
                )
                logger.debug(
                    f"First embedding shape: {embeddings[0].shape if embeddings else 'N/A'}"
                )

                # Verify backend and index initialization
                if not self.backend:
                    raise ValueError("Backend not initialized")
                if not self.backend.index:
                    logger.debug("FAISS index not initialized, initializing now...")
                    self.backend._init_index()
                logger.debug(f"FAISS index dimension: {self.backend.index.d}")

                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_id = f"{doc_id}-chunk-{i}" if doc_id else f"chunk-{i}"
                    logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                    logger.debug(f"Chunk ID: {chunk_id}")
                    logger.debug(f"Chunk length: {len(chunk)}")
                    logger.debug(f"Embedding shape: {embedding.shape}")

                    try:
                        self.backend.store(
                            content_id=chunk_id,
                            text_content=chunk,
                            embedding=embedding,
                            extra_meta={
                                "doc_id": doc_id,
                                "chunk_id": chunk_id,
                                "file_type": file_type,
                                **(extra_meta or {}),
                            },
                        )
                        logger.debug(f"Successfully stored chunk {i+1}")
                    except Exception as chunk_e:
                        logger.error(f"Error storing chunk {i+1}: {str(chunk_e)}")
                        logger.error(f"Chunk content preview: {chunk[:100]}...")
                        raise

                logger.debug(f"✓ Added {len(chunks)} vectors to FAISS index")
                logger.debug(f"Final FAISS index size: {self.backend.index.ntotal}")
            except Exception as e:
                logger.error(f"Error in FAISS indexing: {str(e)}")
                logger.error(f"Backend type: {type(self.backend)}")
                logger.error(
                    f"Backend index type: {type(self.backend.index) if self.backend and self.backend.index else 'None'}"
                )
                raise

            logger.debug("=== DOCUMENT PROCESSING COMPLETE ===")
            return True

        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise

    def query(self, query: str) -> Dict[str, Any]:
        """Query the RAG system with improved response quality"""
        try:
            # Determine query type for better context selection
            query_type = self._classify_query_type(query.lower())

            # Adjust search parameters based on query type
            k = 5  # Default number of chunks
            if query_type == "overview":
                k = 3  # Fewer, more focused chunks for overview questions
            elif query_type == "specific":
                k = 5  # More chunks for specific questions
            elif query_type == "detailed":
                k = 7  # Most chunks for detailed analysis

            # Get relevant chunks with improved selection
            results = self.backend.semantic_search(query, k=k)
            if not results:
                return {
                    "response": "No relevant information found.",
                    "found_in_docs": False,
                }

            # Format context from results with improved structure
            context = []
            for result in results:
                context.append(
                    {
                        "content": result["content"],
                        "source": result["meta"].get("filename", "unknown"),
                        "score": result["distance"],
                        "position": result["meta"].get(
                            "chunk_id", 0
                        ),  # Track position in document
                    }
                )

            if not context:
                return {
                    "response": "No relevant information found.",
                    "found_in_docs": False,
                }

            # Sort context by position to maintain document flow
            context.sort(key=lambda x: x["position"])

            # Determine response language based on query
            is_english_query = self._is_english(query)

            # Format prompt based on query type
            if query_type == "overview":
                prompt = self._create_overview_prompt(context, is_english_query)
            elif query_type == "specific":
                prompt = self._create_specific_prompt(query, context, is_english_query)
            else:
                prompt = self._create_detailed_prompt(query, context, is_english_query)

            # Get response from language model
            model_tool = ModelTool()
            response = model_tool.process(prompt, task_type="rag_qa")

            return {
                "response": response,
                "context": context,
                "found_in_docs": True,
                "metadata": {
                    "query_type": query_type,
                    "language": "english" if is_english_query else "finnish",
                    "num_chunks": len(context),
                    "sources": list(set(c["source"] for c in context)),
                },
            }

        except Exception as e:
            logger.error(f"Error in query: {str(e)}")
            return {
                "response": "An error occurred while processing your query.",
                "found_in_docs": False,
                "error": str(e),
            }

    def _classify_query_type(self, query: str) -> str:
        """Classify query type for better response structuring"""
        overview_patterns = [
            "what is",
            "what are",
            "tell me about",
            "describe",
            "explain",
            "kerro",
            "mikä on",
            "mitä",
        ]
        specific_patterns = [
            "how",
            "why",
            "when",
            "where",
            "who",
            "which",
            "miten",
            "miksi",
            "milloin",
            "missä",
            "kuka",
        ]

        query_lower = query.lower()
        for pattern in overview_patterns:
            if pattern in query_lower:
                return "overview"
        for pattern in specific_patterns:
            if pattern in query_lower:
                return "specific"
        return "detailed"

    def _is_english(self, text: str) -> bool:
        """Determine if text is primarily English"""
        english_words = set(
            [
                "what",
                "is",
                "are",
                "how",
                "why",
                "when",
                "where",
                "who",
                "which",
                "the",
                "a",
                "an",
                "in",
                "on",
                "at",
            ]
        )
        words = text.lower().split()
        english_count = sum(1 for word in words if word in english_words)
        return english_count / len(words) > 0.3 if words else True

    def _create_overview_prompt(self, context: List[Dict], is_english: bool) -> str:
        """Create prompt for overview-type questions"""
        if is_english:
            prompt = """Based on the provided context, create a comprehensive overview that:
1. Starts with a clear main topic or purpose
2. Outlines the key themes or components
3. Provides relevant details in a structured way

Context:
{}

Response should be well-structured and in English."""
        else:
            prompt = """Annetun kontekstin perusteella, luo kattava yleiskatsaus joka:
1. Alkaa selkeällä päätavoitteella tai aiheella
2. Kuvaa keskeiset teemat tai komponentit
3. Tarjoaa olennaiset yksityiskohdat jäsennellyssä muodossa

Konteksti:
{}

Vastauksen tulee olla hyvin jäsennelty ja suomeksi."""

        return prompt.format(self._format_context(context))

    def _create_specific_prompt(
        self, query: str, context: List[Dict], is_english: bool
    ) -> str:
        """Create prompt for specific questions"""
        if is_english:
            prompt = """Answer the following question based on the provided context.
Focus on providing a direct, specific answer with supporting details.

Question: {}

Context:
{}

Response should be clear, concise, and in English."""
        else:
            prompt = """Vastaa seuraavaan kysymykseen annetun kontekstin perusteella.
Keskity antamaan suora, tarkka vastaus ja tue sitä yksityiskohdilla.

Kysymys: {}

Konteksti:
{}

Vastauksen tulee olla selkeä, ytimekäs ja suomeksi."""

        return prompt.format(query, self._format_context(context))

    def _create_detailed_prompt(
        self, query: str, context: List[Dict], is_english: bool
    ) -> str:
        """Create prompt for detailed analysis"""
        if is_english:
            prompt = """Provide a detailed analysis of the following topic based on the context.
Include:
1. Main concepts and their relationships
2. Supporting evidence and examples
3. Relevant implications or applications

Topic: {}

Context:
{}

Response should be comprehensive and in English."""
        else:
            prompt = """Anna yksityiskohtainen analyysi seuraavasta aiheesta kontekstin perusteella.
Sisällytä:
1. Pääkäsitteet ja niiden väliset suhteet
2. Tukevat todisteet ja esimerkit
3. Olennaiset vaikutukset tai sovellukset

Aihe: {}

Konteksti:
{}

Vastauksen tulee olla kattava ja suomeksi."""

        return prompt.format(query, self._format_context(context))

    def _format_context(self, context: List[Dict]) -> str:
        """Format context for prompts with improved structure"""
        formatted_chunks = []
        for i, chunk in enumerate(context, 1):
            formatted_chunks.append(
                f"[{i}] From {chunk['source']} (relevance: {chunk['score']:.2f}):\n{chunk['content']}\n"
            )
        return "\n".join(formatted_chunks)
