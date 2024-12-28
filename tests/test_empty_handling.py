import pytest
import os
from pathlib import Path
from memoryrag.file_handlers import read_document, read_spreadsheet


@pytest.fixture
def test_files(tmp_path):
    """Fixture testitiedostojen hallintaan"""
    # Luo CSV tyhjillä riveillä ja sarakkeilla
    csv_content = """nimi,ikä,kaupunki
    Matti,30,Helsinki

    Liisa,25,Tampere

    Pekka,35,Turku
    """

    csv_file = tmp_path / "empty_test.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    yield tmp_path

    # Siivoa testitiedostot
    if csv_file.exists():
        csv_file.unlink()


def test_empty_handling(test_files):
    """Testaa tyhjien rivien ja sarakkeiden käsittely"""
    csv_file = test_files / "empty_test.csv"
    content = read_document(str(csv_file))

    # Tarkista että sisältö on järkevä
    assert len(content) > 0
    assert "Matti" in content
    assert "Liisa" in content
    assert "Pekka" in content


def test_empty_spreadsheet(test_files):
    """Testaa tyhjän taulukon käsittely"""
    # Luo tyhjä CSV
    empty_csv = test_files / "empty.csv"
    empty_csv.write_text("", encoding="utf-8")

    # Tarkista että tyhjä tiedosto käsitellään oikein
    with pytest.raises(ValueError):
        read_spreadsheet(str(empty_csv))


def test_missing_values(test_files):
    """Testaa puuttuvien arvojen käsittely"""
    # Luo CSV puuttuvilla arvoilla
    missing_content = """nimi,ikä,kaupunki
    Matti,,Helsinki
    ,25,Tampere
    Pekka,35,
    """

    missing_file = test_files / "missing.csv"
    missing_file.write_text(missing_content, encoding="utf-8")

    # Tarkista että puuttuvat arvot käsitellään oikein
    content = read_document(str(missing_file))
    assert len(content) > 0
    assert "Matti" in content
    assert "Tampere" in content
    assert "Pekka" in content
