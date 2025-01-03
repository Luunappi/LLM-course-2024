# MemoryRAG

MemoryRAG yhdistää kielimallin ja hierarkkisen muistin tarjoten skaalautuvan, asynkronisen ja monikerroksisen tavan hallita tietoa. 

MemoryRAG pitää tärkeät faktat, yleisen kontekstin ja keskusteluhistorian järjestyksessä ja helposti haettavissa.

Se tarjoaa neljä muistityyppiä (core, semantic, episodic, working), jotka mahdollistavat dynaamisen ja suorituskykyisen tiedon hallinnan. 


## Keskeiset ominaisuudet

1. Hierarkkinen muistimalli:
   • Core: pysyvät ja tärkeät faktat (hidas vanheneminen).  
   • Semantic: laajempi yleistieto ja dokumentaatio (keskivälin vanheneminen).  
   • Episodic: keskustelu- ja tapahtumahistoria (nopea vanheneminen).  
   • Working: aktiivinen työmuisti kulloistakin operaatio-/kyselytilannetta varten (erittäin nopea vanheneminen).

2. Asynkroninen rakenne:
   • MemoryRAG-luokka luodaan asynkronisesti (await MemoryRAG.create()).  
   • Muistioperaatiot (_store_memory, process_query jne.) ovat asynkronisia (await).  
   • Tarjoaa rinnakkaisen tallennuksen ja hakujonojen käsittelyn (batch-prosessointi, parallel_process).

3. Semanttinen haku:
   • Vektoriavaruushaku (embeddings) helpottaa relevantin tiedon löytämistä.  
   • Tuki erilliselle vektoritietokannalle (esim. Faiss) tai sisäiselle dictionary-rakenteelle.  
   • Kosinisamankaltaisuus ja muut pisteytysmetodit.

4. Muistin vanheneminen ja siivous:
   • Poistaa tai arkistoi liian vanhoja muisteja automaattisesti.  
   • Hallitsee kunkin muistityypin elinaikaa (max_age_days).  
   • Vähentää resurssien kuormitusta säilyttäen relevantit tiedot.

5. Suorituskyvyn optimointi:
   • Batch-prosessointi (kerää tietyt määrät embeddingejä ennen indeksipäivitystä).  
   • Tuki Apple Silicon MPS -kiihdytykselle ja GPU-laskennalle (mikäli torch tai muu taustakirjasto mahdollistaa).  
   • Inkrementaalinen tallennus ja varmuuskopiot.

## Peruskäyttö 

**MemoryRAG:ssa on kaksi käyttöliittymävaihtoehtoa:**
1. Komentorivi-käyttöliittymä (CLI):
```bash
# Käynnistä komentorivityökalu
python MemoryRAG/examples/chat_cli.py
```

2. Graafinen käyttöliittymä (GUI):
```bash
# Käynnistä graafinen käyttöliittymä
python MemoryRAG/examples/chat_gui.py
```
Ennen käynnistystä varmista että:
1. OpenAI API-avain on asetettu .env tiedostossa projektin juuressa.
2. Virtuaaliympäristö on aktivoitu
```bash
# Huom! Luotu koko repon juuressa
source venv/bin/activate
# deactivate
```
3. Tarvittavat riippuvuudet on asennettu:
```bash
pip install -r MemoryRAG/requirements.txt
```
**Graafisessa käyttöliittymässä voit:**
- Ladata dokumentteja
- Tehdä kyselyitä
- Nähdä muistin tilan
- Tallentaa ja ladata muistin

**Komentorivityökalussa käytettävissä olevat komennot:**
- /save <tiedosto> : Tallenna muisti
- /load <tiedosto> : Lataa muisti
- /stats : Näytä muistin tila
- /clear : Tyhjennä muisti
- /exit tai q : Lopeta

Voit myös antaa dokumentteja käsiteltäväksi suoraan käynnistyksen yhteydessä:
```bash
python MemoryRAG/examples/chat_cli.py data/dokumentti.pdf data/toinen.txt
```

### Esimerkki koodista
(asynkroninen)
```python
import asyncio
from memoryrag import MemoryRAG

async def main():
    # Luodaan instanssi asynkronisesti
    rag = await MemoryRAG.create(model_name="o1-mini")

    # Tallennetaan tietoa core- ja semantic-muistiin
    await rag._store_memory("core", "Tekoäly on tietokoneiden kyky simuloida älykästä toimintaa", importance=1.0)
    await rag._store_memory("semantic", "Tekoäly kehitettiin 1950-luvulla", importance=0.7)

    # Kysely
    vastaus = await rag.process_query("Mitä on tekoäly ja milloin se kehitettiin?")
    print(vastaus)

if __name__ == "__main__":
    asyncio.run(main())
```

• create() varmistaa API-avaimen toimivuuden ja lataa mahdollisen muisti-indeksin.  
• _store_memory lisää muistitietoja oikeaan muistityyppiin ja laskee niille embeddingin.  
• process_query tekee semanttisen haun ja muodostaa vastauksen kielimallin avulla.

## Muistin ylläpito

• Muistin säännöllinen siivous (cleanup_old_embeddings tai vastaava) puhdistaa liian vanhat merkinnät.  
• Halutessasi voit nähdä tallennettujen muistien sisällön suoraan rag.memory_types -rakenteesta tai syvemmin rag.storage-luokasta.

## Tallennus ja varmuuskopiot

• Tuki asynkroniselle tallennukselle:  
  await rag.storage.save_memories()  
• Varmuuskopiointi säännöllisin väliajoin (backup_interval).  
• Indeksin voi ladata uudelleen esim. ohjelman käynnistyksessä:  
  await rag.storage.load_memories()

## Suorituskyky

• Voit halutessasi säätää batch_size-arvoa, jolloin embeddingit käsitellään isommissa paloissa.  
• Käyttäessäsi Apple Silicon -laitteita rag.use_mps voi olla True, jolloin laskentaa suoritetaan GPU:lla (Metal Performance Shaders).

## Lokalisointi ja jatkokehitys

• MemoryRAG on mahdollista lokaloida tai kääntää muille kielille, koska se toimii pitkälti kielimallien varassa.  
• Jatkokehitykseen kuuluu mm. tehokkaampien embeddausmallien integrointi (sentence-transformers, LlamaIndex tms.) ja entistä laajempi tuki isojen datamäärien semanttiselle haulle.


