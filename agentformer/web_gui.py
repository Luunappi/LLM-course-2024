"""
Web GUI Application

Flask-pohjainen web-käyttöliittymä, joka:
1. Tarjoaa HTTP-rajapinnat frontendille
2. Hallitsee WebSocket-yhteydet reaaliaikaiseen kommunikointiin
3. Renderöi käyttöliittymän näkymät
4. Hallitsee käyttäjäsessiot

Huom: Kaikki bisneslogiikka on siirretty orchestrator.py:hyn ja työkaluihin.
Tämä moduuli keskittyy vain käyttöliittymän toimintoihin.
"""

from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from flask_socketio import SocketIO
import logging
import os
from dotenv import load_dotenv

# Lataa ympäristömuuttujat
load_dotenv()

# Omat moduulit
from core.orchestrator import AgentFormerOrchestrator
from tools.debug_tool import DebugTool
from tools.model_tool import ModelTool

# Konfiguroi logging kaikille komponenteille
logging.basicConfig(level=logging.INFO)  # Muutetaan oletustaso INFO:ksi
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Säädä muiden komponenttien lokitus
logging.getLogger("werkzeug").setLevel(logging.WARNING)  # Vain varoitukset Flaskista
logging.getLogger("httpx").setLevel(logging.WARNING)  # Vain varoitukset HTTP-pyynnöistä
logging.getLogger("sentence_transformers").setLevel(
    logging.INFO
)  # Näytä mallin latausviestit
logging.getLogger("agentformer").setLevel(logging.INFO)  # Näytä tärkeät viestit

# Alusta Flask ja CORS
app = Flask(__name__, static_folder="static", template_folder="templates")

# Konfiguraatio
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "supersecretkey"),
    SESSION_TYPE="filesystem",
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
)

# Alusta laajennukset
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Salli CORS WebSocketille
orchestrator = AgentFormerOrchestrator()
debug_tool = DebugTool()


# Perusreitit
@app.route("/")
def index():
    """Pääsivu"""
    return render_template("chat.html")


# API-endpointit
@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        message = data.get("message", "")

        # Process message with orchestrator
        result = orchestrator.process_query(message)

        if result.get("error"):
            return jsonify({"error": result["error"]})

        response = result.get("response", "")

        # Update token stats for this message exchange
        orchestrator.token_tool.get_message_stats(
            message=message,
            response=response,
            model=orchestrator.tools["llm"]
            .get_current_model()
            .get("name", "gpt-4o-mini"),
        )

        if "Ei dokumentteja indeksissä" in response:
            response = """Dokumentteja ei ole vielä ladattu järjestelmään. 
            
Voit ladata dokumentin seuraavasti:
1. Klikkaa 'Upload' nappia työkaluriviltä
2. Valitse PDF tai tekstitiedosto
3. Odota kunnes lataus on valmis

Tämän jälkeen voit kysyä dokumentin sisällöstä."""

        return jsonify({"response": response})

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({"error": str(e)})


