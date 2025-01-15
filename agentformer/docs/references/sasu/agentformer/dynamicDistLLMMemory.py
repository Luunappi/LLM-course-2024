# Agent script. Part of the MemoryFormer architecture.
# Note this is experimental POC code
# Sasu Tarkoma

# ---------------------------
# Standard Library Imports
# ---------------------------
import ast
import json
import logging
import re
import threading
import time
import uuid
from collections import defaultdict

# ---------------------------
# Third-Party Library Imports
# ---------------------------
import numpy as np
import requests
import torch
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util

# ---------------------------
# Local / Intra-project Imports
# ---------------------------
from litellm import completion, get_max_tokens
from triggermanagement import TriggerManager
from ceval import execute_code_safely


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CodeExecutor:
    def __init__(self):
        pass
    
    def execute(self, code, params):
        result, localvars = execute_code_safely(code, params)
        return result


class DynamicDistLLMMemory:
    def __init__(self, instructions, contents):
        self.instructions = instructions
        self.contents = contents
        self.subscriptions = TriggerManager()   # manage subscriptions        
        self.subscriptionsWithTrigger = TriggerManager() # manage subscriptions with LLM callbacks    
        self.global_state = "init"  # for state management
        self.code_executor = CodeExecutor()
        self.transition_count = 0
        self.MAX_TRANSITIONS = 100
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
 
        self.default_llm_name = "ollama/llama3.3" 

    def resetContent(self):
        self.contents = {}

    def init_state(self):
        self.global_sate = "init"
        
    def set_global_state(self, state):
        self.global_state=state

    def get_global_state(self):
        return self.global_state
   
    def load_instructions(self, new_instructions):
        self.instructions = new_instructions
        self.state="init"


    def transition_to(self, new_state):
        self.transition_count += 1
        if self.transition_count > self.MAX_TRANSITIONS:
            raise RuntimeError("Infinite loop or too many transitions detected!")
        self.global_state = new_state


    def terminate(self):
        return  
    
    def print_change(self, key, old_value, new_value):
        logger.debug(f"Key '{key}' changed from {old_value} to {new_value}")
                             

    def get_last_sentence(self,text):
        # Split the text into sentences using a regex that matches sentence-ending punctuation.
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        # Return the last sentence if it exists, otherwise return an empty string
        return sentences[-1] if sentences else ""
                  
    def extract_number_and_string(self, input_str):
        # Regular expression to match a number followed by an optional string
        match = re.match(r'(\d+)(?:\s*(.*))?', input_str.strip())
        if match:
            number = int(match.group(1))  # Convert the first group to an integer
            optional_string = match.group(2) or ""  # Get the optional string or default to empty string
            return number, optional_string
        else:
            raise ValueError("Input string does not match the expected format.")



    def execute_instruction_init(self):
        """
        Executes all instructions in self.instructions, typically on system startup
        or initialization (state='init').
        """
        logger.info("Executing all instructions on init.")
        if not hasattr(self, 'instructions') or not self.instructions:
            logger.debug("No instructions found to execute on init.")
            return

        for instruction in self.instructions:
            if not instruction or not isinstance(instruction, dict):
                logger.debug("Skipping invalid or empty instruction: %s", instruction)
                continue
            logger.debug("Executing instruction on init: %s", instruction)
            self.execute_command(instruction)


    def execute_commands_current_state(self):
        """
        Retrieves instructions matching the current global state, then executes them,
        skipping any 'BUTTON' instructions.
        """
        logger.info("Executing commands for current state: %s", self.global_state)

        # Defensive check: ensure 'memory' or 'self' can fetch instructions
        if not hasattr(self, 'get_instructions_current_state'):
            logger.error("'get_instructions_current_state' method not found.")
            return

        current_instructions = self.get_instructions_current_state()
        if not current_instructions:
            logger.debug("No instructions found for current state '%s'.", self.global_state)
            return

        for instruction in current_instructions:
            if not instruction or not isinstance(instruction, dict):
                logger.debug("Skipping invalid or empty instruction: %s", instruction)
                continue

            command = instruction.get('command', '')
            # Skip instructions whose command contains 'BUTTON'
            if 'BUTTON' in command:
                logger.debug("Skipping 'BUTTON' instruction: %s", instruction)
                continue

            logger.debug("Executing instruction for current state: %s", instruction)
            self.execute_command(instruction)


    def prepare_prompt(self, instruction, prompt):
        """
        Prepare a prompt by formatting it with parameters derived from the given instruction.
        
        Steps:
        1. Validate the prompt.
        2. Optionally handle RAG parameters (if 'rag' is specified).
        3. Generate a context array for placeholders.
        4. Format and return the updated prompt.
        
        Returns
        -------
        str
            The updated (or original) prompt after formatting. 
            If any error occurs, falls back to the original `prompt`.
        """
        logger.debug("Preparing prompt. Instruction: %s, Prompt: %s", instruction, prompt)
        try:
            # Validate prompt is a non-empty string
            if not (isinstance(prompt, str) and prompt.strip()):
                logger.debug("Prompt is empty or not a string; returning as is.")
                return prompt

            # Retrieve scope (may be empty)
            scopes = instruction.get('scope', '')
            topk = instruction.get('topk', 2)
            rag = self.prepare_rag(instruction)
            print(f"RAG: {rag}")
            print(f"scopes: {scopes}")
            print(f"prompt: {prompt}")
            print(f"contents: {self.contents}")
            # Initialize RAG parameters
            try:
                parameters = self.getContextArray(scopes, rag, topk)
            except Exception as e:
                logger.warning("Error generating context array: %s", e)
                parameters = {}

            print(f"Parameters: {parameters}")
    
            # Finally, format the prompt
            try:
                updated_prompt = prompt.format(**parameters)
                print(f"Updated prompt: {updated_prompt}")
                return updated_prompt
            except Exception as e:
                logger.warning("Error formatting prompt: %s", e)
                return prompt

        except Exception as e:
            logger.error("Unexpected error in prepare_prompt: %s", e, exc_info=True)
            return prompt

    def prepare_rag(self, instruction):
            """
            Updates RAG prompt and runs it.
            """
            logger.debug("Preparing rag. Instruction: %s", instruction)
            try:
                # Retrieve scope (may be empty)
                scopes = instruction.get('scope', '')

                # Initialize RAG parameters
                rag = instruction.get('rag', None)

                # Handle RAG parameters
                if isinstance(rag, str) and rag.strip():
                    try:
                        # Get topk value from instruction with a fallback
                        topk = instruction.get('topk', 2)
                        # Generate RAG parameters and format RAG string
                        rag_params = self.getContextArray(scopes, None, topk)
                        rag = rag.format(**rag_params)
                    except Exception as e:
                        logger.warning("Error formatting RAG: %s", e)
                    return rag

            except Exception as e:
                logger.error("Unexpected error in prepare_rag: %s", e, exc_info=True)
            return rag
            
   
    def execute_command(self, instruction: dict) -> None:
        """
        Execute a command-based instruction with additional state management logic.

        Parameters
        ----------
        instruction : dict
            A dictionary describing the command and its arguments.
            Expected structure (common keys):
                command   (str)  : The command to be executed.
                state     (str)  : Desired state required for the command (optional).
                setstate  (str)  : Next state to transition to (optional).
                ...
        """
        if not instruction or not isinstance(instruction, dict):
            logger.warning("No instruction provided or instruction is not a dictionary.")
            return

        command = instruction.get('command')
        if not command:
            logger.warning("Instruction missing 'command' key.")
            return

        logger.debug("Received instruction: %s", instruction)

        # Step 1: Handle state gating/updates before command execution
        if not self._check_and_handle_state(instruction):
            # If the command is gated by state and fails, return
            return

        # Step 2: Dispatch to the appropriate command handler
        # You can expand or modify this dictionary based on your use cases.
        command_handlers = {
            'SUBSCRIBE'       : self._handle_subscribe,
            'UNSUBSCRIBE'     : self._handle_unsubscribe,
            'INPUT'           : self._handle_input,
            'TEXT'            : self._handle_text,
            'HTML'            : self._handle_html,
            'BUTTON'          : self._handle_button,
            'CONDITION'       : self._handle_condition,
            'AGENTRUN'        : self._handle_agent_run,
            'LOAD'            : self._handle_load,
            'EMBEDDING'       : self._handle_embedding,
            'RETRIEVE'        : self._handle_retrieve,
            'SELECTOR'        : self._handle_selector,
            'STORE'           : self._handle_store,
            'RAG-QUERY'       : self._handle_rag_query,
            'LLM-QUERY'       : self._handle_llm_query,
            'CODE'            : self._handle_code,
        }

        handler = command_handlers.get(command)
        if handler:
            handler(instruction)
        else:
            logger.warning("Unhandled command: %s", command)

    # -------------------------------------------------------------------------
    #                           STATE CHECKING
    # -------------------------------------------------------------------------
    def _check_and_handle_state(self, instruction: dict) -> bool:
        """
        Checks if the given instruction can be executed based on current
        global state, and updates state if needed.

        Returns
        -------
        bool
            True if we can proceed with execution of the command,
            False if the state condition is not met.
        """
        command = instruction.get('command')
        # Commands that are state-dependent for early gating:
        state_dependent_cmds = {
            'RAG-QUERY', 'LLM-QUERY', 'BUTTON', 'INPUT',
            'TEXT', 'HTML', 'SUBSCRIBE', 'UNSUBSCRIBE', 'CONDITION'
        }

        # If command is in state-dependent set, check state gating
        if command in state_dependent_cmds:
            required_state = instruction.get('state')
            if required_state:
                # If the required state doesn't match current state, exit
                if self.global_state != required_state:
                    logger.debug(
                        "Command '%s' requires state '%s'. Current state: '%s'. Skipping.",
                        command, required_state, self.global_state
                    )
                    return False
            else:
                # If no 'state' key but current global state isn't 'init', skip
                if self.global_state != 'init':
                    logger.debug(
                        "Command '%s' has no 'state' key but current state is '%s'. Skipping.",
                        command, self.global_state
                    )
                    return False

        # If the current state condition is met, check if we need to update state
        if instruction.get('setstate'):
            # The state for subscribed elements might be changed in callbacks,
            # but if it's not one of these special commands, we do it now.
            if command not in {'INPUT', 'SUBSCRIBE', 'UNSUBSCRIBE', 'CONDITION', 
                               'LLM-TRIGGER', 'LLM_CONTENT-TRIGGER'}:
                new_state = instruction['setstate']
                logger.debug("Transitioning to new state: %s", new_state)
                self.transition_to(new_state)

        return True

    def transition_to(self, new_state: str) -> None:
        """ 
        Transition the global state to a new state with any required side effects.
        """
        self.global_state = new_state
        self.transition_count += 1
        logger.info("Transitioned to state '%s'. Transition count: %d", new_state, self.transition_count)

    # -------------------------------------------------------------------------
    #                       COMMAND HANDLER METHODS
    # -------------------------------------------------------------------------
    def _handle_subscribe(self, instruction: dict) -> None:
        """
        Handle SUBSCRIBE command logic.
        """
        query = instruction.get('event')
        if not query:
            logger.warning("SUBSCRIBE command missing 'event' key.")
            return
        self.subscriptions.add_trigger(query, instruction)
        logger.debug("Added subscription trigger for event '%s'.", query)


    def _handle_unsubscribe(self, instruction: dict) -> None:
        """
        Handle UNSUBSCRIBE command logic.
        """
        query = instruction.get('event')
        if not query:
            logger.warning("UNSUBSCRIBE command missing 'event' key.")
            return

        anchor = instruction.get('anchor')
        if self.subscriptions.has_query(query):
            self.subscriptions.remove_trigger(query, instruction)
            # If there's also a separate subscription manager
            if hasattr(self, 'subscriptionsWithTrigger'):
                self.subscriptionsWithTrigger.remove_trigger(query, instruction)
            logger.debug("Removed subscription trigger for event '%s'.", query)




    def _handle_selector(self, instruction):
        """
        Handle a generic selector that shows a list of items and 
        lets the user pick one.
        """
        items = instruction.get("items", [])
        title = instruction.get("text", "Please select:")
        state = instruction.get("state", "")
        anchor = instruction.get("anchor", "")
        setstate = instruction.get("endstate", "")
        rag = instruction.get("rag", "")
        topk = instruction.get("topk", 2)
        scope = instruction.get("scope", "")
        
        if not items and not rag:
            return

        # handle text box
        # note rag content is not processed since the query is None
        if 'scope' in instruction and instruction['scope']:
            # `text` may be absent, so default to empty
            parameters = self.getContextArray(scope, None, 2)
            # Attempt to format text using scope-based parameters
            try:
                title = title.format(**parameters)
            except KeyError as e:
                logger.warning("Missing placeholder for text formatting: %s", e)

        text = {
        "command": "TEXT",
        "text": title,
        "text_ui": title,
        "state": state,
        }

        self.instructions.append(text)

        if rag:
            # prepare rag prompt
            rag = self.prepare_rag(instruction)
            logger.debug(f"SELECTOR: rag {rag}")
            print(f"SELECTOR: rag {rag}")
    
            embedding = None
            # get first RAG scope, only one is supported
            print(f"All scopes {scope}")
            for item in scope.split():
                content = self.contents.get(item, "")
                print(f"Comparing: {item}")
                print(f"Content: {content}")
                if isinstance(content, torch.Tensor):
                    embedding = item
                    break

            print(f"SELECTOR: got embedding {embedding}")
            logger.debug(f"SELECTOR: got embedding {embedding}")

            if embedding:
                top_docs = self.retrieve_top_k(rag, embedding, self.contents[embedding], topk)

                print(f"top docs: {top_docs}")

                if isinstance(top_docs, (set, list)):
                    for doc in top_docs:
                       if isinstance(doc, (set, list)) and len(doc) > 1:
                            doc_text = doc[0]
                            doc_link = doc[1]
                            button = {
                            "command": "BUTTON",
                            "text": doc_text,
                            "event": uuid.uuid4(),
                            "anchor": anchor,
                            "doclink":doc_link, 
                            "state": state,
                            "setstate": setstate
                            }
                            self.instructions.append(button)
        else:    

           # if items has only one item, it is assume to have a file name
            if len(items) < 2: 
                # Load from disk            
                # process file name for scopes
                file_name = items[0].get('file', "")
                new_items = []

                # TBD check allowed file access
                try:
                    with open(file_name, "r") as f:
                        new_items = json.load(f, strict=False)
                except FileNotFoundError:
                    logger.warning("SELECTOR: file '%s' not found.", file_name)
                except Exception as e:
                    logger.warning("SELECTOR: Error loading file '%s': %s", file_name, e)
                logger.debug("SELECTOR: Loaded from file: %s", new_items)
                items = new_items               

            for item in items:
                item_id = item.get("id", "")
                label = item.get("text", "Untitled")
                bstate = item.get("state", "")
            
                button = {
                "command": "BUTTON",
                "text": label,
                "event": item_id,
                "anchor": anchor,
                "state": state,
                "setstate": bstate
                }

                self.instructions.append(button)
                


    def _handle_input(self, instruction: dict) -> None:
        """
        Handle INPUT command logic.
        """
        query = instruction.get('event')
        if not query:
            logger.warning("INPUT command missing 'event' key.")
            return

        self.subscriptions.add_trigger(query, instruction)
        logger.debug("Added INPUT subscription trigger for event '%s'.", query)

    def _handle_text(self, instruction: dict) -> None:
        """
        Handle TEXT command logic (UI rendering only).
        """
        if 'scope' in instruction and instruction['scope']:
            scope = instruction['scope']
            context = self.getContext(scope, None)
            instruction['text-content'] = context
            # `text` may be absent, so default to empty
            text_template = instruction.get('text', "")
            parameters = self.getContextArray(scope, None, 2)
            # Attempt to format text using scope-based parameters
            try:
                text_content_updated = text_template.format(**parameters)
            except KeyError as e:
                logger.warning("Missing placeholder for text formatting: %s", e)
                text_content_updated = text_template
            instruction['text_ui'] = text_content_updated
        else:
            # If no scope is given, just pass the text through
            instruction['text_ui'] = instruction.get('text', "")
            instruction['text-content'] = ""

    def _handle_html(self, instruction: dict) -> None:
        """
        Handle HTML command logic (UI rendering only).
        """
        if 'scope' in instruction and instruction['scope']:
            scope = instruction['scope']
            context = self.getContext(scope, None)
            instruction['text-content'] = context
            html_template = instruction.get('html', "")
            parameters = self.getContextArray(scope, None, 2)
            try:
                text_content_updated = html_template.format(**parameters)
            except KeyError as e:
                logger.warning("Missing placeholder for HTML formatting: %s", e)
                text_content_updated = html_template
            instruction['html_ui'] = text_content_updated
        else:
            instruction['text-content'] = ""
            instruction['html_ui'] = instruction.get('html', "")

    def _handle_button(self, instruction: dict) -> None:
        """
        Handle BUTTON command logic. If no prompt, then a regular button without LLM.
        """

        query = instruction.get('prompt', "")
        anchor = instruction.get('anchor', "")
        doclink = instruction.get('doclink', "")
  
        print("Testing for button")
        if  not query and isinstance(anchor, str) and anchor:
            print(f"BUTTON {doclink}")
            # store button event (selector uses this)
            self.replace_content(anchor, doclink)

        if not isinstance(query, str) or not query:
            logger.debug("BUTTON command has no valid 'prompt'. Skipping LLM call.")
            return

        llm_name = instruction.get('model')
        scopes = instruction.get('scope', "")

        updated_prompt = self.prepare_prompt(instruction, query)
        instruction['updated-prompt'] = updated_prompt  # store for potential future use

        # Example LLM call
        llm_result = self.ask_litellm(updated_prompt, llm_name)
        self.replace_content(anchor, llm_result)

    def _handle_condition(self, instruction: dict) -> None:
        """
        Handle CONDITION command logic.
        """
        query = instruction.get('prompt', "")
        if not query:
            logger.warning("CONDITION command missing 'prompt'.")
            return

        anchor = instruction.get('anchor')
        state_ok = instruction.get('setstate')
        state_fail = instruction.get('setstate-failure')
        llm_name = instruction.get('model')

        # Add instructions for the LLM to produce a <SUCCESS> or <FAIL> terminator
        prompt = (f"{query}. You are a generative system processing inputs. "
                  f"Write an explanation for a human. End output with <SUCCESS> or <FAIL> "
                  f"depending on the given condition. If in doubt or uncertainty, choose <FAIL>. This needs to be THE LAST WORD of the output.")

        updated_prompt = self.prepare_prompt(instruction, prompt)
        llm_result = self.ask_litellm(updated_prompt, llm_name)

        print(f"LLM result: {llm_result}")

        # Check the last term of the LLM result
        term = self.get_last_term(llm_result)
        if '<FAIL>' in term:
            self.transition_to(state_fail)
            logger.debug("*** Fail triggered. New global state: %s", self.global_state)
        else:
            self.transition_to(state_ok)
            logger.debug("*** Success triggered. New global state: %s", self.global_state)

        # Store the LLM result (minus the last term) at the anchor
        cleaned_result = self.remove_last_term(llm_result)
        self.replace_content(anchor, cleaned_result)

    def _handle_agent_run(self, instruction: dict) -> None:
        """
        Handle AGENTRUN command logic.
        """
        query = instruction.get('prompt', "")
        result_anchor = instruction.get('anchor', "")
        exitstate = instruction.get('exit', "")
        llm_name = instruction.get('model')
        scopes = instruction.get('scope', "")
        agentscope = instruction.get('agentscope', "")
        file_name = instruction.get('file', "")
        prefill = instruction.get('prefill', False)

        if not isinstance(query, str) and not query:
            return
        
        # Load memory from file or from self.contents
        new_mem = []
        if file_name:
            # process file name for scopes
            file_name = self.prepare_prompt(instruction, file_name)

            # note: security checks of allowed filenames here
            if file_name in self.contents:
                # Load from memory already in self.contents
                new_mem = self.get_content_json(file_name)
                logger.debug("Loaded content from self.contents[%s].", file_name)
            else:
                # Load from disk
                try:
                    with open(file_name, "r") as f:
                        new_mem = json.load(f, strict=False)
                except FileNotFoundError:
                    logger.warning("AGENTRUN: file '%s' not found.", file_name)
                except Exception as e:
                    logger.warning("AGENTRUN: Error loading file '%s': %s", file_name, e)

        logger.debug("AGENTRUN memory: %s", new_mem)
        updated_prompt = self.prepare_prompt(instruction, query)
        if isinstance(prefill, bool) and prefill is True:   
            # The memory object for the agent
            new_memory = DynamicDistLLMMemory(new_mem, {})
            logger.debug("Prefilling agent memory.")
            new_memory.agent_prefill(updated_prompt, new_memory)
            # load the new memory here
            # TBD
        else:
            logger.debug("Executing agent run.")
            new_memory = DynamicDistLLMMemory(new_mem, {})
            new_memory.agent_run(updated_prompt, new_memory, exitstate)
            # Post-execution, retrieve or format results
            retval = new_memory.prepare_prompt(instruction, agentscope)
            self.replace_content(result_anchor, retval)


    def _handle_load(self, instruction: dict) -> None:
        """
        Handle LOAD command logic (load instructions & reset state).
        """
        file_name = instruction.get('file', "")
        new_mem = []

        if file_name:
            if file_name in self.contents:
                content = self.get_content_json(file_name)
                logger.debug("LOAD: Content found in self.contents[%s]: %s", file_name, content)
                self.load_instructions(content)
            else:
                # Load from disk
            
                # process file name for scopes
                file_name = self.prepare_prompt(instruction, file_name)

                try:
                    with open(file_name, "r") as f:
                        new_mem = json.load(f, strict=False)
                except FileNotFoundError:
                    logger.warning("LOAD: file '%s' not found.", file_name)
                except Exception as e:
                    logger.warning("LOAD: Error loading file '%s': %s", file_name, e)
                logger.debug("LOAD: Loaded from file: %s", new_mem)
                self.load_instructions(new_mem)

            # Reset global state and transition count
            self.global_state = "init"
            self.transition_count = 0

    def _handle_embedding(self, instruction: dict) -> None:
        """
        Handle EMBEDDING command logic (loading embeddings and documents).
        """
        file_name = instruction.get('file', "")
        anchor = instruction.get('anchor', "")
        content = None

        if file_name:
            if file_name in self.contents:
                content = self.get_content_json(file_name)
            else:
                try:
                    with open(file_name, "r") as f:
                        content = json.load(f)
                except FileNotFoundError:
                    logger.warning("EMBEDDING: file '%s' not found.", file_name)
                except Exception as e:
                    logger.warning("EMBEDDING: Error loading file '%s': %s", file_name, e)

        logger.debug("EMBEDDING content: %s", content)
        if content and self.embedder:
            document_embeddings = self.embedder.encode(content, convert_to_tensor=True)
            self.replace_content(anchor, document_embeddings)
            # Store original documents
            self.replace_content(anchor + "_docs", content)

    def _handle_retrieve(self, instruction: dict) -> None:
        """
        Handle RETRIEVE command logic (network retrieval).
        """
        url = instruction.get('url', "")
        compress = instruction.get('compress', False)
        anchor = instruction.get('anchor', "")
        if not url:
            logger.warning("RETRIEVE command missing 'url'.")
            return
        self.retrieve(url, anchor, compress)

    def _handle_store(self, instruction: dict) -> None:
        """
        Handle STORE command logic (save text to anchor in memory).
        """
        text = instruction.get('text', "")
        anchor = instruction.get('anchor', "")
        updated_text= self.prepare_prompt(instruction, text)
        self.replace_content(anchor, updated_text)

    def _handle_rag_query(self, instruction: dict) -> None:
        """
        Handle RAG-QUERY command logic (a type of LLM operation).
        """
        prompt_specification = ""  # placeholder or dynamic
        query = instruction.get('prompt', "")
        anchor = instruction.get('anchor', "")
        if not query:
            logger.warning("RAG-QUERY command missing 'prompt'.")
            return

        prompt = f"{query}\n{prompt_specification}"
        rag_result = self.ask_litellm(prompt)
        self.replace_content(anchor, rag_result)

    def _handle_llm_query(self, instruction: dict) -> None:
        """
        Handle LLM-QUERY command logic.
        """
        query = instruction.get('prompt', "")
        if not query:
            logger.warning("LLM-QUERY command missing 'prompt'.")
            return

        anchor = instruction.get('anchor', "")
        llm_name = instruction.get('model')
        updated_prompt = self.prepare_prompt(instruction, query)

        llm_result = self.ask_litellm(updated_prompt, llm_name)
        self.replace_content(anchor, llm_result)

    def _handle_code(self, instruction: dict) -> None:
        """
        Handle CODE command logic.
        """
        code = instruction.get('code', "")
        scope = instruction.get('scope', "")
        anchor = instruction.get('anchor', "")

        logger.debug("Executing CODE: %s", code)
        context = self.getContextArray(scope, None, 2)
        code_result = self.code_executor.execute(code, context)
        logger.debug("CODE result: %s", code_result)
        self.replace_content(anchor, code_result)


        
    def getContextArray(self, scopestring: str, query, tk) -> dict:
        """
        Provide a dictionary based on the scopestring.
        Each key-value pair corresponds to an item found in self.contents.
        Ensures that each item is a list of dictionaries.
        """
        context_dict = {}
        scope_items = scopestring.split()
        logger.debug(f"getContextArray {scope_items}")
        for item in scope_items:
            #print(f"Item in content {item in self.contents}")
            if item not in self.contents:
               context_dict[item] = None
            else:
                # Ensure the content is parsed correctly and is a list
                try:
                    content = self.contents[item]
                    #print(f"Adding {content}")
                    if isinstance(content, dict):
                        context_dict[item] = content  
                    elif isinstance(content, list):
                        context_dict[item] = content  # Leave lists as they are
                    elif isinstance(content, tuple):
                        context_dict[item] = list(content)  # Convert tuple to list
                    elif isinstance(content, str):
                        context_dict[item] = str(content)  # Convert tuple to list
                    elif isinstance(content, torch.Tensor):
                        if query:
                            # embedding
                            top_docs = self.retrieve_top_k(query, item, content, tk)
                            #print(f"ContextArray: got {top_docs}")
                            if isinstance(top_docs, (set, list)):
                                # Convert the set or list to a string with newline separation
                                context_dict[item] = "\n\n".join(str(doc) for doc in top_docs)
                            else:
                                # Handle other cases if needed, e.g., raise an error or assign a default value
                                context_dict[item] = str(top_docs)  # Convert to string if it's not iterable
                    else:
                        #print(f"Content type {type(content)}")
                        #print(f"{content}")
                        raise ValueError("Content must be a dictionary or list of dictionaries.")
                except json.JSONDecodeError:    
                    context_dict[item] = self.contents[item]
        return context_dict
        
        
    def retrieve_top_k(self, query, item, document_embeddings, k):
        """
        Given a query string, this function returns the top-k most similar documents.
        query: The query string
        item: The anchor for the original documents
        document_embeddings: The document embeddings
        """

        # Regular expression to find and remove content in curly braces
        cleaned_query = re.sub(r'\{.*?\}', '', query)

        logger.debug(f"--- retrieve_top_k query {query}")
        # Encode the query
        query_embedding = self.embedder.encode(cleaned_query, convert_to_tensor=True)
    
        # Compute similarity scores
        similarities = util.pytorch_cos_sim(query_embedding, document_embeddings)
        # similarities is a 1 x N tensor
    
        # Get the top-k documents (descending order)
        top_k_indices = similarities[0].topk(k).indices
     
        logger.debug(f"retrieve_top_k: {top_k_indices}")
        documents = self.get_content(item+"_docs")

        # Return the selected documents
        retrieved_docs = [documents[idx] for idx in top_k_indices]
        return retrieved_docs


        
    def getContext(self, scopestring, query):
        content = ""
        # Split the scopestring into individual items
        scope_items = scopestring.split()

        # Iterate over the dictionary
        for item in scope_items:
            if item in self.contents:
                if item in self.contents:
                    if isinstance(item, torch.Tensor):
                        if query:
                            # embedding
                            top_docs = self.retrieve_top_k(query, item, self.contents[item], 2)
                            content += "\n\n".join(top_docs)
                    else:
                        content += json.dumps(self.contents[item])+"\n"
        return content
    
    
        

    def retrieve_and_clean_url(self, url):
      try:
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        # Get text and remove leading/trailing whitespace
        text = soup.get_text(separator=' ')

        # Further clean up the text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

      except requests.RequestException as e:
        logger.debug(f"Error fetching URL: {e}")
        return None




    def retrieve(self, url, anchor, compress):
        text = self.retrieve_and_clean_url(url)
        prompt2 = f"{compress}\Content:{text}"
        llm_result = self.ask_litellm(prompt2)
        self.replace_content(anchor, llm_result)


