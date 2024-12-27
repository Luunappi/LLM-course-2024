import torch
from sentence_transformers import SentenceTransformer


def retrieve_relevant_resources(
    query: str, embeddings: torch.Tensor, model: SentenceTransformer, top_k: int = 5
):
    """
    Hakee relevanteimmat dokumentit query-embeddingin perusteella.

    Args:
        query: Hakukysely tekstinä
        embeddings: Dokumenttien embedding-tensori
        model: SentenceTransformer-malli embeddingin luomiseen
        top_k: Palautettavien dokumenttien määrä

    Returns:
        tuple: (scores, indices) - relevanssi-pisteet ja indeksit
    """
    # Muunna kysely embedding-vektoriksi
    query_embedding = model.encode(query)
    query_embedding = torch.tensor(query_embedding).unsqueeze(0)

    # Laske kosinietäisyydet
    cos = torch.nn.CosineSimilarity(dim=1)
    scores = cos(query_embedding, embeddings)

    # Hae top-k tulokset
    top_scores, top_indices = torch.topk(scores, min(top_k, len(scores)))

    return top_scores.tolist(), top_indices.tolist()
