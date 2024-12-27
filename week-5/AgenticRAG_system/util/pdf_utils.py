from pypdf import PdfReader
import streamlit as st
from io import BytesIO
import numpy as np


def open_and_read_pdf(file):
    """Lukee PDF:n ja palauttaa tekstin ja kuvat."""
    try:
        pdf_bytes = BytesIO(file.read())
        pdf_reader = PdfReader(pdf_bytes)
        pages_and_texts = []

        for page_num, page in enumerate(pdf_reader.pages, 1):
            try:
                # Käsittele teksti turvallisemmin
                text = page.extract_text() or ""

                # Kerää kuvat turvallisemmin
                images = []
                if "/XObject" in page["/Resources"]:
                    x_objects = page["/Resources"]["/XObject"]
                    if isinstance(x_objects, dict):
                        for obj in x_objects.values():
                            if obj["/Subtype"] == "/Image":
                                try:
                                    # Muunna ArrayObject turvallisesti
                                    if hasattr(obj, "get_object"):
                                        image_data = obj.get_object()
                                        if isinstance(image_data, (bytes, bytearray)):
                                            images.append(
                                                np.frombuffer(
                                                    image_data, dtype=np.uint8
                                                )
                                            )
                                except Exception as e:
                                    st.warning(
                                        f"Kuvan lukuvirhe sivulla {page_num}: {e}"
                                    )
                                    continue

                if text.strip():  # Lisää sivu vain jos siinä on tekstiä
                    pages_and_texts.append(
                        {"page_num": page_num, "text": text.strip(), "images": images}
                    )

            except Exception as e:
                st.warning(f"Virhe sivun {page_num} käsittelyssä: {e}")
                continue

        if not pages_and_texts:
            st.warning("PDF:stä ei löytynyt tekstiä")

        return pages_and_texts

    except Exception as e:
        st.error(f"PDF:n lukuvirhe: {e}")
        return []
