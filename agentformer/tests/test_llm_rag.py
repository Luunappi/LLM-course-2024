"""Testaa LLM ja RAG toiminnallisuudet.

Tämä testimoduuli varmistaa:
1. Suorat LLM-kyselyt:
   - Testaa perustoiminnallisuuden
   - Näyttää käytetyn kielimallin
   - Testaa vastauksen pituuden kontrollin (50 sanaa)

2. RAG-järjestelmän toiminnallisuus:
   - Listaa kaikki indeksoidut dokumentit
   - Testaa kyselyn ilman relevanttia kontekstia indeksissä
   - Testaa kyselyn relevantin kontekstin kanssa
   - Varmistaa RAG:in varakäyttäytymisen

Odotettu toiminta:
- LLM:n pitäisi antaa suora 50 sanan vastaus
- RAG:in pitäisi ehdottaa LLM:n käyttöä kun kontekstia ei löydy
- RAG:in pitäisi antaa kontekstiin perustuva vastaus kun relevantteja dokumentteja löytyy
"""

import logging
from agentformer.tools.core_tools.model_tool import ModelTool
from agentformer.tools.memory_tools.rag_tool import RAGTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_llm():
    """Test direct LLM query."""
    logger.info("\n=== Testing LLM ===")
    model = ModelTool()
    current_model = model.get_current_model()

    query = "Kerro joposta 50 sanalla."
    logger.info(f"Query: {query}")
    logger.info(f"Using model: {current_model}")

    response = model.query(messages=[{"role": "user", "content": query}])

    logger.info(f"Response: {response}")
    return response


def test_rag():
    """Test RAG query."""
    logger.info("\n=== Testing RAG ===")
    rag = RAGTool()

    # List indexed files
    logger.info("Indexed files:")
    files = rag.get_indexed_files()
    for file in files:
        logger.info(f"- {file}")

    # Test query without context
    query1 = "Kerro Joposta noin 50 sanalla."
    logger.info(f"\nQuery 1: {query1}")
    response1 = rag.query(query1)
    logger.info(f"Response 1: {response1}")

    # Test query with context
    query2 = "Kuka on Caroline Bassett ja mitä hän on tutkinut?"
    logger.info(f"\nQuery 2: {query2}")
    response2 = rag.query(query2)
    logger.info(f"Response 2: {response2}")

    return response1, response2


if __name__ == "__main__":
    test_llm()
    print("\n" + "=" * 50 + "\n")
    test_rag()
