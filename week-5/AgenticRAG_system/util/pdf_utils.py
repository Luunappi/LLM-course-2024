from pypdf import PdfReader
from typing import List, Dict
import logging


def open_and_read_pdf(pdf_file) -> List[Dict]:
    """
    Lukee PDF-tiedoston ja palauttaa tekstin ja kuvat sivuittain.
    """
    try:
        reader = PdfReader(pdf_file)
        pages_data = []

        for page_num, page in enumerate(reader.pages, 1):
            try:
                # Yritä lukea teksti turvallisemmin
                text = ""
                try:
                    text = page.extract_text()
                except Exception as text_error:
                    logging.warning(
                        f"Virhe tekstin lukemisessa sivulta {page_num}: {text_error}"
                    )

                # Kerää sivun data
                page_data = {
                    "page_num": page_num,
                    "text": text if text else "",
                }

                # Lisää sivu dataan
                pages_data.append(page_data)

            except Exception as page_error:
                logging.error(f"Virhe sivun {page_num} käsittelyssä: {page_error}")
                # Lisää tyhjä sivu ja jatka
                pages_data.append({"page_num": page_num, "text": ""})
                continue

        return pages_data

    except Exception as e:
        logging.error(f"Virhe PDF:n lukemisessa: {e}")
        raise RuntimeError(f"PDF-tiedoston lukeminen epäonnistui: {str(e)}")
