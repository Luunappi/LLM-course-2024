# AgentFormer - Kehittynyt Tekoälyagenttijärjestelmä

## Yleiskuvaus

AgentFormer on monipuolinen tekoälyagenttijärjestelmä, joka yhdistää useita kielimalleja, muistinhallintaa ja erikoistuneita työkaluja luodakseen älykkään avustajan. Järjestelmä pystyy ymmärtämään, analysoimaan ja vastaamaan monimutkaisiin kyselyihin käyttäen RAG-teknologiaa (Retrieval Augmented Generation) ja erilaisia tekoälymalleja tarjotakseen tarkkoja, kontekstitietoisia vastauksia.

### Keskeiset Ominaisuudet

- **Usean Mallin Tuki**: Integroi useita tekoälymalleja (GPT-4, O1, mukautetut mallit) automaattisella mallivalinnalla
- **Kehittynyt Muistinhallinta**: Toteuttaa sekä lyhyt- että pitkäkestoisen muistin tehokkaan tallennuksen ja haun
- **RAG-Integraatio**: Käyttää kehittynyttä dokumenttien käsittelyä ja hakua
- **Modulaarinen Työkalujärjestelmä**: Tarjoaa erikoistuneet työkalut eri tehtäviin
- **Web-käyttöliittymä**: Selkeä ja responsiivinen graafinen käyttöliittymä
- **Laajennettava Arkkitehtuuri**: Modulaarinen rakenne mahdollistaa uusien ominaisuuksien lisäämisen

## Järjestelmän Rakenne

### Kansiorakenne
```
agentformer/
├── core/                          
│   ├── messaging.py              # Viestintäjärjestelmä (Singleton + Pub/Sub)
│   └── orchestrator.py           # Pääkoordinaattori
├── storage/                     
│   └── memory/                  
│       ├── backends/            # Muistivarastot
│       │   ├── faiss_backend.py # Vektorivarasto FAISS-kirjastolla
│       │   ├── cosmos_backend.py # Pilvivarasto CosmosDB:llä
│       │   ├── hybrid_backend.py # Hybridivarasto (FAISS + Cosmos)
│       │   └── local_json_store.py # Paikallinen JSON-varasto
│       ├── cache/              # Välimuistin tiedostot
│       ├── saved_files/        # Tallennetut dokumentit
│       ├── vector_database/    # Vektoritietokanta
│       └── memory_manager.py   # Muistinhallinnan koordinointi
├── tools/                        # Erikoistuneet työkalut
│   ├── core_tools/              # Keskeiset prosessointityökalut
│   │   ├── model_tool.py        # Tekoälymallien hallinta ja vuorovaikutus
│   │   ├── token_tool.py        # Token-käytön seuranta ja optimointi
│   │   ├── system_tool.py       # Järjestelmäoperaatiot ja konfigurointi
│   │   ├── prompt_tool.py       # Kehotteiden hallinta ja optimointi
│   │   └── text_tool.py         # Tekstin prosessointi ja muokkaus
│   ├── memory_tools/            # Muistinhallinta ja RAG
│   │   ├── processing/          # Tekstin prosessointi
│   │   │   ├── chunker.py      # Dokumenttien pilkkominen
│   │   │   ├── embedder.py     # Tekstin vektorointi
│   │   │   ├── indexer.py      # Dokumenttien indeksointi
│   │   │   └── summarizer.py   # Dokumenttien tiivistäminen
│   │   ├── storage/            # Tietovarastot
│   │   │   ├── document_store.py # Dokumenttien tallennus
│   │   │   └── vector_store.py   # Vektoritietokanta
│   │   ├── conversation/        # Keskustelumuisti
│   │   │   ├── short_term.py   # Lyhytkestoinen muisti
│   │   │   ├── long_term.py    # Pitkäkestoinen muisti
│   │   │   └── memory_chain.py # Muistiketjun hallinta
│   │   └── rag_tool.py         # RAG-toiminnallisuuden pääluokka
│   └── analysis_tools/          # Analyysityökalut
│       ├── analyzer_tool.py     # Vuorovaikutuksen analyysi ja palaute
│       └── debug_tool.py        # Virheenkorjaus ja monitorointi
├── web/                        # Web-käyttöliittymä
│   ├── api/                    # API-päätepisteet
│   │   ├── rag_routes.py       # RAG-toiminnallisuuden reitit
│   │   ├── conversation_routes.py # Keskustelutoiminnot
│   │   └── analysis_routes.py  # Analytiikkatoiminnot
│   ├── static/                 # Staattiset resurssit (CSS, JS, kuvat)
│   │   ├── css/               # Tyylitiedostot
│   │   ├── js/                # JavaScript-tiedostot
│   │   └── images/            # Kuvat ja ikonit
│   ├── templates/              # HTML-mallit käyttöliittymälle
│   │   ├── chat/             # Keskustelunäkymät
│   │   ├── analysis/         # Analytiikkanäkymät
│   │   └── components/       # Uudelleenkäytettävät komponentit
│   ├── sessions/              # Flask-sessiotiedostot
│   └── web_gui.py             # Web-käyttöliittymän toteutus
├── docs/                      # Dokumentaatio
│   ├── api/                   # API-dokumentaatio
│   ├── guides/               # Käyttöoppaat
│   │   ├── setup/           # Asennusohjeet
│   │   ├── usage/           # Käyttöohjeet
│   │   └── development/     # Kehittäjäohjeet
│   └── examples/             # Esimerkkikoodit
│       ├── api/             # API-esimerkit
│       ├── conversation/    # Keskusteluesimerkit
│       └── analysis/        # Analyysiesimerkit
├── tests/                     # Testit
│   ├── unit/                  # Yksikkötestit komponenteille
│   │   ├── tools/            # Työkalujen testit
│   │   ├── memory/           # Muistin testit
│   │   └── web/              # Web-komponenttien testit
│   └── integration/           # Integraatiotestit järjestelmälle
│       ├── conversation/      # Keskustelutestit
│       ├── memory/           # Muistitestit
│       └── api/              # API-testit
├── .env                       # Ympäristömuuttujat
├── requirements.txt           # Python-riippuvuudet
├── setup.py                   # Asennuskonfiguraatio
├── .gitignore                # Git-poissulkemissäännöt
└── __init__.py               # Python-paketin alustus
```

