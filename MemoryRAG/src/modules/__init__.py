"""
MemoryRAG:n moduulit.
• Kuvaus: Yhdistää eri tiedostomuotojen käsittelijät (PDF, HTML, DOCX, Excel/CSV).
• Rooli: Antaa yhden “read_document” -funktion, joka valitsee oikean lukurutiinin tiedostopäätteen perusteella.
• Tarpeellisuus: “Avustava” – tarpeellinen, jos MemoryRAG lukee dokumentteja suoraan diskiltä monessa formaatissa.
"""

from .context_manager import ContextManager
from .memory_manager import MemoryManager
from .storage import StorageManager

__all__ = ["ContextManager", "MemoryManager", "StorageManager"]
