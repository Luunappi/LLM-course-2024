# AgenticAI

Retrieval Augmented Generation (RAG) -pohjainen keskustelujärjestelmä, joka hyödyntää E5-mallia dokumenttien hakuun ja GPT-mallia vastausten generointiin.

## Ominaisuudet

### Dokumenttien käsittely
- Tuki useille tiedostomuodoille (TXT, PDF, Markdown)
- Automaattinen merkistökoodauksen tunnistus
- Dokumenttien persistointi ja indeksointi
- Dokumenttien hallinta käyttöliittymässä

### Kyselytyypit
1. **RAG-haku** 
   - Hakee relevantit kohdat dokumenteista
   - Generoi vastauksen kontekstin perusteella
   - Näyttää käytetyt lähteet
   - Eri mallit eri vaiheisiin (Openai)
        - GPT-4o (yksinkertaiset tehtävät)
        - o1-mini  (keskisnkertaiset tehtävät)
        - o1 (vaikeat tehtävät)

2. **Suora LLM-kysely** (oletus)
   - Kysyy suoraan kielimallilta
   - Ei käytä dokumentteja kontekstina
   - Käytettävä kielimalli: Openai (o1-mini)  

3. **Dokumenttien yhteenveto**
   - Generoi yhteenvedon ladatuista dokumenteista
   - Näyttää käytetyt dokumentit
   - Käytettävä kielimalli: Openai (o1-mini)  

### Prosessin seuranta
- Reaaliaikainen prosessin tilan näyttö
- Sekuntikohtainen ajanseuranta
- Token-käytön ja kustannusten arviointi
- Yksityiskohtaiset prosessitiedot laajennettavassa näkymässä


## Käyttö
Käynnistä sovellus:
```bash
streamlit run src/main.py
```

### Dokumenttien lisäys
1. Käytä sivupaneelin "Lataa dokumentti" -toimintoa
2. Tuetut tiedostomuodot: TXT, PDF, Markdown
3. Dokumentit indeksoidaan automaattisesti
4. Näet ladatut dokumentit sivupaneelissa

### Kyselyiden tekeminen
1. Valitse kyselytyyppi sivupaneelista:
   - RAG (haku dokumenteista)
   - Suora kysely LLM:lle
   - Yhteenveto dokumenteista

2. Kirjoita kysymyksesi chat-kenttään
3. Seuraa prosessin etenemistä info-palkista
4. Tarkastele vastauksen lähteitä ja lisätietoja laajennettavista näkymistä

## Tekninen rakenne

### Core 
- Event System: Tapahtumapohjainen kommunikaatio
- Orchestrator: Agenttien koordinointi

### Agents
- BaseAgent: Perusagentti tapahtumakäsittelyllä
- RAGAgent: RAG-toiminnallisuuden kapselointi

### RAG 
- Retriever: Dokumenttien haku E5-mallilla
- Generator: Vastausten generointi GPT-mallilla
- Manager: RAG-toiminnallisuuden koordinointi

### UI 
- RAGChatUI: Streamlit-pohjainen käyttöliittymä
- FileManager: Tiedostojen hallinta
- ProcessTracker: Prosessien seuranta

## Kehitys

### Testaus
```bash
# Yksikkötestit
pytest tests/unit -v -m "unit"

# Integraatiotestit
pytest tests/integration -v -m "integration"

# Kaikki testit ja kattavuusraportti
pytest tests/unit tests/integration -v --cov=src/agentic --cov-report=term-missing
```

### Seuraavat kehityskohteet
1. Yhteenvedon generoinnin toteutus
2. PDF-tiedostojen tuki
3. Token-käytön optimointi
4. Käyttöliittymän kustomointi 

## Rakenne ja Testauksen Tila

```
AgenticAI/
├── src/agentic/
│   ├── __init__.py           # Paketin päämoduuli [✓]
│   ├── core/                 # Ydinkomponentit
│   │   ├── __init__.py      # [✓]
│   │   ├── events.py        # Event ja EventBus toteutukset [✓]
│   │   └── orchestrator.py  # Agenttien koordinointi [✓]
│   ├── agents/              # Agenttitoteutukset
│   │   ├── __init__.py      # [✓]
│   │   ├── base_agent.py    # BaseAgent-luokka [✓]
│   │   └── rag_agent.py     # RAG-agentti [✓]
│   ├── rag/                 # RAG-komponentit
│   │   ├── __init__.py      # [✓]
│   │   ├── retriever.py     # Dokumenttien haku (E5) [✓]
│   │   ├── generator.py     # Vastausten generointi (GPT) [✓]
│   │   └── manager.py       # RAG koordinointi [✓]
│   └── ui/                  # Käyttöliittymät
│       ├── __init__.py      # [✓]
│       ├── components/      # UI komponentit
│       │   ├── file_manager.py    # Tiedostojen hallinta [✓]
│       │   └── process_tracker.py # Prosessien seuranta [✓]
│       └── rag_chat.py      # Streamlit UI [✓]
``` 