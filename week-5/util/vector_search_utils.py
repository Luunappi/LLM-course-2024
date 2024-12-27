import torch
from sentence_transformers import util, SentenceTransformer
from time import perf_counter as timer
import textwrap

def print_wrapped(text, wrap_length=80):
    """Tulostaa tekstin rivitettynä"""
    wrapped_text = textwrap.fill(text, wrap_length)
    print(wrapped_text)

def retrieve_relevant_resources(
    query: str, 
    embeddings: torch.Tensor, 
    model: SentenceTransformer,
    st,
    n_results: int = 5
) -> tuple[list[float], list[int]]:
    """Hakee relevanteimmat tekstit vektoriavaruudesta
    
    Args:
        query: Hakuteksti
        embeddings: Dokumenttien embeddings-tensori
        model: SentenceTransformer-malli
        st: Streamlit-konteksti
        n_results: Palautettavien tulosten määrä
        
    Returns:
        tuple: (pisteet, indeksit)
    """
    # Laske query embedding
    start_time = timer()
    query_embedding = model.encode(query, convert_to_tensor=True)
    
    # Siirrä embeddings samalle laitteelle
    device = query_embedding.device
    embeddings = embeddings.to(device)
    
    # Laske pistetulot
    dot_scores = util.dot_score(query_embedding, embeddings)[0]
    
    # Siirrä tulokset CPU:lle ja järjestä
    dot_scores = dot_scores.cpu()
    scores_with_indices = [(score.item(), idx) for idx, score in enumerate(dot_scores)]
    scores_with_indices.sort(key=lambda x: x[0], reverse=True)
    
    # Valitse top-n tulokset
    scores = [score for score, _ in scores_with_indices[:n_results]]
    indices = [idx for _, idx in scores_with_indices[:n_results]]
    
    # Näytä suoritusaika
    end_time = timer()
    st.write(f"Search time: {end_time-start_time:.3f}s for {len(embeddings)} documents")
    
    return scores, indices

def print_top_results(
    query: str,
    embeddings: torch.Tensor,
    chunks: list[dict],
    model: SentenceTransformer,
    n_results: int = 5
) -> None:
    """Tulostaa hakutulokset
    
    Args:
        query: Hakuteksti
        embeddings: Dokumenttien embeddings
        chunks: Dokumenttien tekstit ja metatiedot
        model: SentenceTransformer-malli
        n_results: Tulostettavien tulosten määrä
    """
    scores, indices = retrieve_relevant_resources(
        query=query,
        embeddings=embeddings,
        model=model,
        st=None,
        n_results=n_results
    )

    print(f"\nQuery: {query}\n")
    print("Results:")
    for score, idx in zip(scores, indices):
        print(f"Score: {score:.4f}")
        print_wrapped(chunks[idx]["sentence_chunk"])
        print(f"Page: {chunks[idx]['page_number']}\n")