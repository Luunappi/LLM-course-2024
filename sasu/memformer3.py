# LLM Memory (DDMMem) part of the MemoryFormer architecture
# Note this is experimental POC code
# Sasu Tarkoma, 2024


# The MemoryFormer generates LLM memories given the input specifications.
# The idea is that it calibrates the generation process and outputs also auditing results,
# and optimized plan how to distribute the memory usage. 
#
# The LLM use within the memory could generate also executable code. This would require
# additional security measures.
# 
# The memory can include a generated description of the memory that can be given to 
# an LLM for using the memory in the best way. This is only possible in the MemoryFormer
# generation process at the moment. 

import json
import re
from dynamicDistLLMMemory import DynamicDistLLMMemory
from datetime import datetime, timedelta
import random
import time
import numpy as np


instruction_text = [
  {"command": "LLM-QUERY", "prompt": "", "anchor": "Tasklist", "scope": "Input Init XAPPEvents JSON-Example Example-events", "model":"ollama/llama3.1:70b"},
  {"command": "LLM-QUERY", "prompt": "", "anchor": "Code", "scope": "Tasks Models Tasklist Input", "model":"ollama/llama3.1:70b"},
#  {"command": "LLM-QUERY", "prompt": "", "anchor": "Code2", "scope": "Code-opt Code Python Example-events", "model":"ollama/llama3.1:70b"},
#  {"command": "LLM-QUERY", "prompt": "", "anchor": "Code2", "scope": "Code-opt-final InterimCode Python", "model":"ollama/llama3.1:70b"},
#  {"command": "LLM-QUERY", "prompt": "", "anchor": "Memory-structure", "scope": "Memory-prompt Code2", "model":"ollama/llama3:70b-instruct"},
#  {"command": "LLM-QUERY", "prompt": "", "anchor": "Test", "scope": "Test Code2", "model":"ollama/llama3:70b-instruct"},
]

# note should change query = event and use prompt not to confuse LLMs

