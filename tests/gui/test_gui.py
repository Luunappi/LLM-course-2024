import pytest
from PyQt6.QtCore import Qt
from memoryrag.gui.main_window import MainWindow


@pytest.fixture
def window(qtbot):
    """Luo pääikkuna testejä varten"""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


def test_window_title(window):
    """Testaa ikkunan otsikkoa"""
    assert window.windowTitle() == "MemoryRAG Chat"


def test_chat_input(window, qtbot):
    """Testaa chat-syötteen toimintaa"""
    # Kirjoita viesti
    qtbot.keyClicks(window.chat_input, "Testaa muistia")
    assert window.chat_input.text() == "Testaa muistia"
