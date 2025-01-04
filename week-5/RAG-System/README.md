# AI SEARCH - RAG-pohjainen hakujärjestelmä

AI SEARCH on modulaarinen hakujärjestelmä, joka yhdistää tekoälyn, dokumenttihaun ja visualisoinnin. Järjestelmä käyttää RAG (Retrieval Augmented Generation) -tekniikkaa tuottaakseen tarkkoja vastauksia käyttäjän kysymyksiin dokumenttien pohjalta.

## Ominaisuudet

- **Monikielinen tuki**: Tunnistaa kyselyn kielen ja vastaa samalla kielellä
- **Älykäs työkalunvalinta**: Valitsee automaattisesti sopivimmat työkalut kyselyn perusteella
- **Visualisointi**: Luo automaattisesti kaavioita ja visualisointeja datapainotteisiin kyselyihin
- **Dokumenttien käsittely**: Tukee PDF, TXT ja MD -tiedostoja
- **Kontekstuaalinen haku**: Hyödyntää vektori-embeddingiä relevantin tiedon hakuun
- **Mukautettavat asetukset**: Mallin, promptien ja tokenien hallinta

## Toimintaperiaate

Järjestelmä toimii seuraavasti:

1. **Dokumenttien käsittely**
   - Käyttäjä lataa PDF/TXT/MD-dokumentteja
   - Dokumentit pilkotaan pienempiin osiin
   - Osista luodaan vektorimuotoiset embeddings-esitykset

2. **Kyselyn käsittely**
   - Orkestraattori analysoi kyselyn ja valitsee sopivat työkalut
   - Kysely voidaan ohjata joko:
     - RAG-prosessiin (dokumenttipohjainen haku)
     - Suoraan LLM-mallille
     - Visualisointityökalulle

3. **Vastauksen muodostus**
   - RAG: Haetaan relevantit dokumenttiosat ja muodostetaan vastaus niiden pohjalta
   - LLM: Suora vastaus mallilta
   - Visualisointi: Luodaan sopiva kaavio tai graafi

## Modulaarinen rakenne

Järjestelmä koostuu seuraavista pääkomponenteista:

### Tools (Työkalut)
- **RAGTool**: Dokumenttihaku ja vastausten generointi dokumenttien pohjalta
- **LLMTool**: Suorat vastaukset kielimallilta ilman dokumenttikontekstia
- **DiagramTool**: Visualisointien luonti ja datan esittäminen kaavioina
  
Huom: Työkalut keskittyvät vain omiin erikoistehtäviinsä. 
Päätökset työkalujen käytöstä tehdään keskitetysti RAGOrchestrator-komponentissa.

### UI Components (Käyttöliittymäkomponentit)
- **ChatModule**: Keskustelukäyttöliittymä
- **RAGModule**: Dokumenttien hallinta
- **SettingsModules**: Asetukset ja konfiguraatio

### Core (Ydin)
- **RAGOrchestrator**: 
  - Järjestelmän "aivot"
  - Analysoi kyselyt käyttäen kiinteää GPT-4-Turbo-mallia
  - Päättää keskitetysti työkalujen käytöstä
  - Koordinoi työkalujen suoritusta ja yhdistää tulokset

## Tiedostorakenne

```
RAG_System/
├── GUI.py                    # Graafinen käyttöliittymä
├── RAG_Orchestrator.py       # Työkalujen koordinointi
├── tools/                    # Työkalut
│   ├── rag_tool.py          # RAG-toiminnallisuus
│   ├── llm_tool.py          # LLM-integraatio
│   └── diagram_tool.py      # Visualisoinnit
├── ui_components/           
│   ├── chat_module.py       # Chat-käyttöliittymä
│   ├── rag_module.py        # Dokumenttien lataus
│   ├── models_module.py     # Mallien hallinta
│   ├── system_info_module.py   # Järjestelmäviestit
│   ├── prompt_module.py     # Prompt-hallinta
│   ├── document_info_module.py   # Dokumentti-info
│   └── token_info_module.py      # Token-laskurit
└── requirements.txt         # Riippuvuudet
```

## Asennus ja käyttöönotto

1. Kloonaa repositorio
2. Asenna riippuvuudet:
```bash
pip install -r requirements.txt
```

3. Luo .env-tiedosto ja lisää OpenAI API-avain:
```
OPENAI_API_KEY=your-api-key-here
```

4. Käynnistä sovellus:
```bash
cd week-5/RAG-System
streamlit run GUI.py
```

## Tekninen toteutus

### Embeddings ja haku
- Käyttää Sentence Transformers -malleja tekstin vektorisointiin
- Cosine similarity -pohjainen semanttinen haku
- Batch-prosessointi suurille dokumenteille

### Kielimallit
- OpenAI API:n GPT-mallit vastausten generointiin
- Mukautetut promptit eri käyttötarkoituksiin
- Automaattinen kielen tunnistus ja käännös

### Visualisointi
- Plotly-kirjasto interaktiivisiin visualisointeihin
- LLM-pohjainen datan ja kaaviotyypin analyysi
  - Käyttää kiinteää GPT-4-Turbo-mallia visualisointitarpeen arviointiin
  - Käyttää valittua mallia datan generointiin ja tiivistelmiin
- Mukautettu tumma teema

## Käyttöesimerkkejä

1. **Dokumenttipohjainen haku**:
   ```
   Q: "Mitä dokumentissa sanotaan ilmastonmuutoksesta?"
   ```
   Järjestelmä hakee relevantit kohdat dokumenteista ja muodostaa yhtenäisen vastauksen.

2. **Visualisointipyyntö**:
   ```
   Q: "Näytä kuvaaja lämpötilojen kehityksestä"
   ```
   Järjestelmä analysoi datan ja luo sopivan visualisoinnin.

3. **Suora LLM-kysely**:
   ```
   Q: "Selitä RAG-tekniikan toimintaperiaate"
   ```
   Järjestelmä käyttää suoraan LLM:ää vastaamiseen.

## Jatkokehitysidead

1. **Muistinhallinta**
   - Pidempi keskusteluhistoria
   - Kontekstin säilytys sessioiden välillä

2. **Työkalut**
   - Uusien työkalujen helppo lisääminen
   - Työkalujen ketjutus monimutkaisiin tehtäviin

3. **Käyttöliittymä**
   - Drag-and-drop dokumenttien järjestely
   - Edistyneemmät visualisointiasetukset
