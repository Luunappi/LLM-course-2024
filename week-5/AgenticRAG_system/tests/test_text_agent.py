import unittest
from unittest.mock import Mock, patch
import torch
import pandas as pd
from AgenticRAG_system.agents.text_agent import TextAgent


class TestTextAgent(unittest.TestCase):
    def setUp(self):
        # Create mock objects
        self.mock_embedding_model = Mock()
        self.mock_llm_model = Mock()
        self.mock_tokenizer = Mock()

        self.text_agent = TextAgent(
            embedding_model=self.mock_embedding_model,
            llm_model=self.mock_llm_model,
            tokenizer=self.mock_tokenizer,
            device="cpu",
        )

        # Testidatan alustus
        self.test_df = pd.DataFrame(
            {
                "sentence_chunk": ["This is a test document.", "Another test chunk."],
                "page_num": [1, 1],
            }
        )
        self.test_embeddings = torch.randn(2, 768)  # Mock embeddings

    def test_process_valid_input(self):
        input_data = {
            "query": "What is this document about?",
            "df": self.test_df,
            "embeddings": self.test_embeddings,
        }

        result = self.text_agent.process(input_data)
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("sources", result)
