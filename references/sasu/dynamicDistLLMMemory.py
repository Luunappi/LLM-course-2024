# LLM Memory (DDMMem) part of the MemoryFormer architecture
# Note this is experimental POC code


# Notes:
# The content triggers are only evaluated with event processing when using LLMs
# Should expand to all content changes through internal book-keeping of content updates
#
# The graph traversal algorithm is not producing correct results in all cases, need to check.
#
# The memory ops do not have a cost model, should be implemented for future optimizers.
#
# The system should be integrated with DSPY style pipeline compilers. There is no
# no specific support for CoT or GoT. They can be implemented by repeated invocations.
#
# The memory does not publish events at the moment.
#
# The content trigger is very limited due to security / looping issues.
#
# The ZMQ functionality works, but more work is needed.


import threading
import json
import requests
from litellm import completion, get_max_tokens
from bs4 import BeautifulSoup
import pickle
import asyncio
import aiozmq
import zmq
import re
import zmq.asyncio
import time
import networkx as nx
from collections import defaultdict
from events import EventBroker
from ceval import execute_code_safely
import ast


class TriggerManager:
    def __init__(self):
        # Initialize the dictionary with empty lists for each query
        self.subscriptionsWithTrigger = {}

    def add_trigger(self, query, instruction):
        # Check if the query already exists in the dictionary
        if query in self.subscriptionsWithTrigger:
            # Append the new instruction to the existing list
            self.subscriptionsWithTrigger[query].append(instruction)
        else:
            # Create a new list with the instruction
            self.subscriptionsWithTrigger[query] = [instruction]

    def remove_trigger(self, query, instruction):
        # Check if the query exists in the dictionary
        if query in self.subscriptionsWithTrigger:
            try:
                # Remove the instruction from the list
                self.subscriptionsWithTrigger[query].remove(instruction)
                # If the list becomes empty, remove the query from the dictionary
                if not self.subscriptionsWithTrigger[query]:
                    del self.subscriptionsWithTrigger[query]
            except ValueError:
                print(f"Instruction '{instruction}' not found for query '{query}'")

    def get_triggers(self, query):
        # Retrieve the list of instructions for the query
        return self.subscriptionsWithTrigger.get(query, [])

    def has_query(self, query):
        # Check if the query exists in the dictionary
        return query in self.subscriptionsWithTrigger


class CodeExecutor:
    def __init__(self):
        pass

    def execute(self, code, params):
        result, localvars = execute_code_safely(code, params)
        return result


