from stqdm import stqdm
import re

def sentencize(text, nlp_model):
    """Split text into sentences using spaCy.
    
    Args:
        text: Text to split into sentences
        nlp_model: Loaded spaCy model
        
    Returns:
        list: List of sentence strings
    """
    if isinstance(text, (list, tuple)):
        # Jos text on lista, käsitellään jokainen elementti erikseen
        sentences = []
        for item in text:
            doc = nlp_model(str(item))
            sentences.extend([sent.text for sent in doc.sents])
        return sentences
    else:
        # Jos text on string, käsitellään se suoraan
        doc = nlp_model(str(text))
        return [sent.text for sent in doc.sents]

def chunk(sentences_by_page: list, min_length: int = 30) -> list[dict]:
    """Create chunks from sentences."""
    chunks = []
    current_chunk = []
    current_length = 0
    page_number = 0
    
    for page_sentences in sentences_by_page:
        for sentence in page_sentences:
            sentence_length = len(sentence) // 4
            
            # Lisää tarkistus liian pitkille chunkeille
            if current_length + sentence_length > min_length * 2:
                chunks.append({
                    "page_number": page_number,
                    "sentence_chunk": " ".join(current_chunk),
                    "chunk_length": current_length
                })
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length
            
            # Jos chunk sisältää kokonaisen ajatuksen, tallenna se
            if sentence.strip().endswith(('.', '!', '?')) and current_length >= min_length:
                chunks.append({
                    "page_number": page_number,
                    "sentence_chunk": " ".join(current_chunk),
                    "chunk_length": current_length
                })
                current_chunk = []
                current_length = 0
        
        # Käsittele sivun viimeinen chunk...
        page_number += 1
    
    return chunks

def chunks_to_text_elems(chunks: list) -> list[str]:
    """Convert chunks to list of text elements.
    
    Args:
        chunks: List of chunk dictionaries
        
    Returns:
        list: List of text strings
    """
    return [chunk["sentence_chunk"] for chunk in chunks]