# -----------------------------------------------------------


    def get_first_term(self, string):
        # Strip leading/trailing whitespace and split the string
        stripped_string = string.strip()
        if stripped_string:
            return stripped_string.split()[0]
        return None
         
         
    def get_last_term(self, string):
        # Strip leading/trailing whitespace and split the string
        stripped_string = string.strip()
        if stripped_string:
            return stripped_string.split()[-1]
        return None

    def remove_last_term(self, string):
        # Strip leading/trailing whitespace and split the string into words
        stripped_string = string.strip()
        words = stripped_string.split()
    
        # Check if there are at least two words
        if len(words) > 1:
            return ' '.join(words[:-1])  # Join all words except the last one
        elif len(words) == 1:
            return ''  # If there's only one word, return an empty string

        return string  # Return the original string if it's empty



    def react_to_event(self, event_name, event_data):
        """
        React to a given event by updating subscribed triggers and optionally transitioning state.

        Parameters
        ----------
        event_name : str
            Name/key of the event being triggered.
        event_data : Any
            Data associated with the event to store or process.
        """
        logger.info("Reacting to event '%s' with data: %s", event_name, event_data)

        # If there's no subscription for this event, exit early
        if not self.subscriptions.has_query(event_name):
            logger.debug("No subscription found for event '%s'; nothing to do.", event_name)
            return

        # Fetch all triggers/instructions tied to this event
        triggers = self.subscriptions.get_triggers(event_name)
        if not triggers:
            logger.debug("No triggers are associated with event '%s'.", event_name)
            return

        # Process each instruction that is subscribed to this event
        for instruction in triggers:
            if not instruction or not isinstance(instruction, dict):
                logger.debug("Skipping invalid or empty instruction for event '%s'.", event_name)
                continue

            # Retrieve the anchor and the replace flag (with a default of False)
            anchor = instruction.get('anchor')
            replace_flag = instruction.get('replace', False)

            # Update or append event data in the content store
            try:
                self.update_content_json(anchor, event_data, replace_flag)
                logger.debug(
                    "Updated content at anchor='%s' with event data. replace_flag=%s", 
                    anchor, replace_flag
                )
            except Exception as e:
                logger.warning("Error updating content at anchor='%s': %s", anchor, e)

            # Check if we need to transition to a new state
            new_state = instruction.get('setstate')
            if new_state:
                logger.debug("Instruction requests transition to new state: '%s'.", new_state)
                self.transition_to(new_state)




    def notify(self, event_name, event_data ):
         logger.debug("Received server event %s",event_name)
         react_to_event(self, event_name, event_data)
         

