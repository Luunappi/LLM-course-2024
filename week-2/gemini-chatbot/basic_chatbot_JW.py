from fastapi import FastAPI, Form, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from model_utils import get_model
import json
import subprocess
import time
import atexit
import requests
import sys

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent


class OllamaService:
    def __init__(self):
        self.process = None
        atexit.register(self.stop)

    def start(self):
        """Start Ollama service if not running"""
        try:
            # Check if Ollama is already running
            response = requests.get("http://localhost:11434/api/tags", timeout=1)
            if response.status_code == 200:
                print("Ollama is already running")
                return True
        except:
            print("Starting Ollama service...")
            try:
                # Start Ollama
                self.process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,  # Run in new session
                )

                # Wait for Ollama to start
                for _ in range(30):  # 30 second timeout
                    try:
                        response = requests.get(
                            "http://localhost:11434/api/tags", timeout=1
                        )
                        if response.status_code == 200:
                            print("Ollama started successfully")
                            return True
                    except:
                        if self.process.poll() is not None:  # Process died
                            print("Ollama process died")
                            return False
                        time.sleep(1)
                        continue

                print("Failed to start Ollama")
                return False
            except Exception as e:
                print(f"Error starting Ollama: {e}")
                return False

    def stop(self):
        """Stop Ollama service"""
        if self.process:
            print("Stopping Ollama service...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None


# Initialize Ollama service
ollama_service = OllamaService()

# Start Ollama before initializing the model
if not ollama_service.start():
    print("Could not start Ollama. Please start it manually with 'ollama serve'")
    sys.exit(1)

# Initialize model with Mistral
try:
    model = get_model("mistral")
    # Test connection
    test_response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": "test", "stream": False},
        timeout=5,
    )
    if test_response.status_code != 200:
        raise Exception("Failed to connect to Ollama")
except Exception as e:
    print(f"Error initializing model: {e}")
    print("Make sure Mistral model is installed with: ollama pull mistral")
    sys.exit(1)

# Create FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# Chat message class
class ChatMessage:
    def __init__(self, msg, is_user=True, metrics=None):
        self.msg = msg
        self.is_user = is_user
        self.metrics = metrics
        self.bubble_class = (
            "chat-bubble-primary" if is_user else "chat-bubble-secondary"
        )
        self.chat_class = "chat-end" if is_user else "chat-start"
        self.model_name = metrics.get("model_name") if metrics else None


@app.get("/", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "messages": [], "partial": False},
    )


@app.post("/send")
async def send(request: Request, msg: str = Form(...)):
    try:
        print(f"Received message: {msg}")

        # Get response from model with metrics
        response, metrics = model.generate_content([msg])
        print(f"Model response: {response}")
        print(f"Metrics: {json.dumps(metrics, indent=2)}")

        # Varmista että vastaus ja metriikat ovat oikeassa muodossa
        if not response or not metrics:
            raise ValueError("Empty response from model")

        # Return JSON response with proper structure
        return JSONResponse(
            {
                "response": str(response),  # Varmista että vastaus on string
                "metrics": {
                    "model_name": metrics.get("model_name", "mistral"),
                    "duration": float(metrics.get("duration", 0)),
                    "prompt_tokens": int(metrics.get("prompt_tokens", 0)),
                    "completion_tokens": int(metrics.get("completion_tokens", 0)),
                    "total_tokens": int(metrics.get("total_tokens", 0)),
                    "cost": float(metrics.get("cost", 0)),
                },
            }
        )
    except Exception as e:
        error_msg = str(e)
        print(f"Error in /send: {error_msg}")
        # Return error in a format that frontend expects
        return JSONResponse(
            {"error": f"Failed to get response: {error_msg}"}, status_code=500
        )


@app.post("/set-language")
async def set_language(language: str = Body(..., embed=True)):
    try:
        model.set_language(language)
        return JSONResponse({"status": "success"})
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the server on"
    )
    args = parser.parse_args()

    print(f"Templates directory: {BASE_DIR / 'templates'}")
    print(f"Starting server on port {args.port}")

    try:
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    finally:
        ollama_service.stop()  # Ensure Ollama is stopped when app exits
