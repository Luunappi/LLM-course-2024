from flask import request, jsonify
from flask_app import app, socketio
from flask_app.models.rag_tool import RAGTool
import os


def emit_progress(value: float, message: str):
    """Emit progress update through socket.io"""
    socketio.emit("upload_progress", {"value": value, "message": message})


@app.route("/api/rag/files", methods=["GET"])
def get_indexed_files():
    """Get list of indexed files with metadata"""
    try:
        rag_tool = RAGTool()
        result = rag_tool.list_saved_files()
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/rag/reindex", methods=["POST"])
def reindex_file():
    """Reindex a specific file"""
    try:
        data = request.get_json()
        filename = data.get("filename")
        if not filename:
            return jsonify({"status": "error", "message": "Filename not provided"})

        rag_tool = RAGTool()
        file_content = rag_tool.load_saved_file(filename)
        if not file_content:
            return jsonify({"status": "error", "message": "File not found"})

        # Process the file again
        result = rag_tool.process_file(
            file_content, filename, progress_callback=emit_progress
        )
        return jsonify(
            {"status": "success", "message": f"Successfully reindexed {filename}"}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/rag/delete", methods=["POST"])
def delete_file():
    """Delete a file from the index"""
    try:
        data = request.get_json()
        filename = data.get("filename")
        if not filename:
            return jsonify({"status": "error", "message": "Filename not provided"})

        rag_tool = RAGTool()
        # Delete from saved_files directory
        saved_file_path = os.path.join("saved_files", filename)
        if os.path.exists(saved_file_path):
            os.remove(saved_file_path)

        # Reset the index to remove the file's data
        rag_tool.backend.reset_index()

        # Reindex remaining files
        rag_tool.check_and_reindex_files(progress_callback=emit_progress)

        return jsonify(
            {"status": "success", "message": f"Successfully deleted {filename}"}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
