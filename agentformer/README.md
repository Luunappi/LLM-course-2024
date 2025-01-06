# AgentFormer

AgentFormer on modulaarinen tekoälyagenttien kehitysalusta, jonka tavoitteena on yhdistää useita taustalla olevia kielimalleja (esimerkiksi GPT-4o-min, o1-mini ja o1) sekä monipuolisia työkaluja yhden kattavan keskustelualustan alle. 

Sen avulla voit:
- Keskustella eri kielimallien kanssa samassa ympäristössä
- Laajentaa tai räätälöidä toiminnallisuutta erilaisten työkalumoduulien kautta
- Tallentaa ja hyödyntää keskustelumuisteja sekä hallita kontekstia
- Rakentaa järjestelmäpromptien avulla monenlaisia agentteja eri käyttötarkoituksiin
- Seurata tokenien käyttöä ja laskea kustannuksia
- Toteuttaa RAG-toiminnallisuutta (Retrieval-Augmented Generation) dokumenttien käsittelyä varten

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



