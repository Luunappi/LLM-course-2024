"""RAG API Routes - RAG API-reitit

Tämä moduuli sisältää RAG-toiminnallisuuksiin liittyvät API-reitit:
1. Tiedostojen listaus (/api/rag/files)
2. Tiedostojen uudelleenindeksointi (/api/rag/reindex)
3. Tiedostojen poisto (/api/rag/delete)

Huomaa:
- Kaikki reitit palauttavat vastauksen JSON-muodossa
- Virhetilanteet käsitellään ja palautetaan selkeä virheilmoitus
- WebSocket-yhteyttä käytetään edistymisen raportointiin
"""

import os
import logging
from flask import request, jsonify
from agentformer.web.web_gui import app, socketio, orchestrator
from agentformer.tools.memory_tools.rag_tool import RAGTool

# Määritä logger
logger = logging.getLogger(__name__)

# Määritä polut
STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "memory/storage"
)
SAVED_FILES_DIR = os.path.join(STORAGE_DIR, "saved_files")


def emit_progress(value: float, message: str):
    """Lähetä edistymispäivitys WebSocket-yhteyden kautta.

    Args:
        value: Edistymisen arvo välillä 0-1
        message: Edistymisen tekstikuvaus
    """
    socketio.emit("upload_progress", {"value": value, "message": message})


@app.route("/get_indexed_files", methods=["GET"])
def get_indexed_files():
    """Hae indeksoidut tiedostot."""
    try:
        files = orchestrator.rag_tool.list_saved_files()
        # Varmista että palautetaan lista sanakirjan sisällä
        return jsonify(
            {
                "status": "success",
                "files": files,  # files on jo lista tiedostonimistä
                "message": f"Löytyi {len(files)} tiedostoa",
            }
        )
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({"status": "error", "files": [], "message": str(e)}), 500


@app.route("/api/rag/reindex", methods=["POST"])
def reindex_file():
    """Uudelleenindeksoi tietty tiedosto.

    Expects:
        JSON body: {"filename": "tiedosto.txt"}

    Returns:
        JSON-vastaus, joka sisältää:
        - status: "success" tai "error"
        - message: Onnistumis- tai virheilmoitus
    """
    try:
        data = request.get_json()
        filename = data.get("filename")
        if not filename:
            return jsonify({"status": "error", "message": "Filename not provided"})

        rag_tool = RAGTool()
        file_path = os.path.join(SAVED_FILES_DIR, filename)

        # Tarkista että tiedosto on olemassa
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File not found"})

        # Lue ja indeksoi tiedosto
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        metadata = {"filename": filename, "path": file_path, "type": "file"}
        if rag_tool.add_document(content, metadata):
            return jsonify(
                {"status": "success", "message": f"Successfully reindexed {filename}"}
            )
        else:
            return jsonify({"status": "error", "message": "Failed to reindex file"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/rag/delete", methods=["POST"])
def delete_file():
    """Poista tiedosto indeksistä ja saved_files-hakemistosta.

    Expects:
        JSON body: {"filename": "tiedosto.txt"}

    Returns:
        JSON-vastaus, joka sisältää:
        - status: "success" tai "error"
        - message: Onnistumis- tai virheilmoitus
    """
    try:
        data = request.get_json()
        filename = data.get("filename")
        if not filename:
            return jsonify({"status": "error", "message": "Filename not provided"})

        rag_tool = RAGTool()

        # Poista tiedosto saved_files-hakemistosta
        saved_file_path = os.path.join(SAVED_FILES_DIR, filename)
        if os.path.exists(saved_file_path):
            os.remove(saved_file_path)

        # Poista dokumentti document_storesta
        rag_tool.document_store.remove_document(filename)

        # Poista vektorit vector_storesta
        rag_tool.vector_store.remove_vectors_by_metadata({"filename": filename})

        return jsonify(
            {
                "status": "success",
                "message": f"Successfully deleted {filename}",
                "indexed_files": list(
                    rag_tool.document_store.get_all_documents().keys()
                ),  # Palauta päivitetty tiedostolista
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
