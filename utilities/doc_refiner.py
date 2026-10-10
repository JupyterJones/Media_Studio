#!/usr/bin/env python3
"""
Flask-based Code Suggestion and Completion Engine with SQLite Persistence
and Local LLM (Ollama) Integration.

This application provides a web interface for storing, searching, and
suggesting Python/Flask code snippets based on partial user input.
It is designed to act as a lightweight, local-first coding assistant
powered by an Ollama-hosted language model.

Core features:

- Web UI for entering partial code and receiving contextual suggestions
- SQLite-backed persistence layer for storing and editing code snippets
- Pattern-based suggestion engine using the last words of user input
- Optional integration with a local Ollama LLM for structured analysis
- Atomic JSON and TXT prompt collection management
- File-based logging system using a custom `logit()` utility
- Full CRUD support for stored functions via Flask routes
- Inline HTML templates rendered directly from Python for portability
- Safe database initialization and one-time bulk ingestion of source data
- Designed for offline, Docker-based, or air-gapped development workflows

Key routes:

- `/`                : Main code suggestion interface
- `/save`             : Generate suggestions from submitted code
- `/save_code`        : Persist user-submitted code into SQLite
- `/view_functions`   : View and edit all stored code snippets
- `/update_function`  : Update a stored function via form submission
- `/readlog`          : View application log output
- `/delete_log`       : Clear the log file

The application favors simplicity, debuggability, and transparency:
no ORM, no background workers, no external logging frameworks.
All behavior is explicit, traceable, and file-backed.

Intended use cases include:
- Code completion experimentation
- Prompt engineering workflows
- Flask route analysis and reuse
- Offline AI-assisted development
- Building personal or research-oriented coding assistants

Author: Jack
Runtime: Python 3.9+
Model Backend: Ollama (local HTTP API)
"""
import traceback
import sqlite3
import os
import sys
import json
import requests
import time
from datetime import datetime
from icecream import ic
import subprocess
# Flask Imports
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
# -----------------------------
# CONFIG
# -----------------------------
app = Flask(__name__)

#MODEL = "codellama:13b"
#MODEL = "llama3.2:3b"
MODEL = "codellama:13b"
ENDPOINT = "http://localhost:11434/api/generate"
TIMEOUT = 900

JSON_COLLECTION = "docs.json"
TXT_COLLECTION = "docs.txt"
DEFAULT_VARIATIONS = 3

OLLAMA_CONTAINER = "ollama-cpu"
OLLAMA_STARTUP_DELAY = 5  # seconds

# -----------------------------
# LOGGING
# -----------------------------
LOG_FILE_PATH = "static/doc_log.txt"
def logit(*args):
    """
    Lightweight file-based logging utility for debugging and runtime diagnostics.
    Accepts ANY number of positional arguments and safely joins them into a
    single log message.

    Examples:
        logit("Hello world")
        logit("x:", x, "y:", y)
        logit("Paths:", image_paths)
        logit(["list", "of", "values"])
    """

    try:
        # --- timestamp ---
        timestr = datetime.now().strftime('%A_%b-%d-%Y_%H-%M-%S')

        # --- caller info ---
        frame = inspect.stack()[1]
        filename = frame.filename
        lineno = frame.lineno

        # --- normalize all inputs ---
        parts = []
        for arg in args:
            if isinstance(arg, (list, tuple, set)):
                parts.append(' '.join(map(str, arg)))
            else:
                parts.append(str(arg))

        message_str = ' '.join(parts)

        # --- final log line ---
        log_message = (
            f"{timestr} - File: {filename}, Line: {lineno}: {message_str}\n"
        )

        # --- write log ---
        with open(LOG_FILE_PATH, "a") as f:
            f.write(log_message)

        # Optional console echo (leave commented if you want quiet logs)
        # print(log_message, end="")

    except Exception as e:
        print(f"[LOGIT ERROR] {e}")

