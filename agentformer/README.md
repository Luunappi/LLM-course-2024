# AgentFormer - Modulaarinen Tekoälyagenttijärjestelmä

## Yleiskuvaus

AgentFormer on modulaarinen tekoälyagenttijärjestelmä, joka yhdistää:
- Useita kielimalleja (LLM)
- Kontekstuaalisen muistin
- Työkaluintegraatiot
- Vastausten laadun evaluoinnin

Järjestelmä on suunniteltu erityisesti:
- Akateemiseen tutkimukseen
- Opetuskäyttöön
- Tekoälyagenttien kehittämiseen

## Arkkitehtuuri

### Ydinkomponentit

1. **Orchestrator**
   - Hallinnoi viestinvälitystä komponenttien välillä
   - Koordinoi työkalujen käyttöä
   - Ylläpitää järjestelmän tilaa

2. **Memory Manager** 
   - Hierarkkinen muistijärjestelmä
   - Tukee eri muistityyppejä:
     - Core (ydinmuisti)
     - Semantic (semanttinen muisti)
     - Episodic (episodinen muisti)
     - Working (työmuisti)

3. **Model Module**
   - Kielimallien hallinta
   - Tukee useita malleja:
     - GPT-4
     - Claude
     - Muut OpenAI/Anthropic mallit
   - Dynaaminen mallin valinta

4. **CEval (Contextual Evaluator)**
   - Arvioi vastausten laatua
   - Mittaa:
     - Relevanssia
     - Faktuaalisuutta
     - Johdonmukaisuutta
     - Kontekstin käyttöä

### Työkalut

1. **RAG Tool**
   - Retrieval Augmented Generation
   - Dokumenttien haku ja indeksointi
   - Kontekstin rikastaminen

2. **Diagram Tool**
   - Kaavioiden luonti ja muokkaus
   - Tukee useita kaaviotyyppejä
   - Mermaid-syntaksi

### Evaluointi ja laadunvarmistus

Järjestelmä käyttää ceval.py-moduulia vastausten laadun arviointiin:

1. **Vastausten evaluointi**
   ```python
   from core.ceval import CEval
   
   evaluator = CEval()
   score = evaluator.evaluate_response(
       question="Mikä on pääkaupunki?",
       response="Helsinki on Suomen pääkaupunki",
       context="Suomen pääkaupunki on Helsinki"
   )
   ```

2. **Evaluointikriteerit**
   - Vastauksen relevanssi kysymykseen
   - Kontekstin hyödyntäminen
   - Faktojen oikeellisuus
   - Vastauksen selkeys ja ymmärrettävyys

3. **Suorituskykymittarit**
   - Vastausaika
   - Muistin käyttö
   - API-kutsujen määrä
   - Vastausten laatu

## Asennus

### Vaatimukset

- Python 3.9+
- pip
- virtualenv (suositeltu)

### Perusasennus

1. Kloonaa repositorio:
```bash
git clone https://github.com/yourusername/agentformer.git
cd agentformer
```

2. Luo virtuaaliympäristö:
```bash
python -m venv venv
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows
```

3. Asenna riippuvuudet:
```bash
pip install -r requirements.txt
pip install -r test_requirements.txt  # testiriippuvuudet
```

### Konfigurointi

1. Kopioi config-template:
```bash
cp config/api_config.example.json config/api_config.json
```

2. Lisää API-avaimet:
```json
{
    "openai": {
        "api_key": "your-key-here"
    },
    "anthropic": {
        "api_key": "your-key-here"
    }
}
```

## Kehitys

### Testaus

1. Aja kaikki testit:
```bash
python -m pytest tests/
```

2. Aja tietty testitiedosto:
```bash
python -m pytest tests/test_basic.py
```

3. Testikattavuusraportti:
```bash
python -m pytest --cov=agentformer --cov-report=html
```

### Koodityyli

- Käytä black-formatointia:
```bash
black .
```

- Tarkista tyylit:
```bash
flake8 .
```

### Dokumentaatio

- Google-tyylinen docstring
- Tyyppiannotaatiot pakollisia
- Kommentoi monimutkaiset algoritmit

## Käyttö

### Web-käyttöliittymä

1. Käynnistä palvelin:
```bash
python agentformer_web.py
```

2. Avaa selaimessa:
```
http://localhost:5000
```

### Python API

```python
from core.orchestrator import AgentFormerOrchestrator

# Alusta järjestelmä
orchestrator = AgentFormerOrchestrator()

# Lähetä viesti
response = orchestrator.process_request(
    "chat",
    {"message": "Kerro Helsingistä"}
)

# Tarkista tila
state = orchestrator.get_memory_state()
```

## Kontribuutiot

1. Fork-repository
2. Luo feature branch
3. Tee muutokset
4. Aja testit
5. Tee pull request

## Lisenssi

MIT License - katso LICENSE.md

## Yhteystiedot

- Issue Tracker: https://github.com/yourusername/agentformer/issues
- Wiki: https://github.com/yourusername/agentformer/wiki

## Kiitokset

- OpenAI
- Anthropic
- Muut kontribuuttorit

## 8. Testit

### Testien rakenne

1. **Perustestit (test_system_core.py)**
   - Mallien konfiguraation testaus
   - Muistin alustuksen testaus

2. **Mallitestit (test_model_integration.py)**
   - API-kutsujen parametrien validointi
   - Mallin vaihdon vaikutus parametreihin
   - API-virhetilanteiden käsittely

3. **Evaluointitestit (test_evaluation.py)**
   - Kontekstin käytön arviointi
   - Vastausten relevanssin mittaus
   - Faktojen tarkistus
   - Selkeyden arviointi

4. **Web-käyttöliittymätestit (test_web_interface.py)**
   - HTTP-endpointit
   - Viestien käsittely
   - Tilanhallinta
   - Virhetilanteet

### Testien ajo

```bash
# Asenna testiriippuvuudet
pip install -r test_requirements.txt

# Aja kaikki testit
python -m pytest tests/

# Aja tietty testitiedosto
python -m pytest tests/test_web_interface.py
```