contents_text = {
    "AppEvents":"Include only xApp events that are necessary for the tasks. The xApp events are: new_connection_request, incoming_connection_attempt, client_connection_request, connection_termination, client_disconnected, session_end, data_transfer_start, data_transfer_end, data_transfer_metrics, error_occurred, connection_failure, transmission_error, protocol_violation, authentication_successful, authentication_failed, configuration_change, policy_update, device_setting_change, performance_latency, performance_throughput, performance_packet_loss, alert_notification, security_alert, threshold_breach, system_notification, resource_allocation, resource_deallocation, qos_priority_change, qos_traffic_shaping, firmware_update, software_update, user_activity_log, unauthorized_access_attempt, ddos_attack, malware_detection, topology_change, device_addition, device_removal, bandwidth_usage_report, device_health_status, cpu_usage_report, memory_usage_report, operational_status_update",
    "Init": (
        "Generate application memory tasks given the following specification in simple command format for further "
        "processing. The memory has instructions and content. The tasks use commands that operate on named content items. "
         "The prompts will have access to the identified data items (called scopes). These are appended to the prompt as context."
        "The JSON structure is a list of commands that have parameters."
        "You can use intermediate content anchors to store and analyze data. For example selecting a subset of events. Do not mix content objects in JSON anchors. This will help in partitioning of the application."
        "You can also use trigger conditions for triggering further actions, such as complex LLM processing. This will help in later optimization."
        "USE ONLY THESE COMMANDS AND PARAMETERS and OUTPUT JSON. Use step by step reasoning."
        "Important: SUBSCRIBE all events you use in the commands."
        "The command parameters are:"
        "event is a label for event type (not a list), "
        "prompt is a prompt string, "
        "anchor is a string, always the content destination,"
        "scope is a string of one or more content items for the given command separated by whitespaces," 
        "model is the LLM model name to be used. Only use the provided LLM model or omit this. "
        "The commands with their allowed parameters are: "
        "SUBSCRIBE event, anchor;"
        "UNSUBSCRIBE event;"
        "LLM-QUERY (only used in init stage) prompt, anchor, scope, model, datalimit;"
        "LLM-TRIGGER event, prompt, anchor, scope, model, datalimit;"
        "LLM-CONTENT-TRIGGER prompt, anchor, scope (content changed), model, datalimit;"
#        "COMPRESS anchor, prompt, datalimit;"
#        "FETCH url, anchor."
       "Notes: scope can be used to include prompt content to LLM commands."
       "Scopes are useful in reading information, but they are also costly and change in any of the scopes will trigger an update."
       "Anchor write will replace the content. Do not implement multiple writes to the same anchor without updating the whole anchor."
    ),
# ---------------
    "Test" : "Output test events for the given reactive JSON program. The events are used to test the program.",
    "Tasks": """
    Given the input JSON task descriptions with operations examine the prompts for clarity and correctness. 
    The prompts are provided within the JSON commands. Expand prompts  to make them more instructive and accurate for the requested functionality.
    The prompts will have access to the identified data items (called scopes). These are appended to the prompt as context.
    Provide sufficient instruction for the LLM to process the command and write the content without additional remarks or thoughts.
    The LLM should behave like an information processor implementing the planned specification.
    Output only continuous JSON and ONLY MODIFY PROMPTS. DO NOT OUTPUT THOUGHTS."
    Start output from '[', output JSON list of dictionaries: example [{},{}]
    """,
# ---------------
    "JSON-Example":"""Here is an example:
    instruction_text_ = [
    {"command": "SUBSCRIBE", "event": "AA", "anchor": "AAA"},
    {"command": "SUBSCRIBE", "event": "BB", "anchor": "BBB"},
    {"command": "LLM-TRIGGER", "event": "AA", "prompt" :"Re-evaluate the latency values and write update latency part for the analysis.", "anchor": "AAAA", "scope":"AAA"},
    {"command": "LLM-TRIGGER", "event": "BB", "prompt" :"Re-evaluate the packet loss values and write update to this part of the analysis.", "anchor": "BBBB", "scope":"BBB"},
    {"command": "LLM-CONTENT-TRIGGER", "prompt" :"Re-evaluate the overall network slice status and write detailed analysis.", "anchor": "CCCC", "scope":"AAAA BBBB"},
  ]""",    

# ---------------

    "Code-opt-final":"Consider the CODE elements of the JSON and carefully ensure that the code is executable."
    "Do not modify anything except the Python code. Do not modify JSON encoding. The input parameters are given in a list of dictionaries in the order of the scope entries. Scope field identifies the parameters."
    "Output only continuous JSON and pay particular attention to multiline strings."
    "Ensure that the final output can be parsed as JSON and the Python code in JSON is correctly formatted.",

# ---------------
    "Code-opt":"Consider each LLM invocation prompt provided after these instructions (LLM-QUERY, LLM-TRIGGER, LLM-CONTENT-TRIGGER) and if the prompt is implementable in safe basic Python, implement the LLM operation. "
    "If so, change the command to one of the code commands. Include all commands, do not change other commands than requested."
    "The commands are:"
    "scope denotes the params in all code fields (param1 param2...). Only these are available."
    "CODE code scope anchor, where scope denotes the params (param1 param2...). Not used for reactive events, only used in init. "
    "CODE-TRIGGER event code scope anchor, where event is the trigger."
    "CODE-CONTENT-TRIGGER code scope anchor, where scope denotes the parameters and content triggers"
    "The parameter code denotes executable safe Python code. Output only continuous JSON and pay particular attention to multiline strings. "
    "Strip Leading and Trailing Whitespace: Ensures no extraneous whitespace at the beginning or end of the string."
#    "Remove Leading and Trailing Quotes: Checks if the string starts and ends with double quotes and removes them if present."
    "Replace Multiple Spaces: Replaces sequences of two or more spaces with a single space."
#    "Escape Newline Characters: Ensures that newline (\n), carriage return (\r), and tab (\t) characters are properly escaped."
    "Remove Extraneous Whitespace Around Delimiters: Removes spaces around JSON delimiters like braces ({}), brackets ([]), colons (:), and commas (,)."
    "Remove Control Characters: Removes any remaining control characters that may cause issues."
    "Use regular string delimiters with proper escaping for the code part. Output full code for the functionality."
    "Start output from '['"
    "You have to have the def main_function(param1, param2): in the code, the params are the scopes. The input parameters are given in a list of dictionaries. "
    "Ensure that the anchor writes and reads are aligned in terms of the JSON data structure. If you write a list of dicts to an anchor, you need to then use the same format when reading."
    "Do not use import. ONLY INCLUDE CODE in the 'code' value. Here is an example of Python code:"
"""
[
    {
        "command": "CODE-TRIGGER",
        "event": "data_transfer",
        "code": (
            "def main_function(latest_events):\n"
            "    # Extract the 5 most recent data transfer events, including their timestamps and sizes.\n"
            "    data_transfers = [event for event in latest_events if event['type'] == 'data_transfer']\n"
            "    return {'events': data_transfers[:5]}"
        ),
        "scope": "latest_events",
        "anchor": "processed_events"
    }
]
Use dictionaries to store results.
You must use exactly the same term as parameter in the main_function as specified in the scope.
"""

"""
#"""
#{
#  "instruction_text": [
#    {
#      "command": "CODE",
#      "code": "def main_function(param1, param2):\\n    compiled_pattern = re['compile'](param2)\\n    matches = re['findall'](compiled_pattern, param1)\\n    return {\\n        'matches': matches,\\n        'count': len(matches),\\n        'uppercase': str_methods['upper'](param1)\\n    }",
#      "scope": "param1 param2",
#      "anchor": "result"
#    }
#  ]
#}
#"""
"\nOutput the full JSON app without thoughts and carefully check JSON notation."
"Do not escape. Start output from '['",

# ---------------
    "Memory-prompt:":"Instructions: Output the memory structure of the input code in continuous JSON. The output needs to be in the form of available content items (anchors) and their brief description.",
    "Input": (
        "Objective: Develop a lightweight Network Event Analyzer xApp that subscribes to network quality events, processes these "
        "events, and performs basic analysis to provide insights."
        "The xApp should subscribe to data transfer events. "
        "The xApp will implement analysis functions to "
        "calculate average data transfer sizes and detect data size anomalies. "
        "It will generate a summary report in written format. Operate on the 4 latest events that are extracted from the subscription anchor. Events are in an ordered list. "
    ),
    "Models": "Use LLM model: ollama/llama3.1:70b",
    "Example":"Here is an example.",
    "Python":"""
    # ONLY USE THESE Python features. DO NOT import modules.
    SAFE_BUILTINS = {
    'abs': abs,
    'divmod': divmod,
    'pow': pow,
    'round': round,
    'len': len,
    'str': str,
    'format': format,
    'append_to_list': lambda lst, item: lst.append(item),  # Add append function
    'sum': sum  # Add sum function
}

SAFE_MATH = {
    'pi': math.pi,
    'e': math.e,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'factorial': math.factorial
}

SAFE_STATISTICS = {
    'mean': statistics.mean,
    'median': statistics.median,
    'mode': statistics.mode,
    'stdev': statistics.stdev
}

SAFE_STRING_METHODS = {
    'lower': str.lower,
    'upper': str.upper,
    'capitalize': str.capitalize,
    'title': str.title,
    'split': str.split,
    'join': str.join,
    'replace': str.replace
}

SAFE_RE = {
    'compile': re.compile,
    'match': re.match,
    'search': re.search,
    'findall': re.findall,
    'sub': re.sub,
    'split': re.split
}

SAFE_COLLECTIONS = {
    'defaultdict': defaultdict
}

SAFE_PANDAS = {
    'DataFrame': pd.DataFrame,
    'Series': pd.Series
}

SAFE_GLOBALS = {
    'sorted': sorted,
    '__builtins__': SAFE_BUILTINS,
    'math': SAFE_MATH,
    'statistics': SAFE_STATISTICS,
    'str_methods': SAFE_STRING_METHODS,
    're': SAFE_RE,
    'collections': SAFE_COLLECTIONS,
    'pandas': SAFE_PANDAS
}

Note: print is not available.
""",
    # ---------------

    "Example-events" : """Here are example events.
    [
  {
    "type": "connection",
    "timestamp": "2024-07-29T12:34:56Z",
    "source_ip": "192.168.1.1",
    "destination_ip": "192.168.1.100",
    "protocol": "TCP",
    "port": 8080
  },
  {
    "type": "disconnection",
    "timestamp": "2024-07-29T12:45:00Z",
    "source_ip": "192.168.1.1",
    "destination_ip": "192.168.1.100",
    "protocol": "TCP",
    "port": 8080,
    "duration": 600
  },
  {
    "type": "data_transfer",
    "timestamp": "2024-07-29T13:00:00Z",
    "source_ip": "192.168.1.2",
    "destination_ip": "192.168.1.101",
    "protocol": "UDP",
    "port": 9000,
    "size": 1500
  },
  {
    "type": "error",
    "timestamp": "2024-07-29T13:05:30Z",
    "source_ip": "192.168.1.3",
    "destination_ip": "192.168.1.102",
    "protocol": "TCP",
    "port": 443,
    "error_code": "CONNECTION_TIMEOUT",
    "error_message": "Connection timed out after 30 seconds"
  }
]
"""
}