@app.route("/readlog")
def readlog():
    """
    This route declaration is used to open the logfile LOG_FILE_PATH = 'static/app_log.txt'
    created by logit function
    """
    logdatas = open(LOG_FILE_PATH, "r").read().split("\n")
    logit(logdatas)
    return render_template("read_log.html", log_content=logdatas)

@app.route("/save", methods=["POST"])
def save():
    """
    Saves the provided code and generates suggestions.
    """
    code = request.form["code"]
    suggestions = generate_suggestions(code)
    return {"suggestions": suggestions}
# def allowed_file(filename):
#    return '.' in filename and filename.rsplit('.', 1)[1].lower() in{'png', 'jpg', 'jpeg', 'gif'}

# SQLite database setup functions
def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    """
    try:
        conn = sqlite3.connect(DATABASEF)
        conn.row_factory = sqlite3.Row
        print("Database connection established.")
        return conn
    except sqlite3.Error as e:
        print(f"Error establishing database connection: {e}")
        traceback.print_exc()
        return None

def create_db():
    """
    Initializes the database by creating necessary tables if they don't exist.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS functions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_text TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print(f"Database {DATABASEF} initialized.")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        traceback.print_exc()

def read_functions():
    """
    Reads all function texts from the database.
    """
    print("Reading functions from database...")
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return []
        cursor = conn.cursor()
        cursor.execute('SELECT function_text FROM functions')
        functions = [row[0] for row in cursor.fetchall()]
        conn.close()
        print("Functions retrieved from database.")
        return functions
    except sqlite3.Error as e:
        print(f"Error reading functions: {e}")
        traceback.print_exc()
        return []

def insert_function(function_text):
    """
    Inserts a new function text into the database.
    """
    try:
        print("Inserting function into database...")
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return
        cursor = conn.cursor()
        cursor.execute('INSERT INTO functions (function_text) VALUES (?)', (function_text,))
        conn.commit()
        conn.close()
        print("Function inserted into database.")
    except sqlite3.Error as e:
        print(f"Error inserting function: {e}")
        traceback.print_exc()