class DynamicDistLLMMemory:
    def __init__(
        self, instructions, contents, node_id=None, on_send=None, on_receive=None
    ):
        self.instructions = instructions
        self.contents = contents
        self.subscriptions = {}  # manage subscriptions
        self.subscriptionsWithTrigger = (
            TriggerManager()
        )  # manage subscriptions with LLM callbacks
        self.contentTrigger = (
            TriggerManager()
        )  # manage LLM content callbacks, called when event updates content
        self.codeTrigger = TriggerManager()
        self.codeContentTrigger = TriggerManager()
        self.classifyTrigger = TriggerManager()
        self.node_id = node_id
        self.on_send = on_send
        self.on_receive = on_receive
        self.code_executor = CodeExecutor()

        self.default_llm_name = "ollama/nemotron"

    def resetContent(self):
        self.contents = {}

    def terminate(self):
        return

    def print_change(self, key, old_value, new_value):
        print(f"Key '{key}' changed from {old_value} to {new_value}")

    # prompt specification is the prompt fine-tune for the memory use
    def execute_instruction_init(self):
        for instruction in self.instructions:
            self.execute_command(instruction)

    def execute_command(self, instruction):
        prompt_specification = ""  # placeholder

        print(f"Element {instruction}")
        if instruction["command"] == "SUBSCRIBE":
            query = instruction["event"]
            anchor = instruction["anchor"]
            self.subscriptions[query] = instruction

            # Register interest in the event type with the event broker
            print("Initiating send")
            if self.on_send:
                self.on_send(self, self.node_id, "SUBSCRIBE", query)
        elif instruction["command"] == "RETRIEVE":
            url = instruction["url"]
            compress = instruction["compress"]
            anchor = instruction["anchor"]
            self.retrieve(url, anchor, compress)
        elif instruction["command"] == "RAG-QUERY":
            # note this is LLM op for now
            query = instruction["prompt"]
            anchor = instruction["anchor"]
            prompt = f"{query}\n{prompt_specification}"
            rag_result = self.ask_litellm(prompt)
            self.replace_content(anchor, rag_result)
        elif instruction["command"] == "LLM-QUERY":
            query = instruction["prompt"]
            anchor = instruction["anchor"]
            scope = instruction["scope"]
            llm_name = None
            if "model" in instruction:
                llm_name = instruction["model"]
            context = self.getContext(scope)
            prompt = f"{query}\n{prompt_specification}\nYou are processing memory for a task management system. The response will be written to {anchor}. Memory contents for {scope} is provided here:{context}"
            llm_result = self.ask_litellm(prompt, llm_name)
            self.replace_content(anchor, llm_result)
        elif instruction["command"] == "CODIFY":
            prompt = instruction["prompt"]
            print(f"prompt {prompt}")
            anchor = instruction["anchor"]
            source = instruction["source"]
            scope = instruction["scope"]
            llm_name = None
            if "model" in instruction:
                llm_name = instruction["model"]
            context = self.getContext(scope)
            llm_result = self.ask_litellm(prompt, llm_name)
            # we modify the instruction
            source["code"] = llm_result
            if source["command"] == "LLM-QUERY":
                source["command"] = "CODE"
            elif source["command"] == "LLM-TRIGGER":
                source["command"] = "CODE-TRIGGER"
            elif source["command"] == "LLM-CONTENT-TRIGGER":
                source["command"] = "CODE-CONTENT-TRIGGER"
            # convert the style as well
            self.replace_content(anchor, llm_result)
        elif instruction["command"] == "LLM-TRIGGER":
            query = instruction["event"]
            anchor = instruction["anchor"]
            print(f"Setting LLM-TRIGGER for {query}")
            self.subscriptionsWithTrigger.add_trigger(query, instruction)
        elif instruction["command"] == "LLM-CONTENT-TRIGGER":
            scope = instruction["scope"]
            # Iterate over the scope string and set the content trigger
            # note only one trigger can be set -- fix
            for item in scope.split():
                self.contentTrigger.add_trigger(item, instruction)
        elif instruction["command"] == "CODE":
            code = instruction["code"]
            scope = instruction["scope"]
            context = self.getContextArray(scope)
            anchor = instruction["anchor"]
            print(f"Setting CODE for {code}")
            code_result = self.code_executor.execute(code, context)
            print(code_result)
            self.replace_content(anchor, code_result)
        elif instruction["command"] == "CODE-TRIGGER":
            code = instruction["code"]
            scope = instruction["scope"]
            event = instruction["event"]
            context = self.getContextArray(scope)
            anchor = instruction["anchor"]
            self.codeTrigger.add_trigger(event, instruction)
        elif instruction["command"] == "CODE-CONTENT-TRIGGER":
            code = instruction["code"]
            scope = instruction["scope"]
            context = self.getContextArray(scope)
            anchor = instruction["anchor"]
            for item in scope.split():
                self.codeContentTrigger.add_trigger(item, instruction)
        elif instruction["command"] == "LLM-CLASSIFY":
            scope = instruction["scope"]
            context = self.getContextArray(scope)
            anchor = instruction["anchor"]
            for item in scope.split():
                self.classifyTrigger.add_trigger(item, instruction)
        elif instruction["command"] == "UNSUBSCRIBE":
            query = instruction["event"]
            anchor = instruction["anchor"]
            self.subscriptions[query] = ""
            self.subscriptionsWithTrigger.remove(query, instruction)
            if self.on_send:
                self.on_send(self, self.node_id, "UNSUBSCRIBE", query)
        elif instruction["command"] == "REMOVE-CONTENT-TRIGGER":
            scope = instruction["scope"]
            # Iterate over the scope string and set the content trigger
            for item in scope.split():
                self.contentTrigger.remove(item, instruction)
        elif instruction["command"] == "COMPRESS":
            query = instruction["prompt"]
            anchor = instruction["anchor"]
            limit = instruction["datalimit"]
            compress_anchor(query, anchor, limit)
        elif instruction["command"] == "REMOVE-CODE-TRIGGER":
            code = instruction["event"]
            self.codeTrigger.remove_trigger(event, instruction)
        elif instruction["command"] == "REMOVE-CODE-CONTENT-TRIGGER":
            scope = instruction["scope"]
            # Iterate over the scope string and set the content trigger
            for item in scope.split():
                self.codeContentTrigger.remove_trigger(item, instruction)
        elif instruction["command"] == "REMOVE-CLASSIFY-TRIGGER":
            scope = instruction["scope"]
            # Iterate over the scope string and set the content trigger
            for item in scope.split():
                self.codeContentTrigger.remove_trigger(item, instruction)

    def getContextArray(self, scopestring: str) -> dict:
        """
        Provide a dictionary based on the scopestring.
        Each key-value pair corresponds to an item found in self.contents.
        Ensures that each item is a list of dictionaries.
        """
        context_dict = {}
        scope_items = scopestring.split()
        for item in scope_items:
            if item in self.contents:
                # Ensure the content is parsed correctly and is a list
                try:
                    content = self.contents[item]
                    if isinstance(content, dict):
                        context_dict[item] = content
                    elif isinstance(content, list):
                        context_dict[item] = content  # Leave lists as they are
                    elif isinstance(content, tuple):
                        context_dict[item] = list(content)  # Convert tuple to list
                    elif isinstance(content, str):
                        context_dict[item] = str(content)  # Convert tuple to list
                    else:
                        print(f"Content type {type(content)}")
                        print(f"{content}")
                        raise ValueError(
                            "Content must be a dictionary or list of dictionaries."
                        )
                except json.JSONDecodeError:
                    context_dict[item] = self.contents[item]
        return context_dict

    def getContext(self, scopestring):
        content = ""
        # Split the scopestring into individual items
        scope_items = scopestring.split()

        # Iterate over the dictionary
        for item in scope_items:
            if item in self.contents:
                content += json.dumps(self.contents[item]) + "\n"
        return content

    def retrieve_and_clean_url(self, url):
        try:
            # Fetch the webpage content
            response = requests.get(url)
            response.raise_for_status()  # Check for HTTP errors

            # Parse the HTML content
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            # Get text and remove leading/trailing whitespace
            text = soup.get_text(separator=" ")

            # Further clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)

            return text

        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None

    def retrieve(self, url, anchor, compress):
        text = self.retrieve_and_clean_url(url)
        print("-----RETRIEVE")
        print(anchor)
        prompt2 = f"{compress}\Content:{text}"
        llm_result = self.ask_litellm(prompt2)
        print(llm_result)
        print("-----")
        self.replace_content(anchor, llm_result)

    def compress_anchor(self, query, anchor, limit):
        for key, value in self.contents.items():
            if key == anchor:
                print(f"Data limit comparison {value.len} > {limit}")
                if len(value) > limit:
                    prompt = f"{query}\nMemory contents:{value}"
                    llm_result = self.ask_litellm(prompt2)
                    self.contents[key] = llm_result
                    break

    # -----------------------------------------------------------

    # we follow breadth first logic with callbacks
    def react_to_content_callback_trigger(self, event_name):
        anchors = set()

        print("Checking if sub trigger")

        triggers = self.subscriptionsWithTrigger.get_triggers(event_name)
        print(f"Trigger set for event subs:{triggers} for {event_name}")
        if triggers:
            for instruction in triggers:
                print(instruction)
                prompt = instruction["prompt"]
                anchor = instruction["anchor"]
                # datalimit = instruction['datalimit']
                anchors.add(anchor)
                scope = instruction["scope"]
                llm_name = None
                if "model" in instruction:
                    llm_name = instruction["model"]

                content = self.getContext(scope)
                print("-----")
                print(anchor)
                promptfinal = f"{prompt}\nYou are processing memory for a task management system. The response will be written to {anchor}. Memory contents for {scope} is provided here:{content}"
                print(promptfinal)
                llm_result = self.ask_litellm(promptfinal, llm_name)
                print(llm_result)
                print("-----")
                self.replace_content(anchor, llm_result)

            # now check for anchor callbacks, all the anchors are up to date
            if anchors:
                for a in anchors:
                    self.execute_subcontentcallback(a)

    def execute_subcontentcallback(self, anchor):
        anchors = set()

        print("Checking if classify trigger")

        # classify trigger
        triggers = self.classifyTrigger.get_triggers(anchor)
        if triggers:
            print("Yes classify trigger")
            for instruction in triggers:
                if instruction:
                    scope2 = instruction["scope"]
                    prompt2 = instruction["prompt"]
                    anchor2 = instruction["anchor"]
                    llm_name2 = None
                    if "model" in instruction:
                        llm_name2 = instruction["model"]

                    replace = False
                    if "replace" in instruction:
                        replace = instruction["replace"]

                    content = self.getContext(scope2)
                    print("-----")
                    print(anchor2)
                    prompt2 = f"{prompt2}\nYou are processing memory for a task management system. Select one of the following labels {anchor2}. Input data is here:{content}. Only output the chosen anchor without any additional characters or remarks."
                    print(prompt2)
                    llm_result = self.ask_litellm(prompt2, llm_name2)
                    print(llm_result)

                    print("-----")
                    term = self.get_first_term(llm_result)
                    if term in anchor2:
                        if replace:
                            self.add_content(term, content)
                        else:
                            self.replace_content(term, content)

                        # activate any additional callbacks
                        if term not in anchors:
                            anchors.add(term)

        # other triggers
        triggers2 = self.contentTrigger.get_triggers(anchor)
        if triggers2:
            for instruction in triggers2:
                if instruction:
                    scope2 = instruction["scope"]
                    prompt2 = instruction["prompt"]
                    anchor2 = instruction["anchor"]
                    llm_name2 = None
                    if "model" in instruction:
                        llm_name2 = instruction["model"]

                    content = self.getContext(scope2)
                    print("-----")
                    print(anchor2)
                    if anchor2 not in anchors:
                        anchors.add(anchor2)
                    prompt2 = f"{prompt2}\nYou are processing memory for a task management system. The response will be written to {anchor2}. Memory contents for {scope2} is provided here:{content}"
                    print(prompt2)
                    llm_result = self.ask_litellm(prompt2, llm_name2)
                    print(llm_result)
                    print("-----")
                    self.replace_content(anchor2, llm_result)
                    # activate any additional callbacks

            # iterate the anchors down the dag
            if anchors:
                for a in anchors:
                    self.execute_subcontentcallback(a)

    def get_first_term(self, string):
        # Strip leading/trailing whitespace and split the string
        stripped_string = string.strip()
        if stripped_string:
            return stripped_string.split()[0]
        return None

    def react_to_code_trigger(self, event_name):
        # Then react to triggers: code and LLM, and LLM content
        print("Checking if code trigger")
        anchors = set()
        print(f"Triggers {self.codeTrigger.get_triggers(event_name)}")
        if self.codeTrigger.has_query(event_name):
            print("Was code trigger")
            triggers = self.codeTrigger.get_triggers(event_name)
            for instruction in triggers:
                code = instruction["code"]
                scope = instruction["scope"]
                context = self.getContextArray(scope)
                anchor = instruction["anchor"]
                print(f"Setting CODE for {code}")
                print(f"Params: {context}")
                code_result = self.code_executor.execute(code, context)
                print("CODE RESULT")
                print(code_result)
                if anchor not in anchors:
                    anchors.add(anchor)
                self.replace_content(anchor, code_result)

        if anchors:
            for a in anchors:
                self.process_code_trigger(a)

    def process_code_trigger(self, anchor):
        anchors = set()
        # process any content callbacks, limit applies to all content fields
        print(f"CODE CONTENT TRIGGER {self.codeContentTrigger.get_triggers(anchor)}")
        print(f"trigger set {self.codeContentTrigger.has_query(anchor)}")
        if self.codeContentTrigger.has_query(anchor):
            triggers = self.codeContentTrigger.get_triggers(anchor)
            for instruction2 in triggers:
                code = instruction2["code"]
                scope = instruction2["scope"]
                context = self.getContextArray(scope)
                anchor2 = instruction2["anchor"]
                if anchor2 not in anchors:
                    anchors.add(anchor2)
                print(f"Setting CODE for {code}")
                print(f"Params: {context}")
                code_result = self.code_executor.execute(code, context)
                print("CODE RESULT")
                print(code_result)
                self.replace_content(anchor2, code_result)
                # check for any remaining triggers down the graph

        if anchors:
            for a in anchors:
                self.process_code_trigger(a)

    # Can also implement code and LLM in the same command, to add flexibility
    def react_to_event(self, event_name, event_data):
        print("reacted to event")
        print(event_name)
        print(event_data)

        # If the event is not subscribed, we end here
        # The callbacks here require event activation
        if event_name not in self.subscriptions:
            print("No sub")
            return

        # Add content

        instruction = self.subscriptions[event_name]
        if not instruction:
            print("No instruction")
            return

        anchor = instruction["anchor"]
        replace = False
        if "replace" in instruction:
            replace = instruction["replace"]

        if replace:
            self.update_content_json(anchor, event_data, True)
        else:
            self.update_content_json(anchor, event_data, False)

        # react to triggers: first anchor, then content callbacks
        self.react_to_content_callback_trigger(event_name)
        self.execute_subcontentcallback(anchor)

        self.react_to_code_trigger(event_name)
        self.process_code_trigger(anchor)

    def notify(self, event_name, event_data):
        print("Received server event")
        print(event_name)
        react_to_event(self, event_name, event_data)

    # --------------------------------------------------

    def get_contents(self):
        return json.dumps(self.contents)

    def get_contents_json(self):
        return self.contents

    def get_instructions(self):
        return self.instructions

    def replace_content(self, anchor, new_content):
        for key, value in self.contents.items():
            if key == anchor:
                self.contents[key] = new_content
                break
        else:
            self.contents[anchor] = new_content

    def get_content(self, anchor):
        if anchor in self.contents:
            print("Found content")
            print(self.contents[anchor])
            return self.contents[anchor]
        else:
            print("Did not find content")
            return {}

    def get_content_json(self, anchor):
        if anchor in self.contents:
            print("Found content")
            print(self.contents[anchor])
            return self.extract_json_from_llm_output(self.contents[anchor])
        else:
            print("Did not find content")
            return {}

    def extract_json_from_llm_output(self, raw_output):
        """
         Extracts JSON content from LLM output that may include extraneous text,
         handling both JSON objects and arrays, and supporting nested structures accurately.

        Parameters:
        raw_output (str): The raw string containing JSON data with extraneous text.

        Returns:
        dict or list: The extracted JSON content as a Python dictionary or list.
        """
        try:
            # Locate the first opening brace or bracket
            start_object = raw_output.find("{")
            start_array = raw_output.find("[")

            if start_object == -1 and start_array == -1:
                raise ValueError("No JSON structure found in the provided string.")

            if start_object != -1 and (start_array == -1 or start_object < start_array):
                start = start_object
                opening = "{"
                closing = "}"
            else:
                start = start_array
                opening = "["
                closing = "]"

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
                raise ValueError(
                    f"No matching closing {closing} found for the opening {opening}."
                )

            # Extract the JSON string
            json_string = raw_output[start:end]

            # Remove problematic newline patterns and any other known issues
            #  json_string = re.sub(r'}\s*\n\s*\]', '}]', json_string)

            fixed_json_string = self.clean_json_string(json_string)

            print(f"JSON STRING: {fixed_json_string}")

            # For now we use just the raw LLM output
            # Convert JSON string to Python dictionary or list
            python_data = json.loads(raw_output)  # fixed_json_string)

            return python_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

    def clean_json_string(self, json_string):
        # Strip leading and trailing whitespace
        cleaned_string = json_string.strip()

        # Remove leading and trailing quotes if present
        if cleaned_string.startswith('"') and cleaned_string.endswith('"'):
            cleaned_string = cleaned_string[1:-1]

        # Replace multiple spaces with a single space
        cleaned_string = re.sub(r"\s{2,}", " ", cleaned_string)

        # Escape necessary characters (e.g., newlines in values)
        cleaned_string = (
            cleaned_string.replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )

        # Remove extraneous whitespace around JSON delimiters
        cleaned_string = re.sub(r"\s*([\{\}\[\]:,])\s*", r"\1", cleaned_string)

        # Remove control characters
        cleaned_string = re.sub(r"[\x00-\x1F\x7F]", "", cleaned_string)

        cleaned_string = re.sub(r"}\s*\n\s*\]", "}]", cleaned_string)

        cleaned_string = cleaned_string.replace("}\n]", "}]")

        cleaned_string = cleaned_string.replace("}\\n]", "}]")

        return cleaned_string

    def add_content(self, anchor, new_content):
        print("Adding content to anchor")
        print(anchor)
        if anchor in self.contents:
            self.contents[anchor] += f"\n{new_content}"
        else:
            self.contents[anchor] = new_content

    def update_content_json(self, anchor, json_str: str, replace=False) -> None:
        """
        Update the contents dictionary with data from a JSON string.
        Ensure that all content is stored as a list of dictionaries.
        """
        # Ensure new_data is correctly parsed
        if isinstance(json_str, str):
            try:
                new_data = json.loads(json_str)
                print(
                    f"Parsed new_data from string: {new_data} (type: {type(new_data)})"
                )
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON string: {e}")
                print(json_str)
                new_data = json_str
                self.contents[anchor] = new_data
                return
        elif isinstance(json_str, dict) or isinstance(json_str, list):
            new_data = json_str
            print(f"Using new_data as provided: {new_data} (type: {type(new_data)})")
        else:
            print("Input must be a JSON string, dictionary, or list")
            return

        # Transform new_data into a list if it is not already
        if isinstance(new_data, dict):
            new_data = [new_data]
        elif not isinstance(new_data, list):
            print(f"Invalid new_data type: {type(new_data)}")
            return

        # Handle updating the content based on its current type
        if anchor in self.contents:
            existing_content = self.contents[anchor]
            print(
                f"Existing content before update: {existing_content} (type: {type(existing_content)})"
            )

            # Parse existing content if it's a JSON string
            if isinstance(existing_content, str):
                try:
                    existing_content = json.loads(existing_content)
                    print(
                        f"Parsed existing_content: {existing_content} (type: {type(existing_content)})"
                    )
                except json.JSONDecodeError as e:
                    print(f"Error parsing existing content: {e}")
                    return

            # Ensure existing content is a list
            if isinstance(existing_content, dict):
                existing_content = [existing_content]
            elif not isinstance(existing_content, list):
                print(f"Invalid existing_content type: {type(existing_content)}")
                return

            # Extend the existing content list with the new data list
            print(f"Before extending: {existing_content}")
            if replace:
                existing_content = new_data
            else:
                existing_content.extend(new_data)
            print(f"After extending: {existing_content}")

            self.contents[anchor] = existing_content
        else:
            self.contents[anchor] = new_data
            print(f"Added new anchor with content: {self.contents[anchor]}")

        print(
            f"Updated content at {anchor}: {self.contents[anchor]} (type: {type(self.contents[anchor])})"
        )

    # MEMORY OPTIMIZATION

    def create_call_graph(self, operations):
        """Create a call graph where nodes are write objects and edges represent read dependencies."""
        try:
            G = nx.DiGraph()
            reads_to_writes = defaultdict(set)
            writes = set()

            for op in operations:
                write_object = op["write"]
                read_objects = op["read"]

                if write_object not in G:
                    G.add_node(write_object)
                for r in read_objects:
                    if r not in G:
                        G.add_node(r)
                    G.add_edge(r, write_object)

            return G
        except Exception as e:
            print(f"Error creating call graph: {e}")

    def find_clusters(self, graph):
        """Find clusters in the graph."""
        try:
            clusters = list(nx.weakly_connected_components(graph))
            return clusters
        except Exception as e:
            print(f"Error finding clusters: {e}")

    def add_operation(self, operations, command, counter, read_object, write_object):
        """Add a new operation to the list of operations with a unique identifier."""
        try:
            reads = []
            unique_command = f"{command}_{counter}"
            if isinstance(read_object, str):
                # If read_objects is a string, split it into a list of read objects
                reads = read_object.split()
            elif isinstance(read_object, set):
                # If read_objects is a set, convert it to a list
                reads = list(read_object)
            else:
                # If read_objects is already a list, use it directly
                reads = read_object

            operation = {
                "command": unique_command,
                "original_command": command,
                "read": reads,
                "write": write_object,
            }
            operations.append(operation)
            return operations
        except Exception as e:
            print(f"Error adding operation: {e}")

    def identify_end_write_objects(self, graph):
        """Identify objects that are written to by only one operation."""
        end_write_objects = {
            node for node in graph.nodes if graph.out_degree(node) == 0
        }
        return end_write_objects

    def find_partitionable_subgraphs(self, graph, end_write_objects):
        """Find subgraphs where all operations lead to a single end write object."""
        partitionable_subgraphs = []

        for end_obj in end_write_objects:
            subgraph_nodes = [
                node
                for node in graph.nodes
                if node == end_obj or end_obj in nx.descendants(graph, node)
            ]
            if subgraph_nodes:
                subgraph = graph.subgraph(subgraph_nodes)
                partitionable_subgraphs.append(subgraph)

        return partitionable_subgraphs

    def remove_end_nodes(self, graph, end_write_objects):
        """Remove end write objects from the graph."""
        new_graph = graph.copy()
        new_graph.remove_nodes_from(end_write_objects)
        return new_graph

    def traverse_from_end_write_objects(self, graph, original_graph, end_write_objects):
        """Traverse the graph from the predecessors of the removed end write objects to determine partitions."""
        partitions = []
        visited = set()

        def bfs(start_node):
            queue = [start_node]
            partition = set()
            while queue:
                node = queue.pop(0)
                if node not in visited:
                    visited.add(node)
                    partition.add(node)
                    for predecessor in graph.predecessors(node):
                        if predecessor not in visited:
                            queue.append(predecessor)
            return partition

        predecessors = set()
        for end_obj in end_write_objects:
            for predecessor in original_graph.predecessors(end_obj):
                predecessors.add(predecessor)

        for predecessor in predecessors:
            if predecessor not in visited:
                partition = bfs(predecessor)
                partitions.append(partition)

        return partitions

    def traverse_from_end_write_objects_full(self, graph, end_write_objects):
        """Traverse the graph from end write objects to determine partitions."""
        partitions = []
        visited = set()

        def bfs(start_node):
            queue = [start_node]
            partition = set()
            while queue:
                node = queue.pop(0)
                if node not in visited:
                    visited.add(node)
                    partition.add(node)
                    for predecessor in graph.predecessors(node):
                        if predecessor not in visited:
                            queue.append(predecessor)
            return partition

        for end_obj in end_write_objects:
            if end_obj not in visited:
                partition = bfs(end_obj)
                partitions.append(partition)

        return partitions

    def detect_audit_nodes(self):
        operations = []
        counter = 1

        for instruction in self.instructions:
            if instruction["command"] == "SUBSCRIBE":
                query = instruction["event"]
                anchor = instruction["anchor"]
                print(f"Adding {query}")
                self.add_operation(operations, "SUBSCRIBE", counter, query, anchor)
                counter += 1
            # these should be updated to work with scopes
            #            elif instruction['command'] == 'RAG_QUERY':
            #                query = instruction['prompt']
            #                anchor = instruction['anchor']
            #                self.add_operation(operations,'RAG_QUERY',counter, query, anchor)
            #                counter+=1
            elif instruction["command"] == "LLM-QUERY":
                anchor = instruction["anchor"]
                scope = instruction["scope"]
                scopestring = scope
                # Iterate over the scope string and set the content trigger
                reads = []
                for item in scopestring.split():
                    reads.append(item)
                self.add_operation(operations, "LLM_QUERY", counter, reads, anchor)
                counter += 1
            elif instruction["command"] == "LLM-TRIGGER":
                query = instruction["event"]
                anchor = instruction["anchor"]
                scope = instruction["scope"]
                scopestring = scope
                # Iterate over the scope string and set the content trigger
                reads = []
                for item in scopestring.split():
                    reads.append(item)
                self.add_operation(operations, "LLM_TRIGGER", counter, reads, anchor)
                counter += 1
            elif instruction["command"] == "LLM-CONTENT-TRIGGER":
                scope = instruction["scope"]
                anchor = instruction["anchor"]
                scopestring = scope
                # Iterate over the scope string and set the content trigger
                reads = []
                for item in scopestring.split():
                    reads.append(item)
                self.add_operation(
                    operations, "LLM-CONTENT-TRIGGER", counter, reads, anchor
                )
                counter += 1
        #           elif instruction['command'] == 'COMPRESS':
        #               query = instruction['query']
        #               anchor = instruction['anchor']
        #               self.add_operation(operations,'COMPRESS', counter,query, anchor)
        #               counter+=1
        #           elif instruction['command'] == 'RUNLLM':
        #               query = instruction['query']
        #               anchor = instruction['anchor']
        #               scope = instruction['scope']
        #               reads = []
        #               for item in scopestring.split():
        #                   reads.append(item)
        #               self.add_operation(operations,'RUNLLM',counter, reads, anchor)
        #               counter+=1

        # Create the call graph
        call_graph = self.create_call_graph(operations)

        print("Nodes:")
        for node in call_graph.nodes(data=True):
            print(node)
        print("\nEdges:")
        for edge in call_graph.edges(data=True):
            print(edge)

        # Find clusters in the graph
        clusters = self.find_clusters(call_graph)

        # Identify end write objects
        end_write_objects = self.identify_end_write_objects(call_graph)

        return end_write_objects

    def detect_bundles(self):
        operations = []
        counter = 1

        for instruction in self.instructions:
            if instruction["command"] == "SUBSCRIBE":
                query = instruction["event"]
                anchor = instruction["anchor"]
                print(f"Adding {query}")
                self.add_operation(operations, "SUBSCRIBE", counter, query, anchor)
                counter += 1
            # these are init functions so they are not taken into account in the call graph
            #            elif instruction['command'] == 'RAG_QUERY':
            #                query = instruction['prompt']
            #                anchor = instruction['anchor']
            #                self.add_operation(operations,'RAG_QUERY',counter, query, anchor)
            #                counter+=1
            #            elif instruction['command'] == 'LLM-QUERY':
            #                anchor = instruction['anchor']
            #                scope = instruction['scope']
            #                scopestring = scope
            #               # Iterate over the scope string and set the content trigger
            #               reads = []
            #               for item in scopestring.split():
            #                   reads.append(item)
            #               self.add_operation(operations,'LLM_QUERY',counter, reads, anchor)
            #               counter+=1
            elif instruction["command"] == "LLM-TRIGGER":
                query = instruction["event"]
                anchor = instruction["anchor"]
                scope = instruction["scope"]
                scopestring = scope
                # Iterate over the scope string and set the content trigger
                reads = []
                for item in scopestring.split():
                    reads.append(item)
                self.add_operation(operations, "LLM_TRIGGER", counter, reads, anchor)
                counter += 1
            elif instruction["command"] == "LLM-CONTENT-TRIGGER":
                scope = instruction["scope"]
                anchor = instruction["anchor"]
                scopestring = scope
                # Iterate over the scope string and set the content trigger
                reads = []
                for item in scopestring.split():
                    reads.append(item)
                self.add_operation(
                    operations, "LLM-CONTENT-TRIGGER", counter, reads, anchor
                )
                counter += 1
        #           elif instruction['command'] == 'COMPRESS':
        #               query = instruction['query']
        #               anchor = instruction['anchor']
        #               self.add_operation(operations,'COMPRESS', counter,query, anchor)
        #               counter+=1
        #           elif instruction['command'] == 'RUNLLM':
        #               query = instruction['query']
        #               anchor = instruction['anchor']
        #               scope = instruction['scope']
        #               reads = []
        #               for item in scopestring.split():
        #                   reads.append(item)
        #               self.add_operation(operations,'RUNLLM',counter, reads, anchor)
        #               counter+=1

        print(f"Operations: {operations}")
        # Create the call graph

        call_graph = self.create_call_graph(operations)

        print("Nodes:")
        for node in call_graph.nodes(data=True):
            print(node)
        print("\nEdges:")
        for edge in call_graph.edges(data=True):
            print(edge)

        # Find clusters in the graph
        clusters = self.find_clusters(call_graph)

        # Identify end write objects
        end_write_objects = self.identify_end_write_objects(call_graph)

        # Remove end write objects from the graph
        graph_without_end_nodes = self.remove_end_nodes(call_graph, end_write_objects)

        # Traverse from end write objects to determine partitions
        partitions = self.traverse_from_end_write_objects(
            graph_without_end_nodes, call_graph, end_write_objects
        )

        # Display clusters and partitions
        print("Clusters:")
        for idx, cluster in enumerate(clusters):
            print(f"Cluster {idx + 1}: {cluster}")

        print("\nPartitions:")
        for idx, partition in enumerate(partitions):
            print(f"Partition {idx + 1}: {partition}")

    def get_clusters_of_single_write_endpoints(self, contents):
        read_dict = defaultdict(list)
        write_dict = defaultdict(list)

        clusters = []

        for content_key in contents.keys():
            content_reads = self.read_dict[content_key]
            content_writes = self.write_dict[content_key]

            if len(content_reads) == 1 and len(content_writes) > 1:
                cluster = {
                    "content": content_key,
                    "operations": [
                        {"type": "READ", "target": content_key},
                        {"type": "WRITE", "source": content_key},
                    ],
                }

                clusters.append(cluster)

        return clusters

    # LLM invocation
    def extract_output_content(self, llm_response):
        # Use regular expression to find content between <output> and </output> tags
        pattern = r"<output>(.*?)</output>"
        match = re.search(pattern, llm_response, re.DOTALL)

        if match:
            # Return the content inside the <output> tags
            return match.group(1).strip()
        else:
            # If no match is found, return a message
            return "No output content found."

    def ask_litellm(self, prompt, llm_name=None):
        try:
            if not llm_name:
                llm_name = self.default_llm_name
            print(f"LITELLM PROMPT: {prompt}")
            # litellm.set_verbose=True
            response = completion(
                model=llm_name,
                messages=[{"content": prompt, "role": "user"}],
                api_base="http://localhost:11434",
            )

            final_response = response.choices[0].message.content
            if "reflection" in llm_name:
                print("REFLECTION USED")
                final_response = self.extract_output_content(
                    response.choices[0].message.content
                )

            print(f"LITELLM RESPONSE: {final_response}")

            return final_response
        except Exception as e:
            return str(e)
