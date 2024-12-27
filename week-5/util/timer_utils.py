import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TimerStats:
    start_time: float
    end_time: Optional[float] = None
    elapsed: Optional[float] = None
    tokens: int = 0
    cost_estimate: float = 0.0


class ProcessTimer:
    """Seuraa prosessin aikaa, tokeneita ja kustannuksia"""

    def __init__(self):
        self.timers: Dict[str, TimerStats] = {}
        self.total_tokens = 0
        self.total_cost = 0.0

        # Mallien hinnat per 1K tokenia (arviot)
        self.price_per_1k = {
            "gemma-2b": 0.0002,  # Ilmainen, mutta lasketaan vertailun vuoksi
            "gpt-3.5": 0.002,
            "gpt-4": 0.03,
        }

    def start(self, name: str) -> None:
        """Aloita ajastin tietylle prosessille"""
        self.timers[name] = TimerStats(start_time=time.time())

    def stop(self, name: str, tokens: int = 0) -> float:
        """Pysäytä ajastin ja palauta kulunut aika"""
        if name not in self.timers:
            return 0.0

        timer = self.timers[name]
        timer.end_time = time.time()
        timer.elapsed = timer.end_time - timer.start_time
        timer.tokens = tokens

        # Laske kustannusarvio (käytä Gemman hintaa oletuksena)
        timer.cost_estimate = (tokens / 1000) * self.price_per_1k["gemma-2b"]

        self.total_tokens += tokens
        self.total_cost += timer.cost_estimate

        return timer.elapsed

    def get_stats(self, name: str) -> Optional[TimerStats]:
        """Hae prosessin tilastot"""
        return self.timers.get(name)

    def format_time(self, seconds: float) -> str:
        """Muotoile aika luettavaan muotoon"""
        return f"{seconds:.2f}s"
