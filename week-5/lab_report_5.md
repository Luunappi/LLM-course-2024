# Lab Report 5: RAG Implementation with PDF Support

## Tiivistelmä toteutuksesta

Toteutettu RAG-sovellus vastaa tehtävänannon kohtaan 1 (monikielinen PDF-tuki) ja osittain kohtaan 2 (chunking-algoritmi). Sovellus:
- Tukee PDF-dokumenttien käsittelyä eri kielillä
- Käyttää mukautettua chunking-logiikkaa
- Tarjoaa käyttöliittymän dokumenttien käsittelyyn ja kyselyihin
- Seuraa mallien käyttöä ja suorituskykyä

## Tiedostorakenne

RAG_System/
├── RAG-GUI.py                # Graafinen käyttöliittymä
├── RAG-Orchestrator.py       # Pääsovellus
├── ui_components/            
│   ├── chat_module.py         # Chat-toiminnallisuus
│   ├── rag_module.py          # RAG-toiminnallisuus (mm.tiedostojen lataus)
│   ├── diagram_module.py      # Visualisoinnit
│   ├── info_module.py         # Token/kustannusseuranta
│   ├── prompt_module.py       # Prompt-hallinta
│   └── side_info_module.py    # Sivupaneeli
└── requirements.txt           # Riippuvuudet

## Testaaminen
Käynnistä Streamlit-sovellus seuraavalla komennolla projektin hakemistossa:

```bash
cd week-5/RAG_SupplyChain
streamlit run pdf_rag_ui.py
```

## Tehtävänannon analyysi ja toteutus

### Task 1: Monikielisten PDF-dokumenttien tuki
1. Would the same embedding and LLM work for Finnish?
   - Embedding: sentence-transformers/all-mpnet-base-v2 tukee useita kieliä
   - LLM: GPT-mallit toimivat hyvin suomeksi, mutta chunking vaatii säätöä
   - Testattu suomenkielisillä kysymyksillä ja dokumenteilla

2. What about extracting sentences and chunking?
   - Suomen kielen pidemmät sanat vaikuttavat token-pituuksiin
   - Chunk-kokoa kasvatettiin (min_len=100 -> 150)
   - Lauseiden erottelu toimii myös suomeksi (.!? -merkkien tunnistus)

3. Quality Assessment
   - Vastausten laatu hyvä suomeksi kysyttäessä
   - Embedding-malli löytää relevantit kohdat dokumentista
   - LLM osaa vastata kontekstin perusteella suomeksi

4. Improved Multilingual Support
   - Alkuperäinen ongelma: Suomenkielinen kysely englanninkieliseen dokumenttiin ei tuottanut tarkkoja tuloksia
   - Ratkaisu: Kaksivaiheinen käsittely
     1. Kysymys käännetään dokumentin kielelle semanttista hakua varten
     2. Vastaus käännetään takaisin alkuperäisen kysymyksen kielelle
   - Hyödyt:
     - Tarkempi semanttinen haku dokumentin kielellä
     - Parempi kontekstin säilyminen
     - Luonnollisempi vastaus kysyjän kielellä

### Task 2: Vaihtoehtoinen chunking-algoritmi
1. Does this chunker apply to any language?
   - Nykyinen toteutus tukee useita kieliä
   - Perustuu yleisiin välimerkkeihin (.!?)
   - Säädettävä chunk-koko kielen mukaan

2. Can you assess the quality of chunker?
   - Toimii hyvin perusdokumenteille
   - Ei huomioi dokumentin rakennetta (otsikot, listat)
   - Kehityskohteena semanttinen chunking

3. Impact on RAG pipeline quality?
   - Chunk-koko vaikuttaa hakutarkkuuteen
   - Liian pitkät chunkit heikentävät relevanssia
   - Liian lyhyet chunkit hajottavat kontekstin

### Task 3: Agentic RAG

Vaikka tässä projektissa ei toteutettu agenttipohjaista RAG-ratkaisua suoraan, erillisessä hakemistossa (week-5/AgenticRAG_system) on kokeiltu eräänlaista agenttitoiminnallisuutta RAG:lle. Siellä on testattu mm. agentin ohjaamaa hakua ja vastausten koordinointia. 

Viimeisimpänä löytyi openai:n esimerkkikurssi, jossa sivutaan moniagenttista tapaa toteuttaa toiveita.
-> ks. /references/Reasoning-with-o1/L3.ipynb tai
https://learn.deeplearning.ai/courses/reasoning-with-o1/lesson/4/planning-with-o1
(en ehtinyt testata tätä vielä kunnolla tämän kurssin puitteissa mutta jatkon kannalta mielenkiintoinen)

