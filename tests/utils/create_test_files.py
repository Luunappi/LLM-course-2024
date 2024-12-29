"""Apufunktiot testitiedostojen luomiseen"""

from pathlib import Path
import pandas as pd
import json


def create_test_files(test_dir: Path):
    """Luo testitiedostot annettuun hakemistoon"""
    test_dir.mkdir(exist_ok=True)

    # Luo CSV testitiedosto
    csv_content = """nimi,ikä,kaupunki
    Matti,30,Helsinki
    Liisa,25,Tampere
    Pekka,35,Turku"""

    csv_file = test_dir / "test.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    # Luo JSON testitiedosto
    json_content = {
        "data": [
            {"id": 1, "content": "Test content 1"},
            {"id": 2, "content": "Test content 2"},
        ]
    }
    json_file = test_dir / "test.json"
    json_file.write_text(json.dumps(json_content, indent=2), encoding="utf-8")

    # Luo tyhjä tiedosto
    empty_file = test_dir / "empty.txt"
    empty_file.touch()

    return {"csv": csv_file, "json": json_file, "empty": empty_file}
