# Lab Report 3

## 1. Aiheen valinta

Valitsin aiheeksi “taloudellinen neuvonta” (esim. eläkesuunnittelu, säästöt, tai sijoittaminen). Tämä on tärkeä aihealue, koska taloudelliset neuvot vaikuttavat ihmisten arkeen ja tulevaisuuden suunnitelmiin.

## 2. Vertailuparin kieli/dialekti

Käytin suomea ja englantia kontrastiparina. Tavoitteena oli nähdä, vastaavatko eri LLM:t eri tavoin suomeksi ja englanniksi kysyttyihin kehotteisiin.

## 3. Mallipari

Käytössä kaksi LLM:ää konkreettisesti:
1. “mistral_local” (Mistral-malli ladattuna lokalisti Ollaman avulla)
2. “openai_o1-mini” (kutsutaan OpenAI API:n kautta .env-tiedostossa olevalla avaimella)

Tavoitteena oli tutkia, syntyykö eroavaisuuksia näiden kahden mallin välillä samoilla kysymyksillä.

## 4. Kokeen toteutus
(venv) wrightju@mac week-3 % python prompt_experiment.py

Laadin parin “vastaavia” mutta eri tyylisiä promptteja, vieden samaa aihealuetta ja vertaillen suomen- ja englanninkielisten vastausten sävyä:

• Prompt 1 (“Tyylikkäämpi, pitkä muoto” suomenkielisenä):  
  “Voisitko ystävällisesti ehdottaa tapoja, joilla keskituloinen opiskelija voi aloittaa sijoittamisen pienellä riskillä, ottaen huomioon pitkäaikaiset tavoitteet ja kestävän kehityksen ratkaisut?”

• Prompt 2 (“Ytimekkäämpi, suorasukainen” englanniksi):  
  “Give me quick, low-risk investment ideas suitable for a college student with moderate income, focusing on sustainable options.”

### Vastaukset

**Mistral (lokaalisti)**

*Suomenkielinen vastaus:*
```
1. Tutustu tietokoneesi: Ensin tietokoneesi on suuri apuna yhteisöisiä tehtäviään, joten opiskelijat ovat toivottavasti tietokoneita käytettävään. Aloitakaa yksityiseni ja oppikaa etenkin pienellä riskillä.

2. Aloita työpaikan hakeminen: Joskus on mahdollista saada työpaikkaa, jossa voit oppia ja myös rahoitaa itseäsi. Hakee yhteydessä kaapaselaimellasi suotuimman toimipaikan, jossa tiettyäänkin keskitullisesta opiskelijasta ovat mahdollisuudet työpaikkaa saavuttamiseen.

[...loput 8 kohtaa poistettu tilan säästämiseksi...]
```

*Englanninkielinen vastaus:*
```
1. High-Yield Savings Account: Open a high-yield savings account to earn interest on your money without taking on any risk. This type of account offers higher interest rates than traditional savings accounts.

2. Emergency Fund: Build an emergency fund to cover 3-6 months' worth of living expenses. Having this safety net can help you avoid going into debt if unexpected expenses arise.

3. Roth IRA: If your income falls within the eligible range, consider opening a Roth Individual Retirement Account (Roth IRA). Contributions are made with after-tax dollars, but earnings and withdrawals in retirement are tax-free.

[...loput 7 kohtaa poistettu tilan säästämiseksi...]
```

**OpenAI o1-mini**

*Suomenkielinen vastaus:*
```
Totta kai! Tässä muutamia tapoja, joilla keskituloinen opiskelija voi aloittaa sijoittamisen pienellä riskillä:

1. Säästä ensin hätärahasto: Ennen kuin aloitat sijoittamisen, varmista että sinulla on riittävä hätärahasto säästettynä pahan päivän varalle. Yleensä suositellaan säästämään vähintään 3-6 kuukauden elinkustannuk[vastaus katkesi max_tokens-rajoituksen vuoksi]
```

*Englanninkielinen vastaus:*
```
1. Open a high-yield savings account: Look for a savings account that offers a competitive interest rate to help your money grow over time.

2. Invest in a low-cost index fund: Consider investing in a low-cost index fund that tracks the performance of the overall stock market. This can provide diversification and potential for long-term growth.

3. Start a Roth IRA: If you have earned income, consider opening a Roth IRA to save for retirement. Contributions are made with after-tax dollars, so you can withdraw the money tax-free in retirement.

4. Consider peer-to-peer lending: Platforms like Lending Club or Prosper allow you[vastaus katkesi max_tokens-rajoituksen vuoksi]
```

## 5. Havainnot

1. Tyyliero:  
   – Mistral tuotti englanniksi hyvin jäsennellyn, numeroidun listan konkreettisia sijoitusneuvoja (esim. "High-Yield Savings Account", "Emergency Fund", "Roth IRA").
   – Suomeksi Mistralin vastaus oli sekava ja osittain aiheesta poikkeava, sisältäen epärelevantteja neuvoja kuten "Tutustu tietokoneesi".
   – OpenAI o1-mini tuotti molemmilla kielillä johdonmukaisen ja aiheessa pysyvän vastauksen, joskin vastaus jäi kesken max_tokens-rajoituksen vuoksi.

2. Kielelliset erot:  
   – Mistralin suomen kielen laatu oli heikko, sisältäen kielioppivirheitä ja outoja sanayhdistelmiä (esim. "pienoiskaisja", "työtapaukko").
   – Englanninkieliset vastaukset olivat molemmilla malleilla huomattavasti laadukkaampia ja ammattimaisempia.
   – OpenAI o1-mini:n suomenkielinen vastaus oli kieliopillisesti korrekti ja luonteva.

3. Sisältöero:  
   – Mistral englanniksi: Kattava lista erilaisia sijoitusinstrumentteja (säästötilit, rahastot, joukkovelkakirjat)
   – Mistral suomeksi: Vastaus harhautui alkuperäisestä aiheesta yleisiin työelämäneuvoihin
   – o1-mini: Molemmilla kielillä aloitti perusasioista (hätärahasto) ja eteni järjestelmällisesti monimutkaisempiin sijoitusmuotoihin

4. Johtopäätös:  
   – Mistralin vahvuus on selkeästi englanninkielisessä sisällössä
   – OpenAI o1-mini hallitsee molemmat kielet tasaisemmin
   – Vastausten pituuden rajoittaminen (max_tokens=128) vaikutti o1-mini:n vastausten kattavuuteen
   – Suomenkielisten vastausten laatu vaihteli merkittävästi mallien välillä

5. Miten jatkossa:  
   – Mistralin suomenkielistä suorituskykyä voisi parantaa hienosäätämällä mallia suomenkielisellä datalla
   – OpenAI:n vastauksille voisi antaa enemmän tilaa nostamalla max_tokens-arvoa
   – Prompteja voisi tarkentaa pyytämään tietty määrä neuvoja, jotta vastaukset olisivat vertailukelpoisempia
   – Tämä vertailu toimii hyvänä pohjana ELOQUENT-projektille, erityisesti kielten välisten erojen osalta 