# --------------------------------------------------

    def get_contents(self):
        return json.dumps(self.contents)
    
    def get_contents_json(self):
        return self.contents
        
    def get_instructions(self):
        return self.instructions
        
    def get_contents_UI_json(self):
        ucontent = {}
        for element in self.contents:
            if not isinstance(self.contents[element] , torch.Tensor): 
                ucontent[element] = self.contents[element] 
        return ucontent
        


    def get_instructions_UI_current_state(self):
        """
        Return the subset of instructions that:
        - Have commands in {'INPUT', 'TEXT', 'BUTTON', 'HTML'}
        - Either match the global state explicitly OR (if no state key is found) 
            are included when global state is 'init'.
        Also ensure each instruction has a unique 'id' key.
        """
        logger.debug("get_instructions_UI_current_state(): current global state: %s", self.global_state)

        instruction_state = []
        ui_commands = {'INPUT', 'TEXT', 'BUTTON', 'HTML'}

        for instruction in self.instructions:
            # Ensure every instruction has a unique ID
            if 'id' not in instruction:
                instruction['id'] = str(uuid.uuid4())

            # We only care about instructions of these command types
            command = instruction.get('command')
            if command in ui_commands:
                state_required = instruction.get('state')

                # If instruction specifies a state, it must match the current global state
                if state_required:
                    logger.debug("Comparing instruction state '%s' to global state '%s'.",
                                state_required, self.global_state)
                    if self.global_state == state_required:
                        logger.debug("State match found. Adding instruction with id=%s", instruction['id'])
                        instruction_state.append(instruction)
                # If no state is specified but global state is 'init', also include
                elif self.global_state == 'init':
                    logger.debug("Instruction has no specific state. Global state is 'init'. Adding id=%s", 
                                instruction['id'])
                    instruction_state.append(instruction)

        logger.debug("Filtered UI instructions: %s", instruction_state)
        return instruction_state


    def get_instructions_UI_byID_current_state(self, instr_id):
        """
        Given an instruction ID, return the matching UI instruction from self.instructions.
        If no match is found, return None.
        """
        logger.debug("get_instructions_UI_byID_current_state(): Searching for instruction with id='%s'.", instr_id)

        for instruction in self.instructions:
            # Safely get the 'id' field
            current_id = instruction.get('id')
            if current_id == instr_id:
                logger.debug("Found instruction with id='%s'.", instr_id)
                return instruction

        logger.debug("No matching instruction found for id='%s'.", instr_id)
        return None


    def get_instructions_current_state(self):
        """
        Return all instructions that:
        - Either specify a state matching the current global state
        - Or have no state key when the global state is 'init'.
        """
        logger.debug("get_instructions_current_state(): current global state: %s", self.global_state)
        
        instruction_state = []
        for instruction in self.instructions:
            state_required = instruction.get('state')
            if state_required:
                logger.debug("Comparing instruction state '%s' to global state '%s'.", 
                            state_required, self.global_state)
                if self.global_state == state_required:
                    logger.debug("State match found. Adding instruction with id=%s.", instruction.get('id'))
                    instruction_state.append(instruction)
            elif self.global_state == 'init':
                logger.debug("Instruction has no specific state. Global state is 'init'. Adding id=%s.", 
                            instruction.get('id'))
                instruction_state.append(instruction)

        logger.debug("Filtered instructions for current state: %s", instruction_state)
        return instruction_state

  
        
    def replace_content(self, anchor, new_content):
        for key, value in self.contents.items():
            if key == anchor:
                self.contents[key] = new_content
                break
        else:
            self.contents[anchor] = new_content



    def get_content(self, anchor):
        if anchor in self.contents:
            return self.contents[anchor]
        else:
            logger.debug("Did not find content")
            return {}


    def get_content_json(self, anchor):
        if anchor in self.contents:
            return self.extract_json_from_llm_output(self.contents[anchor])
        else:
            logger.debug("Did not find content")
            return {}



    def update_content_json(self, anchor, json_str: str, replace=False) -> None:
        """
        Update the contents dictionary with data from a JSON string.
        Ensure that all content is stored as a list of dictionaries.
        """
        # Ensure new_data is correctly parsed
        if isinstance(json_str, str):
            try:
                new_data = json.loads(json_str,strict=False)
                logger.debug(f"Parsed new_data from string: {new_data} (type: {type(new_data)})")
            except json.JSONDecodeError as e:
                logger.debug(f"Error parsing JSON string: {e}")
                logger.debug(json_str)
                new_data = json_str
                self.contents[anchor] = new_data
                return
        elif isinstance(json_str, dict) or isinstance(json_str, list):
            new_data = json_str
            logger.debug(f"Using new_data as provided: {new_data} (type: {type(new_data)})")
        else:
            logger.debug("Input must be a JSON string, dictionary, or list")
            return

        # Transform new_data into a list if it is not already
        if isinstance(new_data, dict):
            new_data = [new_data]
        elif not isinstance(new_data, list):
            logger.debug(f"Invalid new_data type: {type(new_data)}")
            return

        # Handle updating the content based on its current type
        if anchor in self.contents:
            existing_content = self.contents[anchor]
            logger.debug(f"Existing content before update: {existing_content} (type: {type(existing_content)})")

            # Parse existing content if it's a JSON string
            if isinstance(existing_content, str):
                try:
                    existing_content = json.loads(existing_content,strict=False)
                    logger.debug(f"Parsed existing_content: {existing_content} (type: {type(existing_content)})")
                except json.JSONDecodeError as e:
                    logger.debug(f"Error parsing existing content: {e}")
                    return

            # Ensure existing content is a list
            if isinstance(existing_content, dict):
                existing_content = [existing_content]
            elif not isinstance(existing_content, list):
                logger.debug(f"Invalid existing_content type: {type(existing_content)}")
                return

            # Extend the existing content list with the new data list
            logger.debug(f"Before extending: {existing_content}")
            if replace:
                existing_content = new_data           
            else:            
                existing_content.extend(new_data)
            logger.debug(f"After extending: {existing_content}")

            self.contents[anchor] = existing_content
        else:
            self.contents[anchor] = new_data
            logger.debug(f"Added new anchor with content: {self.contents[anchor]}")

        logger.debug(f"Updated content at {anchor}: {self.contents[anchor]} (type: {type(self.contents[anchor])})")

            
    
