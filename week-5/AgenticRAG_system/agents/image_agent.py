import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from PIL import Image
import io
import os
from dotenv import load_dotenv
from pathlib import Path

# Lataa .env tiedosto repon juuresta
repo_root = Path(__file__).parent.parent.parent.parent
dotenv_path = repo_root / ".env"
load_dotenv(dotenv_path)

# Määritä mallikansio
models_dir = Path(os.getenv("MODELS_DIR", "models"))
blip2_model_path = models_dir / "blip2-opt-2.7b"


class ImageAgent:
    """
    Agentti kuvien analysointiin BLIP2-mallin avulla.
    """

    def __init__(self, device="cpu"):
        """
        Alustaa kuva-agentin.

        Args:
            device: Laite jolle malli ladataan ('cpu' tai 'cuda' tai 'mps')
        """
        self.device = device

        # Tarkista onko malli jo ladattu lokaalisti
        if not blip2_model_path.exists():
            print(f"Ladataan BLIP2-malli kansioon {blip2_model_path}")
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            if not hf_token:
                print("Varoitus: HUGGINGFACE_TOKEN puuttuu .env tiedostosta")

            # Lataa malli Hugging Facesta ja tallenna lokaalisti
            model_id = "Salesforce/blip2-opt-2.7b"
            try:
                self.processor = Blip2Processor.from_pretrained(
                    model_id,
                    token=hf_token,
                    trust_remote_code=True,
                    local_files_only=False,
                )
                self.processor.save_pretrained(blip2_model_path)

                self.model = Blip2ForConditionalGeneration.from_pretrained(
                    model_id,
                    token=hf_token,
                    torch_dtype=torch.float16,
                    device_map={"": device},
                    trust_remote_code=True,
                    load_in_8bit=True,
                )
                self.model.save_pretrained(blip2_model_path)
            except OSError as e:
                print(f"Varoitus: BLIP2-mallin lataus epäonnistui: {e}")
                self.processor = None
                self.model = None
                return
        else:
            # Käytä lokaalisti tallennettua mallia
            print(f"Käytetään lokaalisti tallennettua mallia: {blip2_model_path}")
            try:
                self.processor = Blip2Processor.from_pretrained(
                    blip2_model_path,
                    local_files_only=True,
                )
                self.model = Blip2ForConditionalGeneration.from_pretrained(
                    blip2_model_path,
                    torch_dtype=torch.float16,
                    device_map={"": device},
                    local_files_only=True,
                )
            except Exception as e:
                print(f"Virhe ladattaessa lokaalia mallia: {e}")
                self.processor = None
                self.model = None

    def analyze_image(self, image) -> str:
        """
        Analysoi kuvan ja palauttaa kuvauksen.

        Args:
            image: PIL.Image tai bytes-muotoinen kuva

        Returns:
            str: Kuvan kuvaus tai virheilmoitus
        """
        if self.model is None or self.processor is None:
            return "Kuva-analyysi ei käytettävissä (mallia ei ladattu)"

        try:
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))

            inputs = self.processor(image, return_tensors="pt").to(self.device)

            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs.pixel_values, max_length=50, num_beams=5
                )

            generated_text = self.processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0].strip()

            return generated_text

        except Exception as e:
            return f"Virhe kuvan analysoinnissa: {str(e)}"
