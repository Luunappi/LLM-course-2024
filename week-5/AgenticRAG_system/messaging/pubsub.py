# PubSubSystem hoitaa viestinnän
from typing import Callable, Dict, List
from collections import defaultdict


class PubSubSystem:
    """
    Yksinkertainen publish/subscribe-järjestelmä agenttien väliseen
    kommunikointiin.
    """

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable) -> None:
        """
        Rekisteröi callback-funktion tietylle tapahtumalle.
        """
        self.subscribers[event].append(callback)

    def publish(self, event: str, data: Dict) -> None:
        """
        Julkaisee tapahtuman kaikille sen tilaajille.
        """
        if event in self.subscribers:
            for callback in self.subscribers[event]:
                callback(data)

    def unsubscribe(self, event: str, callback: Callable) -> None:
        """
        Poistaa callback-funktion tapahtuman tilaajista.
        """
        if event in self.subscribers:
            self.subscribers[event].remove(callback)
