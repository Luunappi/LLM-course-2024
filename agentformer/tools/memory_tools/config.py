"""Memory Configuration - Muistin konfiguraatiot

Tämä moduuli sisältää muistinhallintaan liittyvät konfiguraatioluokat:
1. MemoryChainConfig - Muistiketjun asetukset
2. ConversationWindow - Keskusteluikkunan määritykset
3. ArchiveConfig - Arkistoinnin asetukset
4. SummaryConfig - Tiivistämisen asetukset
5. EmbedderConfig - Tekstin vektoroinnin asetukset
6. ChunkConfig - Dokumenttien pilkkomisen asetukset
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union


@dataclass
class ConversationWindow:
    """Keskusteluikkunan asetukset"""

    max_messages: int = 50
    max_tokens: int = 4000
    summary_trigger: int = 40  # Milloin tiivistäminen käynnistyy
    min_messages_for_summary: int = 10
    include_system_messages: bool = True


@dataclass
class ArchiveConfig:
    """Arkistoinnin asetukset"""

    auto_archive_days: int = 7  # Automaattinen arkistointi X päivän jälkeen
    max_conversations: int = 1000  # Maksimi aktiivisten keskustelujen määrä
    archive_batch_size: int = 50  # Montako keskustelua arkistoidaan kerralla
    min_messages_to_archive: int = 5  # Minimikeskustelun pituus arkistointiin
    include_metadata: bool = True  # Tallennetaanko metatiedot


@dataclass
class SummaryConfig:
    """Tiivistämisen asetukset"""

    max_length: int = 200  # Maksimipituus merkkeinä
    min_length: int = 50  # Minimipituus merkkeinä
    temperature: float = 0.3  # Generointimallin lämpötila
    model_name: str = "gpt-4o-mini"  # Käytettävä malli

    # Tiivistämisen strategiat
    use_clustering: bool = True  # Käytetäänkö klusterointia
    num_clusters: int = 3  # Klustereiden määrä
    hierarchical_levels: int = 2  # Hierarkkisen tiivistämisen tasot

    # Välimuistin asetukset
    use_cache: bool = True  # Käytetäänkö välimuistia
    cache_dir: str = "memory/cache/summaries"  # Välimuistin sijainti
    cache_ttl: int = 86400  # Välimuistin elinaika sekunteina (24h)

    # Suoritusasetukset
    batch_size: int = 32  # Eräkoko rinnakkaisessa prosessoinnissa
    use_gpu: bool = False  # Käytetäänkö GPU:ta
    show_progress: bool = True  # Näytetäänkö edistymispalkki

    # Virhetilanteiden käsittely
    fallback_strategy: str = "truncate"  # Varastrategia: truncate/original/skip
    max_retries: int = 3  # Uudelleenyrityskerrat virhetilanteissa
    timeout: int = 30  # Aikakatkaisu sekunteina


@dataclass
class EmbedderConfig:
    """Tekstin vektoroinnin asetukset"""

    # Mallin asetukset
    model_name: str = "all-MiniLM-L6-v2"  # Käytettävä embedding-malli
    model_device: str = "cpu"  # Laitteisto: cpu/cuda/mps
    normalize_embeddings: bool = True  # Normalisoidaanko vektorit

    # Prosessointiasetukset
    batch_size: int = 32  # Eräkoko rinnakkaisessa prosessoinnissa
    max_length: int = 512  # Maksimipituus tokeneina
    truncation: bool = True  # Katkaisu jos ylittää max_length
    padding: bool = True  # Täytetäänkö lyhyet tekstit

    # Välimuistin asetukset
    use_cache: bool = True  # Käytetäänkö välimuistia
    cache_dir: str = "memory/cache/embeddings"  # Välimuistin sijainti
    cache_ttl: int = 604800  # Välimuistin elinaika sekunteina (7 päivää)

    # Suoritusasetukset
    use_gpu: bool = False  # Käytetäänkö GPU:ta
    show_progress: bool = True  # Näytetäänkö edistymispalkki
    num_workers: int = 4  # Rinnakkaisten prosessien määrä

    # Virhetilanteiden käsittely
    max_retries: int = 3  # Uudelleenyrityskerrat virhetilanteissa
    timeout: int = 30  # Aikakatkaisu sekunteina
    fallback_model: Optional[str] = "paraphrase-MiniLM-L3-v2"  # Varamalli


@dataclass
class MemoryChainConfig:
    """Muistiketjun pääkonfiguraatio"""

    conversation_window: ConversationWindow = field(default_factory=ConversationWindow)
    archive_config: ArchiveConfig = field(default_factory=ArchiveConfig)
    summary_config: SummaryConfig = field(default_factory=SummaryConfig)

    # Muistin käyttöasetukset
    use_short_term: bool = True
    use_long_term: bool = True
    enable_auto_summarization: bool = True
    enable_auto_archival: bool = True

    # Hakuasetukset
    max_search_results: int = 5
    similarity_threshold: float = 0.7
    context_window_size: int = 3  # Montako viestiä haetaan ennen/jälkeen osuman

    # Tiivistämisen asetukset
    summary_min_length: int = 50
    summary_max_length: int = 200
    summary_temperature: float = 0.3

    # Tallennusasetukset
    save_format: str = "json"
    compression: bool = True
    backup_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Muunna konfiguraatio sanakirjaksi"""
        return {
            "conversation_window": self.conversation_window.__dict__,
            "archive_config": self.archive_config.__dict__,
            "summary_config": self.summary_config.__dict__,
            "use_short_term": self.use_short_term,
            "use_long_term": self.use_long_term,
            "enable_auto_summarization": self.enable_auto_summarization,
            "enable_auto_archival": self.enable_auto_archival,
            "max_search_results": self.max_search_results,
            "similarity_threshold": self.similarity_threshold,
            "context_window_size": self.context_window_size,
            "summary_min_length": self.summary_min_length,
            "summary_max_length": self.summary_max_length,
            "summary_temperature": self.summary_temperature,
            "save_format": self.save_format,
            "compression": self.compression,
            "backup_enabled": self.backup_enabled,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "MemoryChainConfig":
        """Luo konfiguraatio sanakirjasta"""
        conversation_window = ConversationWindow(
            **config_dict.pop("conversation_window", {})
        )
        archive_config = ArchiveConfig(**config_dict.pop("archive_config", {}))
        summary_config = SummaryConfig(**config_dict.pop("summary_config", {}))
        return cls(
            conversation_window=conversation_window,
            archive_config=archive_config,
            summary_config=summary_config,
            **config_dict,
        )


@dataclass
class ChunkConfig:
    """Configuration for document chunking."""

    chunk_size: int = 1000
    overlap: int = 200  # Muutettu chunk_overlap -> overlap
    min_chunk_size: int = 100

    # Lisäasetukset
    split_by: str = "sentence"  # sentence/paragraph/token/custom
    custom_split_pattern: Optional[str] = None  # Regex pilkkomiseen
    respect_paragraphs: bool = True  # Säilytetäänkö kappalerajat

    # Optimoinnin asetukset
    optimize_chunks: bool = True  # Optimoidaanko palasten kokoa
    target_size: int = 256  # Tavoitekoko optimoinnissa
    size_tolerance: float = 0.2  # Sallittu poikkeama tavoitekoosta

    # Metatietojen käsittely
    include_metadata: bool = True  # Lisätäänkö metatiedot palasiin
    metadata_fields: List[str] = field(
        default_factory=lambda: ["source", "page", "position"]
    )

    # Välimuistin asetukset
    use_cache: bool = True  # Käytetäänkö välimuistia
    cache_dir: str = "memory/cache/chunks"  # Välimuistin sijainti
    cache_ttl: int = 86400  # Välimuistin elinaika sekunteina (24h)

    # Suoritusasetukset
    batch_size: int = 32  # Eräkoko rinnakkaisessa prosessoinnissa
    show_progress: bool = True  # Näytetäänkö edistymispalkki
    num_workers: int = 4  # Rinnakkaisten prosessien määrä

    # Virhetilanteiden käsittely
    max_retries: int = 3  # Uudelleenyrityskerrat virhetilanteissa
    fallback_strategy: str = "token"  # Varastrategia: token/fixed/skip