**Planning**
- Create a plan to solve a task.
- Given a set of tools to carry out the plan and constraints to set bounds around the task.
- This kind of use case would be very slow if we used o1 for every step.
- So what we’ll do is generate a plan with o1-mini, and the execute each step with GPT-4o-mini. 
- This trade-off of intelligence against latency and cost is a practical one that we’ve seen developers use to great effect so far.

**Plan Generation + Execution Architecture**

      **User** -> question / skenario 
      ->  	
      Plan Generation (o1-mini) [instructions of how to build a plan]
      (o1-has build in multi-step reasoning logic to build a durable plan)
      ->	
      Plan Execution (gpt-4o-mini)
      Number of worker (tools which can use to carry out the plan.)
      ->
      Answer to **user**


### Task 4: GraphRAG (ei toteutettu)
- Mahdollinen toteutus:
  - Neo4j tietokanta dokumenttien suhteille
  - Dokumenttien metadata graafiin
  - Graafipohjainen haku


## Toteutuksen tekninen kuvaus

### Implementation Architecture

RAG-toteutus koostuu kolmesta pääkomponentista (dokumenttikäsittely, embedding-pipeline ja LLM) sekä käyttöliittymästä. Komponentit muodostavat putken, jossa dokumentti prosessoidaan, indeksoidaan ja hyödynnetään vastauksien generoinnissa.

```
[PDF Document] -> [Text Extraction] -> [Chunking] -> [Embeddings] -> [Semantic Search] -> [LLM Response]
     |                  |                 |             |                |                    |
     v                  v                 v             v                v                    v
Input file      PyMuPDF extracts    Split text     Create vector    Find relevant     Generate answer
(PDF/TXT)       text content        to chunks      representations   chunks            using context
```

### Components

1. Document Processing (Dokumenttikäsittely)
```python
# Dokumentin tekstin erottaminen ja jakaminen sopiviin paloihin
PyMuPDF (fitz)      # PDF -> text muunnos
re.split()          # Tekstin jako lauseisiin
chunk_text()        # Lauseiden ryhmittely chunkeiksi
```

2. Embedding Pipeline (Vektori-indeksointi)
```python
# Tekstin muuntaminen numeerisiksi vektoreiksi hakua varten
SentenceTransformer # Tekstin -> vektorimuunnos
semantic_search()   # Kosinietäisyyspohjainen haku
torch.tensor        # Vektorilaskenta
```

3. Language Model (Vastausten generointi)
```python
# Kontekstuaalisten vastausten luonti
OpenAI API         # LLM-rajapinta
prompt_template    # Kysymys-konteksti-kehys
token_counter     # Käytön seuranta
```

4. User Interface (Käyttöliittymä)
```python
# Streamlit-pohjainen käyttöliittymä
file_upload       # Dokumenttien lataus
chat_module       # Kysymys-vastaus
debug_info        # Suorituskykytiedot
```

### Key Features

1. Multi-language Support
   - Document processing works with different languages
   - Embedding model handles multiple languages
   - LLM generates responses in query language

2. Improved Processing
   - Adjusted chunking for different languages
   - Document caching for efficiency
   - Progress tracking and error handling

3. User Experience
   - Clear processing status
   - Language-aware responses
   - Debug information available

## Dependencies
See requirements.txt for full list of dependencies.

## Notes
- Test with different languages
- Monitor token usage
- Adjust chunk sizes based on language

### Semantic Search 

Tekniikan toimintaperiaate:
1. Vektorien normalisointi
   - Muunnetaan embeddings-vektorit yksikkövektoreiksi
   - Mahdollistaa kosinietäisyyden laskennan pistetulolla

2. Kosinietäisyys
   - Mittaa vektorien välistä kulmaa
   - Arvo välillä [-1, 1], missä 1 = täysin samansuuntaiset
   - Toteutettu normalisoitujen vektorien pistetulona

3. Top-k valinta
   - Valitaan k kappaletta parhaiten täsmääviä tekstikappaleita
   - Järjestetään similariteetin mukaan laskevasti

Hyödyt:
- Nopea laskenta torch-operaatioilla
- Skaalautuu suuriin dokumentteihin
- Kieliriippumaton toiminta

Rajoitukset:
- Ei huomioi kappaleiden järjestystä
- Ei ymmärrä kontekstin jatkuvuutta
- Perustuu puhtaasti vektorien samankaltaisuuteen