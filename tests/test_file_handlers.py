"""Testit tiedostokäsittelijöille"""

import pytest
from pathlib import Path
from memoryrag.file_handlers import read_document
from tests.utils.create_test_files import create_test_files


@pytest.fixture(scope="module")
def test_files(tmp_path_factory):
    """Luo testitiedostot väliaikaiseen hakemistoon"""
    test_dir = tmp_path_factory.mktemp("test_files")
    files = create_test_files(test_dir)
    yield files
    # Siivoa testitiedostot
    for file in files.values():
        if file.exists():
            file.unlink()
    test_dir.rmdir()


def test_read_csv(test_files):
    """Testaa CSV-tiedoston lukeminen"""
    content = read_document(test_files["csv"])
    assert "Matti" in content
    assert "Helsinki" in content


def test_empty_file(test_files):
    """Testaa tyhjän tiedoston käsittely"""
    with pytest.raises(ValueError):
        read_document(test_files["empty"])