## Ydinkomponentit

### Orkestraattori (Orchestrator)
- Koordinoi järjestelmän komponentteja
- Hallinnoi työkalujen valintaa ja suoritusta
- Käsittelee kyselyiden analyysin ja vastausten generoinnin
- Integroi muistinhallinnan ja mallien valinnan

### Muistinhallinta
1. **Lyhytkestoinen Muisti**
   - Hallinnoi aktiivisia keskusteluja
   - Toteuttaa automaattisen tiivistämisen
   - Käsittelee konteksti-ikkunan hallintaa
   - Optimoi muistin käyttöä dynaamisesti

2. **Pitkäkestoinen Muisti**
   - Vektorivarasto FAISS:lla
   - Dokumenttien arkistointi ja haku
   - Semanttinen haku
   - Tehokas indeksointi ja päivitys

3. **Muistiketju**
   - Koordinoi lyhyt- ja pitkäkestoisen muistin välillä
   - Hallinnoi muistisiirtymiä
   - Toteuttaa siivouksen ja optimoinnin
   - Varmistaa tiedon eheyden

### Mallien Hallinta
- Tukee useita tekoälymalleja:
  - O1: Kehittynyt päättelymalli (200K konteksti)
  - O1-mini: Tehokas päättelymalli
  - GPT-4o: Multimodaalinen malli
  - GPT-4o-mini: Kustannustehokas perusmalli
- Automaattinen mallivalinta tehtävän mukaan
- Token-käytön seuranta ja optimointi
- Mallikohtainen kehotteiden optimointi

### Dokumenttien Käsittely
1. **Indeksointi**
   - Älykäs tekstin pilkkominen
   - Vektorimuunnokset SentenceTransformers-kirjastolla
   - Vektorivarasto FAISS:ssa
   - Metatietojen hallinta

2. **Haku**
   - Semanttinen haku
   - Hybridihaku (semanttinen + avainsanat)
   - Kontekstitietoinen dokumenttien haku
   - Relevanssin arviointi

### Analyysi ja Monitorointi
- Vuorovaikutuksen analyysi
- Suorituskyvyn seuranta
- Automaattinen palautteen generointi
- Debug-lokit ja virheenseuranta
- Käyttöstatistiikan keräys

## Käytetyt Teknologiat

### Tekoälymallit
- OpenAI GPT-4 ja variantit
- Mukautetut O1-mallit
- SentenceTransformers vektorimuunnoksiin
- BERT-pohjaiset luokittelumallit

### Tietovarastot
- FAISS vektorivarastona
- CosmosDB pilvitallennukseen
- Paikallinen tiedostojärjestelmä dokumenteille
- Redis välimuistina

### Web-käyttöliittymä
- Flask backend
- WebSocket reaaliaikaiseen kommunikointiin
- Moderni responsiivinen UI
- REST API integraatioihin

### Prosessointi
- Sentence-Transformers vektorimuunnoksiin
- NLTK tekstinkäsittelyyn
- NumPy vektorioperaatioihin
- Pandas datankäsittelyyn

## Keskeiset Prosessit

### Kyselyn Käsittely
1. Käyttäjä lähettää kyselyn
2. Orkestraattori analysoi kyselyn tyypin
3. Valitaan sopivat työkalut ja mallit
4. Haetaan relevantti konteksti muistista
5. Generoidaan ja analysoidaan vastaus
6. Tallennetaan tulokset muistiin
7. Palautetaan vastaus käyttäjälle

