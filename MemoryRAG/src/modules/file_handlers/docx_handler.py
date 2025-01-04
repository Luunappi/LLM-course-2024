"""Word-tiedostojen käsittelijä"""

from typing import List
import docx
from pathlib import Path


def read_docx(file_path: str) -> List[str]:
    """Lukee Word-tiedoston ja palauttaa tekstin kappaleina"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Tiedostoa ei löydy: {file_path}")

    paragraphs = []
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:  # Ohita tyhjät kappaleet
                paragraphs.append(text)

    except Exception as e:
        raise RuntimeError(f"Virhe Word-tiedoston lukemisessa: {e}")

    return paragraphs
