# Viikko 2: LLM Chatbot


## Gemini-chatbot
- Simppeli chat ikkuna 
    - Web-käyttöliittymällä varustettu chatbot (basic_chatbot_JW.py):
    - Terminaalipohjainen chatbot (gemini_prompting_jw.py)

## in-context-learning
cd week-2/in-context-learning

### Työkalu, joka analysoi tutkimusartikkeleita tekoälyn avulla. 

- Hakee tutkimusartikkeleita Hugging Face:n sivustolta
- Lataa PDF-muotoiset artikkelit
- Analysoi artikkelit Mistral-kielimallilla ja Tuottaa jokaisesta artikkelista:
   -  Yhteenvedon, Vahvuudet, Heikkoudet: Tulostaa HTML-raportin
   - Raportti tallennetaan data/output/papers.html tiedostoon
```shell
open HTML-reports/papers_2024-12-30.html 
```
### Riippuvuudet
```shell
pip install openai python-dotenv beautifulsoup4 pypdf tqdm requests 
pip install psutil
```

```shell
python in_context_learning-JW.py
```

## Rakenne
```shell
week-2/
├── model_utils_jw.py      # Yhteinen model utils (Gemini + Mistral)
└── gemini-chatbot/
    ├── basic_chatbot_JW.py    # Chatbot sovellus
    ├── templates/             # UI templates
    │   └── chat.html
    └── gemini_prompting_jw.py # Gemini kokeilut
```

## Mallit

### Gemini
- Käyttää Google Gemini API:a
- Vaatii GOOGLE_API_KEY:n .env tiedostossa
- Tukee suomea ja englantia

### Mistral (Ollama)
```shell
# Asenna ja käynnistä Ollama
$ ollama serve

# Luo suomenkielinen Mistral-malli
$ cat << EOF > mistral-fi.json
{
  "name": "mistral-fi",
  "base": "mistral",
  "system": "Olet suomenkielinen tekoälyassistentti. Vastaat kysymyksiin selkeällä suomen kielellä."
}
EOF

$ ollama create mistral-fi -f mistral-fi.json
```

## Käyttö

1. Asenna riippuvuudet:
```shell
pip install -r requirements.txt
```

2. Käynnistä chatbot:
```shell
cd gemini-chatbot
python basic_chatbot_JW.py
```

3. Avaa selain: http://localhost:8000

## Mallin vaihtaminen
model = get_model("mistral") → model = get_model("gemini")