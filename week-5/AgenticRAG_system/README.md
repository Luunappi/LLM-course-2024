# AgenticRAG System

Modulaarinen ja laajennettava RAG (Retrieval-Augmented Generation) järjestelmä, joka hyödyntää agenttipohjaista arkkitehtuuria ja pub/sub-viestintää. Järjestelmä on optimoitu erityisesti Apple Silicon -prosessoreille.

## Järjestelmän rakenne 

Tämän rakenteen edut:
1. Selkeä vastuunjako:
- OrchestratorAgent vastaa työnkulun koordinoinnista
- PubSubSystem hoitaa viestinnän
- AgenticRAG toimii kevyenä fasadina/julkisena rajapintana
2. Modulaarisuus:
- Jokainen komponentti on itsenäinen ja helposti testattava
- Uusien agenttien lisääminen on helppoa
- Viestintälogiikka on eriytetty
3. Laajennettavuus:
- PubSub-järjestelmä mahdollistaa uusien kuuntelijoiden lisäämisen
- Orkestroijaan voi helposti lisätä uusia prosessointivaiheita
- Agentteja voi vaihtaa tai päivittää muuttamatta muuta koodia
4. Ylläpidettävyys:
- Selkeä tiedostorakenne helpottaa navigointia
- Yksittäiset komponentit ovat pienempiä ja helpommin ymmärrettäviä
- Testaus voidaan kohdistaa tarkasti eri komponentteihin

AgenticRAG_system/
├── agents/
│ ├── init.py
│ ├── orchestrator_agent.py # Koordinoi agenttien toimintaa
│ ├── text_agent.py # Tekstin käsittely ja RAG-haut
│ └── image_agent.py # Kuvien analysointi (BLIP2)
├── messaging/
│ ├── init.py
│ └── pubsub.py # Pub/Sub-viestintäjärjestelmä
├── AgenticRAG.py # Pääluokka ja julkinen rajapinta
├── AgenticRAG_UI.py # Streamlit-käyttöliittymä
└── README.md

## Komponentit ja niiden vastuut

### Agentit

#### OrchestratorAgent (orchestrator_agent.py)
- Koordinoi eri agenttien toimintaa
- Hallinnoi dokumenttien prosessointityönkulkua
- Yhdistää eri agenttien tulokset
- Kommunikoi pub/sub-järjestelmän kautta

#### TextAgent (text_agent.py)
- Tekstidokumenttien käsittely
- RAG-haut ja vastausten generointi
- Embedding-laskenta ja relevanttien chunkkien haku

#### ImageAgent (image_agent.py)
- Kuvien analysointi BLIP2-mallilla
- Tukee eri kuvaformaatteja ja syöttötapoja
- Optimoitu Apple Silicon -prosessoreille (MPS-backend)

### Viestintä

#### PubSubSystem (pubsub.py)
- Tapahtumapohjainen viestintäjärjestelmä
- Mahdollistaa agenttien välisen löyhän kytkennän
- Tukee subscribe/publish/unsubscribe -operaatioita

### Pääkomponentit

#### AgenticRAG (AgenticRAG.py)
- Järjestelmän julkinen rajapinta
- Alustaa ja koordinoi komponentit
- Tarjoaa helppokäyttöisen API:n RAG-hakuihin

#### AgenticRAG_UI (AgenticRAG_UI.py)
- Streamlit-pohjainen käyttöliittymä
- PDF-dokumenttien lataus ja prosessointi
- Interaktiivinen kysely-vastaus -toiminnallisuus

## Käyttöönotto

1. Asenna tarvittavat riippuvuudet:
bash
pip install -r requirements.txt

2. Varmista, että sinulla on tarvittavat mallit:
- BLIP2 (image_agent.py)
- Embedding-malli (text_agent.py)
- LLM-malli (text_agent.py)

3. Käynnistä Streamlit UI:

bash
streamlit run AgenticRAG_UI.py

bash
streamlit run AgenticRAG_UI.py

## Esimerkkikäyttö koodissa

python
from AgenticRAG import AgenticRAG
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer

## Alusta mallit
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
llm_model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3")
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3")

