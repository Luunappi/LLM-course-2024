# AgentFormer (Refactored)

## Tiivistelmä

Tämä kansio sisältää Flask-pohjaisen web-sovelluksen, joka hyödyntää dynaamista muisti-objektia (DynamicDistLLMMemory) käsitelläkseen tokoja (käskyjä, syötteitä ja tilapäivityksiä) agenttipohjaisessa ympäristössä. Sovellus on rakennettu siten, että kutakin käyttäjää varten luodaan oma muisti (sessionin avulla), jonka avulla järjestelmää voidaan ohjata askeleittain erilaisten "ohjeiden" (instructions) avulla. Käskyjen suorittaminen voi päivittää sovelluksen globaalia tilaa, mikä mahdollistaa dynaamiset siirtymät eri näkymien tai käyttöliittymäelementtien välillä.

Käytännössä käyttäjän toiminnot (tai sisäiset tapahtumat) ohjataan aina muistille, jonka kautta haetaan kulloinkin kontekstinmukainen ohjeistus. Muisti suorittaa kunkin ohjeen sisäisen logiikan (esimerkiksi "LOAD"-komento lataa tietyn JSONin, "AGENTRUN"-komento käynnistää jonkin laajennetun toiminnallisuuden jne.) ja päivittää globaalia tilaa. Flask-sovellus esittää kulloisetkin käyttöliittymän ohjeet (UI instructions) ja vastaanottaa lomakkeiden tai painikkeiden kautta uutta tietoa, joka puolestaan käsitellään muistin kautta. 

## Yksityiskohtainen kuvaus menetelmästä

### 1. Flask-websovellus

• Sovellus on tyypillinen Flask-app, joka avataan tiedostosta "agentformers-web.py".  

• Flask tarjoaa reitit ("/", "/submit", "/command"), joihin front-end lähettää tietoja (POST-pyynnöillä).  

• "/" (index) näyttää sovelluksen päänäkymän. Tämän yhteydessä:  
  - Haetaan tai luodaan käyttäjäkohtainen muisti (get_user_memory).  
  - Tehdään "update_state", joka käy läpi ohjeet (instructions) ja suorittaa kaikki sopivat komennot ennen UI:n piirtämistä.  

• "/submit" on reitti, joka vastaanottaa käyttöliittymän lomaketiedot tai vastaavan eventin ({"name", "value"}). Mood:  
  - Muisteille lähetetään react_to_event.  
  - update_state päivittää tilan, jonka jälkeen palautetaan JSONissa ajantasaiset käyttöliittymäohjeet sekä mahdolliset "results"-sisällöt.  

• "/command" on vastaava reitti, jolla UI voi kutsua tiettyä "command"-kenttää. Tämä on vaihtoehtoinen tapa suoraan käskeä muistiobjektia suorittamaan jokin ohje.  

### 2. DynamicDistLLMMemory ja muistinhallinta

• Jokaiselle käyttäjälle luodaan oma `DynamicDistLLMMemory`-instanssi, jonka konstruktoriin annetaan joukko ohjeita (instruction_text) sekä sisältöjä (contents_text).  

• Muisti pitää kirjaa "globaalista tilasta" sekä ohjeista, jotka ovat sidottuja tiettyyn tilaan. Kun sovellus tekee "update_state", muisti käy läpi oman ohjejoukkonsa ja tunnistaa kaikki kulloinkin oleelliset ohjeet (esim. ohjeet, joiden ’command’ ei ole pelkästään BUTTON).  

• Muisti voi muuttaa omaa (tai sovelluksen käsitteenä "globaalia") tilaa komentojen suorittamisen yhteydessä. Jos tila päivittyy, muisti tarkistaa, onko uusia ohjeita suoritettavaksi (kokonaisuus on dynaaminen).  

• react_to_event (esim. "/submit"-reitillä) päivittää muistin, tallentaen annetun eventin (nimi, arvo) ja mahdollisesti laukaisee ohjeita, jotka reagoivat kyseiseen eventtiin.  

### 3. Käyttöliittymäohjeet (UI Instructions)

• Sovellus säilyttää ohjeet, joiden "scope" on "UI" tai joilla on jokin ehto, joka laukaisee käyttöliittymään jonkin painikkeen tai tekstikentän. Kun flask-route palauttaa dataa front-endille, se sisältää nämä ohjeet muuttujassa "instructions".  

• UI-ohjeet ohjaavat front-endin renderöintiä: tekstikenttiä, painikkeita, valintoja jne.  

• Tämän avulla on joustavaa päivittää UI dynaamisesti pelkän ohjejoukon muutoksella.  

### 4. Tilan (state) päivittyminen

• `update_state(memory)` on funktio, joka kutsuu `memory.get_instructions_current_state()`. Jokainen sovelluksen ohje (instruction) voi sisältää:  
  - "AGENTRUN", "LOAD", "INPUT", “LLM-TRIGGER” tai vastaavia komentoja. Nämä komennot suoritetaan memory.execute_command:in kautta.  
  - Tämän jälkeen muistia pyydetään tarkistamaan, muuttuiko globaali tila (get_global_state). Jos muuttui, ajetaan uudelleen samankaltaiset ohjeet sen varalta, että syntyy uusia komentoja.  

• Näin järjestelmä pystyy siirtymään askeleittain ohjeesta toiseen satunnaisessa järjestyksessä, kunnes tila vakiintuu.  

### 5. Sovelluksen rakenne ja pääkohdat

1. Flask-sovelluksen konfigurointi  
   - secret_key sessionin käyttöön  
   - endpointit index, /submit, /command  

2. Käyttäjäkohtaiset `DynamicDistLLMMemory`-instanssit varastoidaan `user_memories[user_id]`-sanakirjassa.  

3. Muistin käynnistys:  
   - Ladataan ohjejoukko (instruction_text) – ne ohjeet, jotka halutaan alussa.  
   - Suoritetaan niistä heti ne, joiden komennot eivät ole vain BUTTON- tai UI.  

4. Käyttäjä syöttää jonkin eventin ("submit"):  
   - Sovellus reitittää sen `mem.react_to_event(...)`,  
   - Tilanpäivitys (update_state) ajetaan,  
   - Palautetaan UI-ohjeet ja tulossisällöt JSONina.  

5. Käyttäjä syöttää suoran komennon ("command"):  
   - Sovellus hakee ohjetta ID:llä (jos annettu) ja suorittaa sen,  
   - Taas tilanpäivitys,  
   - Palauttaa ohjeet ja sisällöt.  

### 6. Yhteenveto

• AgentFormer (Refactored) -kansion koodi esittelee dynaamisen tavan hallita sovelluksen logiikkaa Flaskin avulla. Sovellus erottaa logiikkaa ohjeisiin (instructions), joita `DynamicDistLLMMemory` suorittaa.  

• Tämän lähestymistavan etuna on selkeä "agenttipohjainen" rakenne, jossa jokainen ohje laukaisee spesifisiä toimia tarpeen mukaan. Tilanvaihdot toteutuvat läpinäkyvästi muistin sisällä.  

• Näin on helppo lisätä uusia komentotyyppejä tai laajentaa ohjeistusta, muuttamatta varsinaista Flask-sovelluksen runkoa merkittävästi.  