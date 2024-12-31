from fastapi import FastAPI, Form, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys
import os
import json

# Debug: tulostetaan mistä moduulit löytyvät
import model_utils

print(f"Using model_utils from: {model_utils.__file__}")
print(f"Current prompt: {model_utils.GeminiModel().system_prompts['en']}")

from model_utils import get_model

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

# Initialize model
try:
    model = get_model("gemini")
    # Debug: tulostetaan käytettävä prompt
    print(f"Using prompt: {model.system_prompts['en'][:100]}...")
except Exception as e:
    print(f"Error initializing model: {e}")
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
    prompt = model.system_prompts["en"]
    print(f"Sending prompt to template: {prompt[:100]}...")  # Debug print
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "messages": [],
            "partial": False,
            "system_prompt": prompt,
        },
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

    uvicorn.run(app, host="0.0.0.0", port=args.port)
