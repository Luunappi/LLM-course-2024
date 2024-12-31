# Lab Report 2

## 1. Prompti ja tavoitteet

Promptin tavoitteena on luoda AI-avustaja, joka arvioi opiskelijoiden esseitä Helsingin yliopiston kursseilla. Avustaja hyödyntää luomaansa arviointimatriisia (rubrics) jakamalla esseen arvioinnin eri osa-alueisiin. Osa-alueet muuttuvat kurssin ja tehtävänannon mukaan, mutta keskeistä on antaa selkeä perustelu jokaiselle arvosanalle.

Tyypillinen prompt (lyhennetty esimerkki):

• Yleiset tyyliohjeet:
1. Ole perusteellinen ja objektiivinen.  
2. Käytä selkeää ja kohteliasta kieltä.  
3. Perustele arvosanat arviointimatriisin avulla.  
4. Kohdista arviointi kurssin tavoitteisiin.  

• Kurssikohtaiset ohjeet (esimerkki Digitaalisten ihmistieteiden kognitiotieteen kurssi):
   - Arvioi esseen mielenfilosofian näkökulmasta, kytkien sen kognitiotieteisiin ja mieluusti myös digitaalisiin ihmistieteisiin.  
   - Kiinnitä huomiota tekoälypohdintoihin, jos niitä esiintyy esseessä.

## 2. Käytetyt Prompting-tekniikat

1. Zero-shot prompting: Esimerkkinä selkeä suora ohje AI:lle arvioida essee ilman konkreettisia esimerkkivastauksia.  
2. Few-shot prompting: Kun halutaan ohjata vastausta tarkemmin, promptiin sisällytetään pieniä mallivastauksia tai arvioinnin esimerkkejä.  
3. Chain-of-thought (CoT) prompting: Kannustetaan tekoälyä perustelemaan arvionsa vaiheittain, jolloin jokainen arvosana saa loogisen selitysaskeleen.  
4. Specify the format: Määritelty arviointimalli, esim. “Arvioi seuraavan taulukon muodossa jokainen kurssin osa-alue.”  
5. Iterative prompting: Parannettiin promptia toistuvasti, kun havaittiin puutteita (esim. tulostustyyli) tai väärin muotoiltuja vastauksia.  
6. Temperature control: Asetettiin matala lämpötila (esim. 0.2–0.5) objekteja ja johdonmukaista arviointia varten – poistettiin “liiallinen” luovuus.

## 3. Käytännön toteutus ja havainnot

- Kokeilin Gemini-chatbotia Colabissa ja lokaalisti. Lisäsin promptingiin ohjeet, jotka pakottavat chatbotin tuottamaan arvioinnin selkeänä taulukkona:  
   - Vahvuudet ja heikkoudet omiin sarakkeisiin.  
   - Yhteenveto omalle rivilleen.  
- In-Context learning -notebookissa muutin kehotetta huomioimaan sama arviointimalli:  
   - Aluksi boldaukseen liittyi ongelmia, joten yksinkertaistin markkereiden käyttöä ja tein lopullisen muotoilun HTML- tai Markdown-jälkikäsittelyssä.  
- Käytin avoimen lähdekoodin mallia Hugging Facesta (esim. Mistral tai Mixtralin7b) samoin menetelmin kuin Gemini. Näin saatiin vastaava arviointitaulukko myös toisella mallilla.  
- Lisäsin vertailutulosten tallennuksen (esim. footer-elementin, joka näyttää aikaleiman ja käytetyn mallin) pienten koodimuutosten avulla (benchmark.py).  

## 4. Johtopäätökset

Osuva ja selkeä prompti on ratkaiseva AI-avustajan onnistuneessa työnkulussa. Erilaisia prompting-menetelmiä yhdistämällä (Zero-shot, Few-shot, Chain-of-thought jne.) saavutettiin toimiva arviointimalli, joka antaa kurssiin sidottuja arvosanoja ja parannusehdotuksia. Iteratiivinen lähestymistapa oli hyödyllinen: kun havaittiin, ettei tulostus tai otsikointi vastannut toiveita, promptia muokattiin kohti parempaa lopputulosta.

Lopulta sekä Gemini-chatbot että avoimet Hugging Face -mallit pystyivät tuottamaan järkevän arvioinnin, kunhan prompti oli tarpeeksi tarkka muodosta ja sisällöstä. Suurimmat erot mallien välillä näkyivät luovuudessa ja “tyylissä”, mutta oikein kohdennetulla promptauksella nämä erot vähenevät merkittävästi. 