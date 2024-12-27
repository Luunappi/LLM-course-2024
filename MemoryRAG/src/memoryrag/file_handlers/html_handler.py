"""HTML-tiedostojen käsittelijä"""

from typing import List
from bs4 import BeautifulSoup
from pathlib import Path
import requests


def read_html(file_path_or_url: str) -> List[str]:
    """Lukee HTML-tiedoston tai URL:n ja palauttaa tekstin kappaleina"""
    try:
        # Muunna Path merkkijonoksi
        if isinstance(file_path_or_url, Path):
            file_path_or_url = str(file_path_or_url)

        # Tarkista onko URL vai tiedosto
        if file_path_or_url.startswith(("http://", "https://")):
            response = requests.get(file_path_or_url)
            html = response.text
        else:
            file_path = Path(file_path_or_url)
            if not file_path.exists():
                raise FileNotFoundError(f"Tiedostoa ei löydy: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()

        # Jäsennä HTML
        soup = BeautifulSoup(html, "html.parser")

        # Poista script ja style
        for script in soup(["script", "style"]):
            script.decompose()

        # Kerää teksti kappaleittain
        paragraphs = []
        for p in soup.find_all(["p", "div", "article", "h1"]):  # Lisätty h1
            text = p.get_text().strip()
            if text:
                paragraphs.append(text)

        return paragraphs

    except Exception as e:
        raise RuntimeError(f"Virhe HTML:n lukemisessa: {e}")
