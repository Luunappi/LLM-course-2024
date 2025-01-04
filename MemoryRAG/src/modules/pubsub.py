from typing import Callable, List, Dict, Any
import time


class EnhancedPubSub:
    """
    Paranneltu pub/sub toteutus, joka tukee:
    - Tapahtumien lokitusta
    - Virheenkäsittelyä
    - Tilaajien priorisointia
    """

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_log = []

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Rekisteröi uuden tilaajan"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, data: Any) -> None:
        """Julkaisee tapahtuman tilaajille"""
        # Loki tapahtumasta
        self.event_log.append(
            {"timestamp": time.time(), "event_type": event_type, "data": data}
        )

        # Kutsu tilaajia
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in subscriber callback: {e}")
                    continue