# LLM invocation

    def ask_litellm(self, prompt, llm_name=None):
        try:
            if not llm_name:
                llm_name = self.default_llm_name
            logger.debug("LITELLM PROMPT: %s",prompt)
            #litellm.set_verbose=True
            response = completion(
                model=llm_name,
                messages=[{"content": prompt, "role": "user"}],
                api_base="http://localhost:11434"
            )
            
            final_response=response.choices[0].message.content
            
            logger.debug("LITELLM RESPONSE: %s",final_response)            
            return final_response
        except Exception as e:
            return str(e)    
        

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
    
                fixed_json_string = self.clean_json_string(json_string)

                logger.debug(f"JSON STRING: %s",fixed_json_string)

                # For now we use just the raw LLM output       
                # Convert JSON string to Python dictionary or list
                python_data = json.loads(raw_output,strict=False) #fixed_json_string)
            
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
        cleaned_string = re.sub(r'\s{2,}', ' ', cleaned_string)
    
        # Escape necessary characters (e.g., newlines in values)
        cleaned_string = cleaned_string.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    
        # Remove extraneous whitespace around JSON delimiters
        cleaned_string = re.sub(r'\s*([\{\}\[\]:,])\s*', r'\1', cleaned_string)
    
        # Remove control characters
        cleaned_string = re.sub(r'[\x00-\x1F\x7F]', '', cleaned_string)
    
        cleaned_string = re.sub(r'}\s*\n\s*\]', '}]', cleaned_string)
   
        cleaned_string = cleaned_string.replace('}\n]', '}]')

        cleaned_string = cleaned_string.replace('}\\n]', '}]')

  
        return cleaned_string


    def add_content(self, anchor, new_content):
        if anchor in self.contents:
            self.contents[anchor] += f"\n{new_content}"
        else:
            self.contents[anchor] = new_content


