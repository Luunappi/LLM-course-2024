"""Tests for document processing components.

This module tests:
1. Document chunking
2. Text embedding
3. Document summarization
4. Processing pipeline integration
"""

import pytest
from agentformer.tools.memory_tools import (
    DocumentChunker,
    TextEmbedder,
    DocumentSummarizer,
    ChunkConfig,
    EmbedderConfig,
    SummaryConfig,
)


@pytest.fixture
def chunker():
    """Create a document chunker instance for testing."""
    config = ChunkConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=50)
    return DocumentChunker(config)


@pytest.fixture
def embedder():
    """Create a text embedder instance for testing."""
    config = EmbedderConfig(model_name="all-MiniLM-L6-v2", batch_size=8)
    return TextEmbedder(config)


@pytest.fixture
def summarizer():
    """Create a document summarizer instance for testing."""
    config = SummaryConfig(max_length=200, min_length=50, num_clusters=3)
    return DocumentSummarizer(config)


def test_document_chunking(chunker):
    """Test document chunking functionality."""
    # Create test document
    document = " ".join(["word" for _ in range(500)])  # Long document

    # Chunk document
    chunks = chunker.chunk_text(document)

    # Verify chunks
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= chunker.config.chunk_size
        assert len(chunk) >= chunker.config.min_chunk_size


def test_chunk_overlap(chunker):
    """Test chunk overlap functionality."""
    # Create test document with distinct sections
    sections = ["Section1 " * 20, "Section2 " * 20, "Section3 " * 20]
    document = " ".join(sections)

    # Chunk document
    chunks = chunker.chunk_text(document)

    # Verify overlap
    for i in range(len(chunks) - 1):
        overlap = set(chunks[i].split()).intersection(set(chunks[i + 1].split()))
        assert len(overlap) > 0


def test_text_embedding(embedder):
    """Test text embedding functionality."""
    # Create test texts
    texts = [
        "This is the first test document.",
        "Here is another document for testing.",
        "And a third one to make it interesting.",
    ]

    # Generate embeddings
    embeddings = embedder.embed_texts(texts)

    # Verify embeddings
    assert len(embeddings) == len(texts)
    assert all(len(embedding) == 384 for embedding in embeddings)  # Default dimension


def test_embedding_batching(embedder):
    """Test batch processing of embeddings."""
    # Create many test texts
    texts = [f"Test document number {i}" for i in range(20)]

    # Generate embeddings
    embeddings = embedder.embed_texts(texts)

    # Verify all texts were embedded
    assert len(embeddings) == len(texts)


def test_document_summarization(summarizer):
    """Test document summarization functionality."""
    # Create test document
    paragraphs = [
        "Machine learning is a field of artificial intelligence.",
        "It focuses on developing systems that can learn from data.",
        "Deep learning is a subset of machine learning.",
        "Neural networks are key to deep learning approaches.",
        "Training data is essential for machine learning models.",
    ]
    document = " ".join(paragraphs)

    # Generate summary
    summary = summarizer.summarize(document)

    # Verify summary
    assert summary is not None
    assert len(summary) <= summarizer.config.max_length
    assert len(summary) >= summarizer.config.min_length


def test_hierarchical_summarization(summarizer):
    """Test hierarchical summarization functionality."""
    # Create test document with sections
    sections = [
        "First major topic with several sentences about machine learning. " * 5,
        "Second topic covering neural networks in detail. " * 5,
        "Third topic about training methodologies and best practices. " * 5,
    ]
    document = "\n\n".join(sections)

    # Generate hierarchical summary
    summary = summarizer.summarize_hierarchical(document)

    # Verify hierarchical summary
    assert len(summary) > 0
    assert isinstance(summary, dict)
    assert "main" in summary
    assert "sections" in summary


def test_processing_pipeline():
    """Test integration of processing components."""
    # Create instances
    chunker = DocumentChunker(ChunkConfig())
    embedder = TextEmbedder(EmbedderConfig())
    summarizer = DocumentSummarizer(SummaryConfig())

    # Create test document
    document = "Long document about machine learning. " * 50

    # Process document
    chunks = chunker.chunk_text(document)
    embeddings = embedder.embed_texts(chunks)
    summary = summarizer.summarize(" ".join(chunks[:3]))  # Summarize first few chunks

    # Verify pipeline results
    assert len(chunks) > 0
    assert len(embeddings) == len(chunks)
    assert summary is not None


if __name__ == "__main__":
    pytest.main([__file__])
