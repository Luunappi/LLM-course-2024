# MemoryRAG

MemoryRAG on kehittynyt RAG (Retrieval-Augmented Generation) toteutus, joka yhdistää hierarkkisen muistin ja älykkään kontekstin hallinnan. Se on suunniteltu parantamaan LLM-mallien vastausten laatua ja johdonmukaisuutta.

## Asennus

```bash
# Kloonaa repositorio
git clone https://github.com/yourusername/MemoryRAG.git
cd MemoryRAG

# Asenna riippuvuudet
pip install -e .
```

## Käyttöesimerkit

### 1. Peruskäyttö
```python
from memoryrag import MemoryRAG

# Alusta MemoryRAG
rag = MemoryRAG()

# Lisää tietoa eri muistityyppeihin
rag._store_memory(
    "core",
    "Tekoäly on tietokoneiden kyky simuloida älykästä toimintaa",
    importance=1.0
)

rag._store_memory(
    "semantic",
    "Tekoäly kehitettiin 1950-luvulla",
    importance=0.7
)

# Tee kysely
response = rag.process_query("Mitä on tekoäly ja milloin se kehitettiin?")
print(response)
```

### 2. Dokumenttien käsittely
```python
# Lue dokumentti ja jaa se kappaleisiin
doc_path = Path("docs/article.txt")
with open(doc_path) as f:
    text = f.read()
    
# Tallenna kappaleet semanttiseen muistiin
for i, para in enumerate(text.split("\n\n")):
    importance = 0.8 if i == 0 else 0.7
    rag._store_memory("semantic", para, importance)
```

### 3. Muistin optimointi
```python
# Tiivistä semanttinen muisti
compressed = rag.memory_manager.compress_memories(
    rag.memory_types["semantic"]
)

# Päivitä muisti tiivistetyllä versiolla
rag.memory_types["semantic"] = compressed
```

## Ominaisuudet

### 1. Hierarkkinen muisti
- **Core (Ydinmuisti)**
  - Kriittiset ja pysyvät tiedot
  - Korkein prioriteetti (1.0)
  - Hidas vanheneminen (365 päivää)

- **Semantic (Semanttinen muisti)**
  - Yleistieto ja faktat
  - Keskitason prioriteetti (0.7-0.8)
  - Keskitason vanheneminen (30 päivää)

- **Episodic (Episodinen muisti)**
  - Keskusteluhistoria
  - Matalampi prioriteetti (0.6)
  - Nopea vanheneminen (1 päivä)

- **Working (Työmuisti)**
  - Nykyinen konteksti
  - Dynaaminen prioriteetti
  - Erittäin nopea vanheneminen (5 minuuttia)

### 2. Älykäs kontekstin hallinta
- Dynaaminen tokenien jako
- Automaattinen optimointi
- Relevantin tiedon priorisointi

### 3. Semanttinen haku
- Embedding-pohjainen muistin haku
- Kosinisamankaltaisuuden laskenta
- Fallback yksinkertaiseen hakuun

## Konfigurointi

1. Luo .env tiedosto projektin juureen:
```
OPENAI_API_KEY=your-api-key-here
```

2. Säädä muistin parametreja tarvittaessa:
- Muistin vanhenemisajat (memory_manager.py)
- Token-budjetin jako (context_manager.py)
- Hakuparametrit (memory_rag.py)

## Lisätietoja

Katso tarkemmat API-dokumentaatiot ja lisäesimerkit [docs/API.md](docs/API.md)

## Lisenssi

MIT 