def insert_functions():
    """
    Inserts functions from 'con_html.txt' into the database if not already initialized.
    """
    print("Checking if functions need to be inserted into the database...")
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key='initialized'")
        result = cursor.fetchone()
        if result is None:
            print("Initializing and inserting functions from 'con_html.txt'...")
            with open('static/TEXT/appbp_all_html.txt', 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            # Assuming functions are separated by '\n.\n'
            segments = content.strip().split('@app')
            for segment in segments:
                cleaned_segment = segment.strip()
                if cleaned_segment:
                    cursor.execute('INSERT INTO functions (function_text) VALUES (?)', (cleaned_segment,))
            cursor.execute("INSERT INTO metadata (key, value) VALUES ('initialized', 'true')")
            conn.commit()
            print("Functions inserted into database.")
        else:
            print("Functions already inserted into database.")
        conn.close()
    except sqlite3.Error as e:
        print(f"Error inserting functions into database: {e}")
        traceback.print_exc()

def get_last_function():
    """
    Retrieves the most recently inserted function from the database.
    """
    print("Retrieving the last function from the database...")
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return None
        cursor = conn.cursor()
        cursor.execute('SELECT function_text FROM functions ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        if result:
            print("Last function retrieved successfully.")
            return result[0]
        else:
            print("No functions found in the database.")
            return None
    except sqlite3.Error as e:
        print(f"Error retrieving last function: {e}")
        traceback.print_exc()
        return None




def generate_suggestions(code):
    """
    Generates suggestions based on the last two words of the provided code.
    Each suggestion is approximately 400 characters long.
    """
    print("Generating suggestions...")
    functions = read_functions()

    if not functions:
        print("No functions available to generate suggestions.")
        return []

    # Retrieve the last line from the code
    lines = code.strip().split("\n")
    last_line = lines[-1] if lines else ""
    print(f"Last line of code: '{last_line}'")

    # Split the last line into words and get the last two words
    words = last_line.split()
    last_two_words = " ".join(words[-2:]) if len(words) >= 2 else last_line
    print(f"Last two words: '{last_two_words}'")

    # Function to split snippet based on last_two_words and return completion
    def split_snippet(snippet, last_two_words):
        index = snippet.rfind(last_two_words)
        if index != -1:
            completion = snippet[index + len(last_two_words) :].strip()
            return completion
        return snippet.strip()

    # Search for matching snippets based on the last two words
    matching_snippets = []
    found_indices = set()  # To store indices of found snippets to avoid duplicates

    for i, snippet in enumerate(functions, start=1):
        if last_two_words in snippet:
            if i not in found_indices:
                found_indices.add(i)
                completion = split_snippet(snippet, last_two_words)
                formatted_snippet = f"<pre>{i}: {completion}</pre>"
                # Adjust the snippet length to approximately 400 characters
                if len(formatted_snippet) > 400:
                    formatted_snippet = formatted_snippet[:397] + "..."
                matching_snippets.append(formatted_snippet)
                print(f"Added snippet {i}: {formatted_snippet}")

    # Return up to 20 suggestions, limited to 5 for demonstration purposes
    suggestions = matching_snippets[:5]
    print(f"Generated {len(suggestions)} suggestions.")
    return suggestions


@app.route("/save_code", methods=["POST"])
def save_code():
    """
    Saves the provided code to the database.
    """
    code = request.data.decode("utf-8")
    print(
        f"Received code to save: {code[:50]}..."
    )  # Log first 50 characters for brevity
    if code:
        insert_function(code)
        return "Code saved successfully", 200
    else:
        print("No code provided in the request.")
        return "No code provided in the request", 400


# Logging function


def readlog():
    """
    This function is used to open the logfile LOG_FILE_PATH = 'static/app_log.txt'
    created by logit function and return the data.
    """
    log_file_path = "static/doc_log.txt"
    with open(log_file_path, "r") as Input:
        logdata = Input.read()
    # print last entry
    logdata = logdata.split("\n")
    return logdata


@app.route("/delete_log")
def delete_log():
    """
    This route declaration is used to delete the logfile LOG_FILE_PATH = 'static/app_log.txt'
    created by logit function
    """
    open(LOG_FILE_PATH, "w").close()
    logit("Log file deleted successfully")
    return redirect("/view_log")

VIEW_LOG="""
<!-- view_log.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>view_log.html</title>

    <link
      rel="stylesheet"
      href="{{ url_for('static', filename='css/doc.css') }}"
    />
 
  </head>
  <body>
    <a href="/readlog"><button>Refresh</button></a><br />
    <a href="/delete_log"><button class = "dred">Delete Log</button></a><br />
    <a href="/"><button>Home</button></a>
    <h1>view_log.html</h1>
    <p>The log file created by logit function.</p>


<ul>
    {% for log in log_content %}
        <li>{{ log }}</li>
    {% endfor %}
</ul>

"""
# Logging function
@app.route("/view_log", methods=["GET", "POST"])
def view_log():
    """
    This route declaration is used to view the logfile LOG_FILE_PATH = 'static/app_log.txt'
    created by logit function
    """
    data = readlog()
    return render_template_string(VIEW_LOG, data=data)
app.config["DATABASEF"] = "static/functions.db"
DATABASEF = app.config["DATABASEF"]

def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    """
    try:
        conn = sqlite3.connect(DATABASEF)
        conn.row_factory = sqlite3.Row
        print("Database connection established.")
        return conn
    except sqlite3.Error as e:
        print(f"Error establishing database connection: {e}")
        traceback.print_exc()
        return None


def get_last_function():
    """
    Retrieves the most recently inserted function from the database.
    """
    print("Retrieving the last function from the database...")
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return None
        cursor = conn.cursor()
        cursor.execute('SELECT function_text FROM functions ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        if result:
            print("Last function retrieved successfully.")
            return result[0]
        else:
            print("No functions found in the database.")
            return None
    except sqlite3.Error as e:
        print(f"Error retrieving last function: {e}")
        traceback.print_exc()
        return None

@app.route("/view_functions", methods=["GET", "POST"])
def view_functions():
    """
    Renders a page to view all functions.
    """
    print("Rendering view_functions page.")
    conn = get_db_connection()
    if conn is None:
        print("Failed to establish database connection.")
        return render_template("view_functions.html", data=[])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functions")
    data = cursor.fetchall()
    conn.close()
    print(f"Retrieved {len(data)} functions for viewing.")
    return render_template("view_functions.html", data=data)


@app.route("/update_function", methods=["POST", "GET"])
def update_function():
    """
    Updates a specific function based on form data and redirects to the view page.
    """
    id = request.form.get("id")
    new_function_text = request.form.get("function_text")
    print(f"Received update for function ID {id}.")
    if not id or not new_function_text:
        print("Missing function ID or new function text in the request.")
        return redirect(url_for("view_functions"))
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to establish database connection.")
            return redirect(url_for("view_functions"))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE functions SET function_text = ? WHERE id = ?",
            (new_function_text, id),
        )
        conn.commit()
        conn.close()
        print(f"Function ID {id} updated successfully via form.")
        return redirect(url_for("view_functions"))
    except sqlite3.Error as e:
        print(f"Error updating function ID {id}: {e}")
        traceback.print_exc()
        return redirect(url_for("view_functions"))






'''
# -----------------------------
# DOCKER CONTROL
# -----------------------------

def start_ollama_container():
    logit(f"Starting Docker container: {OLLAMA_CONTAINER}")
    ic("docker start", OLLAMA_CONTAINER)

    subprocess.run(
        ["docker", "start", OLLAMA_CONTAINER],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )

    logit("Waiting for Ollama to initialize...")
    time.sleep(OLLAMA_STARTUP_DELAY)

def stop_ollama_container():
    logit(f"Stopping Docker container: {OLLAMA_CONTAINER}")
    ic("docker stop", OLLAMA_CONTAINER)

    subprocess.run(
        ["docker", "stop", OLLAMA_CONTAINER],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
'''# -----------------------------
# UTILITIES
# -----------------------------

def call_ollama(prompt: str) -> str:
    ic("PROMPT →", prompt)

    r = requests.post(
        ENDPOINT,
        json={
            "model": MODEL,
            "prompt": prompt,
            "max_tokens": 2000,            
            "stream": False
        },
        timeout=TIMEOUT
    )

    r.raise_for_status()
    result = r.json().get("response", "").lstrip("\ufeff\n ")
    ic("RESPONSE ←", result)
    return result

def atomic_write_json(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

# -----------------------------
# PROMPT REFINEMENT
# -----------------------------

def refine_prompt(rough_idea: str, variations: int = DEFAULT_VARIATIONS) -> dict:
    """
    Refines a rough idea into multiple T2I prompts.
    Returns a dict of variations.
    """
    outputs = {}

    for i in range(1, variations + 1):
        prompt = f"""
    You are a static Python code analyzer.

    Extract ONLY the following fields.
    Return VALID JSON ONLY.

    Required JSON keys:
    - function_name
    - routes
    - template_file
    - docstring
    - required_functions

    CODE:
    {snippet}
    """.strip()

        refined = call_ollama(prompt).strip()
        outputs[f"{rough_idea}_variation_{i}"] = refined

    return outputs

# -----------------------------
# COLLECTION APPENDING
# -----------------------------

def append_to_collections(refined_prompts: dict):
    try:
        with open(JSON_COLLECTION, "r", encoding="utf-8") as f:
            collection = json.load(f)
    except FileNotFoundError:
        collection = {}

    collection.update(refined_prompts)
    atomic_write_json(JSON_COLLECTION, collection)
    logit(f"Appended {len(refined_prompts)} prompts to {JSON_COLLECTION}")

    with open(TXT_COLLECTION, "a", encoding="utf-8") as f:
        for prompt in refined_prompts.values():
            f.write(prompt + "\n")

    logit(f"Appended {len(refined_prompts)} prompts to {TXT_COLLECTION}")
INDEX="""
<!-- templates/index_y.html -->
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Suggestions</title>
    <style>
        html,
        body {
            margin: 0;
            padding: 1%;
            height: 100%;
            font-family: Arial, sans-serif;
        }

        body {
            background-color: black;
            background-image: url('../static/assets/MemMaker_background.png');
            background-repeat: repeat-y;
            background-size: cover;
            /* Use 'cover' to make the image cover the entire body */
            background-position: top;
            color: rgb(61, 195, 12);
        }

        video {
            margin: 10px, auto;
            width: 250px;
            height: auto;
        }

        .wrapper {
            display: flex;
            width: 100%;
            margin-left: auto;
            margin-right: auto;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 70vh;
            border: 1px solid darkgray;
        }

        .columns {
            display: flex;
            width: 100%;
            margin-top: 10px;
        }

        .column {
            padding: 5px;
            box-sizing: border-box;
        }

        .column.left {
            width: 50%;
            border: 1px solid #3b3232;
        }

        .column.right {
            margin: 0 auto;
            /* Center horizontally */
            width: 50%;
            /* Adjusted width to make space for wrapped text */
            border: 1px solid #3b3232;
            text-align: left;
            font-size: 20px;
            /* Allow text wrapping */
            word-wrap: break-word;
            white-space: pre-wrap;
        }


        .column.right video {
            max-width: 100%;
            height: auto;
        }

        .footer {
            width: 98%;
            padding: 20px;
            background-color: #333;
            color: white;
            text-align: center;
            position: relative;
            /* Make it relative to the container */
            bottom: 0;
            /* Push it to the bottom */
        }
        #code {
            font-size: 18px;
            font-family: monospace;
        }
        .notes {
            margin-top: 0px auto;
            font-size: 18px;
            color: rgb(105, 178, 230);
        }
        pre {
            white-space: pre-wrap;
        }
        .sticky {
            position: sticky;
            top: 0;
            z-index: 100;
            background-color: #760909;
            
        }
        .header {
            display: flex;
            align-items: left;
            margin: 0 auto;
            width: 98%;
            padding: 5px;
            text-align: center;
            background-color: #760909;
            color: rgb(238, 232, 201);
            padding: 10px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            margin-left: auto;
            margin-right: auto; 
       }
        .header h2 {
            margin-left: 20px;
        }
        .header button {
            margin-left: 20px;
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            height: 32px;
            font-size: 16px;
            transition: background-color 0.3s ease;
            width: 200px;
        }
        .header button:hover {
            background-color: #45a049;
            height: 36px;
        }
        #search_input {
            height: 30px;
            width: 300px;
            font-size: 16px;
            border: 1px solid #f8e4c4;
            border-radius: 4px;
            margin-left: 20px;
        }
       
    </style>
