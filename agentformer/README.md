# AgentFormer

AgentFormer on modulaarinen tekoälyagenttien kehitysalusta, jonka tavoitteena on yhdistää useita taustalla olevia kielimalleja (esimerkiksi GPT-4o-min, o1-mini ja o1) sekä monipuolisia työkaluja yhden kattavan keskustelualustan alle. 

Sen avulla voit:
- Keskustella eri kielimallien kanssa samassa ympäristössä
- Laajentaa tai räätälöidä toiminnallisuutta erilaisten työkalumoduulien kautta
- Tallentaa ja hyödyntää keskustelumuisteja sekä hallita kontekstia
- Rakentaa järjestelmäpromptien avulla monenlaisia agentteja eri käyttötarkoituksiin
- Seurata tokenien käyttöä ja laskea kustannuksia
- Toteuttaa RAG-toiminnallisuutta (Retrieval-Augmented Generation) dokumenttien käsittelyä varten


## Asennus ja käyttöönotto

1. Kloonaa repositorio
2. Asenna riippuvuudet:
```bash
cd agentformer
pip install -r requirements.txt
```

3. Luo .env-tiedosto ja lisää OpenAI API-avain:
```
OPENAI_API_KEY=your-api-key-here
```

4. Käynnistä sovellus:
```bash
cd agentformer
python agentformer_web.py
```

## Kansiorakenne

agentformer/
├── core/ # Ydinkomponentit
│ ├── __init__.py
│ ├── ceval.py # Evaluointilogiikkaa
│ ├── exceptions.py # Poikkeuksien käsittely
│ ├── messaging.py # Viestinvälitysjärjestelmä
│ ├── orchestrator.py # Pääorkestraattori
│ └── triggermanagement.py # Triggerien hallinta
│
├── memory/ # Muistinhallinta
│ ├── __init__.py
│ ├── base_memory.py # Muistin perusluokka
│ ├── distributed.py # Hajautettu muisti
│ ├── hierarchical.py # Hierarkkinen muisti
│ └── memory_manager.py # Muistin hallinta
│
├── ui_components/ # Käyttöliittymäkomponentit
│ ├── __init__.py
│ ├── model_module.py # Mallien hallinta
│ ├── static/ # Staattiset resurssit
│ │ ├── css/ # Tyylitiedostot
│ │ ├── js/ # JavaScript
│ │ └── images/ # Kuvat ja ikonit
│ └── templates/ # HTML-templatet
│
├── tools/ # Työkalumoduulit
│ ├── __init__.py
│ ├── diagram_tool.py # Kaaviotyökalu
│ └── rag_tool.py # RAG-toiminnallisuus
│
├── config/ # Konfiguraatiotiedostot
│ └── api_config.json
│
├── tests/ # Testit
│ ├── __init__.py
│ ├── conftest.py # Testien konfiguraatio
│ ├── test_basic.py
│ ├── test_e2e.py # End-to-end testit
│ ├── test_evaluation.py # Evaluoinnin testit
│ └── test_openai_api.py # OpenAI API testit
│
├── agentformer_web.py # Web-sovelluksen päämoduuli
├── pytest.ini # Pytest-konfiguraatio
├── requirements.txt # Projektin riippuvuudet
├── test_requirements.txt # Testien riippuvuudet
├── debug.log # Debug-loki
└── README.md # Tämä dokumentti

## Keskeiset Toiminnot

1. **Useita taustamalleja**: AgentFormerin modulariteetti mahdollistaa samanaikaisesti useamman kielimallin hallinnan. Voit helposti vaihtaa mallia tai ottaa käyttöön useita erilaisiin tehtäviin soveltuvia malleja.

2. **Modulaarinen Arkkitehtuuri**: Ratkaisun ydin on joustavasti laajennettavissa. Jokainen työkalu tai agentin osa toimii omana moduulina, jonka voi lisätä tai poistaa tarpeen mukaan.

3. **Muistinhallinta**: Keskustelumuistia (Memory Manager) hyödynnetään aiempien viestien ja kontekstin tallentamiseen. Tämä mahdollistaa rikkaamman ja syvemmän vuorovaikutuksen agentin kanssa.

4. **RAG-toiminnallisuus**: Sivustolle voi ladata erilaisia tiedostoja (kuten PDF, TXT, MD), ja järjestelmä pystyy hyödyntämään niitä osana vastausten tuottamista.

5. **Web-käyttöliittymä**: Sovellusta voi käyttää selaimessa. Käyttöliittymässä on tuki keskustelukomennoille, mallin valinnalle sekä tiedostojen lataamiselle.

