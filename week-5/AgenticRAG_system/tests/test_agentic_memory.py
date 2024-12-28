import unittest
from agentic_memory import AgenticMemory


class TestAgenticMemory(unittest.TestCase):
    def setUp(self):
        """Alustetaan muisti ennen jokaista testiä"""
        self.memory = AgenticMemory()

    def test_basic_memory_operations(self):
        """Testaa perus muistioperaatiot"""
        # Testaa yksittäisen arvon tallennus
        self.memory.update_memory("current_query", "Test query")
        self.assertEqual(self.memory.contents["current_query"], "Test query")

        # Testaa listan päivitys
        self.memory.update_memory("query_history", "Query 1")
        self.memory.update_memory("query_history", "Query 2")
        self.assertEqual(len(self.memory.contents["query_history"]), 2)

    def test_context_retrieval(self):
        """Testaa kontekstin hakeminen"""
        # Asetetaan testidataa
        self.memory.update_memory("current_query", "Test query")
        self.memory.update_memory("query_history", "Old query 1")
        self.memory.update_memory("query_history", "Old query 2")

        # Haetaan konteksti
        context = self.memory.get_context(["current_query", "query_history"])

        # Tarkistetaan että kaikki data on mukana
        self.assertIn("Test query", context)
        self.assertIn("Old query 1", context)
        self.assertIn("Old query 2", context)

    def test_memory_logging(self):
        """Testaa muistin päivitysten lokitus"""
        self.memory.update_memory("current_query", "Test", {"user": "tester"})

        # Tarkista että loki sisältää päivityksen
        self.assertEqual(len(self.memory.memory_log), 1)
        self.assertEqual(self.memory.memory_log[0]["content"], "Test")
        self.assertEqual(self.memory.memory_log[0]["metadata"]["user"], "tester")

    def test_memory_limits(self):
        """Testaa kontekstin rajoitukset"""
        # Lisätään useita arvoja
        for i in range(5):
            self.memory.update_memory("query_history", f"Query {i}")

        # Haetaan rajoitettu määrä
        context = self.memory.get_context(["query_history"], limit=2)

        # Tarkistetaan että vain viimeiset kaksi ovat mukana
        self.assertIn("Query 3", context)
        self.assertIn("Query 4", context)
        self.assertNotIn("Query 0", context)

    def test_memory_clear(self):
        """Testaa muistin tyhjennys"""
        # Lisätään dataa
        self.memory.update_memory("current_query", "Test")
        self.memory.update_memory("query_history", "Query")

        # Tyhjennetään yksittäinen ankkuri
        self.memory.clear_memory("current_query")
        self.assertEqual(self.memory.contents["current_query"], "")
        self.assertEqual(len(self.memory.contents["query_history"]), 1)

        # Tyhjennetään koko muisti
        self.memory.clear_memory()
        self.assertEqual(self.memory.contents["current_query"], "")
        self.assertEqual(len(self.memory.contents["query_history"]), 0)


if __name__ == "__main__":
    unittest.main()
