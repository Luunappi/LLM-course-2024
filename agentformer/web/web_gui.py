"""
Web GUI Application

Flask-pohjainen web-käyttöliittymä, joka:
1. Tarjoaa HTTP-rajapinnat frontendille
2. Hallitsee WebSocket-yhteydet reaaliaikaiseen kommunikointiin
3. Renderöi käyttöliittymän näkymät
4. Hallitsee käyttäjäsessiot

Huom: Kaikki bisneslogiikka on siirretty työkaluihin.
Tämä moduuli keskittyy vain käyttöliittymän toimintoihin.
"""

from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from flask_socketio import SocketIO
import logging
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Core imports
from agentformer.core.orchestrator import AgentFormerOrchestrator
from agentformer.core.messaging import MessageBus, EventType

# Tool imports
from agentformer.tools.analysis_tools.debug_tool import DebugTool
from agentformer.tools.core_tools.model_tool import ModelTool
from agentformer.tools.memory_tools.rag_tool import RAGTool
from agentformer.tools.analysis_tools.analyzer_tool import AnalyzerTool

# Konfiguroi logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
    handlers=[logging.StreamHandler()],
)

# Hiljennä ylimääräiset loggerit
for logger_name in [
    "werkzeug",
    "socketio",
    "engineio",
    "sentence_transformers",
    "httpx",
    "huggingface",
    "urllib3",
]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Lataa ympäristömuuttujat
load_dotenv()

# Alusta Flask ja CORS
app = Flask(__name__, static_folder="static", template_folder="templates")

# Konfiguraatio
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "supersecretkey"),
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR="web/flask_session",  # Päivitetty polku
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
)

# Alusta laajennukset
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Salli CORS WebSocketille
orchestrator = AgentFormerOrchestrator()
debug_tool = DebugTool()

# Initialize tools
logger.info("Initializing tools...")
model_tool = ModelTool()
rag_tool = orchestrator.rag_tool  # Käytetään orkestraattorin RAG-työkalua suoraan
logger.info(f"Using model: {model_tool.get_current_model()}")

# Alusta MessageBus
message_bus = MessageBus()


# Määritellään callback-funktiot
def handle_indexing_started(data):
    """Käsittele indeksoinnin aloitus"""
    socketio.emit(
        "indexing_status", {"status": "started", "filename": data["filename"]}
    )


def handle_indexing_progress(data):
    """Käsittele indeksoinnin edistyminen"""
    socketio.emit(
        "indexing_status",
        {
            "status": "progress",
            "filename": data["filename"],
            "progress": data["progress"],
        },
    )


def handle_indexing_complete(data):
    """Käsittele indeksoinnin valmistuminen"""
    socketio.emit(
        "indexing_status", {"status": "complete", "filename": data["filename"]}
    )


def handle_indexing_error(data):
    """Käsittele indeksointivirheet"""
    socketio.emit(
        "indexing_status",
        {"status": "error", "filename": data["filename"], "error": data["error"]},
    )


def handle_rag_query_started(data):
    """Käsittele RAG-kyselyn aloitus"""
    logger.info(f"RAG query started: {data['query']}")
    socketio.emit("rag_status", {"status": "started", "query": data["query"]})


def handle_rag_query_complete(data):
    """Käsittele RAG-kyselyn valmistuminen"""
    logger.info(f"RAG query completed: {data['query']}")
    socketio.emit(
        "rag_status",
        {"status": "complete", "query": data["query"], "results": data["results"]},
    )


def handle_rag_query_error(data):
    """Käsittele RAG-kyselyn virheet"""
    logger.error(f"RAG query error: {data['error']}")
    socketio.emit(
        "rag_status",
        {"status": "error", "query": data["query"], "error": data["error"]},
    )


# Rekisteröi kuuntelijat
message_bus.subscribe(EventType.INDEXING_STARTED, handle_indexing_started)
message_bus.subscribe(EventType.INDEXING_PROGRESS, handle_indexing_progress)
message_bus.subscribe(EventType.INDEXING_COMPLETE, handle_indexing_complete)
message_bus.subscribe(EventType.INDEXING_ERROR, handle_indexing_error)
message_bus.subscribe(EventType.RAG_QUERY_STARTED, handle_rag_query_started)
message_bus.subscribe(EventType.RAG_QUERY_COMPLETE, handle_rag_query_complete)
message_bus.subscribe(EventType.RAG_QUERY_ERROR, handle_rag_query_error)


# Perusreitit
@app.route("/")
def index():
    """Pääsivu"""
    return render_template("chat.html")