6. **Tokenien seuranta**: Agentti raportoi kussakin viestissä käytetyt tokenit ja laskee kustannusarvion, jolloin kehittäjä pysyy perillä yllätyskuluista.

7. **Järjestelmäpromptien hallinta**: Mahdollistaa erilaisten “systeemitason” alustuspromptien ja työkalujen valintapromptien käytön.

## Arkkitehtuuri

### Työkalut

Järjestelmä käyttää modulaarista työkaluarkkitehtuuria:

- **ModelTool**: Mallien hallinta ja konfigurointi
- **ChatTool**: Keskustelun hallinta ja vastausten generointi
- **TokenTool**: Token-käytön seuranta ja laskenta
- **SystemTool**: Järjestelmän suorituskyvyn monitorointi
- **RAGTool**: Dokumenttipohjainen tiedonhaku
- **PromptTool**: Promptien hallinta

Jokainen työkalu:
- On singleton-instanssi
- Vastaa yhdestä selkeästä toiminnallisuudesta
- Voidaan testata itsenäisesti
- Voidaan konfiguroida erikseen

AgentFormer on rakennettu kerroksittaiseksi järjestelmäksi, jossa Orchestrator toimii keskeisenä koordinaattorina kaikkien komponenttien välillä. Message Bus -järjestelmä mahdollistaa asynkronisen viestinvälityksen eri moduulien välillä, mikä tekee järjestelmästä skaalautuvan ja joustavan. Memory Manager ylläpitää kolmitasoista muistia (työmuisti, episodinen muisti ja semanttinen muisti), mikä mahdollistaa kontekstin säilymisen ja aiempien keskustelujen hyödyntämisen. Työkalumoduulit (Tools) ovat itsenäisiä komponentteja, jotka voidaan dynaamisesti ladata ja poistaa käytöstä tarpeen mukaan. Web-käyttöliittymä on toteutettu Flaskilla ja se kommunikoi Orchestratorin kanssa REST-rajapinnan kautta.

1. **Orchestrator**  
   Vastaa keskustelun ohjauksesta (komponentti nimeltä AgentFormerOrchestrator). Se reitittää viestejä agenttien ja työkalujen välillä sekä koordinoi mallien käyttöä.

2. **Memory Manager**  
   Tallentaa keskusteluhistorian ja palvelee “pitkänä muistina.” Sen avulla malli pystyy hyödyntämään monimutkaisempia käyttäjäkonteksteja ja hakemaan aiemmin kerrottuja tietoja.

3. **Model Module**  
   Käsittelee useita eri mallikonfiguraatioita (esim. GPT-4o-min, o1-mini ja o1). Moduulista säädetään mm. lämpötilaa, token-rajoja ja muita parametreja. Se vastaa myös avoimen rajapinnan kutsuista (OpenAI API).

4. **Message Bus**  
   Mahdollistaa agenttien, muistinhallinnan ja työkalumoduulien välisen viestiliikenteen. Kytkeytyy Orchestratoriin ja huolehtii viestien välittämisestä oikeille osapuolille.

5. **Tools**  
   Joukkio erikoistyökaluja (kuten RAG, kaaviotyökalu, tms.), joiden avulla agentti laajentaa toiminnallisuuttaan. Nämä moduulit lisätään tarpeen mukaan Orchestratoriin.

6. **Web UI**  
   Flask-pohjainen käyttöliittymä tarjoaa selkeän tavan käyttää agenttia selaimessa. Käyttäjä voi syöttää kysymyksiä, ladata tiedostoja ja vaihtaa mallia suoraan selainikkunasta.

## Tiedostorakenne

Alta löytyy tärkeimmät kansiot ja tiedostot yhden lauseen selitteillä:

- **agentformer/agentformer_web.py**  
  Sisältää Flask-sovelluksen juoksevan koodin ja reitit HTTP-pyyntöihin (mm. chat, upload, update_model).

- **agentformer/core/ceval.py**  
  Ydinlogiikkaa evaluointeihin ja laskentatehtäviin liittyen (esim. kontekstin käsittelyyn).

- **agentformer/core/orchestrator.py**  
  Pääorkestraattori, joka ohjaa viestinvälitystä agenttien ja työkalujen välillä.

