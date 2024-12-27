import streamlit as st
from typing import Optional, Union
from transformers import Blip2Processor, Blip2ForConditionalGeneration
import torch
from PIL import Image
import requests
from io import BytesIO


class ImageAgent:
    """
    Kuva-agentti joka käyttää BLIP2-mallia kuva-analyysiin.
    Optimoitu Apple Silicon -prosessoreille.
    """

    def __init__(self, device: str = "mps"):
        """
        Alustaa BLIP2-mallin ja prosessorin.

        Args:
            device: Laite jolla malli ajetaan ('cpu', 'mps' tai 'cuda')
        """
        # Tarkista onko MPS käytettävissä
        if device == "mps" and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        # Käytä pienempää mallia muistin säästämiseksi
        model_id = "Salesforce/blip2-opt-1.7b"

        self.processor = Blip2Processor.from_pretrained(model_id)
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if self.device == "mps" else torch.float32,
            device_map={"": self.device},
        )

    def analyze_image(self, image_input: Union[str, bytes, Image.Image]) -> str:
        """
        Analysoi kuvan BLIP2-mallilla.

        Args:
            image_input: Kuva joko tiedostopolkuna, tavuina tai PIL.Image-oliona

        Returns:
            str: Kuvaus kuvasta

        Raises:
            ValueError: Jos syöte on väärän tyyppinen
        """
        try:
            # Tarkista syötteen tyyppi
            if not isinstance(image_input, (str, bytes, Image.Image)):
                raise ValueError(
                    f"Invalid input type. Expected str, bytes, or PIL.Image, got {type(image_input)}"
                )

            # Muunna syöte PIL.Image-muotoon
            if isinstance(image_input, str):
                if image_input.startswith(("http://", "https://")):
                    response = requests.get(image_input)
                    image = Image.open(BytesIO(response.content))
                else:
                    image = Image.open(image_input)
            elif isinstance(image_input, bytes):
                image = Image.open(BytesIO(image_input))
            elif isinstance(image_input, Image.Image):
                image = image_input
            else:
                # Tämä ei pitäisi koskaan tapahtua validoinnin ansiosta
                raise ValueError("Unsupported image input type")

            # Varmista että kuva on RGB-muodossa
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Prosessoi kuva ja generoi kuvaus
            inputs = self.processor(image, return_tensors="pt")
            if not isinstance(inputs, dict):
                raise ValueError("Processor output must be a dictionary")

            # Siirrä inputit oikealle laitteelle (vain jos ne ovat tensoreita)
            inputs = {
                k: v.to(self.device) if isinstance(v, torch.Tensor) else v
                for k, v in inputs.items()
            }

            prompt = "Describe this image in detail, including any text, diagrams, or important visual elements:"
            inputs["text"] = prompt

            # Käytä torch.no_grad() muistin säästämiseksi
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    min_length=30,
                    num_beams=5,
                    temperature=0.7,
                    use_cache=True,  # Käytä välimuistia nopeuttamiseen
                )

            description = self.processor.decode(outputs[0], skip_special_tokens=True)

            # Vapauta muistia
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            if hasattr(torch.mps, "empty_cache"):
                torch.mps.empty_cache()

            return description

        except Exception as e:
            st.error(f"Error analyzing image: {str(e)}")
            raise  # Nostaa alkuperäisen poikkeuksen uudelleen

    def handle_image_page(self, page_data: dict) -> Optional[str]:
        """
        Käsittelee sivun kuvatiedot.

        Args:
            page_data: Sanakirja joka sisältää sivun tiedot

        Returns:
            Optional[str]: Kuvaus kuvasta tai None jos kuvaa ei löydy
        """
        if "image_path" in page_data:
            try:
                description = self.analyze_image(page_data["image_path"])
                return description
            except Exception as e:
                st.error(f"Error in handle_image_page: {str(e)}")
                return None
        return None
