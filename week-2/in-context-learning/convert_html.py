"""
HTML to Markdown Converter

Tämä skripti muuntaa tutkimuspapereita HTML-muodosta Markdown-muotoon.
Käytetään osana in-context learning esimerkkejä, jossa LLM:lle annetaan
kontekstina tutkimuspapereita.

Käyttö:
    python convert_html.py

Input:
    week-2/in-context-learning/papers.html

Output:
    Tulostaa Markdown-muotoisen tekstin konsoliin
"""

from bs4 import BeautifulSoup


def format_papers(html_file):
    """
    Muuntaa HTML-tiedoston Markdown-muotoon.

    Args:
        html_file (str): Polku HTML-tiedostoon

    Returns:
        None: Tulostaa muunnetun tekstin konsoliin
    """
    # Luetaan HTML-tiedosto ja luodaan BeautifulSoup objekti jäsentämistä varten
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Tulostetaan pääotsikko (h1)
    print("# " + soup.h1.text)
    # Tulostetaan alaotsikko (h4)
    print(soup.h4.text)
    # Tulostetaan kursivoitu teksti
    print(soup.find("i").text + "\n")

    # Käydään läpi kaikki h2-otsikot ja niiden alla olevat kappaleet
    for h2 in soup.find_all("h2"):
        # Tulostetaan h2-otsikko Markdown-muodossa
        print("## " + h2.a.text)
        # Tulostetaan otsikkoa seuraava kappale
        print(h2.find_next("p").text + "\n")


# Suoritetaan muunnos
format_papers("week-2/in-context-learning/papers.html")
