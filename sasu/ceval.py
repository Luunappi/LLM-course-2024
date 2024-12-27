import ast
import json
import math
import statistics
import re
from collections import defaultdict
import pandas as pd


# Define a whitelist of safe built-in functions and modules
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
    # Add more functions as needed
}

SAFE_STATISTICS = {
    'mean': statistics.mean,
    'median': statistics.median,
    'mode': statistics.mode,
    'stdev': statistics.stdev
    # Add more functions as needed
}

SAFE_STRING_METHODS = {
    'lower': str.lower,
    'upper': str.upper,
    'capitalize': str.capitalize,
    'title': str.title,
    'split': str.split,
    'join': str.join,
    'replace': str.replace
    # Add more methods as needed
}

SAFE_RE = {
    'compile': re.compile,
    'match': re.match,
    'search': re.search,
    'findall': re.findall,
    'sub': re.sub,
    'split': re.split
    # Add more functions as needed
}

SAFE_COLLECTIONS = {
    'defaultdict': defaultdict,
    # Add more functions as needed
}

SAFE_PANDAS = {
    'DataFrame': pd.DataFrame,
    'Series': pd.Series
    # Add more functions as needed
}

SAFE_MODULES = {
    'math': math,
    'statistics': statistics,
    're': re,
    'collections': defaultdict,
    'pandas': pd,
    'sorted': sorted
}


def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    print(f"Safe import called for: {name}")  # Debug statement
    if name in SAFE_MODULES:
        return SAFE_MODULES[name]
    raise ImportError(f"Import of {name} is not allowed")


SAFE_GLOBALS = {
    'sorted': sorted,
    '__builtins__': {
        'abs': abs,
        'divmod': divmod,
        'pow': pow,
        'round': round,
        'len': len,
        'str': str,
        'format': format,
        'sum': sum,
        '__import__': safe_import,  # Use custom import function
    }
}


class SafeEvalVisitor(ast.NodeVisitor):
    """Visitor class to ensure the code only contains safe expressions."""

    def visit(self, node):
        # Ensure specific visitor methods are called
        super().visit(node)
        
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            raise ValueError(f"Unsafe operation detected: {ast.dump(node)}")
        
    def visit_Import(self, node):
        print(f"Visit Import: {ast.dump(node)}")  # Debug statement
        for alias in node.names:
            if alias.name not in SAFE_MODULES:
                raise ValueError(f"Unsafe operation detected: Import(names={node.names})")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        print(f"Visit ImportFrom: {ast.dump(node)}")  # Debug statement
        if node.module not in SAFE_MODULES:
            raise ValueError(f"Unsafe operation detected: ImportFrom(module={node.module})")
        self.generic_visit(node)


        


def parse_params(params_str):
    """
    Parse the input parameters which can be a string or a dictionary.
    If it's a string, parse it with ast.literal_eval.
    If it's already a dictionary, use it directly.
    Convert the result to a dictionary.
    """
    try:
        if isinstance(params_str, str):
            params = ast.literal_eval(params_str)
        elif isinstance(params_str, dict):
            params = params_str
        else:
            raise ValueError("Input must be a string or a dictionary")

        # Further parse any nested JSON strings in params
        for key, value in params.items():
            if isinstance(value, str):
                try:
                    params[key] = json.loads(value)
                except json.JSONDecodeError:
                    continue

        return params
    except (ValueError, SyntaxError, json.JSONDecodeError) as e:
        print(f"Error parsing parameters: {e}")
        return None

import ast

def execute_code_safely(code_str, params_str):
    params = parse_params(params_str)
    if params is None:
        return "Error parsing parameters", []

    try:
        # Parse the code to an AST (Abstract Syntax Tree)
        tree = ast.parse(code_str, mode='exec')
        
        # Use the visitor to ensure no unsafe operations are present
        SafeEvalVisitor().visit(tree)
        
        # Define a dictionary to hold local variables during exec
        local_vars = {
            'content': [],
        }

        # Compile the AST to a code object
        code_obj = compile(tree, filename="<string>", mode='exec')

        # Extract values from params to pass as positional arguments
        args = list(params.values())
        print(f"ARGS: {args}")
   
        # Execute the code in a restricted environment
        exec(code_obj, SAFE_GLOBALS, local_vars)

        # Debugging: check the content of local_vars
        print(f"Local vars after exec: {local_vars.keys()}")
        
        # Assuming the code defines a function named `main_function`
        if 'main_function' in local_vars:
            # Pass the values as positional arguments
            result = local_vars['main_function'](*args)
            return result, local_vars['content']
        else:
            raise ValueError("The provided code does not define a 'main_function'. Check for typos or function scope.")
    
    except Exception as e:
        return f"Error executing code: {e}", []

