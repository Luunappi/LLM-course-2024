# MemoryRAG API Documentation

## Yleiskatsaus

MemoryRAG on kehittynyt RAG-toteutus, joka yhdistää hierarkkisen muistin ja älykkään kontekstin hallinnan.

## Core Classes

### MemoryRAG

Pääluokka muistin ja kyselyiden hallintaan.

#### Metodit

- `process_query(query: str) -> str`
  - Käsittelee kyselyn ja palauttaa vastauksen
  - Tallentaa kyselyn työmuistiin
  - Rakentaa kontekstin älykkäästi
  - Tallentaa vastauksen episodiseen muistiin

- `_store_memory(memory_type: str, content: str, importance: float)`
  - Tallentaa muistin tiettyyn muistityyppiin
  - Parametrit:
    - memory_type: "core", "semantic", "episodic", "working"
    - content: Muistin sisältö
    - importance: Tärkeys (0.0-1.0)

- `_search_memories(query: str, memories: List[Dict]) -> List[Dict]`
  - Hakee relevantit muistit embeddingiä käyttäen
  - Järjestää tulokset tärkeyden ja samankaltaisuuden mukaan

### MemoryManager

Hallinnoi muistin priorisointia ja tiivistystä.

#### Metodit

- `compress_memories(memories: List[Dict]) -> List[Dict]`
  - Tiivistää samankaltaiset muistit
  - Käyttää LLM:ää tiivistykseen
  - Säilyttää tärkeimmät tiedot

- `update_importance(memory_item: Dict) -> float`
  - Päivittää muistin tärkeyden ajan mukaan
  - Huomioi muistityypin vanhenemisnopeuden

### ContextManager

Hallinnoi kontekstin rakentamista.

#### Metodit

- `build_context(query: str, max_tokens: int = 2000) -> str`
  - Rakentaa optimaalisen kontekstin kyselylle
  - Analysoi kyselyn tyypin
  - Jakaa token-budjetin dynaamisesti

## Muistityypit

### Core Memory
- Kriittiset, pysyvät tiedot
- Korkein prioriteetti (1.0)
- Hidas vanheneminen (365 päivää)
- Esimerkki: Perusmääritelmät, tärkeät faktat

### Semantic Memory
- Yleistieto ja faktat
- Keskitason prioriteetti (0.7-0.8)
- Keskitason vanheneminen (30 päivää)
- Esimerkki: Taustatiedot, yleiset konseptit

### Episodic Memory
- Keskusteluhistoria
- Matalampi prioriteetti (0.6)
- Nopea vanheneminen (1 päivä)
- Esimerkki: Aiemmat kysymys-vastaus-parit

### Working Memory
- Nykyinen konteksti
- Dynaaminen prioriteetti
- Erittäin nopea vanheneminen (5 min)
- Esimerkki: Nykyinen kysely

## Käyttöesimerkit

### 1. Peruskäyttö
```python
from memoryrag import MemoryRAG

rag = MemoryRAG()

# Lisää tietoa
rag._store_memory("core", "Tärkeä fakta", 1.0)
rag._store_memory("semantic", "Taustatietoa", 0.7)

# Tee kysely
response = rag.process_query("Mitä tiedät tästä?")
```

### 2. Dokumenttien käsittely
```python
from memoryrag import MemoryRAG
from pathlib import Path

def process_document():
    rag = MemoryRAG()
    
    # Lue dokumentti
    doc_path = Path("docs/article.txt")
    with open(doc_path) as f:
        text = f.read()
    
    # Jaa dokumentti kappaleisiin
    paragraphs = text.split("\n\n")
    
    # Tallenna kappaleet semanttiseen muistiin
    for i, para in enumerate(paragraphs):
        # Tärkeämmät kappaleet alkuun
        importance = 0.8 if i == 0 else 0.7
        rag._store_memory("semantic", para, importance)
    
    # Tee kysely dokumentista
    response = rag.process_query("Mikä on dokumentin päätulos?")
    print(response)
```

