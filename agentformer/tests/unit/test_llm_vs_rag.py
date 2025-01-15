import unittest
import logging
from agentformer.tools.memory_tools.rag_tool import RAGTool
from agentformer.tools.core_tools.model_tool import ModelTool
from agentformer.core.orchestrator import AgentFormerOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestLLMvsRAG(unittest.TestCase):
    """Testaa ja vertaa suoraa LLM-käyttöä ja RAG-metodia"""

    @classmethod
    def setUpClass(cls):
        """Alustaa jaetut resurssit kaikille testeille"""
        cls.orchestrator = AgentFormerOrchestrator()
        # Varmista että testidokumentti on indeksoitu
        test_doc = """
        Caroline Bassett on digitaalisen median ja teknologian tutkija. 
        Hän on tutkinut anti-computing ilmiötä, joka viittaa teknologian 
        vastaisiin asenteisiin ja kritiikkiin. Bassettin mukaan anti-computing 
        on tärkeä osa teknologian historian ymmärtämistä.
        """
        cls.orchestrator.add_document(test_doc.encode(), "test_doc.txt")
        logger.info("Testidokumentti indeksoitu")

    def setUp(self):
        """Alustaa RAG- ja LLM-työkalut yksittäisiä testejä varten"""
        self.rag_tool = RAGTool()
        self.model_tool = ModelTool()
        logger.info("\n=== Alustetaan LLM vs RAG testi ===")

    def test_direct_llm_vs_rag(self):
        """Vertaa suoraa LLM-vastausta ja RAG-pohjaista vastausta"""

        test_cases = [
            {
                "query": "Kerro Joposta ja hänen pyörästään.",
                "should_use_rag": False,
                "expected_source": "llm",
            },
            {
                "query": "Kuka on Caroline Bassett ja mitä hän on tutkinut?",
                "should_use_rag": True,
                "expected_source": "rag",
            },
        ]

        for case in test_cases:
            logger.info(f"\nTestataan kyselyä: {case['query']}")

            # Käytä orkestraattoria, joka valitsee sopivan metodin
            orchestrator_response = self.orchestrator.process_query(case["query"])
            logger.info(f"Orkestraattorin vastaus: {orchestrator_response}")

            # Tarkista että orkestraattori valitsi oikean lähteen
            self.assertEqual(
                orchestrator_response.get("source", ""),
                case["expected_source"],
                f"Orkestraattori valitsi väärän lähteen kyselylle: {case['query']}",
            )

            if case["should_use_rag"]:
                # RAG-vastauksen pitäisi sisältää viitteitä dokumenteista
                self.assertTrue(
                    orchestrator_response.get("found_in_docs", False),
                    f"RAG ei löytänyt dokumentteja kyselylle: {case['query']}",
                )

                # Tarkista että vastaus sisältää relevanttia tietoa
                self.assertIn(
                    "Bassett",
                    orchestrator_response["response"],
                    "RAG-vastauksen pitäisi sisältää tietoa Bassettista",
                )
            else:
                # Ilman indeksoitua tietoa pitäisi käyttää suoraa LLM:ää
                self.assertFalse(
                    orchestrator_response.get("found_in_docs", False),
                    f"Ei olisi pitänyt löytää dokumentteja kyselylle: {case['query']}",
                )

    def test_rag_document_retrieval(self):
        """Testaa RAG:in dokumenttien hakua tarkemmin"""

        query = "Mitä anti-computing tarkoittaa Caroline Bassettin mukaan?"
        response = self.orchestrator.process_query(query)

        # Tarkista että dokumentteja löytyi
        self.assertTrue(
            response.get("found_in_docs", False),
            "RAG:in olisi pitänyt löytää dokumentteja anti-computing -termistä",
        )

        # Tarkista että vastaus sisältää relevantteja avainsanoja
        relevant_keywords = ["anti-computing", "Bassett", "teknologia"]
        for keyword in relevant_keywords:
            self.assertIn(
                keyword.lower(),
                response["response"].lower(),
                f"RAG-vastauksen pitäisi sisältää avainsana: {keyword}",
            )

        # Tarkista vastauksen laatu
        self.assertGreater(
            len(response["response"]), 100, "Vastauksen pitäisi olla riittävän kattava"
        )


if __name__ == "__main__":
    unittest.main()
