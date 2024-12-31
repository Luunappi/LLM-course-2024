# LLM Course 2024

## Virtuaaliympäristö
source venv/bin/activate
deactivate

## Requirements
pip install pytest
pip install python-dotenv
pip install pytest-asyncio

## Yleiset testit
(testaa löytyykö tarvittavat avaimet)
pytest api_key_tests/test_api_key_jw.py -v

## Paikalliset mallit
Ollama on avoimen lähdekoodin projekti, joka mahdollistaa LLM-mallien (Large Language Models) ajamisen paikallisesti. Tärkeimmät ominaisuudet:
1. Mallin ajaminen paikallisesti:
```bash 
# Käynnistä Ollama palvelu
ollama serve
# Lataa malli (esim. Mistral)
ollama pull mistral
# Testaa mallia
ollama run mistral "Kerro tekoälystä"
``` 


Mistral-malli on asennettu Ollaman kautta ja se sijaitsee oletuksena polulla:
~/Library/Application Support/ollama/models/mistral

Voit tarkistaa tämän:
ls -l ~/Library/Application\ Support/ollama/models/mistral

Kun suoritat ollama pull mistral, Ollama:
Lataa mallin binäärit
Tallentaa ne yllä olevaan polkuun
Optimoi mallin suoritusta varten
Voit myös tarkistaa asennetut mallit komennolla:
ollama list
Tämä näyttää kaikki lokaalisti asennetut mallit ja niiden koot. 
```bash 
(venv)wrightju@LM4-029-32455 LLM-course-2024 % ollama list
NAME                ID              SIZE      MODIFIED    
mistral:latest      f974a74358d6    4.1 GB    2 weeks ago    
llama2:latest       78e26419b446    3.8 GB    2 weeks
``` 
Mistral-mallia ei voi käyttää ennen kuin:
Asennat Ollaman (jos ei vielä asennettu):
brew install ollama
Käynnistät Ollama-palvelun:
ollama serve
Lataat Mistral-mallin:
ollama pull mistral



