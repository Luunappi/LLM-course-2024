"""Tests for document summarization functionality.

This module tests:
1. Basic text summarization
2. Hierarchical summarization
3. Clustering-based summarization
4. Length control
5. Caching functionality
6. Error handling
"""

import pytest
import os
import shutil
from agentformer.tools.memory_tools import DocumentSummarizer, SummaryConfig


@pytest.fixture
def config():
    """Create a test configuration."""
    return SummaryConfig(
        max_length=200,
        min_length=50,
        num_clusters=3,
        hierarchical_levels=2,
        cache_dir="tests/cache/summaries",
        show_progress=False,  # Disable progress output in tests
    )


@pytest.fixture
def summarizer(config):
    """Create a document summarizer instance for testing."""
    # Clean up test cache directory
    if os.path.exists(config.cache_dir):
        shutil.rmtree(config.cache_dir)
    os.makedirs(config.cache_dir)

    return DocumentSummarizer(config)


def test_basic_summarization(summarizer):
    """Test basic text summarization."""
    # Test text
    text = """
    Machine learning is a field of artificial intelligence that focuses on developing
    systems that can learn from and make decisions based on data. It enables computers
    to improve their performance on a specific task through experience. Deep learning,
    a subset of machine learning, uses artificial neural networks to learn from large
    amounts of data. Neural networks are designed to mimic the way the human brain works,
    with interconnected nodes that process and transmit information.
    """

    # Generate summary
    summary = summarizer.summarize(text)

    # Verify summary
    assert summary is not None
    assert len(summary) > 0
    assert len(summary.split()) <= summarizer.config.max_length
    assert len(summary.split()) >= summarizer.config.min_length


def test_caching(summarizer):
    """Test summary caching functionality."""
    text = "This is a test text that should be cached after summarization."

    # First call should generate and cache
    summary1 = summarizer.summarize(text)

    # Second call should use cache
    summary2 = summarizer.summarize(text)

    # Summaries should be identical
    assert summary1 == summary2

    # Verify cache file exists
    cache_key = summarizer._get_cache_key(text)
    cache_path = summarizer._get_cache_path(cache_key)
    assert os.path.exists(cache_path)


def test_error_handling(summarizer):
    """Test error handling in summarization."""
    # Test with None input
    assert summarizer.summarize(None) == ""

    # Test with empty string
    assert summarizer.summarize("") == ""

    # Test with empty list
    assert summarizer.summarize([]) == ""


def test_hierarchical_error_handling(summarizer):
    """Test error handling in hierarchical summarization."""
    # Test with empty input
    result = summarizer.summarize_hierarchical("")
    assert result["main"] == ""
    assert result["sections"] == []

    # Test with None input
    result = summarizer.summarize_hierarchical(None)
    assert result["main"] == ""
    assert result["sections"] == []


def test_clustering_error_handling(summarizer):
    """Test error handling in clustering summarization."""
    # Test with empty input
    assert summarizer.summarize_by_clustering([]) == ""

    # Test with None input
    assert summarizer.summarize_by_clustering(None) == ""

    # Test with single text
    text = "Single text for clustering"
    assert summarizer.summarize_by_clustering([text]) == text


def test_section_splitting_error_handling(summarizer):
    """Test error handling in section splitting."""
    # Test with empty input
    assert summarizer._split_into_sections("") == []

    # Test with None input
    assert summarizer._split_into_sections(None) == []

    # Test with invalid input type
    assert summarizer._split_into_sections(123) == ["123"]


def test_custom_model_loading(tmp_path):
    """Test loading custom summarization model."""
    config = SummaryConfig(
        model_name="facebook/bart-base",  # Use smaller model for testing
        cache_dir=str(tmp_path / "summaries"),
    )

    summarizer = DocumentSummarizer(config)
    assert summarizer.summarizer is not None


def test_progress_tracking(config):
    """Test progress tracking in hierarchical summarization."""
    # Enable progress tracking
    config.show_progress = True
    summarizer = DocumentSummarizer(config)

    # Test text with multiple sections
    text = """
    Section 1
    First section content.

    Section 2
    Second section content.

    Section 3
    Third section content.
    """

    # Should not raise any errors when showing progress
    result = summarizer.summarize_hierarchical(text)
    assert result["main"] is not None
    assert len(result["sections"]) > 0


def test_cleanup(summarizer, tmp_path):
    """Test cleanup after tests."""
    # Clean up test cache directory
    if os.path.exists(summarizer.config.cache_dir):
        shutil.rmtree(summarizer.config.cache_dir)


if __name__ == "__main__":
    pytest.main([__file__])
