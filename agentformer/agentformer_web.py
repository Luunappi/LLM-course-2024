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
from tools.system_tool import SystemTool
from tools.model_tool import ModelTool
import time

# Konfiguroi logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("Initializing Flask app...")  # Debug tulostus

app = Flask(
    __name__,
    static_folder="static",  # Varmista että tämä on oikein
    template_folder="templates",
)
orchestrator = AgentFormerOrchestrator()

# Sessioasetukset
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Alustetaan työkalut
token_tool = TokenTool()
system_tool = SystemTool()
model_tool = ModelTool()

print("All components initialized")  # Debug tulostus


@app.route("/")
def index():
    """Render main page"""
    return render_template("chat.html")


@app.route("/api/models", methods=["GET"])
def get_models():
    """Get available models"""
    try:
        models = model_tool.get_available_models()
        current = model_tool.get_current_model()
        return jsonify({"models": models, "current": current})
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/models/current", methods=["GET"])
def get_current_model():
    """Get current model"""
    try:
        current = model_tool.get_current_model()
        return jsonify(current)
    except Exception as e:
        logger.error(f"Error getting current model: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/models/select", methods=["POST"])
def select_model():
    """Select model"""
    try:
        data = request.get_json()
        model_name = data.get("model")
        if not model_name:
            return jsonify({"error": "Model name required"}), 400

        success = model_tool.set_model(model_name)
        if success:
            return jsonify(
                {"status": "success", "model": model_tool.get_current_model()}
            )
        else:
            return jsonify({"error": "Invalid model name"}), 400
    except Exception as e:
        logger.error(f"Error selecting model: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        message = data.get("message")
        if not message:
            return jsonify({"error": "Message required"}), 400

        logger.debug(f"[WEB] Received chat message: {message}")
        response = orchestrator.process_message(message)
        logger.debug(f"[WEB] Final response to client: {response}")

        # Tallenna viesti ja vastaus sessioon token-laskentaa varten
        session["current_message"] = {
            "input": message,
            "output": response,
            "model": model_tool.get_current_model()["name"],
        }

        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"[WEB] Error in chat endpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/tokens/stats", methods=["GET"])
def get_token_stats():
    """Get token usage statistics"""
    try:
        current_model = model_tool.get_current_model()
        current_message = session.get("current_message", {})

        # Hae token-tilastot
        current_stats = token_tool.get_message_stats(
            current_message.get("input", ""),
            current_message.get("output", ""),
            current_model["name"],
        )

        # Hae kokonaistilastot
        total_stats = token_tool.get_usage_stats()

        return jsonify({"current": current_stats, "total": total_stats})
    except Exception as e:
        logger.error(f"Error getting token stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/message/<int:message_id>", methods=["DELETE"])
def delete_chat_message(message_id):
    """Delete specific chat message"""
    try:
        success = orchestrator.chat_tool.delete_message(message_id)
        if success:
            return jsonify({"status": "success"})
        return jsonify({"error": "Message not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/history", methods=["DELETE"])
def clear_chat_history():
    """Clear all chat history"""
    try:
        success = orchestrator.chat_tool.clear_history()
        if success:
            return jsonify({"status": "success"})
        return jsonify({"error": "Failed to clear history"}), 500
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/prompts", methods=["GET"])
def get_prompts():
    """Get all available prompts"""
    try:
        prompts = orchestrator.prompt_tool.list_prompts()
        return jsonify({"prompts": prompts})
    except Exception as e:
        logger.error(f"Error getting prompts: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/prompts/set", methods=["POST"])
def set_prompt():
    """Set active prompt"""
    try:
        data = request.get_json()
        success = orchestrator.prompt_tool.set_prompt(data["type"], data["name"])
        return jsonify({"status": "success" if success else "error"})
    except Exception as e:
        logger.error(f"Error setting prompt: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/prompts/reset", methods=["POST"])
def reset_prompt():
    """Reset prompt to default value"""
    try:
        data = request.get_json()
        success = orchestrator.prompt_tool.reset_to_default(data["type"], data["name"])
        if success:
            prompt = orchestrator.prompt_tool.get_prompt(data["type"])
            return jsonify({"status": "success", "prompt": prompt})
        return jsonify({"error": "Failed to reset prompt"}), 400
    except Exception as e:
        logger.error(f"Error resetting prompt: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/settings/word_limit", methods=["POST"])
def set_word_limit():
    """Set max words for responses"""
    try:
        data = request.get_json()
        orchestrator.set_word_limit(data["limit"])
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error setting word limit: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/system/stats", methods=["GET"])
def get_system_stats():
    """Get system performance statistics"""
    try:
        stats = orchestrator.system_tool.get_timing_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/debug/info", methods=["GET"])
def get_debug_info():
    """Get debug information"""
    try:
        debug_info = orchestrator.debug_tool.get_debug_info()
        return jsonify(debug_info)
    except Exception as e:
        logger.error(f"Error getting debug info: {e}")
        return jsonify({"error": str(e)}), 500


# ... muu koodi ...

if __name__ == "__main__":
    print("Starting Flask server...")  # Debug tulostus
    app.run(debug=True, port=5001, host="0.0.0.0")
    print("Server started")  # Debug tulostus
