#!/usr/bin/env python3
import os
import ast


def get_python_file_details(filepath):
    """
    Parses a single Python file using the Abstract Syntax Tree (AST) module
    to extract detailed information about its structure, including all
    available docstrings.

    This function extracts:
    - Module-level docstring
    - Function and async function definitions with arguments and docstrings
    - Class definitions with docstrings and method details
    - Import statements
    - Docstrings inside the __main__ execution block
    """
    details = {
        "purpose": "Purpose not explicitly defined (add a module-level docstring).",
        "functions": [],
        "classes": [],
        "imports": [],
        "main_docstring": None
    }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=filepath)

        # ---------------- MODULE DOCSTRING ----------------
        module_doc = ast.get_docstring(tree)
        if module_doc:
            details["purpose"] = module_doc

        # ---------------- WALK AST ----------------
        for node in ast.walk(tree):

            # -------- FUNCTIONS (sync + async) --------
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                func_docstring = ast.get_docstring(node)
                func_args = [arg.arg for arg in node.args.args]

                details["functions"].append({
                    "name": func_name,
                    "arguments": func_args,
                    "docstring": func_docstring if func_docstring else "No docstring."
                })

            # -------- CLASSES --------
            elif isinstance(node, ast.ClassDef):
                class_docstring = ast.get_docstring(node)
                methods = []

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_docstring = ast.get_docstring(item)
                        method_args = [
                            arg.arg for arg in item.args.args
                            if arg.arg not in ("self", "cls")
                        ]

                        methods.append({
                            "name": item.name,
                            "arguments": method_args,
                            "docstring": method_docstring if method_docstring else "No docstring."
                        })

                details["classes"].append({
                    "name": node.name,
                    "docstring": class_docstring if class_docstring else "No docstring.",
                    "methods": methods
                })

            # -------- IMPORTS --------
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    details["imports"].append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    if module:
                        details["imports"].append(f"{alias.name} from {module}")
                    else:
                        details["imports"].append(alias.name)

            # -------- __MAIN__ DOCSTRING (manual extraction) --------
            elif isinstance(node, ast.If):
                if (
                    isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and node.test.left.id == "__name__"
                ):
                    for item in node.body:
                        if (
                            isinstance(item, ast.Expr)
                            and isinstance(item.value, ast.Constant)
                            and isinstance(item.value.value, str)
                        ):
                            details["main_docstring"] = item.value.value
                            break

    except SyntaxError as e:
        details["purpose"] = f"Syntax Error: {e}"
    except Exception as e:
        details["purpose"] = f"Error parsing file: {e}"

    return details


def generate_python_summary_advanced(directory_path, output_filename="python_ast_summary.md"):
    """
    Generates a comprehensive Markdown summary of Python files in a directory,
    including all extracted docstrings and structural information.
    """
    summary = "# Detailed Python Files Summary (AST Parsing)\n\n"
    summary += f"Directory scanned: `{directory_path}`\n\n"
    summary += "## Table of Contents\n\n"

    file_details = []

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, directory_path)

                details = get_python_file_details(filepath)
                details["path"] = relpath
                details["name"] = file
                file_details.append(details)

                anchor = relpath.replace("/", "").replace("\\", "").replace(".", "").lower()
                summary += f"- [{relpath}](#{anchor})\n"

    summary += "\n---\n\n"

    for detail in file_details:
        anchor = detail["path"].replace("/", "").replace("\\", "").replace(".", "").lower()

        summary += f"## <a name=\"{anchor}\"></a> `{detail['path']}`\n\n"
        summary += f"**Module Purpose:**\n\n```\n{detail['purpose']}\n```\n\n"

        if detail["main_docstring"]:
            summary += "**Main Execution Block Purpose:**\n\n"
            summary += f"```\n{detail['main_docstring']}\n```\n\n"

        if detail["imports"]:
            summary += "**Imports:**\n\n"
            for imp in detail["imports"]:
                summary += f"- `{imp}`\n"
            summary += "\n"

        if detail["functions"]:
            summary += "**Functions:**\n\n"
            for func in detail["functions"]:
                summary += f"### `{func['name']}({', '.join(func['arguments'])})`\n"
                summary += f"```\n{func['docstring']}\n```\n\n"
        else:
            summary += "**Functions:** None found.\n\n"

        if detail["classes"]:
            summary += "**Classes:**\n\n"
            for cls in detail["classes"]:
                summary += f"### `class {cls['name']}`\n"
                summary += f"```\n{cls['docstring']}\n```\n\n"

                if cls["methods"]:
                    summary += "**Methods:**\n\n"
                    for method in cls["methods"]:
                        summary += f"- `{method['name']}({', '.join(method['arguments'])})`\n"
                        summary += f"  ```\n  {method['docstring']}\n  ```\n"
                    summary += "\n"
        else:
            summary += "**Classes:** None found.\n\n"

        summary += "---\n\n"

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Summary written to: {output_filename}")


if __name__ == "__main__":
    """
    Command-line entry point for the AST documentation generator.
    Accepts a directory path and optional output filename.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a detailed Markdown summary of Python files using AST parsing."
    )
    parser.add_argument("directory", help="Directory containing Python files")
    parser.add_argument("-o", "--output", default="python_ast_summary.md")

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Directory not found: {args.directory}")
        exit(1)

    generate_python_summary_advanced(args.directory, args.output)
