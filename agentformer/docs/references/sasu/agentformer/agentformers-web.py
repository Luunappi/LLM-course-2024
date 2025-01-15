# Python Flask with HTML-based UI
from flask import Flask, render_template, request, jsonify, session
from dynamicDistLLMMemory import DynamicDistLLMMemory
import json
import logging
import uuid

instruction_text = [
# INIT STAGE
 {"command": "LOAD", "file":"selector-rag.json"}, # media-html.json"}, #"flamma-rag2.json"},
 # {"command": "AGENTRUN", "scope":"Response {alternative_strategies} {release_decision}","file":"hr-assistant.json", "exit":"media_release_final alternative_final","anchor":"agentresponse","prompt":"I need HR help for professor recruitment. The professor position is for computer science at the Faculty of Science. The end result is an ad for the position. Inspect the ad and if it looks good, approve the draft."}, # media-html.json"}, #"flamma-rag2.json"},
#  {"command": "TEXT", "text":"AgentFormers app helps you to create new apps."},
#  {"command": "INPUT", "text":"Background data", "event": "event_data", "anchor": "app-data", "replace":True},
#  {"command": "INPUT", "text":"What app do you want to create?", "event": "event", "anchor": "app-description", "replace":True},
#  {"command": "LLM-TRIGGER", "event": "event",  "prompt" :"Generate application based on the following specification. {Init} {UI-text} Application description: {app-description} Application data: {app-data}", "anchor": "revised-app-description", "scope":"Init UI-text app-description app-data pattern-lib", "model":"ollama/llama3.3"}
]
contents_text = {}

app = Flask(__name__)
# Required for using sessions
app.secret_key = "98fdc4394eaf1b57e1e335f14eee7db34d0b4f7262ef7efa"
app.config["SESSION_TYPE"] = "filesystem"

# In-memory store for user-based Memory objects
# { user_id: DynamicDistLLMMemory(...) }
user_memories = {}


def get_user_memory():
    """
    Retrieve or create a user-specific Memory object.
    Identifies each user by a 'user_id' in the Flask session.
    """
    user_id = session.get("user_id")
    if not user_id:
        # If no user_id in session, generate one
        user_id = str(uuid.uuid4())
        session["user_id"] = user_id

    # If this user_id has no memory object yet, create one
    if user_id not in user_memories:
        # You can load initial instructions & contents from files, config, etc.
        # For example, placeholders:
        instructions = instruction_text # Load or define instructions
        contents = {}     # Load or define any relevant data

        mem = DynamicDistLLMMemory(instructions, contents_text)
        
        # Mimic your original "setup state" logic
        # (i.e., run instructions for the current state if they are not BUTTON)
        insta = mem.get_instructions_current_state()
        for inst in insta:
            if "BUTTON" not in inst['command']:
                mem.execute_command(inst)

        user_memories[user_id] = mem

    return user_memories[user_id]


def update_state(memory):
    # The instructions may change when state changes mid-processing
    state_instructions = memory.get_instructions_current_state()

    # Process instructions for the current state
    current_state = memory.get_global_state()
    for inst in state_instructions:
        # need to execute the command to ensure state
        if "BUTTON" not in inst['command']:
            memory.execute_command(inst)

        # Check if global state changed
        test_state = memory.get_global_state()
        print("State testing")
        if test_state != current_state:
            print("State change")
            state_instructions.extend(memory.get_instructions_current_state())
            current_state = test_state

    return state_instructions


@app.route("/")
def index():
    """
    Render the main index page. 
    - We first update the state (to ensure any transitions or commands are processed).
    - Then we fetch the UI instructions for the current user state.
    """
    mem = get_user_memory()
    state_instructions = update_state(mem)
    instructions = mem.get_instructions_UI_current_state()
    print(f"UI: returning: {instructions}")
    return render_template("index.html", instructions=instructions)


@app.route("/submit", methods=["POST"])
def submit():
    """
    Handle an event-like submission from the frontend. 
    - The payload includes {"name": <event_name>, "value": <event_data>}.
    - We call memory.react_to_event, then update the state and return UI instructions + results.
    """
    mem = get_user_memory()
    data = request.json or {}

    event_name = data.get("name")
    event_value = data.get("value")
    print(f"/submit called. Event={event_name}, Value={event_value}")

    # React to the event
    mem.react_to_event(event_name, event_value)

    # Update state
    update_state(mem)

    # Return the UI instructions and any result contents
    results = mem.get_contents_UI_json()
    instructions = mem.get_instructions_UI_current_state()
    print(f"UI: returning: {instructions}")
    return jsonify({"instructions": instructions, "results": results})


@app.route("/command", methods=["POST"])
def command():
    """
    Directly execute a command from the UI.
    If an 'id' is provided, we execute that specific instruction in the current state.
    Otherwise, we just update state & fetch instructions.
    """
    mem = get_user_memory()
    data = request.json or {}

    cmd = data.get("command")
    if not cmd:
        return jsonify({"error": "No command specified"}), 400

    if 'id' in data:
        inst_id = data["id"]
        print(f"Received command='{cmd}', ID={inst_id}, Data={data}")
        inst = mem.get_instructions_UI_byID_current_state(inst_id)
        if inst:
            mem.execute_command(inst)
        else:
            print(f"No matching instruction found for ID={inst_id} in current user state.")
        instructions = update_state(mem)
    else:
        print(f"Received command='{cmd}', no ID, Data={data}")
        update_state(mem)
        instructions = mem.get_instructions_UI_current_state()

    results = mem.get_contents_UI_json()
    print(f"UI: returning: {instructions}")
    return jsonify({"instructions": instructions, "results": results})


if __name__ == "__main__":
    app.run(debug=True)

