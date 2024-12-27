def test_empty_handling(tmp_path):
    """Testaa tyhjien rivien ja sarakkeiden käsittely"""
    # Luo CSV tyhjillä riveillä ja sarakkeilla
    csv_content = """nimi,ikä,kaupunki
    Matti,30,Helsinki
    
    Liisa,25,Tampere
    
    Pekka,35,Turku
    """

    csv_file = tmp_path / "empty_test.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    # Lue ja testaa
    paragraphs = read_document(csv_file)

    # Tarkista että tyhjät rivit on poistettu
    assert len(paragraphs) == 5  # meta + header + 3 riviä
