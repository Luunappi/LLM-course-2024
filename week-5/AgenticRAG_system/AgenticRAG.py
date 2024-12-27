# AgenticRAG toimii kevyenä fasadina/julkisena rajapintana
from agents.orchestrator_agent import OrchestratorAgent
from agents.text_agent import TextAgent
from agents.image_agent import ImageAgent
from messaging.pubsub import PubSubSystem
import pandas as pd
import torch
import time
from typing import List, Dict


class AgenticRAG:
    """
    Pääluokka, joka alustaa ja koordinoi RAG-järjestelmän komponentit.
    """

    def __init__(
        self,
        embedding_model,
        llm_model,
        tokenizer,
        device="mps",
        top_k=5,
        model_type=None,  # Lisätty model_type parametri
    ):
        # Alusta pub/sub
        self.pubsub = PubSubSystem()

        # Alusta agentit
        self.text_agent = TextAgent(
            embedding_model=embedding_model,
            llm_model=llm_model,
            tokenizer=tokenizer,
            device=device,
            top_k=top_k,
            model_type=model_type,  # Välitä model_type text_agentille
        )

        self.image_agent = ImageAgent(device=device)

        # Alusta orkestroija
        self.orchestrator = OrchestratorAgent(
            text_agent=self.text_agent,
            image_agent=self.image_agent,
            pubsub=self.pubsub,
            device=device,
        )

    def run_agentic_search(
        self, query: str, df: pd.DataFrame, embeddings: torch.Tensor
    ):
        """
        Suorittaa agenttipohjaisen haun.

        Args:
            query: Käyttäjän kysymys
            df: DataFrame joka sisältää tekstit
            embeddings: Tekstien embeddings-tensori

        Returns:
            Tuple[str, float]: (vastaus, generointiaika)
        """
        start_time = time.time()

        # Hae relevantit dokumentit
        relevant_docs = self.get_relevant_documents(query, df, embeddings)

        # Generoi vastaus
        answer = self.generate_answer(query, relevant_docs)

        generation_time = time.time() - start_time

        return answer, generation_time

    def get_relevant_documents(
        self, query: str, df: pd.DataFrame, embeddings: torch.Tensor
    ) -> List[Dict]:
        """
        Hakee relevantit dokumentit kyselyyn.
        """
        return self.text_agent.get_relevant_documents(query, df, embeddings)

    def generate_answer(self, query: str, relevant_docs: List[Dict]) -> str:
        """
        Generoi vastauksen relevanttien dokumenttien perusteella.
        """
        return self.text_agent.generate_answer(query, relevant_docs)
