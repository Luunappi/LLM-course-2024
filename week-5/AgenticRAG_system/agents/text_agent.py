import torch
import pandas as pd
from util.vector_search_utils import retrieve_relevant_resources
from util.generator_utils import tokenize_with_rag_prompt, generate_answer


class TextAgent:
    """
    Agentti tekstiaineiston RAG-hakuun.
    """

    def __init__(self, embedding_model, llm_model, tokenizer, device="cpu", top_k=5):
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.tokenizer = tokenizer
        self.device = device
        self.top_k = top_k

    def run_rag_search_and_answer(
        self, query: str, df: pd.DataFrame, embeddings_tensor, max_new_tokens=512
    ) -> str:
        """
        Etsi relevantit chunkit ja generoi vastaus.
        """
        # 1) hae top_k chunkkeja
        scores, indices = retrieve_relevant_resources(
            query=query,
            embeddings=embeddings_tensor,
            model=self.embedding_model,
        )
        context_items = []
        for idx, score in zip(indices, scores):
            row = df.iloc[idx].to_dict()
            context_items.append(row)

        # 2) rakenna RAG-prompt
        input_ids = tokenize_with_rag_prompt(query, context_items, self.tokenizer)
        answer, gen_time = generate_answer(input_ids, self.llm_model, self.tokenizer)
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
