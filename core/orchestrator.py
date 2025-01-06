class AgentFormerOrchestrator:
    def __init__(self):
        self.current_model = "gpt-4o"
        self.word_limit = 200
        self.usage_log = []  # Mallikohtaiset usage-tiedot jokaisesta kutsusta

    def set_word_limit(self, limit: int):
        self.word_limit = limit

    def process_request(self, mode: str, payload: dict) -> dict:
        """
        mode: 'chat' tai 'rag'
        payload: esim. {"message": "...", "respect_word_limit": True}
        """
        message = payload.get("message", "")
        respect_word_limit = payload.get("respect_word_limit", False)

        # Lasketaan sallittu max_tokens hiukan isompana kuin word_limit
        # esim. 1 sana ~ 1.33 token. Voit säätää kertoimen.
        max_tokens = int(self.word_limit * 1.5) if respect_word_limit else 512

        # Valitaan prosessi
        if mode == "rag":
            # Palauttaa dict: {"response": "...", "found_in_docs": bool, "usage": {...}, "models_used": [...]}
            return self._rag_flow(message, max_tokens)
        else:
            return self._chat_flow(message, max_tokens)

    def _chat_flow(self, user_text: str, max_tokens: int) -> dict:
        """
        Tavallinen chat ilman RAG:ia. Käyttää self.current_model.
        """
        # Kutsu kielimallia
        response, usage_details = self._call_llm(
            user_text, self.current_model, max_tokens
        )

        # Tallenna usage-loki
        self.usage_log.append(usage_details)

        # Kootaan usage-yhteenveto
        usage_summary = {
            "model_usage_list": [usage_details],
            "input_tokens": usage_details["input_tokens"],
            "output_tokens": usage_details["output_tokens"],
            "total_tokens": usage_details["total_tokens"],
            "cost": usage_details["cost"],
        }
        return {
            "response": response,
            "usage": usage_summary,
            "found_in_docs": True,  # chat-moodissa oletamme "löytyi"
            "models_used": [self.current_model],  # vain yksi malli
        }

    def _rag_flow(self, user_text: str, max_tokens: int) -> dict:
        """
        RAG-haku: 1) Hae relevantit chunkitembedding-mallilla
                  2) Tekstimalli generoi vastauksen
        """
        # 1) Kutsu embeddings-mallia (esim. "text-embedding-ada-002")
        embed_model = "text-embedding-ada-002"
        embedding_usage = self._call_embedding_model(user_text, embed_model)

        # 2) Etsi relevantit kappaleet -> check if found
        docs_found, doc_snippets = self._retrieve_docs(user_text)
        found_in_docs = len(doc_snippets) > 0

        # 3) Kutsu generointimallia (esim. self.current_model)
        # Jos ei aineistoa, annetaan fallback jokatapauksessa ->
        # Or kootaan "We found X docs…"
        answer_model = self.current_model
        answer_text, usage_details = self._call_llm(
            user_text + "\n" + "\n".join(doc_snippets), answer_model, max_tokens
        )

        # Tallenna usage-loki
        self.usage_log.append(embedding_usage)
        self.usage_log.append(usage_details)

        # Rakennetaan usage-lista
        model_usage_list = [embedding_usage, usage_details]
        total_tokens_sum = sum(u["total_tokens"] for u in model_usage_list)
        cost_sum = sum(u["cost"] for u in model_usage_list)

        usage_summary = {
            "model_usage_list": model_usage_list,
            "input_tokens": sum(u["input_tokens"] for u in model_usage_list),
            "output_tokens": sum(u["output_tokens"] for u in model_usage_list),
            "total_tokens": total_tokens_sum,
            "cost": cost_sum,
        }

        return {
            "response": answer_text,
            "usage": usage_summary,
            "found_in_docs": found_in_docs,
            "models_used": [embed_model, answer_model],
        }

    def _call_llm(self, prompt_text: str, model_name: str, max_tokens: int):
        """
        Esimerkki LLM-kutsu, joka palauttaa (response_str, usage_dict).
        Toteuta Oman API-kirjaston mukaisesti.
        """
        # Soitetaan jollekin LLM API:lle.
        # Oletetaan, että se palauttaa usage-tiedot.
        # Alla vain esimerkkipaluu:
        usage_data = {
            "model_name": model_name,
            "input_tokens": 150,
            "output_tokens": 180,
            "total_tokens": 330,
            "cost": calculate_cost(330),
        }
        return "Vastausteksti (ei katkaistu kesken).", usage_data

    def _call_embedding_model(self, text: str, model_name: str):
        """
        Palauta embeddings + usage-tietoja.
        """
        usage = {
            "model_name": model_name,
            "input_tokens": 40,
            "output_tokens": 0,
            "total_tokens": 40,
            "cost": calculate_cost(40),
        }
        return usage

    def _retrieve_docs(self, query: str):
        """
        Palauta listaa relevantteja dokkareita. Jos tyhjä -> ei löytynyt.
        """
        # Tässä vain esimerkkinä: Ei oikeaa haun toteutusta
        # Palauttaa: (bool, list_of_strings)
        # bool: Onko ylipäätään mitään docs
        return True, ["Relevantti pätkä 1", "Relevantti pätkä 2"]


def calculate_cost(total_tokens: int) -> float:
    return (total_tokens / 1000) * 0.002
