"""Tests for vector store functionality.

This module tests:
1. Vector storage and retrieval
2. Similarity search
3. Metadata management
4. Index optimization
"""

import pytest
import numpy as np
from agentformer.tools.memory_tools import VectorStore


@pytest.fixture
def vector_store():
    """Create a vector store instance for testing."""
    return VectorStore()


def test_add_vector(vector_store):
    """Test adding vectors to the store."""
    # Create test vector
    vector = np.random.rand(384)  # Default dimension for sentence-transformers
    metadata = {"text": "Test document", "timestamp": 123456789}

    # Add to store
    doc_id = vector_store.add_vector("test1", vector, metadata)

    # Verify addition
    assert doc_id == "test1"
    stored = vector_store.get_vector("test1")
    assert stored is not None
    assert np.allclose(stored.vector, vector)
    assert stored.metadata == metadata


def test_batch_add_vectors(vector_store):
    """Test adding multiple vectors at once."""
    # Create test vectors
    vectors = [np.random.rand(384) for _ in range(3)]
    ids = [f"test{i}" for i in range(3)]
    metadata = [{"text": f"Test {i}"} for i in range(3)]

    # Add to store
    vector_store.add_vectors(ids, vectors, metadata)

    # Verify addition
    for i, doc_id in enumerate(ids):
        stored = vector_store.get_vector(doc_id)
        assert stored is not None
        assert np.allclose(stored.vector, vectors[i])
        assert stored.metadata == metadata[i]


def test_similarity_search(vector_store):
    """Test similarity search functionality."""
    # Add test vectors
    vectors = [np.random.rand(384) for _ in range(5)]
    ids = [f"test{i}" for i in range(5)]
    metadata = [{"text": f"Test {i}"} for i in range(5)]
    vector_store.add_vectors(ids, vectors, metadata)

    # Perform search
    query_vector = vectors[0] + np.random.normal(
        0, 0.1, 384
    )  # Slightly modified first vector
    results = vector_store.search(query_vector, k=3)

    # Verify results
    assert len(results) == 3
    assert results[0].id == "test0"  # Most similar should be the original vector


def test_vector_removal(vector_store):
    """Test removing vectors from the store."""
    # Add test vector
    vector = np.random.rand(384)
    vector_store.add_vector("test1", vector, {"text": "Test"})

    # Remove vector
    vector_store.remove_vector("test1")

    # Verify removal
    stored = vector_store.get_vector("test1")
    assert stored is None


def test_index_optimization(vector_store):
    """Test index optimization."""
    # Add many test vectors
    vectors = [np.random.rand(384) for _ in range(100)]
    ids = [f"test{i}" for i in range(100)]
    metadata = [{"text": f"Test {i}"} for i in range(100)]
    vector_store.add_vectors(ids, vectors, metadata)

    # Optimize index
    vector_store.optimize_index()

    # Verify search still works
    query_vector = np.random.rand(384)
    results = vector_store.search(query_vector, k=5)
    assert len(results) == 5


def test_metadata_update(vector_store):
    """Test updating vector metadata."""
    # Add test vector
    vector = np.random.rand(384)
    vector_store.add_vector("test1", vector, {"text": "Original"})

    # Update metadata
    new_metadata = {"text": "Updated", "new_field": 123}
    vector_store.update_metadata("test1", new_metadata)

    # Verify update
    stored = vector_store.get_vector("test1")
    assert stored.metadata == new_metadata


if __name__ == "__main__":
    pytest.main([__file__])
