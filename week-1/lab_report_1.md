# Lab Report 1

## 1. Mitä tokenisaattorit ovat? (n. 250 sanaa)

Tokenisaattorit ovat työkaluja, jotka pilkkovat tekstin pienempiin osiin eli tokeneihin. Nämä tokenit voivat olla kokonaisia sanoja, sananosia tai yksittäisiä merkkejä, ja niiden avulla kielimallit, kuten GPT tai BERT, pystyvät käsittelemään tekstiä rakenteellisella tavalla. Ajatuksena on muuttaa inhimillinen kieli mallille ymmärrettävään muotoon, jotta se voi mallintaa sanojen tai merkkien väliset suhteet. Tokenisaattori ei siis pelkästään riko tekstiä satunnaisesti, vaan se on kehitetty tunnistamaan kielen rakenteita ja jakamaan ne juuri sopiviin yksiköihin.

Esimerkkinä yksinkertaisesta tokenisaatiosta voitaisiin mainita menetelmä, jossa teksti “Jussi pussi puuta halasi” jaetaan joko sanoittain (“Jussi”, “pussi”, “puuta”, “halasi”) tai merkki kerrallaan (“J”, “u”, “s”, “s”, “i” ...). Yksinkertainen sana- tai merkkitasoinen jako ei kuitenkaan aina riitä: esimerkiksi suomenkielessä sana “puuta” voi sisältää useampia taivutusmorfemeja, jotka olisi hyödyllistä käsitellä erillisinä yksiköinä. Tällöin voimme hyödyntää ns. alasanoja (subwords), kuten “puu” ja “ta”.

Eri tokenisaattorit (kuten Byte-Pair Encoding, Unigram-malli ja WordPiece) on kehitetty optimoimaan tämä pilkkomisprosessi. Ne ottavat huomioon kielen rakenteen ja toistuvat yksiköt ja pyrkivät löytämään tasapainon harvinaisten ja yleisten sanojen välillä. Näin malli kykenee paremmin käsittelemään laajaa sanastoa ja erilaisia taivutusmuotoja, mikä on äärimmäisen tärkeää etenkin monimutkaisten kielten, kuten suomen, kohdalla. Lopputuloksena on joustava tapa kuvata kieltä, joka mahdollistaa sekä rakenteellisen ymmärryksen että riittävän viitteellisyyden jopa harvinaisiin termeihin ja muotoihin.

---

## 2. Miksi tokenisaattorit ovat tärkeitä kielimallinnuksessa ja suurissa kielimalleissa? (n. 300 sanaa)

Tokenisaattorit ovat olennainen osa kielimallinnusta, koska ne määrittävät tavan, jolla malli “näkee” ja prosessoi tekstin. Ilman tokenisaattoreita modernit kielimallit eivät pystyisi erottelemaan sanoja, sananosia tai merkkejä toisistaan, mikä tekisi kielen ymmärtämisestä ja käsittelemisestä sekavaa ja epätehokasta. Mallin suorituskyky onkin vahvasti sidoksissa siihen, miten järkevällä tavalla teksti on pilkottu: epätarkka tai liian karkea tokenisointi voi johtaa siihen, että malli ei opi kielen hienovaraisia rakenteita.

Suurissa kielimalleissa, kuten GPT- ja BERT-sarjoissa, tokenisaatiossa huomioidaan myös tehokkuus. Koska datamäärät ovat valtavia, jokainen yksittäinen token vaikuttaa siihen, miten iso osa mallin painorakenteista aktivoituu kerrallaan. Laadukas tokenisaatio vähentää "turhaa" informaatiota ja keskittyy olennaisiin yksiköihin, minkä ansiosta malli voi käyttää resurssinsa olennaisten merkityskehysten oppimiseen. Lisäksi hyvä tokenisaattori auttaa käsittelemään täysin uudenlaisia tai harvinaisia sanoja — erityisesti suomen kaltaisen kielen taivutusmuotojen kohdalla — jakamalla ne jo opittuihin osiin, jolloin malli kykenee ymmärtämään sanan, vaikkei sitä olisi sellaisenaan tavannut aiemmin.

