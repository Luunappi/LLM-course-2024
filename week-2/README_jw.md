
## Virtual environment 
deactivate
source ./venv/bin/activate

which python
which pip

rm -rf venv # poista venv

which python
which pip
python: aliased to /opt/homebrew/bin/python3.12
pip: aliased to /opt/homebrew/bin/pip3.12

The problem is that you have a Python alias set up in your shell that's interfering with the virtual environment. Let's fix this:
1. First, remove the Python alias. Open your ~/.zshrc file and comment out or remove the Python alias line. You can do this with:

nano ~/.zshrc 

2. After editing, reload your shell configuration:

source ~/.zshrc

3. Now let's create and activate a fresh virtual environment:
Remove old venv if it exists
rm -rf venv

Create new venv with explicit Python path
/opt/homebrew/bin/python3.12 -m venv venv

Activate the virtual environment
source venv/bin/activate

4. Verify you're using the correct Python from the virtual environment:
which python # Should show path to venv/bin/python                        
/Users/wrightju/Library/Mobile Documents/com~apple~CloudDocs/Code-Projects/LLM-course-2024/venv/bin/python

which pip # Should show path to venv/bin/pip
/Users/wrightju/Library/Mobile Documents/com~apple~CloudDocs/Code-Projects/LLM-course-2024/venv/bin/pip

## Asenna tarvittavat riippuvuudet 
./venv/bin/pip install -r week-2/in-context-learning/requirements.txt
./venv/bin/pip install -r week-2/gemini-chatbot/requirements.txt
./venv/bin/pip install -r  week-2/prompting-notebook/requirements.txt

./venv/bin/pip install -r  week-5/requirements.txt

### Tai mene halutuun viikkokansioon ja asenna suoraan siellä 
```bash
cd week-2/in-context-learning
```

Asenna riippuvuudet requirements.txt tiedostosta:

```bash
pip install -r requirements.txt
```
Tässä:
pip on paketinhallintaohjelma
-r kertoo pip:lle että luetaan vaatimukset tiedostosta
requirements.txt on tiedoston polku

## Luo .env
- tänne avaimet ym. salassapidettävät  

## Notebooks
Täällä näytetään kuinka voit ajaa python koodia kuten jypyter notebookissa mutta ilman jypyteria tai colabia 

VS Code Settings -> jupyter interactive window (X)
## Sift + Enter
 -> Normaalisti ajaa koodin terminaalissa mutta jos täppä on päällä niin code sniplet ajetaan erillisessä ikkunassa kuten jupyterissä.
https://youtu.be/mpk4Q5feWaw?si=Hw32UCZ_gBprC6R2&t=1362 


**<span style="color:green">Done!</span>**

