import unittest
from unittest.mock import Mock, patch, MagicMock
import torch
from PIL import Image
import io
from AgenticRAG_system.agents.image_agent import ImageAgent


class TestImageAgent(unittest.TestCase):
    def setUp(self):
        self.device = "cpu"

        # Patch BLIP2 model loading
        self.model_patcher = patch(
            "transformers.Blip2ForConditionalGeneration.from_pretrained"
        )
        self.processor_patcher = patch("transformers.Blip2Processor.from_pretrained")

        # Create mock objects
        self.mock_model = self.model_patcher.start()
        self.mock_processor = self.processor_patcher.start()

        # Configure mock processor
        mock_processor_instance = MagicMock()

        # Configure processor output
        mock_processor_output = {
            "pixel_values": torch.randn(1, 3, 224, 224),
            "input_ids": torch.tensor([[1, 2, 3]]),
        }
        # Käytä side_effect-funktiota palauttamaan sanakirja
        mock_processor_instance.side_effect = (
            lambda *args, **kwargs: mock_processor_output
        )
        mock_processor_instance.decode.return_value = "Test image description"
        self.mock_processor.return_value = mock_processor_instance

        # Configure mock model
        mock_model_instance = MagicMock()
        mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3]])
        self.mock_model.return_value = mock_model_instance

        # Create ImageAgent with mocked components
        self.image_agent = ImageAgent(device=self.device)
        # Explicitly set the mocked processor and model
        self.image_agent.processor = mock_processor_instance
        self.image_agent.model = mock_model_instance

        # Luo testikuva
        self.test_image = Image.new("RGB", (100, 100), color="red")

    def tearDown(self):
        self.model_patcher.stop()
        self.processor_patcher.stop()

    def test_analyze_image_with_pil_image(self):
        """Testaa kuva-analyysiä PIL Image -syötteellä"""
        result = self.image_agent.analyze_image(self.test_image)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        # Verify that processor and model were called correctly
        self.assertTrue(self.image_agent.processor.called)
        self.assertTrue(self.image_agent.model.generate.called)

    def test_analyze_image_with_invalid_input(self):
        """Testaa virheenkäsittelyä väärällä syötteellä"""
        with self.assertRaises(ValueError):
            self.image_agent.analyze_image(123)  # Invalid input type

    def test_analyze_image_with_none_input(self):
        """Testaa None-syötteen käsittelyä"""
        with self.assertRaises(ValueError):
            self.image_agent.analyze_image(None)

    def test_analyze_image_with_invalid_path(self):
        """Testaa virheellisen tiedostopolun käsittelyä"""
        with self.assertRaises(FileNotFoundError):
            self.image_agent.analyze_image("nonexistent_image.jpg")

    def test_analyze_image_with_invalid_url(self):
        """Testaa virheellisen URL:n käsittelyä"""
        with self.assertRaises(Exception):  # Voi olla requests.RequestException
            self.image_agent.analyze_image("http://invalid.url/image.jpg")