<script>
    // Function to find and highlight the search string
    function findString(str) {
        if (parseInt(navigator.appVersion) < 4) return;
        
        // Check if find method is supported
        if (window.find) {
            // Find the search string
            var strFound = window.find(str);
            if (!strFound) {
                // If not found, try to find from the beginning
                window.find(str, 0, 1);
            }
            if (strFound) {
                // Highlight the found text
                var range = window.getSelection().getRangeAt(0);
                var span = document.createElement('span');
                span.style.backgroundColor = 'yellow';
                range.surroundContents(span);
            }
        } else if (navigator.appName.indexOf("Microsoft") != -1) {
            // Handle Microsoft browsers
            // Not implemented for brevity
        } else if (navigator.appName == "Opera") {
            // Handle Opera browsers
            alert("Opera browsers not supported, sorry...");
            return;
        }

        // If not found, show alert
        if (!strFound) alert("String '" + str + "' not found!");
    }

    // Function to move cursor to next occurrence of search input
    function moveToNextOccurrence() {
        var search_str = document.getElementById("search_input").value;
        findString(search_str);
    }
</script>

</head>

<body>
    <div class="wrapper">
        <div class="header sticky">
            <h2>Code Suggestions: text_completion/templates/index_code.html  |</h2>&nbsp;&nbsp;&nbsp;&nbsp;
            <button id="search_submit" onclick="moveToNextOccurrence()">Find Next</button>
