from stqdm import stqdm
import fitz
import numpy as np
from typing import List
import PyPDF2
from pathlib import Path


def text_formatter(text: str) -> str:
    """Performs minor formatting on text."""
    cleaned_text = text.replace("\n", " ").strip()
    return cleaned_text


def open_and_read_pdf(pdf_path_or_file) -> list[dict]:
    """
    Opens a PDF file, reads its text content page by page, and collects statistics.

    Parameters:
        pdf_path_or_file: Either a file path string or a Streamlit UploadedFile object

    Returns:
        list[dict]: A list of dictionaries, each containing the page number,
        character count, word count, sentence count, token count, and the extracted text
        for each page.
    """
    # Handle both file path strings and Streamlit uploaded files
    if isinstance(pdf_path_or_file, str):
        doc = fitz.open(pdf_path_or_file)
    else:
        # For Streamlit uploaded files
        bytes_data = pdf_path_or_file.read()
        doc = fitz.open(stream=bytes_data, filetype="pdf")

    pages_and_texts = []
    for page_number, page in stqdm(enumerate(doc)):
        text = page.get_text()
        text = text_formatter(text)
        pages_and_texts.append(
            {
                "page_number": page_number,
                "page_char_count": len(text),
                "page_word_count": len(text.split(" ")),
                "page_sentence_count_raw": len(text.split(". ")),
                "page_token_count": len(text) / 4,
                "text": text,
            }
        )

    doc.close()
    return pages_and_texts


def load_page(filename: str, page_num: int, query: str):
    # Open PDF and load target page
    doc = fitz.open(filename)
    page = doc.load_page(page_num)

    # Get the image of the page
    img = page.get_pixmap(dpi=300)
    doc.close()

    # Convert the Pixmap to a numpy array
    img_array = np.frombuffer(img.samples_mv, dtype=np.uint8).reshape(
        (img.h, img.w, img.n)
    )

    # Display the image using Matplotlib
    import matplotlib.pyplot as plt

    plt.figure(figsize=(13, 10))
    plt.imshow(img_array)
    plt.title(f"Query: '{query}' | Most relevant page:")
    plt.axis("off")
    plt.show()


def pdf_to_text(pdf_file) -> List[str]:
    """Muuntaa PDF-tiedoston tekstiksi sivu kerrallaan.

    Args:
        pdf_file: Ladattu PDF-tiedosto (streamlit UploadedFile)

    Returns:
        List[str]: Lista sivujen teksteistä
    """
    pages = []

    # Lue PDF streamista
    reader = PyPDF2.PdfReader(pdf_file)

    # Käy läpi sivut
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():  # Lisää vain sivut joissa on tekstiä
            pages.append(text)

    return pages