#   "Input": (
#        "Develop a lightweight Network Event Analyzer XAPP that subscribes to network quality events, processes these "
#        "events, and performs basic analysis to provide insights."
#        "The XAPP should subscribe to events such as connection "
#        "requests, disconnections, data transfers, and error occurrences."
#        "The XAPP will implement analysis functions to "
#        "count event types, calculate average data transfer sizes, identify peak times for connections and disconnections, "
#        "and detect error patterns. It will generate summary reports."


def extract_json_from_llm_output(raw_output):
    """
    Extracts JSON content from LLM output that may include extraneous text,
    handling both JSON objects and arrays, and supporting nested structures accurately.

    Parameters:
    raw_output (str): The raw string containing JSON data with extraneous text.

    Returns:
    dict or list: The extracted JSON content as a Python dictionary or list.
    """
    try:
        # Remove leading and trailing quotes if present
        if raw_output.startswith('"') and raw_output.endswith('"'):
            raw_output = raw_output[1:-1]

      
        # Locate the first opening brace or bracket
        start_object = raw_output.find('{')
        start_array = raw_output.find('[')
        
        if start_object == -1 and start_array == -1:
            raise ValueError("No JSON structure found in the provided string.")
        
        if start_object != -1 and (start_array == -1 or start_object < start_array):
            start = start_object
            opening = '{'
            closing = '}'
        else:
            start = start_array
            opening = '['
            closing = ']'

        # Use a stack to find the matching closing brace or bracket
        stack = []
        end = start
        for i in range(start, len(raw_output)):
            if raw_output[i] == opening:
                stack.append(opening)
            elif raw_output[i] == closing:
                stack.pop()
                if not stack:
                    end = i + 1
                    break

        if stack:
            raise ValueError(f"No matching closing {closing} found for the opening {opening}.")

        # Extract the JSON string
        json_string = raw_output[start:end]

        # Remove problematic newline patterns and any other known issues
        #  json_string = re.sub(r'}\s*\n\s*\]', '}]', json_string)
  
        fixed_json_string = clean_json_string(json_string)

        print(f"JSON STRING {fixed_json_string}")

        # For now we use just the raw LLM output       
        # Convert JSON string to Python dictionary or list
        python_data = json.loads(json_string)
        
        return python_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON: {e}")


