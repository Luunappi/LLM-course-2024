# Lab Report 4

Tämä on raportti DPO-fine-tuning -kokeilusta Mistral-7B -mallilla. Seuraavassa käydään läpi sovellettua menetelmää, käytettyä dataa sekä havaintoja mallien vertailusta.

## 1. Tavoite

Tavoitteena oli totuttaa DPO (Direct Preference Optimization) -pohjainen jälkikoulutus (fine-tuning) Mistral-7B -mallille. Aiemmin vastaavat kokeilut perustuivat pääosin perinteiseen valvottuun (SFT, supervised fine-tuning) menetelmään. DPO:n ideana on käyttää parivastineita (chosen–rejected), joiden avulla malli oppii tuottamaan suositeltavampia vastauksia. 

## 2. Toteutus

1. Vaihdettiin perusmalli Mistral-7B-Instruct-v0.3:een (kuten Hugging Facen repossa “mistralai/Mistral-7B-Instruct-v0.3”).
2. Etsittiin DPO-data Hugging Facesta (esim. [Anthropic HH-RLHF](https://huggingface.co/datasets/Anthropic/hh-rlhf) tai [Intel/orca_dpo_pairs](https://huggingface.co/datasets/Intel/orca_dpo_pairs)) ja laskettiin datasetin kokoonpano.  
3. Toteutettiin DPO-fine-tuning menetelmä:
   - Vaihdettiin BitsAndBytes-optimoija (bitsandbytes, 4-bit kvantisaatio jne.) tavalliseen AdamW/Torch-optimointiin.  
   - Poistettiin evaluaatiostrategia (“no” / “save_strategy=’no’”) tai muutoin rajoitettiin evalointia.  
   - Lisäksi dataset jaettiin train–eval-osuuksiin (kuten 90%/10%).  
4. Fine-tuning toteutettiin LoRA-adaptereilla, joilla pyrittiin vähentämään muistin käyttöä.
5. Harjoitetun mallin lopputulos tallennettiin Hugging Face Hubiin, josta se on suoraan ladattavissa.

## 3. Testaus

Testausta varten tehtiin erillinen vertailuskripti, joka:
1. Lataa sekä base- että fine-tuned -mallin.  
2. Syöttää molemmille joukon samantyyppisiä kysymyksiä (viisi erilaista testipromptia).  
3. Vertailee mallien tuottamia vastauksia laatukriteereillä (koherenssi, relevanssi, syvyys).  

Havaintojen mukaan fine-tuned -malli suoriutui base-mallia paremmin 4/5 testissä. Fine-tuned -malli osoitti:
- Syvällisempää analyysia  
- Parempaa koherenssia  
- Joissain tapauksissa pitkiä, ”liian perusteellisia” vastauksia, kun yksinkertainen vastaus olisi riittänyt  

Perusmalli pärjäsi parhaiten hyvin yksinkertaisissa, vähäsisältöisissä kysymyksissä, joissa laaja ”analyysi” ei ollut tarpeen.

## 4. Johtopäätökset ja jatkokehitys

- DPO-fine-tuning näyttäisi parantavan mallin kykyä tuottaa hyödyllisiä ja sisällöllisesti täsmällisiä vastauksia, erityisesti kun koulutusdata sisältää ihmisten mielestä “parempana” pidettyjä esimerkkivastauksia.  
- Jatkokehityksenä voisi kokeilla useampaa DPO-datasettiä ja vertailla vielä laajemmin eri base-malleja (myös <7B -kokoon).  
- Bitsandbytesin käyttö voi madaltaa VRAM-tarvetta, mutta jos laitteisto mahdollistaa, tavallinen float16 + AdamW voi olla riittävä.  
- Suuremmalla (tai monipuolisemmalla) datasetillä, pidemmällä harjoittelulla tai lisämäärittelyillä (kuten deltalle, betalle, tms. parametreille) voisi vielä kohentaa tuloksia.  

## 5. Yhteenveto

Koe vahvisti, että Mistral-7B hyötyy DPO-lähestymistavasta, etenkin ihmisten mieltymysten (chosen vs. rejected) suhteen. Koulutettu malli toimi yhden testausajon perusteella luotettavammin ja kattavammin verrattuna base-malliin. Myös ominaisuuksien (kuten perusteluiden kirjoittamisen) kehitys oli selvästi havaittavissa. Käytännön sovelluksia ajatellen malli on hyödyllinen erityisesti tehtävissä, joissa vastauksen laatuun vaikuttavat inhimilliset mieltymykset tai eettiset/harkintaa vaativat näkökulmat.

---
Viimeksi muokattu: {{ site.time | date: "%Y-%m-%d" }} 