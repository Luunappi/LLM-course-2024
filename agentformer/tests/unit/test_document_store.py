"""Tests for document store functionality.

This module tests:
1. Document storage and retrieval
2. Metadata management
3. Version control
4. Storage optimization
"""

import pytest
import os
import json
from agentformer.tools.memory_tools import DocumentStore


@pytest.fixture
def document_store(tmp_path):
    """Create a document store instance for testing."""
    store = DocumentStore(storage_dir=str(tmp_path))
    return store


def test_store_document(document_store):
    """Test storing and retrieving documents."""
    # Create test document
    content = "This is a test document."
    metadata = {"type": "text", "author": "test"}

    # Store document
    doc_id = document_store.store(content, metadata)

    # Retrieve document
    retrieved = document_store.get(doc_id)

    # Verify storage
    assert retrieved.content == content
    assert retrieved.metadata == metadata
    assert retrieved.id == doc_id


def test_document_versioning(document_store):
    """Test document version control."""
    # Store initial version
    content_v1 = "Initial version"
    doc_id = document_store.store(content_v1)

    # Update document
    content_v2 = "Updated version"
    document_store.update(doc_id, content_v2)

    # Get latest version
    latest = document_store.get(doc_id)
    assert latest.content == content_v2

    # Get version history
    history = document_store.get_history(doc_id)
    assert len(history) == 2
    assert history[0].content == content_v1


def test_metadata_management(document_store):
    """Test metadata management."""
    # Store document with metadata
    content = "Test document"
    initial_metadata = {"type": "text", "tags": ["test"]}
    doc_id = document_store.store(content, initial_metadata)

    # Update metadata
    new_metadata = {"type": "text", "tags": ["test", "updated"], "status": "reviewed"}
    document_store.update_metadata(doc_id, new_metadata)

    # Verify metadata
    doc = document_store.get(doc_id)
    assert doc.metadata == new_metadata


def test_batch_operations(document_store):
    """Test batch document operations."""
    # Create test documents
    documents = [
        ("Doc 1", {"type": "text"}),
        ("Doc 2", {"type": "text"}),
        ("Doc 3", {"type": "text"}),
    ]

    # Store batch
    doc_ids = document_store.store_batch(
        [d[0] for d in documents], [d[1] for d in documents]
    )

    # Retrieve batch
    retrieved = document_store.get_batch(doc_ids)

    # Verify batch operations
    assert len(retrieved) == len(documents)
    for i, doc in enumerate(retrieved):
        assert doc.content == documents[i][0]
        assert doc.metadata == documents[i][1]


def test_document_deletion(document_store):
    """Test document deletion."""
    # Store document
    doc_id = document_store.store("Test document")

    # Delete document
    document_store.delete(doc_id)

    # Verify deletion
    assert document_store.get(doc_id) is None


def test_storage_cleanup(document_store):
    """Test storage cleanup functionality."""
    # Store multiple documents
    doc_ids = []
    for i in range(10):
        doc_id = document_store.store(f"Document {i}")
        doc_ids.append(doc_id)

    # Mark some as deletable
    for doc_id in doc_ids[:5]:
        document_store.mark_deletable(doc_id)

    # Run cleanup
    deleted_count = document_store.cleanup()

    # Verify cleanup
    assert deleted_count == 5
    for doc_id in doc_ids[:5]:
        assert document_store.get(doc_id) is None
    for doc_id in doc_ids[5:]:
        assert document_store.get(doc_id) is not None


def test_document_search(document_store):
    """Test document search functionality."""
    # Store documents with searchable content
    doc1_id = document_store.store("Python programming guide", {"type": "tutorial"})
    doc2_id = document_store.store("Java programming guide", {"type": "tutorial"})
    doc3_id = document_store.store("Python data science", {"type": "article"})

    # Search documents
    results = document_store.search("Python")

    # Verify search results
    assert len(results) == 2
    assert any(r.id == doc1_id for r in results)
    assert any(r.id == doc3_id for r in results)


def test_storage_persistence(tmp_path):
    """Test document store persistence."""
    # Create store and add documents
    store1 = DocumentStore(storage_dir=str(tmp_path))
    doc_id = store1.store("Test document", {"type": "text"})

    # Create new store instance with same storage
    store2 = DocumentStore(storage_dir=str(tmp_path))

    # Verify document persistence
    doc = store2.get(doc_id)
    assert doc is not None
    assert doc.content == "Test document"


if __name__ == "__main__":
    pytest.main([__file__])