- **agentformer/tests/**  
  Kokoelma testejä, joilla varmistetaan eri osien toimivuus (test_basic.py, test_e2e.py, test_openai_api.py jne.).

- **agentformer/tools/diagram_tool.py**  
  Laajennus, joka mahdollistaa kaavion tai diagrammin muodostamisen tai käsittelyn osana agentin toimintoja.

- **agentformer/tools/rag_tool.py**  
  RAG (Retrieval-Augmented Generation) -työkalumoduuli dokumenttien lukemiseen ja hankitun tiedon hyödyntämiseen vastauksissa.

- **agentformer/ui_components/model_module.py**  
  Model Module, joka hallinnoi kielimallien konfiguraatiota, API-kutsuja ja vastausten generointia.

- **agentformer/static/**  
  Kansio staattisille tiedostoille, kuten CSS-tyyleille, JavaScript-tiedostoille ja kuville.

- **agentformer/templates/**  
  HTML-pohjat Flask-käyttöliittymälle (chat.html, index.html).

- **agentformer/config/api_config.json**  
  Esimerkkikonfiguraatiot (esim. API-avaimet), joita käytetään mallikutsujen yhteydessä.

- **agentformer/pytest.ini**  
  Pytest-konfiguraatiotestausta varten (esim. asetukset kattavuusraportointiin yms.).

- **agentformer/test_requirements.txt**  
  Lista riippuvuuksista, jotka asennetaan testejä varten.

- **agentformer/README.md**  
  Tämä tiedosto, joka sisältää AgentFormerin yleiskuvauksen.

- **agentformer/memory/memory_manager.py**  
  Hallinnoi kolmitasoista muistijärjestelmää (työmuisti, episodinen muisti, semanttinen muisti) ja tarjoaa rajapinnan muistin käsittelyyn.

- **agentformer/memory/memory_types.py**  
  Määrittelee eri muistityyppien toteutukset ja niiden erityispiirteet.

- **agentformer/memory/memory_operations.py**  
  Sisältää toiminnot muistin hakuun, tallentamiseen ja päivittämiseen.

- **agentformer/memory/memory_utils.py**  
  Apufunktiot muistin käsittelyyn, kuten muistin siivoukseen ja optimointiin.

- **agentformer/core/context.py**  
  Hallinnoi keskustelukontekstia ja sen päivittämistä.

## Lisätietoja

AgentFormerin modulaarisuus tekee siitä joustavan alustan, joka soveltuu monenlaisiin luonnollisen kielen käsittelytehtäviin. Jokainen komponentti on suunniteltu laajennettavaksi, jotta kehittäjät voivat hyödyntää haluamiaan kielimalleja sekä liittää omia erikoistyökalujaan mukaan.

## Työkalut ja modulaarinen arkkitehtuuri

### Työkalujen periaatteet

AgentFormer käyttää modulaarista työkaluarkkitehtuuria, jossa jokainen työkalu on itsenäinen komponentti omalla vastuualueellaan. Tämä lähestymistapa tarjoaa useita etuja:

1. **Single Responsibility Principle**: Jokainen työkalu keskittyy yhteen tehtävään ja tekee sen hyvin
2. **Helppo testattavuus**: Työkaluja voidaan testata erikseen muusta järjestelmästä
3. **Uudelleenkäytettävyys**: Työkaluja voidaan käyttää eri konteksteissa ja sovelluksissa
4. **Ylläpidettävyys**: Yksittäisen työkalun päivittäminen tai korjaaminen ei vaikuta muihin
5. **Laajennettavuus**: Uusien työkalujen lisääminen on helppoa

### Ydintyökalut

#### TokenTool
- **Tarkoitus**: Token-käytön laskenta ja seuranta
- **Toiminnallisuudet**:
  - Token-määrän laskenta teksteille
  - Kustannusten laskenta mallikohtaisesti
  - Käyttötilastojen ylläpito
- **Perustelut**:
  - Erottaa token-laskennan logiikan muusta sovelluksesta
  - Mahdollistaa tarkan kustannusseurannan
  - Helpottaa eri mallien käyttökustannusten vertailua

#### WordLimitTool
- **Tarkoitus**: Tekstin pituuden hallinta
- **Toiminnallisuudet**:
  - Tekstin katkaisu määriteltyyn sanamäärään
  - Dynaaminen raja-arvojen hallinta
  - Automaattinen tekstin tiivistys
- **Perustelut**:
  - Estää liian pitkät vastaukset
  - Optimoi token-käyttöä
  - Parantaa vastausten luettavuutta

#### RAGTool
- **Tarkoitus**: Dokumenttipohjainen tiedonhaku ja vastausten generointi
- **Toiminnallisuudet**:
  - Dokumenttien prosessointi ja indeksointi
  - Semanttinen haku
  - Kontekstuaalinen vastausten generointi
- **Perustelut**:
  - Mahdollistaa tarkat vastaukset dokumenttien pohjalta
  - Vähentää hallusinaatioita
  - Parantaa vastausten luotettavuutta

#### DiagramTool
- **Tarkoitus**: Visualisointien luonti
- **Toiminnallisuudet**:
  - Automaattinen kaaviotyypin valinta
  - Datan muotoilu visualisointiin
  - Interaktiivisten kaavioiden luonti
- **Perustelut**:
  - Parantaa tiedon ymmärrettävyyttä
  - Mahdollistaa datan visuaalisen analyysin
  - Tukee päätöksentekoa

### Työkalujen integraatio

Työkalut integroidaan järjestelmään orkestraattorin kautta:

1. **Rekisteröinti**: Työkalut rekisteröidään orkestraattorille käynnistyksessä
2. **Viestinvälitys**: Työkalut kommunikoivat MessageBus-järjestelmän kautta
3. **Tilanvalvonta**: Orkestraattori valvoo työkalujen tilaa ja suoritusta

### Esimerkki työkalun käytöstä

```python
# Esimerkki TokenTool-työkalun käytöstä
from tools.token_tool import TokenTool

token_tool = TokenTool()

# Laske tokenit ja kustannus
stats = token_tool.calculate_tokens("Analysoi tämä teksti", model="gpt-4")
print(f"Tokens used: {stats['total_tokens']}")
print(f"Cost: ${stats['cost']:.4f}")

# Päivitä käyttötilastot
token_tool.update_usage(stats)

# Hae kokonaistilastot
total_stats = token_tool.get_usage_stats()
print(f"Total cost so far: ${total_stats['total_cost']:.4f}")
```

### Uuden työkalun lisääminen

Uuden työkalun lisääminen järjestelmään:

1. Luo uusi luokka tools/-hakemistoon
2. Toteuta tarvittavat metodit (calculate, update, get_stats tms.)
3. Rekisteröi työkalu orkestraattorissa
4. Lisää tarvittavat testit

## Mallit ja niiden käyttö

AgentFormer tukee useita kielimalleja eri käyttötarkoituksiin:

- **gpt-4o-mini (1x€)**
  - Nopea ja edullinen perusmalli
  - Soveltuu: chat, perustason tekstintuotanto
  - Max tokens: 8192 (n. 6000 sanaa)

- **o1-mini (3x€)**
  - Tarkka malli faktantarkistukseen
  - Optimoitu tarkkuuteen matalalla lämpötilalla
  - Max tokens: 2048 (n. 1500 sanaa)

- **gpt-4o (20x€)**
  - Tehokas malli monimutkaisiin tehtäviin
  - Erinomainen reasoning-kyky
  - Max tokens: 1024 (n. 750 sanaa)

- **o1 (30x€)**
  - Kehittynein malli vaativiin tehtäviin
  - Tukee multimodaalista sisältöä
  - Max tokens: 512 (n. 400 sanaa)

Mallin voi vaihtaa käyttöliittymän oikeasta yläkulmasta. Hintakerroin (x€) näkyy mallin nimen perässä.

### Token-seuranta ja kustannukset

Järjestelmä seuraa token-käyttöä ja kustannuksia:

- Reaaliaikainen näkymä nykyisen viestin token-määrästä
- Session kokonaiskäyttö malleittain
- Kustannuslaskenta perustuen mallien hinnoitteluun
- Token-käytön visualisointi käyttöliittymässä

Esimerkki token-näkymästä:
```
Current message: 150 tokens used (50 in, 100 out)
Cost: $0.0045

Session total: 1500 tokens ($0.0450)
Per model:
- gpt-4o-mini: 800 tokens ($0.0120)
- o1-mini: 700 tokens ($0.0330)
```

### Työkalukohtaiset optimoinnit

Työkalut voivat määritellä omat malliasetuksensa tehtäväkohtaisesti:

```python
# RAG-työkalu käyttää tarkkaa mallia hakuun
"rag_retrieval": "o1-mini"  # Tarkka haku
"rag_generation": "gpt-4o"  # Hyvä vastausten muodostus

# Koodityökalu käyttää kehittynyttä mallia
"code_generation": "gpt-4o"  # Tarkka koodin tuotto
```

Asetukset optimoivat:
- Lämpötilan (temperature)
- Maksimi token-määrän
- Mallin valinnan tehtävän mukaan



