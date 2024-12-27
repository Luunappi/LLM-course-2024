"""CSV ja Excel tiedostojen käsittelijä"""

from typing import List
import pandas as pd
from pathlib import Path


def read_spreadsheet(file_path: str, max_rows: int = 1000) -> List[str]:
    """Lukee CSV/Excel-tiedoston ja palauttaa tekstin kappaleina

    Args:
        file_path: Tiedoston polku
        max_rows: Maksimi rivimäärä (oletuksena 1000)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Tiedostoa ei löydy: {file_path}")

    try:
        # Tarkista onko tiedosto tyhjä
        if Path(file_path).stat().st_size == 0:
            return []

        # Lue tiedosto pandas DataFrameksi
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(
                file_path,
                nrows=max_rows,
                skipinitialspace=True,
                on_bad_lines="error",  # Nosta virhe jos rivit eivät täsmää
            )
        else:  # Excel
            df = pd.read_excel(file_path, nrows=max_rows)

        # Poista tyhjät sarakkeet ja rivit
        df = df.dropna(how="all", axis=1)
        df = df.dropna(how="all", axis=0)
        df = df.fillna("")

        # Muotoile sarakkeiden nimet
        df.columns = [str(col).strip().lower() for col in df.columns]

        paragraphs = []

        # Lisää metatiedot
        meta = f"Taulukko: {file_path.name}"
        meta += f"\nSarakkeet: {len(df.columns)}, Rivit: {len(df)}"
        paragraphs.append(meta)

        # Lisää otsikkorivi
        headers = " | ".join(df.columns)
        paragraphs.append(headers)

        # Lisää jokainen rivi omana kappaleenaan
        for _, row in df.iterrows():
            values = [str(val).strip() for val in row.values]
            line = " | ".join(values)
            if line.strip():
                paragraphs.append(line)

        return paragraphs

    except Exception as e:
        raise RuntimeError(f"Virhe taulukon lukemisessa: {e}")