## Luo AgenticRAG-instanssi
rag = AgenticRAG(
embedding_model=embedding_model,
llm_model=llm_model,
tokenizer=tokenizer,
device="mps" # tai "cpu" tai "cuda"
)
## Suorita haku
result = rag.run_agentic_search(
query="Mitä dokumentissa kerrotaan tekoälystä?",
df=document_dataframe,
embeddings_tensor=embeddings
)

## Testaus

Järjestelmän testit sijaitsevat `tests/`-hakemistossa. Testit on toteutettu käyttäen Pythonin unittest-kehystä ja pytest-työkalua.

### Testien rakenne

tests/
├── test_image_agent.py # Kuva-agentin testit
├── test_text_agent.py # Tekstiagentin testit
├── test_orchestrator.py # Orkestroija-agentin testit
└── test_pubsub.py # Pub/Sub-järjestelmän testit

### Yksikkötestit

#### ImageAgent (test_image_agent.py)
- `test_analyze_image_with_pil_image`: Testaa kuva-analyysiä PIL Image -muotoisella syötteellä
  - Varmistaa että analyysi palauttaa merkkijonon
  - Tarkistaa että tulos ei ole tyhjä
- `test_analyze_image_with_invalid_input`: Testaa virheenkäsittelyä väärällä syötetyypillä
  - Varmistaa että ValueError nostetaan kun syöte on väärän tyyppinen

#### TextAgent (test_text_agent.py)
- `setUpClass`: Alustaa jaetut mallit testisarjalle
  - Lataa embedding-mallin (all-mpnet-base-v2)
  - Lataa kevyen LLM-mallin (distilgpt2) testausta varten
- `test_process_valid_input`: Testaa tekstin prosessointia validilla syötteellä
  - Varmistaa että prosessointi palauttaa sanakirjan
  - Käyttää mock-embeddings-tensoria simuloimaan oikeaa dataa

#### OrchestratorAgent (test_orchestrator.py)
- `test_process_document_with_text`: Testaa dokumentin prosessointia tekstisisällöllä
  - Käyttää mock-objekteja text_agent ja image_agent -komponenteille
  - Varmistaa että text_agent.process() kutsutaan oikeilla parametreilla
  - Tarkistaa että pubsub.publish() kutsutaan asianmukaisesti

#### PubSubSystem (test_pubsub.py)
- `test_subscribe_and_publish`: Testaa tilausta ja julkaisua
  - Varmistaa että callback-funktio kutsutaan julkaistaessa
  - Tarkistaa että data välittyy oikein tilaajalle
- `test_unsubscribe`: Testaa tilauksen peruutusta
  - Varmistaa että callback ei enää kutsu peruutuksen jälkeen

### Testien ajaminen

1. Asenna testiriippuvuudet:
```bash
pip install -r requirements-test.txt
```

2. Asenna paketti kehitystilassa:
```bash
pip install -e .
```

3. Aja testit:
```bash
# Kaikki testit
pytest

# Yksittäinen testitiedosto
pytest tests/test_image_agent.py

# Testit kattavuusraportilla
pytest --cov=.

# Testit verbose-tilassa
pytest -v
```

### Testien laajentaminen

Uusia testejä lisätessä huomioi:
- Käytä mock-objekteja raskaiden komponenttien simulointiin
- Testaa virhetilanteet ja rajatapaukset
- Varmista että testit ovat toistettavia
- Dokumentoi testien tarkoitus docstringeissä

### Huomioita testauksesta

- Testit käyttävät CPU-laitetta MPS:n sijaan yhteensopivuuden vuoksi
- Raskaiden mallien sijaan käytetään kevyempiä vaihtoehtoja (esim. DistilGPT2)
- Pub/Sub-testit varmistavat viestinnän toimivuuden
- Mock-objekteja käytetään ulkoisten riippuvuuksien simulointiin

Tämä dokumentaatio auttaa kehittäjiä ymmärtämään:
- Mitä kukin testi testaa
- Miten testit ajetaan
- Miten testejä voi laajentaa
- Mitä erityishuomioita testauksessa on tehty

## Riippuvuudet

- PyPDF2 (vanhentunut)
+ pypdf (PDF-tiedostojen käsittelyyn)
streamlit (käyttöliittymä)
torch (koneoppimismallit)
...

