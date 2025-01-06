"""
AgentFormer Web Application
Flask-pohjainen web-käyttöliittymä
"""

from flask import Flask, request, jsonify, render_template, session
from core.orchestrator import AgentFormerOrchestrator
from flask_session import Session
import logging
import os
import re
from tools.token_tool import TokenTool

app = Flask(__name__, static_folder="static", template_folder="templates")
orchestrator = AgentFormerOrchestrator()
logger = logging.getLogger(__name__)

# Sessioasetukset
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Alustetaan token-työkalu
token_tool = TokenTool()


# Remove the global session check and move it to a before_request handler
@app.before_request
def initialize_session():
    if "global_usage" not in session:
        session["global_usage"] = {
            "models": {},  # Mallikohtainen token-laskuri
            "total_tokens": 0,  # Kaikki tokenit yhteensä
            "total_cost": 0.0,  # Kumulatiiviset kustannukset
        }


@app.route("/")
def index():
    """Render main page"""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Handle chat messages
    Käytetään RAG:ia, jos käyttäjä on ladannut tiedoston (rag_mode).
    Tallennetaan myös kumulatiivista token-käyttöä session kautta.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid JSON"}), 400

        message = request.json.get("message", "")
        if not message:
            return jsonify({"error": "Empty message"}), 400

        # Tarkista, onko RAG-tila päällä
        use_rag = session.get("rag_mode", False)

        # Parametrit orkestraattorikutsuun
        mode = "rag" if use_rag else "chat"
        # Pyydetään lopulliselta modelta vastaus, max_word_limit huomioituna
        response_data = orchestrator.process_request(
            mode,
            {
                "message": message,
                "respect_word_limit": True,  # ohjevipu orkestraattorille
            },
        )

        # Jäsennellään orkestraattorin palauttama data
        answer = response_data.get("response", "")
        usage_info = response_data.get("usage", {})
        found_in_docs = response_data.get("found_in_docs", True)
        used_models = response_data.get(
            "models_used", []
        )  # lista eri vaiheissa käytetyistä malli-aloituksista

        # -------- Esimerkki: Päivitä session globaalia usagea ------------
        for model_usage in usage_info.get("model_usage_list", []):
            model_name = model_usage["model_name"]
            tokens_used = model_usage["total_tokens"]
            cost = model_usage["cost"]

            if "global_usage" not in session:
                session["global_usage"] = {
                    "models": {},
                    "total_tokens": 0,
                    "total_cost": 0.0,
                }

            session["global_usage"]["models"].setdefault(
                model_name, {"tokens": 0, "cost": 0.0}
            )
            session["global_usage"]["models"][model_name]["tokens"] += tokens_used
            session["global_usage"]["models"][model_name]["cost"] += cost
            session["global_usage"]["total_tokens"] += tokens_used
            session["global_usage"]["total_cost"] += cost

        session.modified = True

        # Jos RAG-käyttö päällä eikä aineistosta löytynyt vastausta:
        # Palautamme fallback-vastauksen + huomautuksen.
        if use_rag and not found_in_docs:
            # Kohtelias maininta, ettei aineistosta löytynyt + kielimallin fallback
            rag_msg = (
                "Emme löytäneet vastausta ladatusta aineistosta. "
                "Alla on lyhyt vastaus kielimallin omasta tietopohjasta:\n\n"
                f"{answer}\n\n"
                "_(Tämä vastaus annettiin kielimallin oman tiedon pohjalta, ei ladatusta artikkelista.)_"
            )
            answer = rag_msg
        elif use_rag:
            # Jos vastaus löytyi, lisätään maininta RAG-käytöstä himmeällä lopussa
            answer += "\n\n<span style='opacity:0.6;font-size:small;'>RAG-systeemiä käytettiin vastauksen löytämiseen ladatusta aineistosta.</span>"

        # Palautetaan data front-endille
        token_usage_for_this_answer = {
            "input_tokens": usage_info.get("input_tokens", 0),
            "output_tokens": usage_info.get("output_tokens", 0),
            "total_tokens": usage_info.get("total_tokens", 0),
            "cost": usage_info.get("cost", 0.0),
        }

        return jsonify(
            {
                "response": format_response(answer),
                "token_usage": token_usage_for_this_answer,
                "session_usage": {
                    "total_tokens": session["global_usage"]["total_tokens"],
                    "total_cost": session["global_usage"]["total_cost"],
                    "models": session["global_usage"]["models"],
                },
                "models_used": used_models,
            }
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/state")
def get_state():
    """Get current system state"""
    return jsonify(orchestrator.get_current_state())


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Handle file upload
    Oletuksena mennään RAG-polkuun, jos tiedosto on ladattu.
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Aseta RAG-tila sessioon
        session["rag_mode"] = True

        # Process file using RAG components
        result = orchestrator.process_document(file)

        return jsonify(
            {"success": True, "message": f"File {file.filename} processed successfully"}
        )

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/prompts")
def get_prompts():
    """Get system and tool selection prompts"""
    return jsonify(
        {
            "system_prompt": orchestrator.get_system_prompt(),
            "tool_selection_prompt": orchestrator.get_tool_selection_prompt(),
        }
    )


@app.route("/update_model", methods=["POST"])
def update_model():
    """Update current model"""
    model = request.json.get("model")
    success = orchestrator.set_model(model)
    return jsonify({"success": success})


@app.route("/update_word_limit", methods=["POST"])
def update_word_limit():
    """Update word limit"""
    limit = request.json.get("limit")
    orchestrator.set_word_limit(int(limit))
    return jsonify({"success": True})


def calculate_cost(total_tokens):
    """Calculate cost based on token usage. Esimerkki, muokkaa haluamallasi hinnoittelulla."""
    # Voidaan myös siirtää orkestraattorin sisään. Tässä yksinkertainen placeholder-hinnoittelu:
    return (total_tokens / 1000) * 0.002


@app.route("/switch_model", methods=["POST"])
def switch_model():
    """Switch between models"""
    try:
        model = request.json.get("model")
        if not model:
            return jsonify({"error": "No model specified"}), 400

        success = orchestrator.set_model(model)
        if success:
            # Hae päivitetyn mallin tiedot
            current_model = orchestrator.model_tool.get_current_model()
            # Päivitä token-työkalun hinnoittelu
            model_config = orchestrator.model_tool.get_model_config(model)
            token_tool.update_pricing(model_config["cost_per_1k"])

            return jsonify(
                {
                    "success": True,
                    "model": current_model,  # Palauta mallin tiedot
                }
            )
        return jsonify({"error": "Invalid model"}), 400
    except Exception as e:
        logger.error(f"Model switch error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/update_prompt", methods=["POST"])
def update_prompt():
    """
    Päivitä system- tai tool-prompt
    Vastaanotetaan front-endiltä promptin tyyppi sekä sisältö
    """
    try:
        data = request.json
        prompt_type = data.get("type")  # esim. 'system-prompt' tai 'tool-prompt'
        prompt_content = data.get("content", "")

        # Asetetaan orkestraattorin system- tai tool-prompt
        if prompt_type == "system-prompt":
            orchestrator.set_system_prompt(prompt_content)
        elif prompt_type == "tool-prompt":
            orchestrator.set_tool_selection_prompt(prompt_content)

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"update_prompt error: {e}")
        return jsonify({"error": str(e)}), 500


