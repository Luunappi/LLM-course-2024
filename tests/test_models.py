import ollama
import unittest


# Määritellään tuetut mallit ja niiden tiedot
SUPPORTED_MODELS = {
    "mistral": {"size": "7B", "type": "instruction", "quantization": "4-bit"},
    "llama2": {"size": "7B", "type": "chat", "quantization": "4-bit"},
    "tinyllama": {"size": "1.1B", "type": "base", "quantization": "4-bit"},
}


class TestLlama(unittest.TestCase):
    def setUp(self):
        """Suoritetaan ennen jokaista testiä"""
        self.models = ollama.list()
        print("\nLadatut mallit:")
        print(self.models)

    def test_models_loaded(self):
        """Testaa että mallit ovat ladattu"""
        model_names = [model.model.split(":")[0] for model in self.models.models]
        print(f"\nLöydetyt mallit: {model_names}")

        # Tulosta mallien tiedot
        for model in self.models.models:
            name = model.model.split(":")[0]
            print(f"\nMalli: {name}")
            if name in SUPPORTED_MODELS:
                info = SUPPORTED_MODELS[name]
                print(f"Parametrien määrä: {info['size']}")
                print(f"Tyyppi: {info['type']}")
                print(f"Kvantisointi: {info['quantization']}")
            print(f"Koko levyllä: {model.size / 1024 / 1024:.1f} MB")

    def test_chat(self):
        """Testaa mallien keskustelua"""
        # Testaa jokaista ladattua mallia
        for model in self.models.models:
            model_name = model.model.split(":")[0]
            print(f"\nTestataan mallia: {model_name}")

            response = ollama.chat(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": "What is machine learning? Answer in 2-3 sentences.",
                    }
                ],
            )

            self.assertTrue(response["message"]["content"])
            print(f"\n{model_name.capitalize()} vastaus:")
            print(response["message"]["content"])


if __name__ == "__main__":
    unittest.main()