### Dokumenttien Käsittely
1. Dokumentti ladataan
2. Teksti esikäsitellään
3. Sisältö pilkotaan älykkäästi
4. Generoidaan vektorimuunnokset
5. Vektorit tallennetaan FAISS:iin
6. Tallennetaan metatiedot
7. Generoidaan ja tallennetaan tiivistelmä

### Muistinhallinta
1. Uusi tieto käsitellään
2. Lyhytkestoinen muisti päivitetään
3. Automaattinen tiivistäminen tarvittaessa
4. Vanha tieto arkistoidaan pitkäkestoiseen muistiin
5. Suoritetaan säännöllinen siivous ja optimointi

## Konfigurointi ja Asennus

### Ympäristömuuttujat
- Tekoälymallien API-avaimet
- Tietovarastojen asetukset
- Web-käyttöliittymän asetukset
- Lokituksen asetukset
- Suoritusympäristön määritykset

### Mallien Konfigurointi
- Mallien valintaparametrit
- Token-käytön rajoitukset
- Lämpötila ja muut generointiparametrit
- Konteksti-ikkunoiden koot
- Mallikohtaiset optimoinnit

### Tietovarastojen Konfigurointi
- Vektorivaraston asetukset
- Dokumenttien tallennuspolut
- Tietokantayhteydet
- Varmuuskopioinnin asetukset
- Välimuistin asetukset

## Käyttö ja Integraatio

### API-rajapinnat
- Kyselyiden käsittely
- Dokumenttien hallinta
- Muistioperaatiot
- Järjestelmän tilan seuranta
- Analytiikka ja tilastot

### Web-käyttöliittymä
- Keskustelukäyttöliittymä
- Dokumenttien hallinta
- Järjestelmän tilan seuranta
- Asetusten hallinta
- Analytiikkanäkymät

### Laajennuspisteet
- Uusien työkalujen integrointi
- Mukautettujen mallien tuki
- Tietovarastojen lisääminen
- Analyysimoodulien laajentaminen
- Uusien käyttöliittymien kehitys

## Tiedostojen indeksointi

AgentFormerin RAG-ominaisuudet etsivät tiedostoja hakemistosta:
```
agentformer/storage/memory/saved_files
```
Kun haluat indeksoida tiedostoja ja nähdä ne RAGToolin kautta:
1. Aseta tiedostot suoraan yllä mainittuun hakemistoon, TAI
2. Lähetä tiedostot /upload-rajapinnalla, joka tallentaa ne samaan hakemistoon.

Tämän jälkeen kutsu /reindex (tai vastaavaa "check_and_reindex_files") -päätepistettä.  
Onnistuneen indeksoinnin jälkeen:
• Metatiedot tallentuvat DocumentStoreen.  
• Vektoriedustukset tallentuvat VectorStoreen.  
• list_saved_files()-metodi palauttaa indeksoitujen tiedostojen nimet.  

Jos reindeksointi ei löydä tiedostoja tai list_saved_files() on tyhjä, varmista siis että tiedostot ovat oikeassa hakemistossa ja RAGTool:in check_and_reindex_files on kutsuttu. 

## Viestintäarkkitehtuuri

#### MessageBus (Singleton + Pub/Sub)
- Keskitetty viestintäjärjestelmä komponenttien välillä
- Singleton-malli varmistaa yhden instanssin
- Pub/Sub mahdollistaa löyhän kytkennän
- Tukee tapahtumapohjaista kommunikointia

#### RAG-prosessi yksityiskohtaisesti
1. **Dokumentin käsittely**
   - Chunkkaus: Dokumentti pilkotaan sopivan kokoisiksi palasiksi (chunker.py)
   - Embeddings: Tekstipalat muunnetaan vektoreiksi (SBERT-malli)
   - Indeksointi: Vektorit tallennetaan FAISS-indeksiin

2. **Hakuprosessi**
   - Kyselyn vektorointi
   - Semanttinen haku FAISS:lla
   - Kontekstin muodostus
   - LLM-vastauksen generointi

3. **Muistinhallinta**
   - Lyhytkestoinen: Aktiivinen keskustelu
   - Pitkäkestoinen: Indeksoidut dokumentit
   - Automaattinen siivous ja optimointi

### Järjestelmän laajentaminen
1. **Uusien työkalujen luominen**
   - Periytetään BaseToolista
   - Toteutetaan vaaditut metodit
   - Rekisteröidään orchestrator.py:ssä

2. **Backend-integraatiot**
   - Toteutetaan BaseBackend-rajapinta
   - Lisätään konfiguraatio
   - Rekisteröidään memory_manager.py:ssä



