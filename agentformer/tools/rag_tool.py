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


class NoProgressBar:
    """A progress bar that does nothing, used to suppress SBERT output"""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def set_description(self, *args, **kwargs):
        pass


class RAGTool:
    """Tool for RAG operations"""

    def __init__(self, embedding_model="sbert"):
        """Initialize RAG tool with chosen embedding model and FAISS backend

        Args:
            embedding_model (str): Choice of embedding model: 'sbert' or 'ada'
        """
        from sentence_transformers import SentenceTransformer
        import torch

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

    def _check_and_index_saved_files(self):
        """Check saved_files directory and index any unindexed documents"""
        saved_files = self.backend.get_saved_files()
        if not saved_files:
            logger.debug("No saved files found")
            return

        logger.debug(f"Found {len(saved_files)} saved files")
        for filename in saved_files:
            if not self.backend.is_file_indexed(filename):
                logger.debug(f"Indexing new file: {filename}")
                file_content = self.backend.load_file(filename)
                if file_content:
                    self.add_document(
                        document=file_content,
                        doc_id=f"saved-{filename}",
                        file_type="pdf" if filename.endswith(".pdf") else "text",
                        extra_meta={"filename": filename},
                    )

    def _check_and_index_saved_files(self):
        """Check saved_files directory and index any unindexed documents"""
        try:
            # Get saved files
            saved_files = self.backend.get_saved_files()
            if not saved_files:
                logger.debug("No files found in saved_files directory")
                return

            # Get already indexed documents from metadata
            indexed_docs = set()
            for meta in self.backend.metadata:
                if isinstance(meta, dict) and "meta" in meta:
                    meta_data = meta.get("meta", {})
                    if isinstance(meta_data, dict):
                        filename = meta_data.get("filename")
                        if filename:
                            indexed_docs.add(filename)

            # Only index new files
            new_files = [f for f in saved_files if f not in indexed_docs]
            if not new_files:
                logger.debug("No new files to index")
                return

            # Index only new documents
            for filename in new_files:
                logger.info(f"Indexing new file: {filename}")
                try:
                    file_content = self.backend.load_file(filename)
                    if file_content:
                        # Determine file type
                        file_type = (
                            "pdf" if filename.lower().endswith(".pdf") else "text"
                        )

                        # Add document to index with filename in metadata
                        self.add_document(
                            document=file_content,
                            doc_id=f"saved-{filename}",
                            file_type=file_type,
                            extra_meta={"filename": filename},
                        )
                        logger.info(f"Successfully indexed {filename}")
                except Exception as e:
                    logger.error(f"Error indexing {filename}: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking saved files: {str(e)}")

    def add_document(
        self,
        document: str,
        doc_id: str = None,
        file_type: str = "text",
        extra_meta: Dict[str, Any] = None,
    ):
        """Add document to index with chunking"""
        try:
            if file_type == "pdf":
                document = self._process_pdf(document)

            # Split document into chunks
            chunks = self._split_into_chunks(document, chunk_size=500)
            if not chunks:
                raise ValueError("Chunking produced no chunks")

            # Calculate embeddings
            embeddings = []
            for chunk in chunks:
                chunk_embedding = self.embedding_model.encode([chunk])[0]
                embeddings.append(chunk_embedding)

            # Add to FAISS index
            try:
                # Verify backend and index initialization
                if not self.backend:
                    raise ValueError("Backend not initialized")
                if not self.backend.index:
                    self.backend._init_index()

                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_id = f"{doc_id}-chunk-{i}" if doc_id else f"chunk-{i}"

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
                    except Exception as chunk_e:
                        logger.error(f"Error storing chunk {i+1}: {str(chunk_e)}")
                        raise

            except Exception as e:
                logger.error(f"Error in FAISS indexing: {str(e)}")
                raise

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

Provide a clear, focused answer in English."""
        else:
            prompt = """Vastaa seuraavaan kysymykseen annetun kontekstin perusteella.
Keskity antamaan suora, täsmällinen vastaus ja sitä tukevat yksityiskohdat.

Kysymys: {}

Konteksti:
{}

Anna selkeä, kohdennettu vastaus suomeksi."""

        return prompt.format(query, self._format_context(context))

    def _create_detailed_prompt(
        self, query: str, context: List[Dict], is_english: bool
    ) -> str:
        """Create prompt for detailed analysis"""
        if is_english:
            prompt = """Provide a detailed analysis based on the following question and context.
Include:
1. Main points and key concepts
2. Supporting evidence and examples
3. Relevant relationships and implications

Question: {}

Context:
{}

Provide a comprehensive answer in English."""
        else:
            prompt = """Tee yksityiskohtainen analyysi seuraavan kysymyksen ja kontekstin perusteella.
Sisällytä:
1. Pääkohdat ja keskeiset käsitteet
2. Tukevat todisteet ja esimerkit
3. Olennaiset suhteet ja vaikutukset

Kysymys: {}

Konteksti:
{}

