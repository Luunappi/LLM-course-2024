from typing import List, Dict
import spacy


def sentencize(text: str, nlp) -> List[str]:
    """
    Jakaa tekstin lauseiksi käyttäen spaCy:a.

    Args:
        text: Teksti joka jaetaan lauseiksi
        nlp: spaCy nlp objekti

    Returns:
        List[str]: Lista lauseita
    """
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def chunk(sentences_by_page: List[List[str]], min_token_length: int = 30) -> List[Dict]:
    """
    Jakaa lauseet sopivan kokoisiksi chunkeiksi.

    Args:
        sentences_by_page: Lista lauselistoja sivuittain
        min_token_length: Minimipituus chunkeille tokeneina

    Returns:
        List[Dict]: Lista chunkkeja ja niiden metatietoja
    """
    chunks = []
    current_chunk = []
    current_length = 0
    current_page = 1

    for page_num, page_sentences in enumerate(sentences_by_page, 1):
        for sentence in page_sentences:
            # Karkea arvio tokenien määrästä
            sentence_length = len(sentence.split())

            if current_length + sentence_length > min_token_length and current_chunk:
                # Tallenna nykyinen chunk
                chunks.append(
                    {
                        "sentence_chunk": " ".join(current_chunk),
                        "page_num": current_page,
                    }
                )
                current_chunk = []
                current_length = 0

            current_chunk.append(sentence)
            current_length += sentence_length
            current_page = page_num

    # Lisää viimeinen chunk jos sellainen on
    if current_chunk:
        chunks.append(
            {"sentence_chunk": " ".join(current_chunk), "page_num": current_page}
        )

    return chunks