Tokenisaattorit vaikuttavat paljon myös siihen, kuinka “sulavasti” malli tuottaa kieltä. Jos jokin sana pilkkoutuu liian moneen tokeniin, malli saattaa tuottaa outoja tuloksia tai virheellisiä yhdistelmiä. Toisaalta, jos mallissa on liian karkea tokenisaatio, se voi jäädä jumiin harvinaisiin muotoihin eikä opi kielen rakenteita tarpeeksi tarkasti. Tämän vuoksi tokenisaattorit ovat tärkeässä roolissa sekä kielimallin koulutuksessa että sen käytössä, kun se vastaanottaa uusia tekstisyötteitä. Kokonaisuudessaan tokenisaattorit auttavat sekä tehostamaan mallin oppimista että varmistamaan, että mallin tuottama ja ymmärtämä teksti on mahdollisimman luonnollista ja täsmällistä.

---

## 3. Erilaiset tokenisaatioalgoritmit ja suosituimmat menetelmät (n. 300 sanaa)

Tokenisaatioalgoritmit kehittyvät jatkuvasti, ja eri menetelmillä on omat etunsa. Yksi suosituimmista on Byte-Pair Encoding (BPE), jota käytetään esimerkiksi GPT-sarjan malleissa. BPE aloittaa merkkikohtaisesta jaosta ja yhdistää yleisimmin esiintyviä merkkijonoja, kunnes syntyy optimaaliseksi katsottu sanasto. Tällä tavalla se pystyy hallitsemaan sekä yleisiä että harvinaisia sanoja varsin tehokkaasti. BPE:n vahvuus on sen yksinkertaisuus ja kyky sopeutua erilaisiin kieliin, joissa sanojen muodot vaihtelevat.

Toinen yleinen menetelmä on WordPiece, jota käytetään muun muassa BERT-malleissa. WordPiece on melko samanlainen kuin BPE, mutta siinä yhdistämiskriteerit painottuvat hieman eri tavoin. WordPiece keskittyy löytämään “arvokkaimpia” yhtymiä, mikä auttaa etenkin tilanteissa, joissa sanojen esiintymistiheydet vaihtelevat laajasti. Kuten BPE:ssäkin, WordPiece-tokenisaattori käyttää usein erityistä merkintää (esim. “##”) osoittaakseen, että token liittyy edelliseen sananosaan.

SentencePiece on kieliriippumaton ja usein monikielisissä malleissa käytetty menetelmä. Se voi hyödyntää sekä BPE- että Unigram-pohjaista mallia, eikä se vaadi ennakkotaivutettua tai “siistittyä” tekstisyötettä, koska se käsittelee kaiken raakatekstinä. Erikoisuutena SentencePiecessä on alaviiva-merkintä, joka osoittaa sanan alun tai välilyönnin (“_Jussi”). Tämä auttaa palauttamaan alkuperäisen tekstin mahdollisimman tarkasti.

Unigram Language Model on SentencePiecen taustalla usein käytetty menetelmä, jossa jokaiselle tokenille määritellään todennäköisyys. Malli poimii sanastoon oikean kokoelman tokeneita niin, että kokonaiskieli on mahdollisimman hyvin katettu. Tämä mahdollistaa joustavan käsittelyn harvinaisille, pitkittyneille tai muuten monimutkaisille sanoille.

Oikea tokenisaattori valitaan yleensä kielen ja sovelluksen tarpeiden mukaan. Esimerkiksi suomenkielisissä projekteissa, joissa on paljon taivutusmuotoja, voidaan suosia menetelmiä, jotka tunnistavat tehokkaasti sananosia (kuten BPE tai Unigram). Lopputuloksena on menetelmä, jolla voidaan parhaiten tasapainottaa sanaston koko ja kielen rakenteiden oppiminen. 