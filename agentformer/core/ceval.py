"""
Contextual Evaluation Module (CEval)

Evaluoi vastausten laatua huomioiden:
- Kontekstin käytön
- Vastauksen relevanssin kysymykseen
- Faktojen oikeellisuuden
- Vastauksen selkeyden
"""

import logging
from typing import Dict, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class CEval:
    def __init__(self):
        self.metrics = {
            "context_usage": 0.0,  # Miten hyvin kontekstia hyödynnetty
            "relevance": 0.0,  # Vastauksen relevanssi kysymykseen
            "factuality": 0.0,  # Faktojen oikeellisuus
            "clarity": 0.0,  # Vastauksen selkeys
        }
        logger.debug("Initialized CEval")

    def evaluate_response(
        self, question: str, response: str, context: Optional[str] = None
    ) -> Dict[str, float]:
        """Evaluate response quality"""
        if not question or not response:
            return {"relevance": 0.0, "clarity": 0.0, "context_usage": 0.0}

        metrics = {
            "relevance": self._calculate_relevance(question, response),
            "clarity": self._calculate_clarity(response),
            "context_usage": self._calculate_context_usage(response, context)
            if context
            else 0.0,
        }

        # Varmista että arvot ovat välillä 0-1
        return {k: min(max(v, 0.0), 1.0) for k, v in metrics.items()}

    def _calculate_relevance(self, question: str, response: str) -> float:
        """Calculate response relevance"""
        # Paranna relevanssin laskentaa
        question_words = set(question.lower().split())
        response_words = set(response.lower().split())
        common_words = question_words.intersection(response_words)
        return len(common_words) / len(question_words) if question_words else 0.0

    def _calculate_context_usage(self, response: str, context: str) -> float:
        """Evaluate how well context is used"""
        # Käytä sequence matcher vertailuun
        matcher = SequenceMatcher(None, response.lower(), context.lower())
        return matcher.ratio()

    def _calculate_clarity(self, response: str) -> float:
        """Evaluate response clarity"""
        # Yksinkertaistettu selkeyden arviointi
        words = response.split()
        if not words:
            return 0.0

        # Lyhyemmät lauseet ovat selkeämpiä
        sentence_count = max(
            1, response.count(".") + response.count("!") + response.count("?")
        )
        words_per_sentence = len(words) / sentence_count

        # Optimaalinen pituus 10-15 sanaa per lause
        clarity = 1.0 - abs(words_per_sentence - 12.5) / 25.0

        return max(0.5, min(1.0, clarity))  # Vähintään 0.5 jos vastaus on järkevä

    def _extract_facts(self, text: str) -> set:
        """Extract potential facts from text"""
        # Yksinkertainen faktojen erottelu
        sentences = text.split(".")
        return set(s.strip().lower() for s in sentences if s.strip())
