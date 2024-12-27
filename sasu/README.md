# MemoryFormer Architecture

MemoryFormer on arkkitehtuuri, joka mahdollistaa LLM (Large Language Model) -pohjaisten muistien luomisen ja hallinnan. Järjestelmä on suunniteltu erityisesti xApp-sovellusten tarpeisiin, mahdollistaen tapahtumapohjaisen prosessoinnin ja analyysin.

## Tiedostot ja niiden toiminnallisuudet

### Ydinkomponentit

**dynamicDistLLMMemory.py**
- Järjestelmän ydinkomponentti
- Toteuttaa dynaamisen LLM-muistin toiminnallisuuden
- Hallinnoi tapahtumien käsittelyä, sisällön päivitystä ja LLM-operaatioita
- Sisältää rajapinnat LLM-mallien käyttöön ja tapahtumien käsittelyyn

**memformer3.py**
- MemoryFormer-arkkitehtuurin pääkomponentti
- Generoi LLM-muisteja annettujen määritysten perusteella
- Sisältää toiminnallisuuden muistin optimointiin ja auditointiin
- Toteuttaa muistien generoinnin ja validoinnin

### Apukomponentit

**events.py**
- Toteuttaa tapahtumavälittäjän (Event Broker)
- Mahdollistaa hajautetun viestinvälityksen ZMQ:n avulla
- Hallinnoi tilaaja-julkaisija -mallin mukaista viestinvälitystä
- Tukee asynkronista viestinvälitystä

**ceval.py**
- Turvallinen Python-koodin suoritusympäristö
- Mahdollistaa dynaamisen koodin suorituksen rajoitetussa ympäristössä
- Sisältää whitelisting-mekanismin sallituille operaatioille
- Tukee perustietorakenteiden ja matemaattisten operaatioiden käyttöä

### Esimerkit ja testit

**KPI-slices.py**
- Esimerkki KPI-mittareiden käsittelystä
- Demonstroi muistin käyttöä verkon suorituskykymittareiden analysoinnissa
- Näyttää kuinka käsitellä pakettihäviötä, latenssia ja suorituskykyä

**classify.py**
- Esimerkki tapahtumien luokittelusta
- Näyttää kuinka MemoryFormer voi käsitellä ja luokitella tapahtumia
- Demonstroi LLM-pohjaista luokittelua

**xappbench.py**
- Suorituskykytestaustyökalu
- Vertailee LLM- ja koodipohjaisten toteutusten suorituskykyä
- Sisältää työkalut suoritusaikojen ja muistinkäytön mittaamiseen

**dist-test.py**
- Hajautetun järjestelmän testaustiedosto
- Demonstroi hajautettua tapahtumankäsittelyä
- Testaa ZMQ-pohjaista viestinvälitystä

## Käyttöönotto ja käyttö

1. Asenna tarvittavat riippuvuudet:
```bash
pip install -r requirements.txt
```

Tärkeimmät riippuvuudet:
- ZMQ (PyZMQ >= 25.1.1)
- LiteLLM >= 1.15.4
- NetworkX >= 3.2.1
- NumPy >= 1.26.3
- BeautifulSoup4 >= 4.12.2

2. LLM-palvelimen vaatimukset:
- Ollama (versio >= 0.1.27)
- Tuetut mallit: llama2, nemotron, mistral
- Palvelimen oletusportti: 11434
- Minimivaatimus RAM: 16GB

Käynnistä Ollama:
```bash
ollama serve
```

3. Perusesimerkki muistin luomisesta:

```python
from dynamicDistLLMMemory import DynamicDistLLMMemory

# Määritä ohjeet ja sisältö
instruction_text = [
    {"command": "SUBSCRIBE", "event": "event_type", "anchor": "data_anchor"},
    {"command": "LLM-TRIGGER", "event": "event_type", "prompt": "Analyze data", 
     "anchor": "analysis", "scope": "data_anchor"}
]

contents_text = {
    "data_anchor": "",
    "analysis": ""
}

# Luo muisti-instanssi
memory = DynamicDistLLMMemory(instruction_text, contents_text)

# Alusta muisti
memory.execute_instruction_init()

# Käsittele tapahtuma
memory.react_to_event("event_type", {"data": "example"})
```

4. Hajautetun järjestelmän käyttöönotto:

```python
# Käynnistä Event Broker
from events import EventBroker
broker = EventBroker()
broker_thread = threading.Thread(target=broker.run)
broker_thread.start()

# Määritä solmun ID ja yhteys
node_id = "node1"
context = zmq.Context()
socket = context.socket(zmq.DEALER)
socket.connect("tcp://localhost:5555")

# Luo hajautettu muisti
memory = DynamicDistLLMMemory(instructions, contents, node_id, on_send, on_receive)
```

5. Suorituskykytestaus:
```bash
python xappbench.py
```

## Huomioita ja rajoitukset

### Yleiset huomiot
- Järjestelmä on kokeellinen POC-toteutus
- LLM-operaatiot vaativat paikallisen LLM-palvelimen (esim. Ollama)
- Hajautettu toiminnallisuus vaatii ZMQ-infrastruktuurin
- Koodin suoritus on rajoitettu turvallisiin operaatioihin

### Tunnetut rajoitukset
1. Muistin käsittely
   - Muistin koko on rajoittamaton
   - Ei automaattista muistin puhdistusta
   - Vanhojen tapahtumien poisto tehtävä manuaalisesti

2. LLM-operaatiot
   - Ei tukea ketjutetuille LLM-kutsuille
   - Rajoitettu virheiden käsittely LLM-vastauksissa
   - Ei automaattista uudelleenyritystä epäonnistuneille kutsuille

3. Hajautettu toiminta
   - Ei automaattista palautumista yhteyden katketessa
   - Rajoitettu skaalautuvuus suurilla solmumäärillä
   - Ei tukea automaattiselle kuormantasaukselle

4. Turvallisuus
   - Rajoitettu tuki käyttäjäoikeuksien hallinnalle
   - Ei salattua viestinvälitystä
   - Rajoitettu syötteiden validointi

## Jatkokehityskohteet

- Kustannusmallin implementointi LLM-operaatioille
- DSPY-tyylisen pipeline-kääntäjän integrointi
- Tapahtumien julkaisutoiminnallisuuden laajentaminen
- Sisältötriggereiden toiminnallisuuden laajentaminen

## Dokumentaatio ja lisätiedot

- [MemoryFormer Architecture Documentation](docs/architecture.md)
- [API Reference](docs/api.md)
- [Security Guidelines](docs/security.md)
- [Performance Benchmarks](docs/benchmarks.md)

## Viitteet

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [ZeroMQ Guide](https://zguide.zeromq.org/)
- [NetworkX Documentation](https://networkx.org/documentation/stable/)

