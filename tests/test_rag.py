import pytest
import logging
from agentformer.tools.memory_tools.rag_tool import RAGTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_rag_functionality():
    """Testaa RAG-työkalun perustoiminnallisuuden"""

    # Alusta RAG
    logger.info("\n=== Starting RAG Test ===")
    rag = RAGTool()

    # Aja toiminnallisuustesti
    results = rag.test_functionality()

    # Tarkista tulokset
    logger.info("\n=== Test Results ===")
    for test, result in results.items():
        logger.info(f"{test}: {result}")
        assert "ERROR" not in result, f"Test failed: {test} - {result}"

    # Testaa hakutoiminto käytännössä
    test_queries = [
        "Mitä anti-computing tarkoittaa?",
        "Kuka on Caroline Bassett?",
        "Mikä on kirjan pääteema?",
    ]

    logger.info("\n=== Testing Queries ===")
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        response = rag.query(query)

        # Tarkista vastauksen rakenne
        assert isinstance(response, dict), "Response should be a dictionary"
        assert "response" in response, "Response should contain 'response' field"
        assert "found_in_docs" in response, (
            "Response should contain 'found_in_docs' field"
        )

        # Tulosta vastaus
        logger.info(f"Found in docs: {response['found_in_docs']}")
        logger.info(
            f"Response: {response['response'][:200]}..."
        )  # Näytä alku vastauksesta


if __name__ == "__main__":
    test_rag_functionality()
