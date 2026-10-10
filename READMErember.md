# 💾 REMEMBER – Flask Knowledge & Media Database

A lightweight, monolithic, self-contained personal knowledge hub and media database built with **Flask**, **SQLite**, and a modern **Dark Slate & Glass UI**.

---

## 🌟 Overview

**REMEMBER** is designed for fast note-taking, rich knowledge storage, media clipping, and live UI customization. Everything runs locally with minimal dependencies and zero bloat.

### 🏗️ Architecture

```
REMEMBER/
├── remember.py             # Core Flask application, routes, DB logic, and file management
├── ui_html.py              # Modern CSS design system & all HTML templates (Python strings)
├── README.md               # Documentation and usage guide
└── static/                 # Persistent storage
    ├── REMEMBER.db         # SQLite long-term memory database
    ├── REMEMBER_log.txt    # Application trace logs
    ├── TEXT/               # User-created text and markdown files
    ├── videos/             # Uploaded MP4/video files
    ├── audio/              # Uploaded MP3/audio files
    └── play/               # Audio library tracks
```

- **`remember.py`**: Handles HTTP routing, SQLite queries, multipart file uploads, logging, and text file operations.
- **`ui_html.py`**: Centralizes the modern dark theme CSS and Jinja2-compatible HTML templates as Python strings. Enables live in-app template editing without server restarts.
- **SQLite + Local Storage**: Stores posts, attachments, logs, and text files locally.

---

## ✨ Key Features

### 1. ✍️ Knowledge & Post Management
- **Rich Posts**: Create structured entries with titles, multi-line content, attached base64 images, video clips, and audio tracks.
- **Table of Contents (`/contents`)**: Master index of all database entries with instant client-side search filtering.
- **Full-Text Multi-Term Search (`/search`)**: Search posts by multiple comma-separated keywords matched across both titles and body text.
- **Direct Attachment Uploads**: Upload or replace video and audio attachments directly on any individual post page.

### 2. 📝 Text Files Manager & Creator
- **Dedicated Text Creator (`/create_text`)**:
  - Create `.txt`, `.md`, `.py`, `.json`, or config files directly in `static/TEXT/`.
  - **⚡ Quick Starter Templates**: Instant scaffolding for Notes, To-Do checklists, Markdown documents, and Python scripts.
  - **Live Statistics**: Real-time counter for lines, word count, and character length.
  - **Keyboard Shortcuts**: Tab key support (inserts 4 spaces) and `Ctrl + S` / `Cmd + S` for instant saving.
- **Text Files Directory (`/edit_text`)**:
  - Live filter search across all text files by name or content preview.
  - Displays file size, last modified timestamp, and content snippet.
  - Actions for **Edit**, **Download**, and **Delete**.
  - Collapsible **⚡ Quick Create** panel for fast note creation without leaving the list.
- **Full Text Editor (`/edit/<filename>`)**:
  - Monospace dark editor with line statistics.
  - **📋 Copy All Text** button with visual feedback.
  - Direct file download (`/download/<filename>`).

### 3. 🎬 Media & Audio Hub (`/tube`)
- **Video Player**: Responsive embedded video player grid with 16:9 aspect ratio preservation.
- **MP3 Audio Library**: Plays audio files located in `static/play/` with native media controls.

### 4. 🛠️ Live UI & CSS Editor (`/edit_ui_html`)
- Built-in dark IDE split-view to inspect and modify any template or the global CSS directly from the browser.
- **Split Pane**: Code editor on the left with search functionality and a live interactive preview iframe on the right.
- Hot-reloads templates on save using Python's `importlib.reload()`.

### 5. 📊 Real-Time Logging (`/view_log` & `/readlog`)
- Lightweight file-based logger (`logit()`) that tracks file locations, timestamps, and messages in `static/REMEMBER_log.txt`.
- Terminal-styled UI with line numbering, live filtering, refresh, and clear actions.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required packages:
  ```bash
  pip install flask werkzeug pillow icecream markupsafe
  ```

### Running the Application

1. Navigate to the project directory:
   ```bash
   cd /home/jack/Desktop/REMEMBER
   ```
2. Start the Flask server:
   ```bash
   python3 remember.py
   ```
3. Open your browser and visit:
   ```
   http://localhost:5101
   ```

---

## 🗺️ Route Reference

| Route | Method | Description |
|---|---|---|
| `/` | `GET` | Home page displaying recent posts grid |
| `/new` | `GET`, `POST` | Create a new post with title, content, image, video, and audio |
| `/post/<id>` | `GET`, `POST` | View post details, play media, and upload attachments |
| `/edit/<id>` | `GET`, `POST` | Edit existing post content and update attachments |
| `/contents` | `GET` | Master table of contents for all posts |
| `/search` | `GET`, `POST` | Multi-keyword search across posts |
| `/create_text` | `GET`, `POST` | Dedicated text file creator with starter templates |
| `/edit_text` | `GET`, `POST` | Text file manager with metadata and inline creator |
| `/edit/<filename>` | `GET`, `POST` | Text file editor with stats and copy tool |
| `/download/<filename>` | `GET` | Direct download of text file |
| `/delete/<filename>` | `GET` | Delete a text file from `static/TEXT` |
| `/tube` | `GET` | Video streams and MP3 audio library |
| `/view_log` | `GET` | Terminal-style log viewer |
| `/delete_log` | `GET` | Clear application log file |
| `/edit_ui_html` | `GET`, `POST` | In-browser UI template and CSS code editor |
| `/_ui_css/<name>.css` | `GET` | Serves global CSS stylesheet |

---

## ⌨️ Shortcuts & Tips

- **Save Anywhere in Text Editors**: Press `Ctrl + S` (or `Cmd + S` on macOS) to instantly save changes.
- **Tab Key Indentation**: Pressing `Tab` inside the text editor inserts 4 spaces instead of defocusing the input.
- **Quick Find**: Use the top navigation search bar on any page to jump to text occurrences.
- **Comma-Separated Search**: On the search page, input comma-separated terms (e.g., `python, flask, audio`) to match any of the terms.

---

## 📄 License

Open-source personal knowledge and media database. Feel free to customize and extend.
