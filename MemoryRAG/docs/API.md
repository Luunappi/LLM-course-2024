# MemoryRAG API Documentation

## Yleiskatsaus
MemoryRAG on järjestelmä, joka yhdistää:
- RAG-pohjaisen tiedonhaun
- Hierarkkisen muistin
- Dokumenttien prosessoinnin

## Pääkomponentit

### Orchestrator
Järjestelmän ydin, joka koordinoi muita komponentteja.

```python
from memoryrag import orchestrator

# Alustetaan perusasetuksilla
rag = await orchestrator.create()

# Tai määritellyllä mallilla
rag = await orchestrator.create(model_name="gpt-4o-mini")
```

#### Tärkeimmät metodit

##### process_query
```python
async def process_query(query: str) -> str:
    """
    Käsittelee kyselyn ja palauttaa vastauksen.
    
    Args:
        query (str): Käyttäjän kysymys
        
    Returns:
        str: Vastaus perustuen muistiin ja kontekstiin
    """
```

##### load_document
```python
async def load_document(file_path: str):
    """
    Lataa dokumentin ja tallentaa sen semanttiseen muistiin.
    
    Args:
        file_path (str): Polku dokumenttiin (.pdf, .docx, .txt)
    """
```

### Muistin hallinta

#### Muistityypit
- core: Kriittiset faktat (importance: 0.8-1.0)
- semantic: Yleistieto (importance: 0.5-0.8)
- episodic: Keskusteluhistoria (importance: 0.3-0.6)
- working: Nykyinen konteksti (importance: 0.1-0.4)

#### Muistin tallennus
```python
await rag._store_memory(
    memory_type: str,  # "core", "semantic", "episodic", "working"
    content: str,      # Tallennettava sisältö
    importance: float  # 0.0-1.0
)
```

### Mallit ja konfiguraatio

#### Tuetut LLM-mallit
- gpt-4o-mini: Yleiskäyttöinen (oletus)
- o1-mini: Kevyt reasoning
- o1: Vaativa reasoning

#### Embedding-malli
- all-mpnet-base-v2 (768d)
- Optimoitu semantic search -käyttöön
- MIT-lisenssi

## Esimerkkejä

### Peruskäyttö
```python
# Alustus
rag = await RAGOrchestrator.create()

# Dokumentin lataus
await rag.load_document("data/article.pdf")

# Kysely
response = await rag.process_query("Mitä dokumentti kertoo aiheesta X?")
print(response)
```

### Muistin käyttö
```python
# Tallennus eri muistityyppeihin
await rag._store_memory("core", "Tärkeä fakta", 1.0)
await rag._store_memory("semantic", "Yleistieto", 0.7)

# Muistin tilan tarkastelu
state = rag.get_memory_state()
print(state)
``` 