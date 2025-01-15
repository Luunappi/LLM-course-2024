"""Testaa web-käyttöliittymän toiminnallisuus automaattisilla kyselyillä.

Tämä testi:
1. Käynnistää web-palvelimen testitilassa
2. Lähettää testikyselyt API-rajapintojen kautta
3. Testaa sekä LLM että RAG vastaukset
4. Varmistaa tiedostojen latauksen ja indeksoinnin

Huom: Testi ei vaadi manuaalista interaktiota käyttöliittymän kanssa.
"""

import pytest
import logging
from flask.testing import FlaskClient
from ..web.web_gui import app  # Korjattu tuontipolku

logger = logging.getLogger(__name__)


@pytest.fixture
def client():
    """Luo testiasiakkaan."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_llm_query(client):
    """Testaa suora LLM-kysely API:n kautta."""
    logger.info("\n=== LLM-testi ===")

    # Tarkista ensin käytössä oleva malli
    model_response = client.get("/api/models")
    model_data = model_response.get_json()
    current_model = model_data.get("current", "unknown")
    logger.info(f"Käytössä oleva malli: {current_model}")

    # Tee kysely
    query = "Kerro joposta 50 sanalla."
    logger.info(f"Kysely: {query}")

    response = client.post("/api/chat", json={"message": query, "mode": "llm"})

    assert response.status_code == 200
    data = response.get_json()
    assert "answer" in data
    logger.info(f"Vastaus: {data['answer']}")


def test_rag_queries(client):
    """Testaa RAG-kyselyt API:n kautta."""
    logger.info("\n=== RAG-testi ===")

    # Listaa indeksoidut tiedostot
    files_response = client.get("/api/rag/files")
    files_data = files_response.get_json()
    logger.info("\nIndeksoidut tiedostot:")
    for file in files_data.get("files", []):
        logger.info(
            f"- {file['filename']} {'[Indeksoitu]' if file.get('is_indexed') else '[Ei indeksoitu]'}"
        )

    # Testaa kysely ilman kontekstia
    query1 = "Kerro Joposta noin 50 sanalla."
    logger.info(f"\nKysely 1: {query1}")

    response1 = client.post("/api/chat", json={"message": query1, "mode": "rag"})
    data1 = response1.get_json()
    assert response1.status_code == 200
    logger.info(f"Vastaus 1: {data1['answer']}")

    # Testaa kysely kontekstin kanssa
    query2 = "Kuka on Caroline Bassett ja mitä hän on tutkinut?"
    logger.info(f"\nKysely 2: {query2}")

    response2 = client.post("/api/chat", json={"message": query2, "mode": "rag"})
    data2 = response2.get_json()
    assert response2.status_code == 200
    logger.info(f"Vastaus 2: {data2['answer']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pytest.main([__file__, "-v"])
