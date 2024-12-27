import torch
from stqdm import stqdm

def embed_chunks(df, model, batch_size=32):
    """Embed text chunks using the given model.
    
    Args:
        df: DataFrame containing text chunks
        model: SentenceTransformer model
        batch_size: Number of chunks to embed at once
        
    Returns:
        list: List of embeddings
    """
    embeddings = []
    chunks = df['sentence_chunk'].tolist()  # Get chunks as list
    
    # Process in batches
    for i in stqdm(range(0, len(chunks), batch_size)):
        batch = chunks[i:i + batch_size]
        batch_embeddings = model.encode(batch)
        embeddings.extend(batch_embeddings)
    
    return embeddings

def save_embeddings(embeddings, filename):
    """Save embeddings to a file.
    
    Args:
        embeddings: List of embeddings
        filename: Path to save file
    """
    torch.save(embeddings, filename)

def embeddings_to_tensor(embeddings):
    """Convert embeddings to tensor.
    
    Args:
        embeddings: List of embeddings
        
    Returns:
        torch.Tensor: Tensor of embeddings
    """
    return torch.tensor(embeddings)