# AgenticRAG toimii kevyenä fasadina/julkisena rajapintana
from agents.orchestrator_agent import OrchestratorAgent
from agents.text_agent import TextAgent
from agents.image_agent import ImageAgent
from messaging.pubsub import PubSubSystem


class AgenticRAG:
    """
    Pääluokka, joka alustaa ja koordinoi RAG-järjestelmän komponentit.
    """

    def __init__(self, embedding_model, llm_model, tokenizer, device="mps", top_k=5):
        # Alusta pub/sub
        self.pubsub = PubSubSystem()

        # Alusta agentit
        self.text_agent = TextAgent(
            embedding_model=embedding_model,
            llm_model=llm_model,
            tokenizer=tokenizer,
            device=device,
            top_k=top_k,
        )

        self.image_agent = ImageAgent(device=device)

        # Alusta orkestroija
        self.orchestrator = OrchestratorAgent(
            text_agent=self.text_agent,
            image_agent=self.image_agent,
            pubsub=self.pubsub,
            device=device,
        )

    def run_agentic_search(self, query, df, embeddings_tensor, max_rounds=2):
        """
        Suorittaa agenttipohjaisen haun delegoimalla orkestroijalle.
        """
        document = {
            "text": {"query": query, "df": df, "embeddings": embeddings_tensor},
            "max_rounds": max_rounds,
        }

        return self.orchestrator.process_document(document)
