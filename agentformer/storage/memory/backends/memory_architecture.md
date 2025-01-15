# AgentFormer – Muistinhallinnan arkkitehtuuri

Tämä dokumentti kokoaa yhteen AgentFormerin muistin hallinnan rakenteen ja jatkosuunnitelmat. Koko arkkitehtuurin tavoitteena on tarjota modulaarinen, monitasoinen muistiratkaisu, joka tukee sekä lyhyen että pitkän aikavälin keskustelu- ja kontekstitietoa. Alla kootut keskeiset osiot:

---

## 1. Nykyinen Rakenne

1) MemoryManager (agentformer/memory/memory_manager.py)  
   • Koordinoi muistitoimenpiteet ja reitittää pyynnöt varsinaisille muistiluokille (HierarchicalMemory, DistributedMemory, tms.).  

2) HierarchicalMemory (agentformer/memory/hierarchical.py)  
   • Perinteinen nelitasoinen rakenne (core, semantic, episodic, working).  
   • Tekee suorasanaisia tallennuksia ja hakuja (string-match).  

3) DistributedMemory (agentformer/memory/distributed.py)  
   • Modulaarinen, solmupohjainen rakenne.  
   • Ei laajasti käytössä tällä hetkellä.  

4) Backends-kansio (agentformer/memory/backends/)  
   • Tarjoaa muistijärjestelmälle vaihtoehtoisia fyysisiä toteutuksia.  
   • LocalJsonMemoryBackend – Yksinkertainen JSON-pohjainen tallennus.  
   • FaissMemoryBackend – Vektori-indeksointia (FAISS) tukemaan RAG-hakua.  

5) RAGTool (agentformer/tools/rag_tool.py)  
   • Mahdollistaa retitriivalisen generaation (Retrieval-Augmented Generation) periaatteen.  
   • Tällä hetkellä hyödyntää FaissMemoryBackendia upotushaussa (dummy tai SBERT).  

---

## 2. Suunnitelma – Jatkokehitys

1) SBERT-Embeddings (tai muu embedding)  
   • Vektorihaun laatu paranee merkittävästi oikeilla tekstistä vektoreiksi -muunnoksilla (esim. sentence-transformers).  
   • Tällä hetkellä rag_tool.py käyttää “_compute_embedding” -funktiota vain dummy-satunnaisvektorilla.  
   • Toteutus: Kun haluat oikeat upotukset, asenna “sentence-transformers” ja avaa SBERT-lataus riviltä:  
     ```python
     # self.sbert_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
     ```  
   • Palauta sen .encode(text).tolist() RAGToolin `_compute_embedding` -metodissa.  

2) Tiivistys / Summarisointi (MemGPT-tyylinen “self-edit” -prosessi)  
   • Toteutetaan erillinen SummarizationTool tai “cleanup” -luokka, joka käy läpi vanhoja “episodic”-muisti-entryjä.  
   • Pyyntö esimerkinomaisesti GPT-tyyliselle mallille: “Summarize these 5 messages in max 512 tokens.”  
   • Korvaa/tai arkistoi vanhat 5 entryä yhdellä “semantic”–tyyppisellä “tiivistelmä-chunkilla.”  
   • Keskitetty paikka: MemoryManager tai jokin “MemoryCleaner” -luokka.  
   • Aktivoidaan esim. 10 viestin välein tai ajastettuna.  

3) Pitkäkestoinen muisti – Tietokanta (Cosmos DB / NoSQL)  
   • Faiss on paikallinen vektorihaku, mutta itse data + meta voidaan tallentaa myös Cosmos DB -tauluun.  
   • Saman rajapinnan pohjalta (store, search, update, remove) voimme laajentaa FaissMemoryBackend → CosmosDbMemoryBackend.  
   • Käytännössä *embedding-haku* voidaan yhä hoitaa Faiss:lla, mutta pysyvä raakatieto (alkuperäinen teksti) tallentuu Cosmos DB:hen.  

4) Ketterä RAG-työnkulku (päivitetty)  
   1. Käyttäjä lataa dokumentin → RAGTool prosessoi PDF:n tai tekstitiedoston
   2. Teksti puhdistetaan ja chunkataan (500 tokenia, 50 tokenin overlap)
   3. SBERT (paraphrase-multilingual-mpnet-base-v2) luo embeddingin jokaiselle chunkille
   4. Chunkit ja embeddingt tallennetaan FAISS-indeksiin
   5. Kyselyn saapuessa:
      - SBERT luo embedding kyselylle
      - FAISS hakee top-3 relevanteinta chunkkia
      - OpenAI Ada (text-ada-002) generoi vastauksen kontekstin perusteella
   6. Vastaus muotoillaan selkeästi ja palautetaan käyttäjälle

Huomioita toteutuksesta:
- Monikielinen SBERT-malli mahdollistaa tehokkaan haun suomenkielisistä dokumenteista
- Ada-mallin matala temperature (0.3) tuottaa asiallisia ja faktapohjaisia vastauksia
- PDF-tiedostojen käsittelyssä erityishuomio skandinaavisten merkkien oikeaan tulkintaan
- Chunkkaus huomioi kappaleiden rajat ja sisältää overlapin kontekstin säilyttämiseksi

---

## 3. Käyttöönoton Vaiheet

Vaihe 1: “Perus RAG”  
• Käytä dummy-embeddiä tai SBERTiä, laita dokumentit .upload-loppupisteen kautta (jo toteutettu rag_upload).  
• Kokeile /api/rag/query -endpointilla kyselyitä.  
• Varmista, että FAISS-indeksitiedostot (rag_faiss_index.bin, rag_faiss_meta.json) päivittyvät.  

Vaihe 2: Summarisoinnin toteutus  
• Luo SummarizeTool / MemoryCleaner, joka (a) hakee vanhimmat N muistia, (b) pyyntää GPT:ltä tiivistelmää, (c) korvaa N entriä yhdellä “summary-chunkilla.”  
• Kutsu siivousmetodi esim. 10 viestin välein.  

Vaihe 3: Cosmos DB -varaston kytkentä  
• Toteuta “CosmosDbMemoryBackend” tai laajenna FaissMemoryBackend tallentamaan metadata kosmokseen.  
• Mahdollistaa skaalautuvamman “pitkän historian” varastoinnin.  

---

## 4. Yhteenveto ja Hyödyt

• Rakenne pysyy modulaarisena: koordinoiva MemoryManager ohjaa, minkä back-endin valitsemme.  
• FaissMemoryBackend + SBERT rendaa RAG-hakuun relevanttia kontekstia, nopeuttaa isojen dokumenttien hakua.  
• Summarisointi pidentää käytettävyyttä, estää laajojen token-laskujen kasvua.  
• “Pitkäkestoisen muistin” tuki helpottaa arkistoimista (Cosmos DB), jolloin data on edelleen palautettavissa, jos siirtyy pois Faissin “aktiivisesta” vektorihakemistosta.  

Tämän suunnitelman avulla AgentFormerin muistin hallinta laajenee yksinkertaisesta tallennuksesta skaalautuvaan, modulaariseen RAG-järjestelmään, jossa on helppo lisätä summarisointia, eri vektorihakubackendeja ja pysyviä tietokantayhteyksiä (Cosmos DB).