<input type="text" id="search_input"><a href="/view_functions" target="_blank">view_functions</a>
        </div>
        <div class="columns">
            <div class="column left">
<pre class="notes">

</pre>
                <a style="font-size: 24px;
                color: antiquewhite;" href="/readlog" target="_blank">readlog</a>
                <form id="codeForm">
                    <label for="code">Enter your code:</label><br>
                    <textarea id="code" name="code" rows="10" cols="55"></textarea><br>
                    <button type="button" onclick="submitForm()">Generate Suggestions</button>
                </form>
            </div>
            <div class="column right">
                <div id="suggestions">
                    <!-- Suggestions will be displayed here -->
                </div>

                <script>
                    function submitForm() {
                        var code = document.getElementById('code').value;
                        var formData = new FormData();
                        formData.append('code', code);

                        fetch('/save', {
                            method: 'POST',
                            body: formData,
                        })
                            .then(response => response.json())
                            .then(data => {
                                displaySuggestions(data.suggestions);
                            })
                            .catch((error) => {
                                console.error('Error:', error);
                            });
                    }

                    function displaySuggestions(suggestions) {
                        var suggestionsDiv = document.getElementById('suggestions');
                        suggestionsDiv.innerHTML = '<h2>Suggestions:</h2>';
                        suggestions.forEach(function (suggestion) {
                            suggestionsDiv.innerHTML += '<p>' + suggestion + '</p>';
                        });
                    }
                </script>
            </div>
        </div>
    </div>
    <footer class="footer">
        <p>Code Suggestions</p>
        <p>Append suggestions to the completion source</p>
        <!-- Footer content with textarea -->
        <textarea id="userCode" placeholder="Your message here" rows="25" cols="120"></textarea>
        <button onclick="saveCode()">Submit</button>
        <script>    function saveCode() {
            var code = document.getElementById('userCode').value;
        
            fetch('/save_code', {
                method: 'POST',
                body: code, // Send the code directly without JSON.stringify
            })
                .then(response => {
                    if (response.ok) {
                        alert('Code saved successfully!');
                    } else {
                        alert('Failed to save code.');
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    alert('Failed to save code.');
                });
        }
        </script>        
    </footer>
    

</body>

</html>
"""
# -----------------------------
# ENTRY POINT
# -----------------------------
@app.route("/")
def index_code():
    """
    Renders the main index page with the latest function.
    """
    functions = get_last_function()
    return render_template_string(INDEX, functions=functions)


@app.route("/index")
def index():
    if len(sys.argv) < 2:
        print("Usage: doc_refiner.py <rough idea> [num_variations]")
        sys.exit(1)

    rough_idea = """sys.argv[1]"""
    variations = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_VARIATIONS

    start_ollama_container()

    try:
        logit("Refining prompt for idea:", rough_idea)
        refined_prompts = refine_prompt(rough_idea, variations)
        append_to_collections(refined_prompts)

        logit("Refined prompts:")
        for prompt in refined_prompts.values():
            logit(prompt)

    finally:
        stop_ollama_container()
        logit("Done.")

if __name__ == "__main__":
    create_db()
    insert_functions()
    app.run(debug=True, host="0.0.0.0", port=5300)

