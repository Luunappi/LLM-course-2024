from pypdf import PdfReader
from PIL import Image
import io


def open_and_read_pdf(file):
    """
    Lukee PDF:n ja palauttaa tekstin ja kuvat sivuittain.
    """
    reader = PdfReader(file)
    pages = []

    for page_num, page in enumerate(reader.pages, 1):
        page_data = {"page_num": page_num, "text": page.extract_text()}

        # Extract images if any
        if page.images:
            page_data["images"] = []
            for image in page.images:
                img = Image.open(io.BytesIO(image.data))
                page_data["images"].append(img)

        pages.append(page_data)

    return pages
