import os
import ast
import argparse

def analyze_python_file_for_docstring_suggestions(filepath):
    """
    Analyzes a Python file to suggest docstrings for the module, functions, and classes.
    Args:
        filepath (str): The path to the Python file.
    Returns:
        dict: A dictionary containing suggested docstrings.
              Keys are 'module', 'functions', 'classes'.
    """
    suggestions = {
        "module": None,
        "functions": [],
        "classes": []
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)

        # Module-level docstring suggestion
        current_module_doc = ast.get_docstring(tree)
        if not current_module_doc:
            suggestions["module"] = "Module for [briefly describe the module's purpose].\n\n" \
                                    "This module provides [more detailed description of functionality, components, etc.]."
        else:
            suggestions["module"] = current_module_doc # Keep existing if it exists

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                func_docstring = ast.get_docstring(node)
                func_args = [arg.arg for arg in node.args.args]
                
                if func_name == '__init__': # Special handling for constructor
                    suggested_doc = f"Initializes the {node.parent.name} object." if hasattr(node, 'parent') and hasattr(node.parent, 'name') else "Initializes the object."
                    if func_args:
                        # Exclude 'self'
                        args_for_doc = [arg for arg in func_args if arg != 'self']
                        if args_for_doc:
                            suggested_doc += "\n\nArgs:\n"
                            for arg in args_for_doc:
                                suggested_doc += f"    {arg} ([type]): [Description of {arg}].\n"
                else:
                    suggested_doc = f"Brief description of what `{func_name}` does.\n\n"
                    if func_args:
                        # Exclude 'self' or 'cls' for methods
                        args_for_doc = [arg for arg in func_args if arg not in ('self', 'cls')]
                        if args_for_doc:
                            suggested_doc += "Args:\n"
                            for arg in args_for_doc:
                                suggested_doc += f"    {arg} ([type]): [Description of {arg}].\n"
                    suggested_doc += "\nReturns:\n    [type]: [Description of return value].\n"
                    suggested_doc += "\nRaises:\n    [ExceptionType]: [Condition under which exception is raised]."

                suggestions["functions"].append({
                    "name": func_name,
                    "suggestion": suggested_doc,
                    "has_docstring": bool(func_docstring)
                })

            elif isinstance(node, ast.ClassDef):
                class_name = node.name
                class_docstring = ast.get_docstring(node)
                
                suggested_doc = f"Represents a [briefly describe what the `{class_name}` class represents].\n\n" \
                                "This class handles [more detailed description of responsibilities or state]."

                suggestions["classes"].append({
                    "name": class_name,
                    "suggestion": suggested_doc,
                    "has_docstring": bool(class_docstring)
                })

        # Add parent to nodes for __init__ detection. This is not natively in ast.walk
        # but useful for better __init__ docstring suggestions.
        # This is a bit of a hack, a full AST visitor pattern would be cleaner.
        for child_node in tree.body:
            if isinstance(child_node, ast.ClassDef):
                for item in child_node.body:
                    if isinstance(item, ast.FunctionDef):
                        item.parent = child_node # Attach parent for __init__ context

    except SyntaxError as e:
        suggestions["module"] = f"Error: Syntax Error in file - {e}"
    except Exception as e:
        suggestions["module"] = f"Error: Failed to parse file - {e}"

    return suggestions

def print_docstring_suggestions(filepath, suggestions):
    """
    Prints the generated docstring suggestions in a formatted way.
    """
    output = []
    output.append(f"### Docstring Suggestions for `{filepath}` ###\n")
    output.append("---")

    # Module Docstring
    output.append("\n**Module Docstring:**\n")
    if suggestions["module"] and "Error: " not in suggestions["module"]:
        output.append(f'```python\n"""\n{suggestions["module"]}\n"""\n```')
    else:
        output.append(f'```\n{suggestions["module"]}\n```') # Print error or existing doc

    # Functions
    output.append("\n**Function Docstrings:**\n")
    if not suggestions["functions"]:
        output.append("No functions found.\n")
    else:
        for func in suggestions["functions"]:
            status = " (Existing Docstring)" if func["has_docstring"] else " (SUGGESTION - Missing Docstring)"
            output.append(f"\n#### `def {func['name']}` {status}\n")
            output.append(f'```python\n"""\n{func["suggestion"]}\n"""\n```')
    
    # Classes
    output.append("\n**Class Docstrings:**\n")
    if not suggestions["classes"]:
        output.append("No classes found.\n")
    else:
        for cls in suggestions["classes"]:
            status = " (Existing Docstring)" if cls["has_docstring"] else " (SUGGESTION - Missing Docstring)"
            output.append(f"\n#### `class {cls['name']}` {status}\n")
            output.append(f'```python\n"""\n{cls["suggestion"]}\n"""\n```')
    
    return "\n".join(output)


# --- Main execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate suggested docstrings for a single Python file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "filepath",
        help="The path to the Python file for which to generate docstring suggestions."
    )
    parser.add_argument(
        "-o", "--output",
        help="Optional: Path to an output Markdown file to save the suggestions. "
             "If not provided, suggestions will be printed to stdout."
    )
    
    args = parser.parse_args()

    if not os.path.isfile(args.filepath):
        print(f"Error: File '{args.filepath}' not found.")
        exit(1)
    
    suggestions = analyze_python_file_for_docstring_suggestions(args.filepath)
    formatted_output = print_docstring_suggestions(args.filepath, suggestions)

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            print(f"Docstring suggestions saved to '{args.output}'.")
        except IOError as e:
            print(f"Error: Could not write to output file '{args.output}': {e}")
            exit(1)
    else:
        print(formatted_output)