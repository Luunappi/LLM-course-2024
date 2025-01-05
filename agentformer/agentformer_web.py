"""
AgentFormer Web Application
Flask-pohjainen web-käyttöliittymä
"""

from flask import Flask, request, jsonify, render_template
from core.orchestrator import AgentFormerOrchestrator
import logging
import os

app = Flask(__name__, static_folder="static", template_folder="templates")
orchestrator = AgentFormerOrchestrator()
logger = logging.getLogger(__name__)


@app.route("/")
def index():
    """Render main page"""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages"""
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid JSON"}), 400

        message = request.json.get("message", "")
        if not message:
            return jsonify({"error": "Empty message"}), 400

        # Käsittele viesti orkestraattorin kautta
        response = orchestrator.process_request("chat", {"message": message})

        # Lisää token usage tiedot vastaukseen
        token_usage = {
            "input_tokens": response.get("input_tokens", 0),
            "output_tokens": response.get("output_tokens", 0),
            "total_tokens": response.get("total_tokens", 0),
            "cost": calculate_cost(response.get("total_tokens", 0)),
        }

        return jsonify(
            {
                "response": response.get("response", ""),
                "token_usage": token_usage,
                "state": orchestrator.get_current_state(),
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
    """Handle file upload"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

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
    """Calculate cost based on token usage"""
    # Esimerkki hinnoittelu: $0.002 per 1K tokenia
    return (total_tokens / 1000) * 0.002


@app.route("/switch_model", methods=["POST"])
def switch_model():
    """Switch between models"""
    try:
        model = request.json.get("model")
        if not model:
            return jsonify({"error": "No model specified"}), 400

        success = orchestrator.set_model(model)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Model switch error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
