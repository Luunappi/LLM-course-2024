"""Tiedostoformaattien käsittelijät"""

from typing import List
from pathlib import Path
from .pdf_handler import read_pdf
from .docx_handler import read_docx
from .html_handler import read_html
from .spreadsheet_handler import read_spreadsheet


def read_document(file_path: str, max_rows: int = 1000) -> List[str]:
    """Lukee dokumentin ja palauttaa tekstin kappaleina"""
    file_path = Path(file_path)

    # Valitse käsittelijä tiedostopäätteen perusteella
    if file_path.suffix.lower() == ".pdf":
        return read_pdf(file_path)
    elif file_path.suffix.lower() in [".docx", ".doc"]:
        return read_docx(file_path)
    elif file_path.suffix.lower() in [".html", ".htm"]:
        return read_html(file_path)
    elif file_path.suffix.lower() == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            # Jaa teksti kappaleisiin tyhjien rivien perusteella
            paragraphs = []
            current = []

            for line in text.split("\n"):
                line = line.strip()
                if line:
                    current.append(line)
                elif current:  # Tyhjä rivi -> uusi kappale
                    paragraphs.append(" ".join(current))
                    current = []

            # Lisää viimeinen kappale
            if current:
                paragraphs.append(" ".join(current))

            return paragraphs
    elif file_path.suffix.lower() in [".csv", ".xlsx", ".xls"]:
        return read_spreadsheet(file_path, max_rows=max_rows)
    else:
        raise ValueError(f"Tuntematon tiedostomuoto: {file_path.suffix}")