Anna kattava vastaus suomeksi."""

        return prompt.format(query, self._format_context(context))

    def _format_context(self, context: List[Dict]) -> str:
        """Format context with improved structure"""
        formatted_chunks = []
        for i, ctx in enumerate(context, 1):
            chunk = f"[Chunk {i}, Relevance: {ctx['score']:.2f}]\n{ctx['content']}"
            formatted_chunks.append(chunk)
        return "\n\n".join(formatted_chunks)

    def _focused_qa(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Specialized pipeline for Q&A with focused retrieval"""
        try:
            if not self.has_documents():
                return {
                    "response": "Ei dokumentteja indeksissä. Lataa ensin dokumentti.",
                    "context": [],
                    "found_in_docs": False,
                }

            # Compute query embedding with higher precision
            query_embedding = self._compute_embeddings([query])
            query_embedding_np = query_embedding.cpu().numpy()
            faiss.normalize_L2(query_embedding_np)

            # Use stricter similarity threshold for Q&A
            D, I = self.backend.index.search(
                query_embedding_np, k * 2
            )  # Get more candidates

            # Filter results with higher similarity threshold
            min_similarity = 0.6  # Adjust based on testing
            results = [
                (idx, float(score))
                for score, idx in zip(D[0], I[0])
                if score > min_similarity and idx < len(self.backend.metadata)
            ][:k]  # Take top k after filtering

            if not results:
                return {
                    "response": "En löytänyt tarpeeksi relevanttia tietoa vastatakseni kysymykseen.",
                    "context": [],
                    "found_in_docs": False,
                }

            # Collect and format context
            context = self._get_context_from_results(results)

            # Use focused Q&A prompt
            prompt = f"""Vastaa kysymykseen annetun kontekstin perusteella.
Jos et löydä tarkkaa vastausta kontekstista, kerro se selkeästi.
Keskity vain olennaiseen ja anna ytimekäs vastaus.

Konteksti:
{self._format_context(context)}

Kysymys: {query}

Vastaus:"""

            response = self.model_tool.process(prompt, task_type="rag_qa")

            return {
                "response": response,
                "context": context,
                "found_in_docs": True,
                "metadata": {
                    "num_chunks": len(context),
                    "similarity_threshold": min_similarity,
                    "query_time": time.time(),
                },
            }

        except Exception as e:
            logger.error(f"Q&A processing error: {str(e)}")
            return {
                "response": f"Error in Q&A processing: {str(e)}",
                "success": False,
            }

    def _theme_based_summary(self, theme: str) -> Dict[str, Any]:
        """Create a theme-focused summary using RAG"""
        try:
            # First find relevant chunks using the theme
            theme_embedding = self._compute_embeddings([theme])
            theme_embedding_np = theme_embedding.cpu().numpy()
            faiss.normalize_L2(theme_embedding_np)

            # Get more candidates for theme-based summary
            D, I = self.backend.index.search(theme_embedding_np, 20)

            # Use lower similarity threshold for themes
            min_similarity = 0.4  # More permissive for thematic content
            results = [
                (idx, float(score))
                for score, idx in zip(D[0], I[0])
                if score > min_similarity and idx < len(self.backend.metadata)
            ]

            if not results:
                return {
                    "response": f"En löytänyt sisältöä liittyen teemaan '{theme}'",
                    "success": False,
                }

            # Get context and sort by document order
            context = self._get_context_from_results(results)
            context.sort(key=lambda x: x.get("chunk_index", 0))

            # Create hierarchical summary of theme-relevant content
            summary = self._hierarchical_summarize(
                [{"content": c["content"]} for c in context],
                "keskipitkä",  # Use medium length for thematic summaries
            )

            return {
                "response": summary,
                "success": True,
                "metadata": {
                    "theme": theme,
                    "num_relevant_chunks": len(context),
                    "similarity_threshold": min_similarity,
                    "timestamp": time.time(),
                },
            }

        except Exception as e:
            logger.error(f"Theme-based summary error: {str(e)}")
            return {
                "response": f"Error in theme-based summary: {str(e)}",
                "success": False,
            }

    def _full_document_summary(self) -> Dict[str, Any]:
        """Create a full document summary using hierarchical summarization"""
        try:
            if not self.has_documents():
                return {
                    "response": "Ei dokumentteja indeksissä. Lataa ensin dokumentti.",
                    "success": False,
                }

            # Get all chunks from the latest document in order
            chunks = self._get_latest_document_chunks()
            if not chunks:
                return {
                    "response": "Ei löytynyt sisältöä tiivistettäväksi.",
                    "success": False,
                }

            # Create hierarchical summary
            summary = self._hierarchical_summarize(
                chunks, "pitkä"
            )  # Use longer format for full document

            return {
                "response": summary,
                "success": True,
                "metadata": {
                    "doc_id": chunks[0].get("parent_id"),
                    "filename": chunks[0].get("meta", {}).get("filename", "unknown"),
                    "num_chunks": len(chunks),
                    "timestamp": time.time(),
                },
            }

        except Exception as e:
            logger.error(f"Full document summary error: {str(e)}")
            return {
                "response": f"Error in full document summary: {str(e)}",
                "success": False,
            }

    def _get_context_from_results(self, results: List[Tuple[int, float]]) -> List[Dict]:
        """Get and format context from search results"""
        context = []
        for idx, score in results:
            try:
                chunk_data = self.backend.metadata[idx]
                if not chunk_data:
                    continue

                content = chunk_data.get("content", "").strip()
                if not content:
                    continue

                meta = chunk_data.get("meta", {})
                if not isinstance(meta, dict):
                    meta = {}

                context.append(
                    {
                        "content": content,
                        "source": meta.get("filename", "unknown"),
                        "score": score,
                        "chunk_index": meta.get("chunk_index", 0),
                    }
                )

            except Exception as e:
                logger.error(f"Error processing chunk {idx}: {str(e)}")
                continue

        return context

    def _get_latest_document_chunks(self) -> List[Dict]:
        """Get all chunks from the latest document in order"""
        chunks = []
        latest_doc_id = None

        # Find the latest document ID
        for item in reversed(self.backend.metadata):
            if latest_doc_id is None:
                latest_doc_id = item.get("parent_id")
                break

        if not latest_doc_id:
            return []

        # Collect all chunks from this document
        for item in self.backend.metadata:
            if item.get("parent_id") == latest_doc_id:
                content = item.get("content", "").strip()
                if content:
                    chunks.append(
                        {
                            "content": content,
                            "meta": item.get("meta", {}),
                            "parent_id": latest_doc_id,
                            "chunk_index": item.get("meta", {}).get("chunk_index", 0),
                        }
                    )

        # Sort by chunk index
        chunks.sort(key=lambda x: x["chunk_index"])
        return chunks

    def _format_context(self, context: List[Dict]) -> str:
        """Format context for prompts"""
        return "\n\n".join(
            [
                f"[Source: {c['source']}, Relevance: {c['score']:.2f}]\n{c['content']}"
                for c in context
            ]
        )

    def _compute_embedding(self, text: str) -> List[float]:
        """Laske embedding SBERT:llä"""
        embedding = self.model.encode(text)
        return embedding.tolist()

    def _process_pdf(self, document: str) -> str:
        """Process PDF text with proper space handling"""
        try:
            # Initialize PDF reader
            pdf = fitz.open(stream=document, filetype="pdf")
            logger.debug(f"PDF page count: {len(pdf)}")

            # Extract and clean text
            text = ""
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                # Get text blocks with proper formatting
                blocks = page.get_text("blocks")

                # Process each text block
                for block in blocks:
                    block_text = block[4]  # The text content is at index 4
                    # Clean text while preserving meaningful spaces
                    cleaned_text = " ".join(block_text.split())
                    text += cleaned_text + "\n\n"

                logger.debug(f"Page {page_num + 1}/{len(pdf)} processed")

            # Final cleanup
            text = text.replace("\n\n\n", "\n\n").strip()
            logger.debug(f"Total length after cleaning: {len(text)} chars")
            logger.debug("PDF processing complete")
            return text

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    def _split_into_chunks(
        self, text: str, chunk_size: int = None, overlap: int = None
    ) -> List[str]:
        """Split text into chunks while preserving structure and avoiding duplicates"""
        try:
            logger.debug("Starting adaptive chunking")
            chunk_size = chunk_size or self.chunk_size
            overlap = overlap or self.chunk_overlap

            if not text or not text.strip():
                raise ValueError("Empty text")

            # Split into paragraphs first
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not paragraphs:
                # If no paragraph breaks, try splitting by newlines
                paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
                if not paragraphs:
                    raise ValueError("No paragraphs found in text")

            logger.debug(f"Found {len(paragraphs)} paragraphs")

            # Process paragraphs into chunks
            chunks = []
            current_chunk = []
            current_size = 0

            for paragraph in paragraphs:
                # Skip empty paragraphs
                if not paragraph.strip():
                    continue

                # Check if paragraph is a heading
                is_heading = len(paragraph) < 100 and not paragraph.strip().endswith(
                    "."
                )

                # If heading and we have content, save previous chunk
                if is_heading and current_chunk:
                    chunk_text = " ".join(current_chunk)
                    if len(chunk_text) >= self.min_chunk_size:
                        chunks.append(chunk_text)
                    current_chunk = [paragraph]
                    current_size = len(paragraph)
                    continue

                # If current paragraph fits in chunk
                if current_size + len(paragraph) <= chunk_size:
                    current_chunk.append(paragraph)
                    current_size += len(paragraph)
                else:
                    # Save current chunk if it exists
                    if current_chunk:
                        chunk_text = " ".join(current_chunk)
                        if len(chunk_text) >= self.min_chunk_size:
                            chunks.append(chunk_text)
                        current_chunk = []
                        current_size = 0

                    # Handle large paragraphs
                    if len(paragraph) > chunk_size:
                        # Split into sentences
                        sentences = []
                        for sent in re.split("[.!?]+", paragraph):
                            sent = sent.strip()
                            if sent:
                                sentences.append(sent + ".")

                        # Combine sentences into chunks
                        current_sentences = []
                        current_sent_size = 0

                        for sentence in sentences:
                            if current_sent_size + len(sentence) <= chunk_size:
                                current_sentences.append(sentence)
                                current_sent_size += len(sentence)
                            else:
                                if current_sentences:
                                    chunk_text = " ".join(current_sentences)
                                    if len(chunk_text) >= self.min_chunk_size:
                                        chunks.append(chunk_text)
                                current_sentences = [sentence]
                                current_sent_size = len(sentence)

                        if current_sentences:
                            chunk_text = " ".join(current_sentences)
                            if len(chunk_text) >= self.min_chunk_size:
                                chunks.append(chunk_text)
                    else:
                        current_chunk = [paragraph]
                        current_size = len(paragraph)

            # Add final chunk
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(chunk_text)

            # Remove duplicates while preserving order
            seen = set()
            unique_chunks = []
            for chunk in chunks:
                chunk_text = chunk.strip()
                if chunk_text not in seen:
                    unique_chunks.append(chunk_text)
                    seen.add(chunk_text)

            if not unique_chunks:
                # If no chunks met the minimum size, use the original text as one chunk
                unique_chunks = [text.strip()]

            logger.debug(f"Created {len(unique_chunks)} unique chunks")
            return unique_chunks

        except Exception as e:
            logger.error(f"Error in chunking: {str(e)}")
            raise

    def _compute_embeddings(
        self, chunks: List[str], progress_callback=None
    ) -> np.ndarray:
        """Compute embeddings efficiently in batches"""
        try:
            all_embeddings = []
            total_chunks = len(chunks)

            if self.embedding_model_choice == "sbert":
                # Replace tqdm with our custom progress bar
                self.embedding_model.progress_bar_class = NoProgressBar

                # Process in batches with SBERT
                for i in range(0, total_chunks, self.batch_size):
                    batch = chunks[i : min(i + self.batch_size, total_chunks)]
                    with torch.no_grad():
                        batch_embeddings = self.embedding_model.encode(
                            batch,
                            convert_to_tensor=True,
                            device=self.device,
                            show_progress_bar=False,
                            batch_size=self.batch_size,
                            silent=True,
                        )
                        if isinstance(batch_embeddings, torch.Tensor):
                            batch_embeddings = batch_embeddings.cpu().numpy()
                        faiss.normalize_L2(batch_embeddings)
                        all_embeddings.append(batch_embeddings)

            else:  # Ada
                # Process with OpenAI Ada
                for i in range(0, total_chunks, self.batch_size):
                    batch = chunks[i : min(i + self.batch_size, total_chunks)]
                    try:
                        response = self.embedding_model.Embedding.create(
                            input=batch, model="text-embedding-ada-002"
                        )
                        batch_embeddings = np.array(
                            [r["embedding"] for r in response["data"]]
                        )
                        faiss.normalize_L2(batch_embeddings)
                        all_embeddings.append(batch_embeddings)
                    except Exception as e:
                        logger.error(f"OpenAI API error: {str(e)}")
                        raise

            # Combine all batches
            if all_embeddings:
                final_embeddings = np.vstack(all_embeddings)
                return final_embeddings
            else:
                raise ValueError("No embeddings were computed")

        except Exception as e:
            logger.error(f"Error computing embeddings: {str(e)}")
            raise

    def process_file(
        self,
        file: bytes,
        filename: str,
        progress_callback=None,
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """Prosessoi tiedoston RAG-järjestelmään"""
        try:
            # Tarkista onko tiedosto jo indeksoitu
            is_indexed = False
            for meta in self.backend.metadata:
                if isinstance(meta, dict) and "meta" in meta:
                    meta_data = meta.get("meta", {})
                    if (
                        isinstance(meta_data, dict)
                        and meta_data.get("filename") == filename
                    ):
                        is_indexed = True
                        break

            # MUUTOS: Lisätty force_reindex tarkistus
            if is_indexed and not force_reindex:
                logger.info(
                    f"Tiedosto '{filename}' on jo indeksoitu - käytetään olemassa olevaa indeksiä"
                )
                # Tee heti esimerkki kysely tiedoston sisällöstä
                example_query = "Mistä tämä dokumentti kertoo? Anna lyhyt yhteenveto."
                example_result = self.semantic_search(example_query, k=3)

                if example_result:
                    # Yhdistä relevantit tekstit
                    context = " ".join([r["content"] for r in example_result])
                    # Käytä ModelTool:ia tiivistämään vastaus
                    model_tool = ModelTool()
                    prompt = f"""Luo lyhyt ja ytimekäs yhteenveto dokumentista annetun kontekstin perusteella.
                    Vastaa VAIN yhteenvedolla, älä lisää mitään muuta tekstiä.

                    Konteksti:
                    {context}"""
                    overview = model_tool.process(prompt, task_type="summarization")
                else:
                    overview = (
                        "En valitettavasti pystynyt hakemaan yhteenvetoa dokumentista."
                    )

                return {
                    "status": "success",
                    "message": f"""Tiedosto '{filename}' on jo indeksoitu.

    Yhteenveto:
        {overview}

    Voit kysyä lisää tiedoston sisällöstä!""",
                    "already_indexed": True,
                }

            # Jos tiedostoa ei ole indeksoitu tai force_reindex=True, jatka prosessointia
            if progress_callback:
                progress_callback(0.1, "Luetaan tiedostoa...")

            # Tallenna ladattu tiedosto muistiin
            self.last_uploaded_file = filename

            # Tunnista tiedostotyyppi ja prosessoi
            file_type = filename.split(".")[-1].lower()
            text = ""

            if file_type == "pdf":
                if progress_callback:
                    progress_callback(0.2, "Käsitellään PDF-tiedostoa...")
                text = self._process_pdf(file)
                progress_callback(0.3, "Teksti luettu, jaetaan osiin...")
            else:
                text = file.decode("utf-8")

            # Jaa chunkkeihin
            chunks = self._split_into_chunks(text)
            logger.debug(f"Luotu {len(chunks)} chunkkia")

            if progress_callback:
                progress_callback(0.5, "Lasketaan embeddingiä...")

            # Laske embeddingt tehokkaasti batch-prosessointina
            embeddings = self._compute_embeddings(chunks, progress_callback)
            logger.debug(f"Embeddings muoto: {embeddings.shape}")

            # Varmista että vektorit ovat contiguous muistissa ja float32-tyyppiä
            embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

            if progress_callback:
                progress_callback(0.8, "Tallennetaan indeksiin...")

            # Varmista että FAISS-indeksi on alustettu
            if self.backend.index is None:
                self.backend._init_index()

            try:
                # Luo dokumentin ID
                doc_id = f"doc_{len(self.backend.metadata)}"

                # Tallenna tiedosto levylle
                self.backend.save_file(file, filename)

                # Lisää embeddingt indeksiin kerralla
                try:
                    # Normalisoi vektorit
                    faiss.normalize_L2(embeddings)

                    # Lisää kaikki vektorit kerralla
                    self.backend.index.add(embeddings)

                    # Add metadata for each chunk
                    for i, chunk in enumerate(chunks):
                        chunk_metadata = {
                            "parent_id": doc_id,
                            "chunk_id": i,
                            "content": chunk,
                            "meta": {
                                "filename": filename,
                                "type": "document",
                                "timestamp": time.time(),
                            },
                        }
                        self.backend.metadata.append(chunk_metadata)

                    # Save metadata
                    self.backend._save_metadata()

                    logger.debug(f"Lisätty {len(chunks)} vektoria FAISS-indeksiin")

                except Exception as e:
                    logger.error(f"FAISS add error: {str(e)}")
                    raise

            except Exception as e:
                logger.error(f"Virhe tiedoston prosessoinnissa: {str(e)}")
                if progress_callback:
                    progress_callback(1.0, f"Virhe: {str(e)}")
                raise

            if progress_callback:
                progress_callback(1.0, "Valmis!")

            # Tee heti esimerkki kysely tiedoston sisällöstä
            example_query = "Mistä tämä dokumentti kertoo?"
            example_result = self.query(example_query)
            overview = example_result.get("response", "")

            return {
                "status": "success",
                "message": f"Tiedosto käsitelty onnistuneesti!\n\n{overview}\n\nVoit kysyä lisää tiedoston sisällöstä!",
                "chunks": len(chunks),
                "file_type": file_type,
                "text_length": len(text),
                "embedding_dim": embeddings.shape[1],
            }

        except Exception as e:
            logger.error(f"Virhe tiedoston prosessoinnissa: {str(e)}")
            if progress_callback:
                progress_callback(1.0, f"Virhe: {str(e)}")
            raise

    def has_documents(self) -> bool:
        """Check if any documents are loaded in the FAISS index"""
        try:
            # Tarkista että backend ja indeksi on olemassa
            if not self.backend or not self.backend.index:
                return False

            # Tarkista että indeksissä on dataa
            return self.backend.index.ntotal > 0

        except Exception as e:
            logger.error(f"Error checking documents: {str(e)}")
            return False

    def get_documents_info(self) -> List[Dict[str, Any]]:
        """Get information about loaded documents"""
        try:
            if not self.backend or not self.backend.metadata:
                return []

            # Kerää uniikit dokumentit (parent_id:n perusteella)
            documents = {}
            for item in self.backend.metadata:
                parent_id = item["parent_id"]
                if parent_id not in documents:
                    documents[parent_id] = {
                        "id": parent_id,
                        "chunks": 0,
                        "type": item["meta"]["type"],
                        "timestamp": item["meta"]["timestamp"],
                        "first_chunk": item["content"][:100]
                        + "...",  # Näytä alkua dokumentista
                    }
                documents[parent_id]["chunks"] += 1

            # Järjestä uusimmasta vanhimpaan
            sorted_docs = sorted(
                documents.values(), key=lambda x: x["timestamp"], reverse=True
            )

            logger.debug(f"Found {len(sorted_docs)} documents in RAG index")
            return sorted_docs

        except Exception as e:
            logger.error(f"Error getting documents info: {str(e)}")
            return []

    def get_loaded_file(self) -> Optional[bytes]:
        """Palauta ladattu tiedosto muistista"""
        return self.last_uploaded_file

    def get_saved_files(self) -> List[str]:
        """Get list of all saved files"""
        return self.backend.get_saved_files()

    def load_saved_file(self, filename: str) -> Optional[bytes]:
        """Load a previously saved file"""
        return self.backend.load_file(filename)

    def get_file_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific file"""
        try:
            # Etsi tiedoston metadata
            for item in self.backend.metadata:
                if item.get("meta", {}).get("filename") == filename:
                    return {
                        "id": item["parent_id"],
                        "type": item["meta"]["type"],
                        "timestamp": item["meta"]["timestamp"],
                        "chunks": sum(
                            1
                            for m in self.backend.metadata
                            if m.get("parent_id") == item["parent_id"]
                        ),
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            return None

    def _hierarchical_summarize(self, chunks: List[Dict], target_length: str) -> str:
        """Create a hierarchical summary of the document"""
        try:
            # First summarize each chunk
            chunk_summaries = []
            total_chunks = len(chunks)
            logger.debug(f"Starting chunk-level summarization ({total_chunks} chunks)")

            for i, chunk in enumerate(chunks):
                prompt = f"""Tiivistä seuraava tekstikappale ytimekkäästi säilyttäen keskeiset asiat ja faktat:

                {chunk['content']}
                """
                summary = self.model_tool.process(prompt, task_type="summarization")
                if summary:
                    chunk_summaries.append(summary)
                logger.debug(f"Processed chunk {i+1}/{total_chunks}")

            if not chunk_summaries:
                return "Ei onnistuttu luomaan tiivistelmä."

            # Then combine summaries into sections (max 3 chunks per section for better coherence)
            section_summaries = []
            section_size = 3
            num_sections = (len(chunk_summaries) + section_size - 1) // section_size
            logger.debug(f"Creating {num_sections} section summaries")

            for i in range(0, len(chunk_summaries), section_size):
                section = chunk_summaries[i : i + section_size]
                section_text = " ".join(section)

                prompt = f"""Tiivistä seuraava tekstiosio yhtenäiseksi kappaleeksi säilyttäen tärkeimmät asiat:

                {section_text}
                """
                summary = self.model_tool.process(prompt, task_type="summarization")
                if summary:
                    section_summaries.append(summary)
                logger.debug(
                    f"Created section summary {len(section_summaries)}/{num_sections}"
                )

            # Finally create the complete summary
            length_guide = {
                "lyhyt": "noin 150 sanan",
                "keskipitkä": "noin 300 sanan",
                "pitkä": "noin 600 sanan",
            }.get(target_length, "ytimekkään")

            final_prompt = f"""Luo {length_guide} tiivistelmä alla olevasta tekstistä.
            Säilytä tärkeimmät asiat ja varmista että tiivistelmä on yhtenäinen, selkeä ja loogisesti etenevä.
            Keskity olennaisiin faktoihin ja pääkohtiin.
            
            {" ".join(section_summaries)}
            """

            logger.debug("Creating final summary")
            final_summary = self.model_tool.process(
                final_prompt, task_type="summarization"
            )
            return final_summary or "Tiivistelmän luonti epäonnistui."

        except Exception as e:
            logger.error(f"Error in hierarchical summarization: {str(e)}")
            return f"Error in hierarchical summarization: {str(e)}"

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant content"""
        try:
            results = self.backend.search(query, top_k=top_k)

            # Jos viimeksi ladattu tiedosto on tiedossa ja tuloksia löytyy
            if self.last_uploaded_file and results:
                # Järjestä tulokset niin että viimeksi ladatun tiedoston tulokset ovat ensin
                results.sort(
                    key=lambda x: (
                        x["record"]["meta"].get("source", "")
                        != self.last_uploaded_file,
                        -x["distance"],  # Säilytä etäisyysjärjestys muuten
                    )
                )

            return results
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []

    def _semantic_search_fallback(
        self, query: str, chunks: List[str], top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """Semantic search fallback using direct tensor operations"""
        try:
            # Encode query
            query_embedding = self.model.encode([query], convert_to_tensor=True)
            query_embedding = query_embedding.squeeze(0)
            query_embedding = query_embedding / query_embedding.norm()

            # Encode all chunks
            chunk_embeddings = self.model.encode(chunks, convert_to_tensor=True)
            chunk_embeddings = chunk_embeddings / chunk_embeddings.norm(
                dim=1, keepdim=True
            )

            # Calculate similarities
            similarities = torch.matmul(chunk_embeddings, query_embedding)

            # Get top k indices and scores
            top_k = min(top_k, len(chunks))
            scores, indices = similarities.topk(top_k)

            return [(idx.item(), score.item()) for idx, score in zip(indices, scores)]

        except Exception as e:
            logger.error(f"Semantic search fallback error: {str(e)}")
            return []

    def _get_chunks_from_metadata(self) -> List[str]:
        """Get all chunks from metadata"""
        chunks = []
        for item in self.backend.metadata:
            content = item.get("content", "")
            if isinstance(content, str) and content.strip():
                chunks.append(content)
        return chunks

    def summarize(self, target_length: str = "lyhyt") -> Dict[str, Any]:
        """Create a summary of the loaded document"""
        try:
            if not self.has_documents():
                return {
                    "response": "Ei dokumentteja indeksissä. Lataa ensin dokumentti.",
                    "success": False,
                }

            # Get all chunks from the latest document
            latest_chunks = []
            latest_doc_id = None
            latest_filename = None

            # Find the latest document ID and filename
            for item in reversed(self.backend.metadata):
                if latest_doc_id is None:
                    latest_doc_id = item.get("parent_id")
                    latest_filename = item.get("meta", {}).get("filename", "unknown")

                if item.get("parent_id") == latest_doc_id:
                    content = item.get("content", "").strip()
                    if content:  # Only add non-empty chunks
                        latest_chunks.append(
                            {
                                "content": content,
                                "meta": item.get("meta", {}),
                                "chunk_index": item.get("meta", {}).get(
                                    "chunk_index", 0
                                ),
                            }
                        )

            if not latest_chunks:
                return {
                    "response": "Ei löytynyt sisältöä tiivistettäväksi.",
                    "success": False,
                }

            # Sort chunks by their index to maintain document order
            latest_chunks.sort(key=lambda x: x["chunk_index"])

            logger.debug(
                f"Creating summary for document {latest_filename} with {len(latest_chunks)} chunks"
            )

            # Create hierarchical summary with progress tracking
            summary = self._hierarchical_summarize(latest_chunks, target_length)

            return {
                "response": summary,
                "success": True,
                "metadata": {
                    "doc_id": latest_doc_id,
                    "filename": latest_filename,
                    "num_chunks": len(latest_chunks),
                    "timestamp": time.time(),
                },
            }

        except Exception as e:
            logger.error(f"Error creating summary: {str(e)}")
            return {
                "response": f"Error creating summary: {str(e)}",
                "success": False,
            }

    def _fast_summarize(self, chunks: List[Dict], target_length: str = "lyhyt") -> str:
        """Create a fast summary using SBERT and clustering for smart chunk selection"""
        try:
            # Get all chunk contents - varmista että käsitellään tekstiä oikein
            texts = []
            for chunk in chunks:
                if isinstance(chunk, dict):
                    content = chunk.get("content", "")
                else:
                    content = str(chunk)
                if content.strip():
                    texts.append(content)

            if not texts:
                return "Ei löytynyt sisältöä tiivistettäväksi."

            # Create embeddings for all chunks
            chunk_embeddings = self._compute_embeddings(texts)
            chunk_embeddings_np = chunk_embeddings.cpu().numpy()
            faiss.normalize_L2(chunk_embeddings_np)

            # Määritä klusterien määrä dokumentin pituuden mukaan
            n_clusters = min(5, len(texts) // 2)  # Max 5 klusteria
            if n_clusters < 2:
                n_clusters = 2

            # Klusteroi chunkit
            kmeans = faiss.Kmeans(
                d=chunk_embeddings_np.shape[1], k=n_clusters, niter=20
            )
            kmeans.train(chunk_embeddings_np)
            _, cluster_labels = kmeans.index.search(chunk_embeddings_np, 1)

            # Valitse edustavimmat chunkit jokaisesta klusterista
            selected_chunks = []
            for i in range(n_clusters):
                # Hae klusterin chunkit
                cluster_indices = np.where(cluster_labels.flatten() == i)[0]
                if len(cluster_indices) == 0:
                    continue

                # Laske etäisyydet klusterin keskipisteeseen
                cluster_center = kmeans.centroids[i].reshape(1, -1)
                cluster_embeddings = chunk_embeddings_np[cluster_indices]
                distances = np.linalg.norm(cluster_embeddings - cluster_center, axis=1)

                # Valitse lähin chunkki (edustavin)
                best_idx = cluster_indices[np.argmin(distances)]
                selected_chunks.append(texts[best_idx])

            if not selected_chunks:
                return "Ei onnistuttu löytämään keskeistä sisältöä."

            # Järjestä chunkit alkuperäiseen järjestykseen
            selected_indices = [texts.index(chunk) for chunk in selected_chunks]
            selected_chunks = [
                x for _, x in sorted(zip(selected_indices, selected_chunks))
            ]

            # Yhdistä valitut chunkit
            combined_text = "\n\n".join(selected_chunks)

            # Create length guide based on target
            length_guide = {
                "lyhyt": "noin 50 sanan",
                "keskipitkä": "noin 150 sanan",
                "pitkä": "noin 300 sanan",
            }.get(target_length, "ytimekkään")

            # Create single summary with one model call
            prompt = f"""Luo TASAN {length_guide} tiivistelmä alla olevasta tekstistä.
            Säilytä tärkeimmät asiat ja varmista että tiivistelmä on yhtenäinen, selkeä ja loogisesti etenevä.
            Keskity olennaisiin faktoihin ja pääkohtiin.
            ÄLÄ YLITÄ PYYDETTYÄ SANAMÄÄRÄÄ.
            
            Laske sanamäärä ennen vastaamista ja varmista että se on tasan pyydetty määrä.
            
            {combined_text}
            
            Vastaa muodossa:
            [Sanamäärä: X]
            [Tiivistelmä]
            """

            summary = self.model_tool.process(prompt, task_type="summarization")

            # Poista sanamäärä vastauksesta jos se on mukana
            if summary and "[Sanamäärä:" in summary:
                summary = summary.split("]", 1)[-1].strip()

            return summary or "Tiivistelmän luonti epäonnistui."

        except Exception as e:
            logger.error(f"Error in fast summarization: {str(e)}")
            return f"Error in fast summarization: {str(e)}"

    def check_and_reindex_files(self, progress_callback=None) -> Dict[str, Any]:
        """Check saved_files directory and reindex if needed"""
        try:
            # Get current files in directory
            current_files = set(self.backend.get_saved_files())

            # Get indexed files from metadata
            indexed_files = set()
            for meta in self.backend.metadata:
                if isinstance(meta, dict) and "meta" in meta:
                    meta_data = meta.get("meta", {})
                    if isinstance(meta_data, dict):
                        filename = meta_data.get("filename")
                        if filename:
                            indexed_files.add(filename)

            # Find files that need indexing
            files_to_index = current_files - indexed_files
            files_to_remove = indexed_files - current_files

            # First show status of all files
            if progress_callback:
                for filename in sorted(current_files):
                    status = (
                        "Already indexed"
                        if filename in indexed_files
                        else "Not indexed"
                    )
                    progress_callback(0, f"{filename}: {status}")

            if not files_to_index and not files_to_remove:
                return {
                    "status": "up_to_date",
                    "message": "Index is up to date.",
                    "indexed_files": len(indexed_files),
                    "current_files": len(current_files),
                }

            # Reset index if files need to be removed
            if files_to_remove:
                logger.info(f"Removing {len(files_to_remove)} files from index")
                self.backend.reset_index()
                indexed_files = set()
                files_to_index = current_files

            # Index new files
            total_files = len(files_to_index)
            for i, filename in enumerate(sorted(files_to_index), 1):
                if progress_callback:
                    progress_callback(0, f"Indexing {filename}...")

                try:
                    file_content = self.backend.load_file(filename)
                    if file_content:
                        start_time = time.time()
                        self.add_document(
                            document=file_content,
                            doc_id=f"saved-{filename}",
                            file_type="pdf"
                            if filename.lower().endswith(".pdf")
                            else "text",
                            extra_meta={"filename": filename},
                        )
                        end_time = time.time()
                        if progress_callback:
                            progress_callback(
                                1.0,
                                f"Completed indexing: {filename} ({(end_time - start_time):.2f}s)",
                            )
                        logger.info(f"Indexed: {filename}")
                except Exception as e:
                    logger.error(f"Error indexing file {filename}: {str(e)}")

            return {
                "status": "reindexed",
                "message": f"Indexed {len(files_to_index)} new files.",
                "indexed_files": len(current_files),
                "current_files": len(current_files),
            }

        except Exception as e:
            logger.error(f"Error checking index: {str(e)}")
            return {
                "status": "error",
                "message": f"Error checking index: {str(e)}",
                "error": str(e),
            }

    def semantic_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar content"""
        try:
            # Get query embedding
            query_embedding = self.embedding_model.encode([query])

            # Ensure query embedding is the right shape and type
            query_embedding = np.ascontiguousarray(query_embedding, dtype=np.float32)

            # Normalize the embedding
            faiss.normalize_L2(query_embedding)

            # Search
            D, I = self.backend.index.search(query_embedding, k)

            # Get results
            results = []
            for score, idx in zip(D[0], I[0]):
                if idx >= len(self.backend.metadata) or idx < 0:
                    continue

                metadata = self.backend.metadata[idx]
                if not isinstance(metadata, dict):
                    continue

                result = {
                    "content": metadata.get("content", ""),
                    "meta": metadata.get("meta", {}),
                    "distance": float(score),
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def list_saved_files(self) -> dict:
        """List all saved files with their metadata"""
        try:
            # Get all unique filenames from metadata
            files_info = {}
            for record in self.backend.metadata:
                if isinstance(record, dict):
                    meta = record.get("meta", {})
                    filename = meta.get("filename")
                    if filename:
                        if filename not in files_info:
                            files_info[filename] = {
                                "filename": filename,
                                "timestamp": meta.get("timestamp", 0),
                                "chunk_count": 1,
                                "type": meta.get("type", "unknown"),
                                "chunks": [record.get("content", "")],
                                "size": 0,  # Will be updated from file system
                                "is_indexed": True,
                            }
                        else:
                            files_info[filename]["chunk_count"] += 1
                            files_info[filename]["chunks"].append(
                                record.get("content", "")
                            )

            # Get file sizes from file system
            saved_files_dir = os.path.join("agentformer", "saved_files")
            if os.path.exists(saved_files_dir):
                for filename in os.listdir(saved_files_dir):
                    file_path = os.path.join(saved_files_dir, filename)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        if filename in files_info:
                            files_info[filename]["size"] = size
                        else:
                            files_info[filename] = {
                                "filename": filename,
                                "timestamp": os.path.getctime(file_path),
                                "chunk_count": 0,
                                "type": "unknown",
                                "chunks": [],
                                "size": size,
                                "is_indexed": False,
                            }

            # Generate summaries for each file
            for file_info in files_info.values():
                if file_info["chunks"]:
                    # Use first few chunks for summary
                    summary_text = "\n".join(file_info["chunks"][:3])
                    prompt = f"""Create a brief summary (max 2-3 sentences) of this document based on the following excerpt:

                    {summary_text}"""
                    try:
                        model_tool = ModelTool()
                        summary = model_tool.process(prompt, task_type="summarization")
                        file_info["summary"] = summary
                    except Exception as e:
                        logger.error(f"Error generating summary: {str(e)}")
                        file_info["summary"] = "Summary not available"
                else:
                    file_info["summary"] = "File not indexed"

                # Clean up chunks to save memory
                file_info.pop("chunks", None)

            # Convert to list and sort by timestamp
            files_list = list(files_info.values())
            files_list.sort(key=lambda x: x["timestamp"], reverse=True)

            return {"status": "success", "files": files_list}

        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return {"status": "error", "error": str(e)}