# API-endpointit
@app.route("/api/chat", methods=["POST"])
def chat():
    """Chat endpoint that processes messages and returns responses"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        query = data.get("message")
        if not query:
            return jsonify({"error": "No message provided"}), 400

        mode = data.get("mode", True)  # true = LLM, false = RAG
        logger.info(f"Processing {mode} query: {query[:50]}...")

        if mode:  # LLM mode
            try:
                response = model_tool.query(
                    messages=[{"role": "user", "content": query}]
                )
                return jsonify(
                    {
                        "answer": response,
                        "source": "llm",
                        "model": "gpt-4o-mini",
                        "found_in_docs": False,
                    }
                )
            except Exception as e:
                logger.error(f"LLM query failed: {str(e)}")
                return jsonify({"error": f"LLM query failed: {str(e)}"}), 500
        else:  # RAG mode
            try:
                response = rag_tool.query(query)
                return jsonify(
                    {
                        "answer": response.get("response"),
                        "source": "rag",
                        "model": "gpt-4o-mini",
                        "found_in_docs": response.get("found_in_docs", False),
                    }
                )
            except Exception as e:
                logger.error(f"RAG query failed: {str(e)}")
                return jsonify({"error": f"RAG query failed: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rag/upload", methods=["POST"])
def upload_file():
    """Lataa tiedosto ja indeksoi se"""
    try:
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "Ei tiedostoa"})

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"status": "error", "message": "Ei valittua tiedostoa"})

        if file:
            # Hae polut PathManagerilta
            paths = PathManager.get_storage_paths()
            save_dir = paths["saved_files"]

            # Luo tiedostopolku
            filename = secure_filename(file.filename)
            save_path = os.path.join(save_dir, filename)

            # Tallenna tiedosto
            file.save(save_path)

            # Tarkista että tiedosto on tallennettu
            if not os.path.exists(save_path):
                return jsonify(
                    {"status": "error", "message": "Tiedoston tallennus epäonnistui"}
                )

            logger.info(
                f"File saved successfully. Size: {os.path.getsize(save_path)} bytes"
            )

            # Indeksoi tiedosto
            result = rag_tool.index_file(filename, save_path)

            if result["status"] == "success":
                # Hae päivitetty tiedostolista
                files = rag_tool.list_saved_files()
                return jsonify(
                    {
                        "status": "success",
                        "message": result["message"],
                        "files": [{"filename": f, "is_indexed": True} for f in files],
                    }
                )
            else:
                # Poista tiedosto jos indeksointi epäonnistui
                os.remove(save_path)
                return jsonify(
                    {
                        "status": "error",
                        "message": result["message"],
                        "error_type": result.get("error_type", "unknown"),
                    }
                )

    except Exception as e:
        logger.error(f"Error in file upload: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})


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
    """Käsittele uusi WebSocket-yhteys"""
    logger.info("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    """Käsittele WebSocket-yhteyden katkaisu"""
    logger.info("Client disconnected")


@socketio.on("reindex")
def handle_reindex():
    """Käsittele reindeksointipyyntö"""
    try:
        # Lähetä aloitusviesti
        socketio.emit(
            "reindex_progress", {"value": 0.0, "message": "Aloitetaan reindeksointi..."}
        )

        result = rag_tool.check_and_reindex_files()

        # Lähetä valmistumisviesti
        socketio.emit(
            "reindex_progress", {"value": 1.0, "message": "Reindeksointi valmis"}
        )

        socketio.emit(
            "reindex_complete",
            {"status": result["status"], "message": result["message"]},
        )
    except Exception as e:
        logger.error(f"Error during reindexing: {str(e)}")
        socketio.emit("reindex_error", {"message": str(e)})


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
    """Select model to use"""
    try:
        data = request.get_json()
        if not data or "model" not in data:
            return jsonify({"error": "No model specified"}), 400

        model_name = data["model"]
        logger.info(f"Selecting model: {model_name}")

        # Update model in ModelTool
        model_tool.set_model(model_name)

        # Update model in RAG tool
        rag_tool.model_tool = model_tool

        return jsonify(
            {
                "status": "success",
                "message": f"Model changed to {model_name}",
                "model": model_name,
            }
        )

    except Exception as e:
        logger.error(f"Error selecting model: {str(e)}", exc_info=True)
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
def reindex_files():
    """Reindex all files"""
    try:
        logger.info("Starting reindexing...")

        # Get list of files
        files = rag_tool.list_saved_files()
        if not files:
            return jsonify({"status": "error", "message": "No files found to reindex"})

        # Track successfully indexed files
        indexed = []

        # Reindex each file
        for filename in files:
            try:
                # Read file content
                file_path = os.path.join(rag_tool.saved_files_dir, filename)

                # Handle PDF files
                if filename.lower().endswith(".pdf"):
                    from pypdf import PdfReader

                    reader = PdfReader(file_path)
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text()
                else:
                    # Handle text files
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                # Add to vector store
                rag_tool.vector_store.add_texts([content], [filename])
                indexed.append(filename)
                logger.info(f"Reindexed: {filename}")

            except Exception as e:
                logger.error(f"Error indexing {filename}: {str(e)}")
                continue

        return jsonify(
            {
                "status": "success",
                "message": f"Reindexed {len(indexed)} files",
                "indexed": indexed,
            }
        )

    except Exception as e:
        logger.error(f"Error reindexing files: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/rag/update_index", methods=["POST"])
def update_index():
    """Indeksoi vain indeksoimattomat tiedostot"""
    try:
        # Tarkista mitkä tiedostot puuttuvat indeksistä
        paths = PathManager.get_storage_paths()
        save_dir = paths["saved_files"]

        disk_files = set(f for f in os.listdir(save_dir) if not f.startswith("."))
        indexed_files = set(rag_tool.list_saved_files())

        missing_files = disk_files - indexed_files

        if not missing_files:
            return jsonify(
                {"status": "info", "message": "Kaikki tiedostot on jo indeksoitu"}
            )

        # Indeksoi puuttuvat tiedostot
        indexed = []
        for filename in missing_files:
            file_path = os.path.join(save_dir, filename)
            if rag_tool.index_file(filename, file_path):
                indexed.append(filename)

        return jsonify(
            {
                "status": "success",
                "message": f"Indeksoitu {len(indexed)} uutta tiedostoa",
                "indexed_files": rag_tool.list_saved_files(),
            }
        )

    except Exception as e:
        logger.error(f"Error updating index: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/rag/files", methods=["GET"])
def list_saved_files():
    """List all saved files with summaries"""
    try:
        logger.info("Haetaan indeksoidut tiedostot...")
        files = orchestrator.list_saved_files()

        if not files:
            return jsonify(
                {
                    "status": "no_files",
                    "message": (
                        "Ei indeksoituja dokumentteja. Lisää dokumentteja:\n"
                        "1. Raahaa ja pudota tiedosto tähän ikkunaan, TAI\n"
                        "2. Aseta tiedostot hakemistoon 'storage/memory/saved_files' ja "
                        "paina 'Reindex All Files' -nappia."
                    ),
                    "files": [],  # Tyhjä lista jos ei tiedostoja
                }
            )

        # Muodosta lista tiedostoista
        formatted_files = []
        for filename in files:
            formatted_files.append(
                {
                    "filename": filename,
                    "is_indexed": True,  # Jos tiedosto on listalla, se on indeksoitu
                }
            )

        # Palauta aina sanakirja jossa on status, message ja files
        return jsonify(
            {
                "status": "success",
                "message": f"Löytyi {len(files)} tiedostoa",
                "files": formatted_files,
            }
        )

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify(
            {
                "status": "error",
                "message": "Virhe tiedostojen haussa",
                "error": str(e),
                "files": [],  # Tyhjä lista virhetilanteessa
            }
        ), 500


@app.route("/api/chat/analyze", methods=["POST"])
def analyze_query():
    """Analyze query to determine best model and tools to use"""
    try:
        data = request.get_json()
        message = data.get("message")

        # Use a fast model (o1-mini) to analyze the query
        analysis = orchestrator.analyze_query(message)

        return jsonify(
            {
                "status": "success",
                "analysis": analysis.get("explanation"),
                "model": analysis.get("model"),
                "should_use_rag": analysis.get("should_use_rag", False),
                "tools": analysis.get("tools", []),
            }
        )
    except Exception as e:
        logger.error(f"Error analyzing query: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/guidelines/pending", methods=["GET"])
def get_pending_guideline_update():
    """Get any pending guideline update proposal"""
    try:
        update = orchestrator.analyzer.get_pending_update()
        if update:
            return jsonify({"status": "success", "update": update})
        return jsonify({"status": "success", "update": None})
    except Exception as e:
        logger.error(f"Error getting guideline update: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/guidelines/apply", methods=["POST"])
def apply_guideline_update():
    """Apply pending guideline update after user confirmation"""
    try:
        if orchestrator.analyzer.apply_guideline_update(orchestrator):
            return jsonify(
                {"status": "success", "message": "Guidelines updated successfully"}
            )
        return jsonify(
            {"status": "error", "message": "No pending update to apply"}
        ), 400
    except Exception as e:
        logger.error(f"Error applying guideline update: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/guidelines/reject", methods=["POST"])
def reject_guideline_update():
    """Reject and clear pending guideline update"""
    try:
        orchestrator.analyzer.clear_pending_update()
        return jsonify({"status": "success", "message": "Update rejected"})
    except Exception as e:
        logger.error(f"Error rejecting guideline update: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/reindex", methods=["POST"])
def reindex():
    """Reindeksoi tiedostot ja palauta tulokset"""
    try:
        # Lähetä aloitusviesti WebSocketin kautta
        socketio.emit(
            "reindex_progress", {"value": 0.0, "message": "Aloitetaan reindeksointi..."}
        )

        # Suorita reindeksointi ilman progress_callback-parametria
        result = rag_tool.check_and_reindex_files()

        # Lähetä valmistumisviesti
        socketio.emit(
            "reindex_progress", {"value": 1.0, "message": "Reindeksointi valmis"}
        )

        # Päivitä tiedostolista reindeksoinnin jälkeen
        indexed_files = rag_tool.document_store.get_all_documents().keys()

        return jsonify(
            {
                "status": result["status"],
                "message": result["message"],
                "indexed_files": list(indexed_files),
            }
        )

    except Exception as e:
        logger.error(f"Reindex error: {str(e)}")
        # Lähetä virheviesti WebSocketin kautta
        socketio.emit("reindex_progress", {"value": 0.0, "message": f"Virhe: {str(e)}"})
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/rag/info", methods=["GET"])
def get_rag_info():
    """Get RAG system information"""
    try:
        files = rag_tool.list_saved_files()
        if not files:
            return jsonify(
                {
                    "status": "no_files",
                    "message": (
                        "Ei indeksoituja dokumentteja. Lisää dokumentteja:\n"
                        "1. Raahaa ja pudota tiedosto tähän ikkunaan, TAI\n"
                        "2. Aseta tiedostot hakemistoon 'storage/memory/saved_files' ja "
                        "paina 'Reindex All Files' -nappia."
                    ),
                    "files": [],
                    "action_needed": "upload_files",
                }
            )

        return jsonify(
            {
                "status": "success",
                "message": f"Löytyi {len(files)} indeksoitua dokumenttia",
                "files": files,
            }
        )

    except Exception as e:
        logger.error(f"Error getting RAG info: {str(e)}")
        return jsonify(
            {
                "status": "error",
                "message": (
                    "Virhe indeksitietojen haussa. "
                    "Jos ongelma jatkuu, kokeile indeksoida tiedostot uudelleen 'Reindex All Files' -napilla."
                ),
                "error": str(e),
            }
        ), 500


@app.route("/api/rag/cancel", methods=["POST"])
def cancel_indexing():
    """Keskeytä käynnissä oleva indeksointi"""
    try:
        rag_tool.cancel_indexing()
        return jsonify(
            {"status": "success", "message": "Indeksoinnin keskeytys aloitettu"}
        )
    except Exception as e:
        return jsonify(
            {"status": "error", "message": f"Virhe keskeytyksen aloituksessa: {str(e)}"}
        )


# Tool endpoints
@app.route("/api/tools/<tool_name>", methods=["GET"])
def get_tool_info(tool_name):
    """Get tool info and status"""
    try:
        logger.info(f"Tool request received: {tool_name}")

        if tool_name == "data":
            # Get indexed files
            logger.info("Getting indexed files...")
            files = rag_tool.list_saved_files()  # Käytetään list_saved_files-metodia
            logger.info(f"Found {len(files)} files")

            if not files:
                return jsonify(
                    {
                        "status": "no_files",
                        "message": "No indexed files found. Add files using the Data tool.",
                        "files": [],
                    }
                )

            return jsonify(
                {
                    "status": "ok",
                    "files": [{"filename": f, "is_indexed": True} for f in files],
                }
            )

        elif tool_name == "model":
            # Show model selection
            return jsonify(
                {
                    "status": "ok",
                    "models": [
                        {
                            "name": "GPT-4o",
                            "description": "Most capable model, best for complex tasks and reasoning",
                        },
                        {
                            "name": "GPT-4o Mini",
                            "description": "Balanced performance and speed, good for most tasks",
                            "selected": True,
                        },
                        {
                            "name": "O1 Mini",
                            "description": "Fastest model, best for simple tasks and quick responses",
                        },
                    ],
                }
            )

        elif tool_name == "tokens":
            # Show token usage
            return jsonify(
                {
                    "status": "ok",
                    "usage": {"total": 1234, "last_24h": 567, "cost": "0.123€"},
                }
            )

        elif tool_name == "prompts":
            # Show prompt settings
            return jsonify(
                {
                    "status": "ok",
                    "system_prompt": "You are a helpful AI assistant...",
                    "response_length": 50,
                    "temperature": 0.7,
                }
            )

        else:
            logger.warning(f"Unknown tool requested: {tool_name}")
            return jsonify({"error": "Unknown tool"}), 404

    except Exception as e:
        logger.error(f"Error in tool endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    socketio.run(app, debug=True, port=5001)
