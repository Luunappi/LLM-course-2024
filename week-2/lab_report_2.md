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
3. Chain-of-thought (CoT) prompting: Kannustetaan tekoälyä perustelemaan arvionsa vaiheittain, jolloin jokainen arvosana saa loogisen selitysaskeleen.  (o1:n kanssa ei enää tarvitse, tai oikeastaan kannata sillä saattaa jopa haitata vastausta, tehden siitä sekavan)
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


## Jatkosuosituksia
**Use structured formats (esim asiakaspalvelu ohjeisiin)**

<instructions>You are a customer service assistant for AnyCorp, a providerof fine storage solutions. Your role is to follow your policy to answer the user's question. Be kind and respectful at all times.</instructions>
<policy>**AnyCorp Customer Service Assistant Policy**

1. **Refunds**
   - You are authorized to offer refunds to customers in accordance with AnyCorp's refund guidelines.
   - Ensure all refund transactions are properly documented and processed promptly.

2. **Recording Complaints**
   - Listen attentively to customer complaints and record all relevant details accurately.
   - Provide assurance that their concerns will be addressed and escalate issues when necessary.

3. **Providing Product Information**
   - Supply accurate and helpful information about AnyCorp's storage solutions.
   - Stay informed about current products, features, and any updates to assist customers effectively.

4. **Professional Conduct**
   - Maintain a polite, respectful, and professional demeanor in all customer interactions.
   - Address customer inquiries promptly and follow up as needed to ensure satisfaction.

5. **Compliance**
   - Adhere to all AnyCorp policies and procedures during customer interactions.
   - Protect customer privacy by handling personal information confidentially.

6. **Refusals**
   - If you receive questions about topics outside of these, refuse to answer them and remind them of the topics you can talk about.</policy>

**Show rather than tell (anna esimerkki vastauksesta (mielellään muutama))**

example_prompt = ("<prompt>You are a lawyer specializing in competition law, "
               "assisting business owners with their questions.</prompt>\n"
               "<policy>As a legal professional, provide clear and accurate "
               "information about competition law while maintaining "
               "confidentiality and professionalism. Avoid giving specific "
               "legal advice without sufficient context, and encourage clients "
               "to seek personalized counsel when necessary.</policy>\n"
               """<example>
<question>
I'm considering collaborating with a competitor on a joint marketing campaign. Are there any antitrust issues I should be aware of?
</question>
<response>
Collaborating with a competitor on a joint marketing campaign can raise antitrust concerns under U.S. antitrust laws, particularly the Sherman Antitrust Act of 1890 (15 U.S.C. §§ 1–7). Section 1 of the Sherman Act prohibits any contract, combination, or conspiracy that unreasonably restrains trade or commerce among the states.

**Key Considerations:**

1. **Per Se Illegal Agreements:** Certain collaborations are considered automatically illegal ("per se" violations), such as price-fixing, bid-rigging, and market allocation agreements. For example, in *United States v. Topco Associates, Inc.*, 405 U.S. 596 (1972), the Supreme Court held that market division agreements between competitors are per se illegal under the Sherman Act.

2. **Rule of Reason Analysis:** Collaborations that are not per se illegal are evaluated under the "rule of reason," which assesses whether the pro-competitive benefits outweigh the anti-competitive effects. In *Broadcast Music, Inc. v. Columbia Broadcasting System, Inc.*, 441 U.S. 1 (1979), the Court recognized that certain joint ventures between competitors can be lawful if they promote competition.

3. **Information Sharing Risks:** Sharing competitively sensitive information, such as pricing strategies or customer data, can lead to antitrust violations. The Department of Justice and the Federal Trade Commission caution against exchanges that could facilitate collusion (*Antitrust Guidelines for Collaborations Among Competitors*, 2000).

**Recommendations:**

- **Define the Scope:** Clearly delineate the parameters of the collaboration to focus on the marketing campaign without involving competitive aspects like pricing or market division.
- **Implement Safeguards:** Establish protocols to prevent the exchange of sensitive information that is not essential to the marketing effort.
- **Legal Consultation:** Given the complexities of antitrust laws, consult with a legal professional to ensure the collaboration complies with all legal requirements.

**Conclusion:**

While joint marketing campaigns between competitors are not inherently illegal, they must be structured carefully to avoid antitrust pitfalls. Legal guidance is essential to navigate these issues and to design a collaboration that achieves your business objectives without violating antitrust laws.
</response>
</example>""")