### 3. Keskusteluhistorian käyttö
```python
def chat_session():
    rag = MemoryRAG()
    
    # Tallenna taustatietoa
    rag._store_memory(
        "core",
        "Projekti X on ohjelmistokehitysprojekti, joka alkoi 2023",
        importance=1.0
    )
    
    # Keskustelu
    questions = [
        "Mikä on Projekti X?",
        "Milloin se alkoi?",
        "Mitä siinä on saavutettu?",
    ]
    
    for question in questions:
        # Jokainen kysely hyödyntää aiempaa kontekstia
        response = rag.process_query(question)
        print(f"Q: {question}")
        print(f"A: {response}\n")
        
        # Tarkista episodinen muisti
        print("Keskusteluhistoria:")
        for mem in rag.memory_types["episodic"]:
            print(f"- [{mem['importance']:.1f}] {mem['content']}")
```

### 4. Muistin optimointi
```python
def optimize_memory():
    rag = MemoryRAG()
    
    # Lisää paljon samankaltaista tietoa
    versions = [
        "Python 3.8 julkaistiin 2019",
        "Python 3.9 toi parannuksia 2020",
        "Python 3.10 lisäsi match-lausekkeen 2021",
        "Python 3.11 paransi suorituskykyä 2022"
    ]
    
    for v in versions:
        rag._store_memory("semantic", v, 0.7)
    
    # Tiivistä muisti
    before_count = len(rag.memory_types["semantic"])
    rag.memory_types["semantic"] = rag.memory_manager.compress_memories(
        rag.memory_types["semantic"]
    )
    after_count = len(rag.memory_types["semantic"])
    
    print(f"Muisteja ennen: {before_count}")
    print(f"Muisteja tiivistyksen jälkeen: {after_count}")
```

### 5. Dynaaminen kontekstin hallinta
```python
def demonstrate_context():
    rag = MemoryRAG()
    
    # Lisää erilaista tietoa
    rag._store_memory("core", "AI on tekoäly", 1.0)
    rag._store_memory("semantic", "AI kehitettiin 1950", 0.8)
    rag._store_memory("semantic", "AI käyttää koneoppimista", 0.7)
    
    # Kokeile eri kysymystyyppejä
    questions = [
        "Mitä AI on?",  # Määritelmä -> core-painotus
        "Miten AI toimii?",  # Prosessi -> semantic-painotus
        "Milloin AI kehitettiin?",  # Aika -> episodic-painotus
    ]
    
    for q in questions:
        # Näytä kontekstin rakentuminen
        context = rag.context_manager.build_context(q)
        print(f"\nKysymys: {q}")
        print(f"Konteksti:\n{context}")
        
        # Tee kysely
        response = rag.process_query(q)
        print(f"Vastaus: {response}")
```

### 6. Virheenkäsittelyn testaus
```python
def test_error_handling():
    rag = MemoryRAG()
    
    try:
        # Kokeile virheellistä muistityyppiä
        rag._store_memory("invalid_type", "test", 1.0)
    except KeyError as e:
        print(f"Virheellinen muistityyppi: {e}")
    
    # Kokeile liian pitkää kontekstia
    huge_text = "x" * 10000
    context = rag.context_manager._truncate_context(huge_text, 100)
    print(f"Tiivistetyn kontekstin pituus: {len(context)}")
    
    # Testaa fallback-toiminnallisuutta
    rag.client = None  # "Riko" OpenAI client
    results = rag._search_memories("test", [{"content": "test", "importance": 1.0}])
    print("Fallback-haku toimii:", len(results) > 0)
```

## Virheenkäsittely

Kaikki metodit sisältävät virheenkäsittelyn ja fallback-toiminnallisuuden:
- Semanttinen haku -> yksinkertainen tekstihaku
- LLM-tiivistys -> alkuperäinen muisti
- Kontekstin rakennus -> yleiset painotukset 