@app.route("/api/rag/upload", methods=["POST"])
def rag_upload():
    """Handle file upload for RAG"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"error": "No file selected"}), 400

        # MUUTOS: Lisätty force_reindex=True
        result = orchestrator.tools["rag"].process_file(
            file.read(),
            file.filename,
            progress_callback=lambda value, msg: socketio.emit(
                "upload_progress", {"value": value, "message": msg}
            ),
            force_reindex=True,  # Pakota uudelleenindeksointi
        )

        # Jos tiedosto oli jo indeksoitu, se on nyt reindeksoitu
        if result.get("already_indexed"):
            return jsonify({"status": "success", "message": result["message"]})

        return jsonify(
            {
                "status": "success",
                "message": f"Tiedosto '{file.filename}' käsitelty onnistuneesti. Lisätty {result['chunks']} vektoria indeksiin.",
            }
        )

    except Exception as e:
        logger.error(f"Error in file upload: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rag/list", methods=["GET"])
def rag_list():
    """Get list of files from RAG tool"""
    try:
        # Get files from RAG tool
        files = orchestrator.tools["rag"].list_files()

        # Parse the files into a list of dictionaries
        file_list = []
        for file in files:
            # Each file string is in format: "filename [Indexed]" or "filename [Not indexed]"
            parts = file.split(" [")
            filename = parts[0]
            is_indexed = parts[1].strip("]") == "Indexed"
            file_list.append({"filename": filename, "is_indexed": is_indexed})

        return jsonify({"status": "success", "files": file_list})

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/models", methods=["GET"])
def get_models():
    """Palauta käytettävissä olevat mallit"""
    try:
        model_tool = orchestrator.tools["llm"]
        models = model_tool.get_available_models()
        current = model_tool.get_current_model()
        return jsonify({"models": models, "current": current})
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        # Return a default response with at least one model
        default_model = {
            "name": "gpt-4o-mini",
            "button_name": "gpt-4o-mini",
            "display_name": "gpt-4o-mini (1x€)",
            "config": {
                "type": "chat",
                "context_length": 8192,
                "temperature": 0.7,
                "max_tokens": 8192,
            },
        }
        return jsonify(
            {
                "models": [default_model],
                "current": {
                    "name": "gpt-4o-mini",
                    "button_name": "gpt-4o-mini",
                    "display_name": "gpt-4o-mini (1x€)",
                },
            }
        )


@app.route("/api/debug/info", methods=["GET"])
def debug_info():
    """Debug-tiedot"""
    try:
        return jsonify(
            {
                "stats": {
                    "error_count": len(debug_tool.get_errors()),
                    "warning_count": len(debug_tool.get_warnings()),
                },
                "events": debug_tool.get_events(),
            }
        )
    except Exception as e:
        logger.error(f"Debug info error: {e}")
        return jsonify({"error": str(e)}), 500


# WebSocket-käsittelijät
@socketio.on("connect")
def handle_connect():
    """WebSocket-yhteyden avaus"""
    logger.info("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    """WebSocket-yhteyden katkaisu"""
    logger.info("Client disconnected")


@app.route("/api/tool_info/<tool>", methods=["GET"])
def tool_info(tool):
    """Työkalujen tiedot"""
    try:
        if tool == "documents":
            docs = orchestrator.tools["rag"].get_documents_info()
            return jsonify(docs)
        elif tool == "tokens":
            # Get token stats directly from the token tool
            token_stats = orchestrator.token_tool.get_usage_stats()
            logger.debug(f"Token stats: {token_stats}")  # Add debug logging
            return jsonify(token_stats)
        elif tool == "system":
            return jsonify(
                {"os": os.name, "cwd": os.getcwd(), "server": "AgentFormer v1.0"}
            )
        elif tool == "prompt":
            prompts = orchestrator.tools["llm"].get_prompts()
            return jsonify({"info": prompts})
        else:
            return jsonify({"error": "Unknown tool"}), 404
    except Exception as e:
        logger.error(f"Tool info error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def direct_chat():
    """Suora LLM chat ilman RAG:ia"""
    try:
        data = request.get_json()
        message = data.get("message")
        if not message:
            return jsonify({"error": "No message provided"}), 400

        result = orchestrator.tools["llm"].process(message)
        return jsonify({"response": result})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/models/select", methods=["POST"])
def select_model():
    """Vaihda käytettävä malli"""
    try:
        data = request.get_json()
        model_name = data.get("model")
        if not model_name:
            return jsonify({"error": "Model name required"}), 400

        model_tool = orchestrator.tools["llm"]
        if model_tool.set_model(model_name):
            current = model_tool.get_current_model()
            return jsonify({"status": "success", "model": current})
        else:
            return jsonify({"error": "Invalid model"}), 400
    except Exception as e:
        logger.error(f"Error selecting model: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rag/query", methods=["POST"])
def rag_query():
    """RAG-kysely"""
    try:
        data = request.get_json()
        query = data.get("query")
        if not query:
            return jsonify({"error": "No query provided"}), 400

        # Soitetaan rag-työkalun kyselyfunktiota (oletus: .query)
        result = orchestrator.tools["rag"].query(query)
        return jsonify({"result": result})
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tokens/stats", methods=["GET"])
def get_token_stats():
    """Get token usage statistics"""
    try:
        # Get fresh stats from ModelTool singleton
        model_tool = ModelTool()
        stats = model_tool.get_usage_stats()

        # Ensure we have all required fields
        if not stats:
            stats = {
                "current": {
                    "model": "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                },
                "total": {"total_tokens": 0, "total_cost": 0.0},
                "models": {},
            }

        logger.debug(f"Token stats: {stats}")  # Log the stats for debugging
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting token stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/system/stats", methods=["GET"])
def system_stats():
    """Get system statistics"""
    try:
        system_info = orchestrator.tools["system"].get_timing_stats()
        return jsonify(system_info)
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/prompts", methods=["GET"])
def get_prompts():
    """Get prompt information"""
    try:
        prompt_tool = orchestrator.tools["prompt"]
        prompts = {
            "prompts": prompt_tool.list_prompts(),
            "active": prompt_tool.get_active_prompts(),
        }
        return jsonify(prompts)
    except Exception as e:
        logger.error(f"Error getting prompts: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/prompts/update", methods=["POST"])
def update_prompt():
    """Update prompt content"""
    try:
        data = request.get_json()
        prompt_type = data.get("type")
        content = data.get("content")
        name = data.get("name", "custom")

        if not prompt_type or not content:
            return jsonify({"error": "Missing prompt type or content"}), 400

        prompt_tool = orchestrator.tools["prompt"]
        if prompt_tool.set_prompt(prompt_type, content, name):
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Failed to update prompt"}), 400
    except Exception as e:
        logger.error(f"Error updating prompt: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rag/documents", methods=["GET"])
def get_documents():
    """Get information about loaded documents"""
    try:
        documents = orchestrator.tools["rag"].get_documents_info()
        return jsonify({"status": "success", "documents": documents})
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/prompts/length", methods=["POST"])
def update_response_length():
    """Update response length setting"""
    try:
        data = request.get_json()
        length = data.get("response_length")

        if not length:
            return jsonify({"error": "Missing response length"}), 400

        model_tool = ModelTool()
        if model_tool.set_response_length(length):
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Invalid response length"}), 400

    except Exception as e:
        logger.error(f"Error updating response length: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rag/reindex", methods=["POST"])
def rag_reindex():
    """Tarkista ja päivitä RAG-indeksi"""
    try:

        def progress_callback(value, msg):
            # Log progress to terminal
            if isinstance(value, float):
                progress = int(value * 100)
                print(f"\rReindexing: [{progress}%] {msg}", end="", flush=True)
            else:
                print(f"\n{msg}")
            # Also emit to socket
            socketio.emit("reindex_progress", {"value": value, "message": msg})

        result = orchestrator.tools["rag"].check_and_reindex_files(
            progress_callback=progress_callback
        )

        # Print final message
        if result["status"] == "up_to_date":
            print("\nIndex is up to date. No files to reindex.")
        elif result["status"] == "reindexed":
            print(f"\nReindexing complete. {result['message']}")
        else:
            print(f"\nReindex status: {result['message']}")

        return jsonify(result)
    except Exception as e:
        logger.error(f"Reindex error: {e}")
        print(f"\nError during reindexing: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rag/files", methods=["GET"])
def list_saved_files():
    """List all saved files with summaries"""
    try:
        logger.info("Haetaan indeksoidut tiedostot...")
        result = orchestrator.tools["rag"].list_saved_files()

        # MUUTOS: Muokataan vastauksen rakenne oikeaksi
        if result.get("status") == "success" and "files" in result:
            files = result["files"]

            # Näytä tiedostojen nimet ja indeksointistatus
            logger.info("Löydetyt tiedostot:")
            for file in files:
                status = "[Indexed]" if file.get("is_indexed") else "[Not indexed]"
                logger.info(f"- {file['filename']} {status}")

            # Muotoile tiedot front-endin odottamaan muotoon
            formatted_files = []
            for file in files:
                formatted_files.append(
                    {
                        "filename": file["filename"],
                        "summary": file.get("summary", ""),
                        "timestamp": file.get("timestamp", 0),
                        "size": file.get("size", 0),
                        "is_indexed": file.get("is_indexed", False),
                    }
                )
            return jsonify(formatted_files)

        logger.warning("Ei löydetty tiedostoja tai vastauksen muoto väärä")
        return jsonify([])  # Tyhjä lista jos ei tiedostoja
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    socketio.run(app, debug=True, port=5001)
