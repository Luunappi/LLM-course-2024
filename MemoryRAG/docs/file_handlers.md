# Tiedostokäsittelijät

## Tuetut formaatit
- PDF (.pdf)
- Word (.docx, .doc) 
- HTML (.html, .htm)
- Tekstitiedostot (.txt)
- CSV (.csv)
- Excel (.xlsx, .xls)

## Taulukkotiedostot
- Maksimi rivimäärä: 1000 (muutettavissa)
- Tyhjät rivit ja sarakkeet poistetaan
- Sarakkeiden nimet muunnetaan pieniksi kirjaimiksi
- Metatiedot (tiedoston nimi, rivien ja sarakkeiden määrä) lisätään

## Käyttö
```python
from memoryrag.file_handlers import read_document

# Lue tiedosto
paragraphs = read_document("dokumentti.pdf")

# Käsittele kappaleet
for paragraph in paragraphs:
    print(paragraph)
``` 