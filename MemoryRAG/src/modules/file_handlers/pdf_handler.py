"""PDF-tiedostojen käsittelijä"""

from typing import List
from pypdf import PdfReader  # PyPDF2:n sijaan
from pathlib import Path


def read_pdf(file_path: str) -> List[str]:
    """Lukee PDF-tiedoston ja palauttaa tekstin kappaleina"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Tiedostoa ei löydy: {file_path}")

    paragraphs = []
    try:
        with open(file_path, "rb") as f:
            pdf = PdfReader(f)

            # Käsittele koko dokumentti yhtenä tekstinä
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            # Jaa järkeviin kappaleisiin
            raw_paragraphs = full_text.split("\n\n")

            # Yhdistä lyhyet kappaleet ja poista tyhjät
            min_length = 100  # Minimipituus kappaleelle
            current_paragraph = []

            for p in raw_paragraphs:
                p = p.strip()
                if not p:  # Ohita tyhjät
                    continue

                if len(p) < min_length:
                    current_paragraph.append(p)
                else:
                    if current_paragraph:
                        paragraphs.append(" ".join(current_paragraph))
                        current_paragraph = []
                    paragraphs.append(p)

            # Lisää viimeinen kappale
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph))

    except Exception as e:
        raise RuntimeError(f"Virhe PDF:n lukemisessa: {e}")

    return paragraphs
