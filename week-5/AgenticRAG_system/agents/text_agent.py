import torch
import pandas as pd
from util.vector_search_utils import retrieve_relevant_resources
from util.generator_utils import tokenize_with_rag_prompt, generate_answer
from typing import List, Dict


class TextAgent:
    """
    Agentti tekstin käsittelyyn ja vastausten generointiin.
    """

    def __init__(
        self,
        embedding_model,
        llm_model,
        tokenizer,
        device="mps",
        top_k=5,
        model_type=None,
    ):
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.tokenizer = tokenizer
        self.device = device
        self.top_k = top_k
        self.model_type = model_type

    def get_relevant_documents(
        self, query: str, df: pd.DataFrame, embeddings: torch.Tensor
    ) -> List[Dict]:
        """
        Hakee relevantit dokumentit kyselyyn.
        """
        # Laske kyselyn embeddings
        query_embedding = self.embedding_model.encode(query)
        query_tensor = torch.tensor(query_embedding).unsqueeze(0)

        # Laske samankaltaisuudet
        similarities = torch.nn.functional.cosine_similarity(query_tensor, embeddings)

        # Hae top-k indeksit
        top_k_indices = torch.topk(similarities, k=self.top_k).indices

        # Palauta relevantit dokumentit
        relevant_docs = []
        for idx in top_k_indices:
            relevant_docs.append(df.iloc[idx].to_dict())

        return relevant_docs

    def generate_answer(self, query: str, relevant_docs: List[Dict]) -> str:
        """
        Generoi vastaus relevanttien dokumenttien perusteella.
        """
        # Tokenisoi syöte RAG-promptilla
        input_ids = tokenize_with_rag_prompt(query, relevant_docs, self.tokenizer)

        # Generoi vastaus
        answer, _ = generate_answer(
            input_ids=input_ids,
            model=self.llm_model,
            tokenizer=self.tokenizer,
            model_type=self.model_type,
            max_new_tokens=512,
        )

        return answer

    def summarize_entire_text(self, df: pd.DataFrame) -> str:
        """
        Summaroi koko PDF/dataset. Tällä voi ohittaa retrievalin ja
        koota kaiken tekstin yhteen promptiin.
        """
        all_text = "\n".join(df["sentence_chunk"].tolist())
        prompt = (
            "Please provide a thorough summary of the following text:\n\n" + all_text
        )
        input_ids = self.tokenizer(prompt, return_tensors="pt")["input_ids"]
        answer, gen_time = generate_answer(input_ids, self.llm_model, self.tokenizer)
        return answer

    def process(self, input_data: dict) -> dict:
        """
        Prosessoi tekstidatan.

        Args:
            input_data: Sanakirja, joka sisältää:
                - query: Kysely
                - df: DataFrame dokumenttichunkeista
                - embeddings: Embedding-tensori

        Returns:
            dict: Prosessoinnin tulos
        """
        query = input_data["query"]
        df = input_data["df"]
        embeddings = input_data["embeddings"]

        # Toteuta RAG-haku ja vastauksen generointi tässä
        # Tämä on yksinkertaistettu esimerkki
        return {
            "answer": "This is a test response",
            "sources": df.iloc[: self.top_k].to_dict("records"),
        }
