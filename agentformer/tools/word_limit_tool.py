"""Word limit management tool"""


class WordLimitTool:
    def __init__(self, default_limit: int = 100):
        self._limit = default_limit

    def set_limit(self, limit: int) -> bool:
        """Set word limit"""
        try:
            self._limit = max(1, min(limit, 1000))  # Rajoita järkeviin arvoihin
            return True
        except Exception:
            return False

    def get_limit(self) -> int:
        """Get current word limit"""
        return self._limit

    def truncate_text(self, text: str) -> str:
        """Truncate text to current word limit"""
        words = text.split()
        if len(words) <= self._limit:
            return text
        return " ".join(words[: self._limit]) + "..."