# Agent functions

    def agent_run(self, prompt_background, memory, exit_state):
      """
      Execute the agent script in a loop, handling 'BUTTON' and 'INPUT' commands
      via an LLM. This function:
        - Executes all non-BUTTON commands for the current state to set things up.
        - Then enters a loop:
            * Checks for and executes any pending non-BUTTON commands.
            * Detects state changes and updates instructions accordingly.
            * Gathers any UI instructions that contain 'BUTTON' or 'INPUT'.
            * Uses the LLM to decide which command (and optional input) to invoke next.
            * Executes that command or reacts to the INPUT event.
        - Exits when there are no more interactive UI elements to handle.
      """

      # Step 1: Get the initial instructions for the current state and execute them
      initial_instructions = self.get_instructions_current_state()
      for inst in initial_instructions:
          if 'command' in inst and "BUTTON" not in inst['command']:
              self.execute_command(inst)

      # Step 2: Start the simulated UI loop
      state_instructions = memory.get_instructions_current_state()
      current_state = memory.get_global_state()

      # note that the script may go back to arbitrary states, also init state
      # this can result in an infinite loop
      # thus we require an explicit end state

      exits = exit_state.split(" ")  # ["done", "exit", "stop"]

      loop_counter=0
      loop = True
      while loop:
          # Execute non-BUTTON commands in the current state instructions
          for inst in state_instructions:
              if 'command' in inst and "BUTTON" not in inst['command']:
                  memory.execute_command(inst)

              # Check if the global state has changed
              new_state = memory.get_global_state()
              if new_state != current_state:
                  logger.debug(f"State changed from {current_state} to {new_state}")
                  # Extend our state instructions with whatever the new state requires
                  state_instructions.extend(memory.get_instructions_current_state())
                  current_state = new_state
                  if new_state in exits:
                      loop = False
                      break

          # Gather UI instructions (BUTTON/INPUT)
          ui_instructions = memory.get_instructions_UI_current_state()
 
          # Build up a list of interactive instructions we need to present to the LLM
          interactive_instructions = []
          subset_idx=0
          for idx, inst in enumerate(ui_instructions):
              if 'command' in inst:
                  cmd = inst['command']
                  if "BUTTON" in cmd or "INPUT" in cmd:
                      interactive_instructions.append((subset_idx, inst))
                      subset_idx+=1

          # If there are no BUTTON or INPUT commands, we assume we're done
          if not interactive_instructions:
              loop = False
              break

          # Build the prompt for the LLM
          instructions_str = "\n".join(
              [f"ID {idx}: {instr}" for idx, instr in interactive_instructions]
          )
          
          loop_counter+=1
          if loop_counter > 255:
              logger.debug("AgentRun: loop counter exceeded")
              loop = False
              break

          prompt = f"""
You are an agent executing a script. The script is based on JSON commands and
proceeds via state-based UI views. Here is the current UI view. You must output
the command ID number and, if needed, the INPUT data to move the script forward
toward the project objective. If you are asked to evaluate something, consider 
the user intent and the provided data. If evaluation is not possible, document
the assessment in your response to the INPUT element.

**Prioritize filling in 'INPUT' elements** when present. Use the given user
intent for any data that needs to be filled and do not hallucinate data outside
the given context.

User intent: {prompt_background}

--- UI View ---
{instructions_str}

#--- Full Script (for chain-of-thought reference) ---
{state_instructions}

IMPORTANT: Provide your response as (only use IDs provided in the UI view). 
The last line needs to be as follows without any preamble or closing element:
<numeric ID number in the UI view above> <input data for INPUT commands, string>
Example (for INPUT element 2): 
2 The answer is ...
"""
# Full script not included due to LLM limitations in handling big scripts

          # Invoke the LLM to decide on next step
          llm_result = self.ask_litellm(prompt, "ollama/llama3.3:latest")

          last_sentence = self.get_last_sentence(llm_result)

          # Extract the chosen ID (and optional input text) from the LLM response
          chosen_id, input_data = self.extract_number_and_string(last_sentence)
          logger.debug(f"Testing for chosen id {chosen_id} len {len(interactive_instructions)}")
     
          # Validate the choice
          if not (0 <= chosen_id < len(interactive_instructions)):
              logger.debug(f"Invalid choice: {chosen_id}. Stopping execution.")
              return

          _, chosen_command = interactive_instructions[chosen_id]
          
          # Check the command type
          if "BUTTON" in chosen_command.get('command', ''):
              self.execute_command(chosen_command)
          elif "INPUT" in chosen_command.get('command', ''):
              # `input_data` is any text the LLM provided for the INPUT
              self.react_to_event(chosen_command.get("event"), input_data)
          else:
              logger.debug("LLM returned an invalid command ID; stopping execution.")
              loop = False


    def agent_prefill(self, prompt_background, memory):
      """
      Prefill agent template (INPUT elements)
      """

      instructions = self.get_instructions()
 
      # Build up a list of interactive instructions we need to present to the LLM
      interactive_instructions = []
      subset_idx=0
      for idx, inst in enumerate(instructions):
          if 'command' in inst:
              cmd = inst['command']
              if "BUTTON" in cmd or "INPUT" in cmd:
                  interactive_instructions.append((subset_idx, inst))
                  subset_idx+=1

      # If there are no BUTTON or INPUT commands, we assume we're done
      if not interactive_instructions:
          return

      # Build the prompt for the LLM
      instructions_str = "\n".join(
          [f"ID {idx}: {instr}" for idx, instr in interactive_instructions]
      )
          
      prompt = f"""
You are an agent prefilling a script. The script is based on JSON commands and
proceeds via state-based UI views. Here is the current script. Given your input data, 
you must write prefilled text for the INPUT fields if that is possible. You must output
the command ID number and the INPUT data to move the script forward
toward the project objective.

User intent: {prompt_background}

--- UI View ---
{instructions_str}

IMPORTANT: Provide your response as (only use IDs provided in the UI view). 
The last line needs to be as follows without any preamble or closing element:
<numeric ID number in the UI view above> <input data for INPUT commands, string>
Example (for INPUT element 2): 
2 The answer is ...
"""
# Full script not included due to LLM limitations in handling big scripts
#--- Full Script (for chain-of-thought reference) ---
#{state_instructions}

      # Invoke the LLM to decide on next step
      llm_result = self.ask_litellm(prompt, "ollama/llama3.3:latest")

      last_sentence = self.get_last_sentence(llm_result)

      # Extract the chosen ID (and optional input text) from the LLM response
      chosen_id, input_data = self.extract_number_and_string(last_sentence)
      logger.debug(f"Testing for chosen id {chosen_id} len {len(interactive_instructions)}")
     
      # Validate the choice
      if not (0 <= chosen_id < len(interactive_instructions)):
          logger.debug(f"Invalid choice: {chosen_id}. Stopping execution.")
          return

      _, chosen_command = interactive_instructions[chosen_id]
          
       # Check the command type
      if "INPUT" in chosen_command.get('command', ''):
            # `input_data` is any text the LLM provided for the INPUT 
            logger.debug(f"Pre-filled {input_data}")
            #    self.react_to_event(chosen_command.get("event"), input_data)
      else:
            logger.debug("LLM returned an invalid command ID; stopping execution.")
              
        
