import pytest
import numpy as np
import torch
from agentic.rag import Retriever
from unittest.mock import MagicMock, patch


@pytest.fixture
async def get_mock_retriever():
    """Fixture for Retriever testing with mocked embeddings"""
    mock_tokenizer = MagicMock()
    mock_model = MagicMock()

    # Määritellään vakiokoot E5-mallin mukaan
    BATCH_SIZE = 1
    SEQ_LENGTH = 10
    HIDDEN_SIZE = 768

    # Mock tokenizer output
    mock_inputs = {
        "input_ids": torch.ones((BATCH_SIZE, SEQ_LENGTH)),
        "attention_mask": torch.ones((BATCH_SIZE, SEQ_LENGTH)),
    }
    mock_tokenizer.return_value = mock_inputs

    # Mock model output
    mock_hidden_state = torch.ones((BATCH_SIZE, SEQ_LENGTH, HIDDEN_SIZE))

    class MockOutput:
        def __init__(self):
            self.last_hidden_state = mock_hidden_state

        def to(self, device):
            return self

    mock_output = MockOutput()
    mock_model.return_value = mock_output

    # Mock tensor operations
    mock_attention_mask = mock_inputs["attention_mask"]

    # Simuloidaan mean pooling operaatiot
    expanded_mask = torch.ones((BATCH_SIZE, SEQ_LENGTH, HIDDEN_SIZE))
    mock_attention_mask.unsqueeze.return_value = torch.ones((BATCH_SIZE, SEQ_LENGTH, 1))
    mock_attention_mask.expand.return_value = expanded_mask

    # Mock muut tensor operaatiot
    for tensor in mock_inputs.values():
        tensor.to = MagicMock(return_value=tensor)
        tensor.float = MagicMock(return_value=tensor)
        tensor.cpu = MagicMock(return_value=tensor)
        tensor.unsqueeze = MagicMock(
            return_value=torch.ones((BATCH_SIZE, SEQ_LENGTH, 1))
        )
        tensor.expand = MagicMock(return_value=expanded_mask)

    mock_model.to = MagicMock(return_value=mock_model)

    with (
        patch(
            "transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer
        ),
        patch("transformers.AutoModel.from_pretrained", return_value=mock_model),
        patch("torch.cuda.is_available", return_value=False),
    ):
        ret = Retriever()
        await ret.initialize()
        return ret


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retriever_embedding(get_mock_retriever):
    """Test embedding generation"""
    retriever = get_mock_retriever
    embedding = retriever._get_embedding("test text")

    # Tarkista embedding
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (768,)  # E5 embedding koko
    assert not np.any(np.isnan(embedding))  # Ei NaN arvoja
    assert np.all(np.isfinite(embedding))  # Kaikki arvot äärellisiä


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retriever_chunking(get_mock_retriever):
    """Test text chunking"""
    retriever = get_mock_retriever
    chunks = retriever._chunk_text("test " * 1000)
    assert all(len(chunk.split()) <= 512 for chunk in chunks)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retriever_empty_chunking(get_mock_retriever):
    """Test chunking with edge cases"""
    retriever = get_mock_retriever

    # Test empty text
    empty_chunks = retriever._chunk_text("")
    assert len(empty_chunks) == 0

    # Test single word
    single_chunks = retriever._chunk_text("test")
    assert len(single_chunks) == 1
    assert single_chunks[0] == "test"

    # Test exactly chunk_size
    words = ["test"] * 512
    exact_chunks = retriever._chunk_text(" ".join(words), chunk_size=512)
    assert len(exact_chunks) == 1
    assert len(exact_chunks[0].split()) == 512