def clean_json_string(json_string):
    # Strip leading and trailing whitespace
    cleaned_string = json_string.strip()
    
    # Remove leading and trailing quotes if present
    if cleaned_string.startswith('"') and cleaned_string.endswith('"'):
        cleaned_string = cleaned_string[1:-1]
    
    # Replace multiple spaces with a single space
    cleaned_string = re.sub(r'\s{2,}', ' ', cleaned_string)
    
    # Escape necessary characters (e.g., newlines in values)
    cleaned_string = cleaned_string.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    
    # Remove extraneous whitespace around JSON delimiters
    cleaned_string = re.sub(r'\s*([\{\}\[\]:,])\s*', r'\1', cleaned_string)
    
    # Remove control characters
    cleaned_string = re.sub(r'[\x00-\x1F\x7F]', '', cleaned_string)
    
    #cleaned_string = re.sub(r'}\s*\n\s*\]', '}]', cleaned_string)
   
    cleaned_string = cleaned_string.replace('}\n]', '}]')

    cleaned_string = cleaned_string.replace('}\\n]', '}]')

  
    return cleaned_string


def normalize_json_string(json_string):
    # Remove newline and escape characters
    json_string = json_string.replace('\n', '').replace('\r', '').replace('\t', '')

    # Normalize spaces around keys and values
    json_string = json_string.strip()

    # Attempt to load the JSON string to verify its correctness
    try:
        json_data = json.loads(json_string)
        return json_data
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        return None
        
        
        
        
def generate_random_events(event_type, num_events=100):
    protocols = ["TCP", "UDP"]
    error_codes = ["CONNECTION_TIMEOUT", "DATA_CORRUPTION", "UNKNOWN_ERROR"]
    error_messages = {
        "CONNECTION_TIMEOUT": "Connection timed out after 30 seconds",
        "DATA_CORRUPTION": "Data corruption detected during transfer",
        "UNKNOWN_ERROR": "An unknown error occurred"
    }
    
    events = []
    current_time = datetime.utcnow()

    for _ in range(num_events):
        event = {
            "type": event_type,
            "timestamp": (current_time - timedelta(minutes=random.randint(0, 1440))).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_ip": f"192.168.1.{random.randint(1, 254)}",
            "destination_ip": f"192.168.1.{random.randint(1, 254)}",
            "protocol": random.choice(protocols),
            "port": random.randint(1024, 65535)
        }
        
        if event_type == "disconnection":
            event["duration"] = random.randint(1, 7200)  # duration in seconds
        elif event_type == "data_transfer":
            event["size"] = random.randint(64, 10000)  # size in bytes
        elif event_type == "error":
            error_code = random.choice(error_codes)
            event["error_code"] = error_code
            event["error_message"] = error_messages[error_code]
        
        events.append(event)

    return events #json.dumps(events, indent=2)




        
        

