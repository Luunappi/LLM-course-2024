import unittest
from unittest.mock import Mock, patch
from AgenticRAG_system.agents.orchestrator_agent import OrchestratorAgent


class TestOrchestratorAgent(unittest.TestCase):
    def setUp(self):
        # Luo mock-objektit agenteille
        self.text_agent = Mock()
        self.image_agent = Mock()
        self.pubsub = Mock()

        self.orchestrator = OrchestratorAgent(
            text_agent=self.text_agent,
            image_agent=self.image_agent,
            pubsub=self.pubsub,
            device="cpu",
        )

    def test_process_document_with_text(self):
        # Testidokumentti
        document = {
            "text": {"query": "test query", "data": "test data"},
            "id": "test_id",
        }

        # Määritä mock-vastaus text_agent.process-kutsulle
        self.text_agent.process.return_value = {"result": "text analysis"}

        result = self.orchestrator.process_document(document)

        # Tarkista että metodeja kutsuttiin oikein
        self.text_agent.process.assert_called_once_with(document["text"])
        self.pubsub.publish.assert_called()
