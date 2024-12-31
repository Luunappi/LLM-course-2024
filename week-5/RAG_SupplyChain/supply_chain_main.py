import os
import time
import sys

# Mahdollinen .env-lataus
from dotenv import load_dotenv

load_dotenv()

import random

# Mock-OpenAI tai jokin vastaava, jos haluat käyttää azure
# Voit halutessasi laajentaa esim.:
# from openai import OpenAI, AzureOpenAI
# ...
# Joko suora openai-kirjasto taikka "openai.api_type='azure'"

# Tässä yksinkertaista pseudokoodia agenttimaisesta orkestroinnista
# Käytetään karkeasti "o1" isoon suunnitteluun, "o1-mini" pieneen toteutukseen.


class SupplyChainOrchestrator:
    """
    Orkestroi supply chain -optimointia käyttämällä kahta eri LLM-mallia:
    - Päämalli (o1) strategiseen suunnitteluun
    - Kevyempi malli (o1-mini tai GPT-4o-mini) pienempiin osatehtäviin
    """

    def __init__(self):
        # Ympäristömuuttujat
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.azure_api_key = os.getenv("AZURE_API_KEY", "")
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT", "")
        self.azure_version = os.getenv("AZURE_OPENAI_API_VERSION", "")

        # Voit säätää, kumpaa mallia käytetään "isossa" ja "pienessä" roolissa
        self.planning_model = "o1"  # isompi
        self.execution_model = "o1-mini"  # pienempi

    def gather_data(self):
        """
        Esimerkkifunktio, joka simuloi jonkin supply chain -aineiston lukua.
        Käytännössä voisit hakea PDF:stä, CSV:stä tms.
        """
        # Tässä vain mock-data: varasto, kuljetuskustannus, kysyntäarviot yms.
        data = {
            "inventory": 1500,
            "demand_forecast": 1200,
            "transport_cost": 1.2,
            "production_cost": 7.5,
        }
        return data

    def ask_planning_model(self, data):
        """
        Kutsutaan 'o1'-mallia (suurempaa mallia) strategiseen suunnitteluun:
        'Miten optimoida supply chain, mitkä stepit?'
        (Tässä vain simuloidaan - ei oikeasti kutsuta APIa).
        """
        # Oikeassa toteutuksessa:
        # prompt = "Given the following data, plan the steps for an optimized supply chain" + str(data)
        # ...kutsu OpenAI/Azure APIa...

        # Esimerkkipaluu: "Tee 4 askelta":
        steps = [
            "Analysoi nykyisen inventaarin taso ja kysyntäennuste.",
            "Suunnittele tuotantomäärä sen perusteella.",
            "Optimoi kuljetusaikataulut, huomioi kustannukset.",
            "Toteuta fallback-suunnitelma, jos kysyntä nousee.",
        ]
        print("[PlanningModel - o1] Ehdottaa steppejä:", steps)
        return steps

    def ask_execution_model(self, step):
        """
        Jokaiselle stepille pyydetään pienemmältä mallilta (o1-mini tai GPT-4o-mini):
        'Toteuta yksityiskohtainen tehtävä'.
        (Tässä myös simuloitu.)
        """
        # Jenkkifuturoidulla promptilla:
        # prompt = f"Your task is to detail how to accomplish this step: {step}"
        # calling smaller LLM...

        response = (
            f"[ExecutionModel - {self.execution_model}] Detaljoidaan askel: {step}"
        )
        print(response)
        # Palautetaan esim. random-lauseke
        detail = f"Yksityiskohtia {step.lower()} => Tarvitaan mm. resurssitaulukko, 2kpl kuljetusta..."
        return detail

    def run_optimization(self):
        """
        Korkean tason funktio, joka:
        1) Hakee dataa
        2) Kysyy 'planning_model':lta askeleet
        3) Jokaiselle askeleelle pyytää 'execution_model':lta toteutusstrategian
        """
        print("=== Supply Chain Orchestration Start ===")
        data = self.gather_data()

        steps = self.ask_planning_model(data)

        all_details = []
        for s in steps:
            detail = self.ask_execution_model(s)
            all_details.append(detail)
            # Voisit halutessasi testata moottoreiden erot

        print("\n=== Lopputulos: ===")
        for idx, det in enumerate(all_details, 1):
            print(f"Askel {idx}:", det)
        print("=== Orkestraatio päättynyt. ===")


def main():
    orchestrator = SupplyChainOrchestrator()
    orchestrator.run_optimization()


if __name__ == "__main__":
    main()
