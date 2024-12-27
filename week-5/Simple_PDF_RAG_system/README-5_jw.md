# Viikko 5: PDF RAG (Retrieval Augmented Generation)

## Sovelluksen kuvaus
PDF RAG -sovellus on Streamlit-pohjainen älykäs kyselyjärjestelmä, joka mahdollistaa PDF-dokumenttien analysoinnin ja niihin liittyviin kysymyksiin vastaamisen. Sovellus toimii osoitteessa localhost:8501.

## Prosessin vaiheet

### 1. Dokumentin prosessointi
Kun käyttäjä lataa PDF-tiedoston, ohjelma käsittelee sen automaattisesti seuraavissa vaiheissa:
- Reading pdf: PDF-tiedoston muuntaminen tekstimuotoon
- Extracting sentences: Tekstin jakaminen lauseiksi
- Chunking: Tekstin pilkkominen sopivan kokoisiin paloihin
- Loading to DataFrame: Datan järjestäminen taulukkomuotoon
- Embedding: Tekstipalojen muuntaminen vektorimuotoon

### 2. Kysely ja vastaus
Käyttäjä voi:
- Kirjoittaa kysymyksen dokumenttiin liittyen
- Valita vastaustavan (vanilla/rag)
- Seurata prosessoinnin edistymistä käyttöliittymän edistymispalkista

## Asennus ja käyttöönotto

1. Lataa tarvittavat mallit:
```bash
# Lataa mallit Hugging Facesta
huggingface-cli download sentence-transformers/all-mpnet-base-v2
huggingface-cli download google/gemma-2b-it

# Lataa SpaCy:n englanninkielinen malli
python -m spacy download en_core_web_sm
```

2. Asenna riippuvuudet:
```bash
pip install -r requirements.txt
```

3. Käynnistä sovellus:
```bash
cd week-5
streamlit run Simple_PDF_RAG_system/pdf_rag_ui_JW.py
```
## Sovelluksen rakenne

### Pääkomponentit:
- `pdf_rag_ui_JW.py`: Streamlit-käyttöliittymä
- `util/`: Apufunktiot ja työkalut
  - `embedings_utils.py`: Tekstin vektorointi
  - `pdf_utils.py`: PDF-tiedostojen käsittely
  - `nlp_utils.py`: Tekstin prosessointi
  - `generator_utils.py`: Vastausten generointi
  - `session_utils.py`: Streamlit-session hallinta
  - `vector_search_utils.py`: Vektorihaku

### Käytetyt mallit:
- Pääkielimalli: `google/gemma-2b-it` (2B parametria, instruction-tuned versio)
- Vektorointi: `sentence-transformers/all-mpnet-base-v2` (tekstin muuntaminen vektoreiksi)
- Tekstin prosessointi: `en_core_web_sm` (SpaCy, tekstin jako lauseiksi)

## Toiminnallisuudet

1. PDF-dokumenttien lataus ja prosessointi
2. Tekstin jakaminen osiin ja vektorointi
3. Semanttinen haku vektoriavaruudessa
4. Kaksi vastausgenerointitapaa:
   - Vanilla (Gemma 2B): Perusmuotoinen kielimalli, joka vastaa kysymyksiin ilman dokumenttikontekstia
   - RAG (Gemma 2B + Embeddings): Kontekstipohjainen vastaus, joka hyödyntää dokumentista löydettyä relevanttia tietoa

Esimerkki eroista:

Kysymys: "Mitä on koneoppiminen?"

- Vanilla (Gemma 2B) vastaa yleisen tietämyksensä perusteella, käyttäen vain mallin omaa koulutustietoa
- RAG (Gemma 2B + Embeddings) etsii ensin dokumentista koneoppimiseen liittyvät kohdat ja muodostaa vastauksen niiden perusteella

Tämä ero on merkittävä, koska:
- Vanilla (Gemma 2B) ei voi viitata dokumentin sisältöön
- RAG (Gemma 2B + Embeddings) pystyy antamaan tarkempia, dokumenttiin perustuvia vastauksia
- RAG voi löytää uudempaa tai spesifimpää tietoa kuin mitä malliin on koulutettu

## Käyttöohje

1. Lataa PDF-tiedosto käyttöliittymään
2. Kirjoita kysymys dokumenttiin liittyen
3. Valitse mallin tyyppi:
   - "vanilla (Gemma 2B)" yleiseen tietämykseen perustuviin vastauksiin
   - "rag (Gemma 2B + Embeddings)" dokumenttiin perustuviin vastauksiin
4. Paina "Generate"-nappia
5. Tarkastele tuloksia:
   - Löydetyt relevantit tekstikappaleet
   - Generoidut vastaukset

## Tekninen toteutus

### Tekstin prosessointi:
1. PDF muunnetaan tekstiksi
2. Teksti jaetaan lauseisiin (spaCy)
3. Lauseet yhdistetään sopivan kokoisiksi kappaleiksi
4. Kappaleet vektoroidaan Sentence Transformerilla

### RAG-prosessi:
1. Kysymys vektoroidaan
2. Etsitään samankaltaisimmat tekstikappaleet
3. Yhdistetään löydetty konteksti kysymykseen
4. Generoidaan vastaus LLM-mallilla

## Jatkokehitysideat

1. Tuki useammalle dokumentille
2. Parempi virheenkäsittely
3. Vastausten laadun arviointi
4. Käyttöliittymän parannukset
5. Mallin vaihtamisen mahdollisuus

## Huomioita

- Ensimmäinen käynnistys voi olla hidas mallien latauksen takia
- Laitteistokiihdytys:
  - Embedding-malli käyttää MPS:ää (Metal Performance Shaders) Apple Silicon -laitteilla
  - Gemma-malli toimii CPU:lla yhteensopivuusongelmien vuoksi (BFloat16-tuki puuttuu MPS:stä)
  - MPS mahdollistaa GPU-kiihdytyksen M1/M2/M3/M4 -prosessoreilla
- Session state säilyttää prosessoidun datan uudelleenlatauksien välillä
- Debug-informaatio näyttää prosessoinnin etenemisen:
  - Aikaleimoja eri vaiheille
  - Edistymispalkit prosessoinnille
  - Virheilmoitukset ja niiden yksityiskohdat
  - Tilastot prosessoidusta datasta