# Define the memory instance
memory = DynamicDistLLMMemory(instruction_text, contents_text)

# Initialize memory and subscribe
memory.execute_instruction_init()

print("-----------------------------")
#print(memory.getContext("Code"))
print(memory.get_contents())
print("-----------------------------")

#print(f"Trying to extract JSON from {memory.getContext('Code2')}")
print("-----------------------------")


code = memory.getContext("Code")
print(f"Extracted json: {code}")
code2 = extract_json_from_llm_output(code)
print(f"Extracted json: {code2}")
codeMem0 = DynamicDistLLMMemory(code2, {})
codeMem = DynamicDistLLMMemory(code2, {})

print("Memory structure")
print(codeMem.get_instructions())

#------
# Create the code
insta = codeMem.get_instructions()
print("---------------------------- code gen")
code_prompt = memory.getContext("Code-opt Code Python Example-events")
for inst in insta:
    print(f"Inst: {inst}")
    if 'command' in inst:
        print(f"Comparing {inst['command']}")
        if "LLM" in inst['command']:
            print(f"Processing code {inst}")
            anchor = inst['anchor']
            iprompt = inst['prompt']
            scopes = inst['scope']
            prompt = (f"Implement the following functionality: ({iprompt}) in safe Python."
            f"The scope references (JSON objects) are: {scopes}."
            f"Code instructions: {code_prompt}")
            codeMem.execute_command({"command": "CODIFY", "prompt": prompt, "anchor": anchor, "scope": "", "model":"ollama/llama3.1:70b", "source":inst})
        
print("Memory structure with code")
print(codeMem.get_instructions())
print(codeMem.get_contents())


codeMem.execute_instruction_init()

print("Testing LLM memory")
events = generate_random_events("data_transfer", 20)

for e in events:
    codeMem.react_to_event(e["type"], e)


# note that we should have a cost model (trigger events)
# the graph has the details for determinen costs based on this
# average in-degree might suffice as a cost-metric

print("-----------------------------")
print("Auditing:")
audit_nodes = codeMem.detect_audit_nodes()

print(f"Audit nodes: {audit_nodes}")
audit_mem = ""
for a in audit_nodes:
    audit_mem += f"{a} "

contents_text['Audit-points'] = audit_mem.strip()  

# Then we need to generate the audit tests, e.g., with prompts
# Tests should be generated for all LLM processed items and then
# these are used based on the auditing plan. The default plan
# would be to audit only edge nodes + log information from the predecessors in the call graph.

# Then the placement of audit logic

print("-----------------------------")
print("Optimized memory:")
bundle = codeMem.detect_bundles()
print(bundle)




