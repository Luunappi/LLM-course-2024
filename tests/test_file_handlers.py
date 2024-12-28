import pytest
import os
from pathlib import Path
from memoryrag.file_handlers import read_document, read_spreadsheet


@pytest.fixture
def test_files(tmp_path):
    """Fixture testitiedostojen hallintaan"""
    # Luo testitiedostot
    from tests.utils.create_test_files import (
        create_test_pdf,
        create_test_docx,
        create_test_excel,
    )

    # Luo hakemisto
    test_dir = tmp_path / "test_files"
    test_dir.mkdir(exist_ok=True)

    # Luo testitiedostot
    create_test_pdf(test_dir)
    create_test_docx(test_dir)
    create_test_excel(test_dir)

    yield test_dir

    # Siivoa testitiedostot
    if test_dir.exists():
        import shutil

        shutil.rmtree(test_dir)


def test_read_pdf(test_files):
    """Testaa PDF-tiedoston lukeminen"""
    content = read_document(test_files / "test.pdf")
    assert len(content) > 0
    assert "Test PDF Document" in content
    assert "test content for MemoryRAG" in content


def test_read_docx(test_files):
    """Testaa DOCX-tiedoston lukeminen"""
    content = read_document(test_files / "test.docx")
    assert len(content) > 0
    assert "Test Document" in content


def test_read_excel(test_files):
    """Testaa Excel-tiedoston lukeminen"""
    content = read_spreadsheet(test_files / "test.xlsx")
    assert len(content) > 0
    assert "Test Data" in content


def test_invalid_file():
    """Testaa virheellisen tiedoston käsittely"""
    with pytest.raises(ValueError):
        read_document("nonexistent.pdf")


def test_empty_file(test_files):
    """Testaa tyhjän tiedoston käsittely"""
    empty_file = test_files / "empty.txt"
    empty_file.write_text("")

    with pytest.raises(ValueError):
        read_document(empty_file)
