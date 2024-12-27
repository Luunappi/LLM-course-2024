# OrchestratorAgent vastaa työnkulun koordinoinnista
from typing import List, Dict, Any
from .text_agent import TextAgent
from .image_agent import ImageAgent
from ..messaging.pubsub import PubSubSystem


class OrchestratorAgent:
    """
    Orkestroija-agentti, joka koordinoi eri agenttien toimintaa ja
    hallinnoi työnkulkua.
    """

    def __init__(
        self,
        text_agent: TextAgent,
        image_agent: ImageAgent,
        pubsub: PubSubSystem,
        device: str = "mps",
    ):
        self.text_agent = text_agent
        self.image_agent = image_agent
        self.pubsub = pubsub
        self.device = device

    def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prosessoi dokumentin käyttäen eri agentteja tarpeen mukaan.
        """
        results = {}

        # Julkaise tieto prosessoinnin aloituksesta
        self.pubsub.publish("process_start", {"doc_id": document.get("id")})

        # Käsittele teksti
        if "text" in document:
            text_result = self.text_agent.process(document["text"])
            results["text_analysis"] = text_result
            self.pubsub.publish("text_processed", {"result": text_result})

        # Käsittele kuvat
        if "images" in document:
            image_results = []
            for img in document["images"]:
                img_result = self.image_agent.analyze_image(img)
                image_results.append(img_result)
            results["image_analysis"] = image_results
            self.pubsub.publish("images_processed", {"results": image_results})

        # Yhdistä tulokset
        final_result = self.combine_results(results)
        self.pubsub.publish("process_complete", {"final_result": final_result})

        return final_result

    def combine_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Yhdistää eri agenttien tulokset kokonaisuudeksi.
        """
        # Toteuta tulosten yhdistämislogiikka
        return results
