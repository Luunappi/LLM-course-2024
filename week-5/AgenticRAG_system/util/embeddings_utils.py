import torch
from typing import List


def embeddings_to_tensor(embeddings: List[List[float]]) -> torch.Tensor:
    """
    Muuntaa embedding-listan PyTorch tensoriksi.

    Args:
        embeddings: Lista embedding-vektoreista (lista listoja)

    Returns:
        torch.Tensor: Embedding-tensori
    """
    return torch.tensor(embeddings, dtype=torch.float32)


def normalize_embeddings(embeddings: torch.Tensor) -> torch.Tensor:
    """
    Normalisoi embedding-vektorit.

    Args:
        embeddings: Embedding-tensori

    Returns:
        torch.Tensor: Normalisoidut embeddings
    """
    return torch.nn.functional.normalize(embeddings, p=2, dim=1)