def format_response(text):
    """Format response text with proper markdown and numbering"""
    lines = text.split("\n")
    formatted_lines = []
    in_list = False

    for line in lines:
        # Lisää lihavointi numeroituihin kohtiin
        is_list_item = bool(re.match(r"^\d+\.", line))
        if is_list_item:
            # Korvaa "1. Teksti:" muotoon "1. **Teksti**:"
            line = re.sub(r"^(\d+)\.\s*([^:]+):", r"\1. **\2**:", line)
            if not in_list:
                formatted_lines.append("")
                in_list = True
        else:
            if in_list:
                formatted_lines.append("")
                in_list = False
        formatted_lines.append(line)

    # Poista turhat tyhjät rivit
    while "" in formatted_lines:
        if formatted_lines[0] == "":
            formatted_lines.pop(0)
        elif formatted_lines[-1] == "":
            formatted_lines.pop()
        else:
            break

    return "\n".join(formatted_lines)


@app.route("/token_info", methods=["GET"])
def get_token_info():
    """Get current token usage information"""
    try:
        return jsonify(token_tool.get_usage_stats())
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/calculate_tokens", methods=["POST"])
def calculate_tokens():
    """Calculate tokens for given text"""
    try:
        text = request.json.get("text", "")
        model = request.json.get("model", "default")

        if not text:
            return jsonify({"error": "No text provided"}), 400

        token_info = token_tool.calculate_tokens(text, model)
        token_tool.update_usage(token_info)

        return jsonify({"token_usage": token_info})
    except Exception as e:
        logger.error(f"Token calculation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/models/current", methods=["GET"])
def get_current_model():
    """Get current model information"""
    try:
        current_model = orchestrator.model_tool.get_current_model()
        logger.debug(f"Current model data: {current_model}")  # Debug-loggaus
        if not isinstance(current_model, dict) or "button_name" not in current_model:
            raise ValueError("Invalid model data structure")
        return jsonify(current_model)
    except Exception as e:
        logger.error(f"Error getting current model: {e}")
        # Palauta oletusarvo virhetilanteessa
        return jsonify(
            {
                "name": "gpt-4o-mini",
                "button_name": "gpt-4o-mini",
                "display_name": "gpt-4o-mini (1x€)",
            }
        )


@app.route("/models/available", methods=["GET"])
def get_available_models():
    """Get list of available models"""
    try:
        models = orchestrator.model_tool.get_available_models()
        return jsonify(models)
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
