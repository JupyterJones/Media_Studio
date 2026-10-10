# Embedded Post Image Generator & Metadata Guide

Created by **Esperanza** for **Jack**  
Script: [`embed_post_image.py`](file:///home/jack/Desktop/Media_Studio/embed_post_image.py)  
Target Directory: `static/embedded_images/`  
Database: `static/blog4.db`

---

## 1. Overview

In **Media Studio**, generation posts (prompts, checkpoints, LoRAs, VAEs, seeds, dimensions, CFG scale, etc.) are recorded in SQLite alongside the generated images. 

`embed_post_image.py` extracts the image BLOB and all associated post details from `static/blog4.db`, embeds the complete textual parameter block, title, date, video info, and custom notes directly into the image file's metadata headers (PNG text chunks and EXIF tags), and saves the resulting image to `static/embedded_images/`.

### Key Benefits
- **Zero Image Degradation**: Metadata is written to header chunks (`tEXt` / `iTXt` / EXIF) and does not alter image pixels or compress image quality.
- **AI Tool Ecosystem Compatible**: Uses the industry-standard `parameters` PNG chunk recognized by **Automatic1111 WebUI**, **ComfyUI**, **InvokeAI**, and **Civitai**.
- **OS & Viewer Compatible**: Injects standard EXIF tags (`ImageDescription` and `DateTime`), making details viewable in standard file properties across Linux, macOS, and Windows.
- **Dual Mode**: Runs interactively with guided prompts or via command-line flags.

---

## 2. Database Schema Reference

The script reads from the `post` table in `static/blog4.db`:

```sql
CREATE TABLE post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE,
    content TEXT UNIQUE NOT NULL,
    video_filename TEXT NULL,
    image BLOB
);
```

### Storage Handling
The `image` column in `post` can contain either:
1. **Base64 ASCII string** (the default encoding produced by `MediaStudioSD2.py`).
2. **Raw binary bytes** (standard SQLite BLOBs).

`embed_post_image.py` automatically detects and decodes both formats seamlessly.

---

## 3. Metadata Structure

When an image is processed, the following metadata fields are embedded:

### PNG Metadata Chunks
| Chunk Key | Content Description |
| :--- | :--- |
| `parameters` | The raw post `content` (contains Prompt, Models, LoRAs, Steps, CFG, Seed, etc.). Recognized by SD prompt readers. |
| `Title` | The post title. |
| `Comment` | Full consolidated block containing Post ID, Title, Date, Video Filename, Custom Notes, and Parameters. |
| `Date` | Timestamp (e.g., `YYYY-MM-DD HH:MM:SS`). |
| `UserNotes` | Any extra comment or annotation provided during export. |
| `VideoFilename` | Associated video filename (if any). |
| `Software` | `Media Studio`. |

### EXIF Tags (Supported in PNG & JPEG)
| Tag | Value |
| :--- | :--- |
| `ImageDescription` (0x010E) | Full consolidated comment with title, notes, and parameters. |
| `DateTime` (0x0132) | Formatted timestamp (`YYYY:MM:DD HH:MM:SS`). |
| `Software` (0x0131) | `Media Studio`. |

---

## 4. Usage & Commands

### 4.1. Interactive Mode (Default)
Run without arguments to launch the interactive selector:
```bash
python3 embed_post_image.py
```

**Walkthrough:**
1. Displays a formatted table of all posts with images:
   ```text
   Available posts with images in 'static/blog4.db':
   ID     | Title                               | Content Snippet
   ---------------------------------------------------------------------------
   2      | prompts01 An old  weathered iron... | Prompt An old  weathered iron rob...
   ---------------------------------------------------------------------------
   ```
2. Prompts: `Enter Post ID to embed (or 'q' to quit): 2`
3. Prompts: `Enter any additional comment or notes (press Enter to skip):`
4. Prompts: `Enter date [default: YYYY-MM-DD HH:MM:SS]:`
5. Automatically creates `static/embedded_images/` (if not already present), embeds metadata, and prints a preview.

---

### 4.2. Command-Line Arguments

#### Embed a Specific Post ID
```bash
python3 embed_post_image.py -i 2
```

#### Embed with Custom Comment & Date
```bash
python3 embed_post_image.py -i 2 -c "Final high-res render" -d "2026-09-15 12:00:00"
```

#### List All Posts That Have Images
```bash
python3 embed_post_image.py --list
```

#### Batch Process All Posts With Images
Exports every post in the database that has an image into `static/embedded_images/`:
```bash
python3 embed_post_image.py --all
```

#### View / Inspect Embedded Metadata
Verify the embedded chunks and EXIF tags inside any image:
```bash
python3 embed_post_image.py --view static/embedded_images/post_2_prompts01_An_old_weathered_iron_robotic_cyborg.png
```

---

## 5. Command Reference Table

| Argument | Long Flag | Description |
| :--- | :--- | :--- |
| `-i <ID>` | `--id <ID>` | Specify post ID to extract and embed. |
| `-c "<TEXT>"` | `--comment "<TEXT>"` | Add an optional custom note or comment into the metadata. |
| `-d "<DATE>"` | `--date "<DATE>"` | Provide a custom date/time string (defaults to current time). |
| `-l` | `--list` | List all post IDs and titles that have image data. |
| `-a` | `--all` | Embed and export all posts with images in the database. |
| `-v <PATH>` | `--view <PATH>` | Inspect and print all metadata chunks & EXIF from an image file. |
| | `--db <PATH>` | Path to database (default: `static/blog4.db`). |
| | `--outdir <DIR>` | Directory to save images (default: `static/embedded_images`). |

---

## 6. Output Filename Convention

Filenames are automatically generated and sanitized from the post ID and title:
```
post_{ID}_{sanitized_title}.{ext}
```
Example:
```
static/embedded_images/post_2_prompts01_An_old_weathered_iron_robotic_cyborg.png
```
If the post has no title, the filename falls back to:
```
static/embedded_images/post_{ID}.{ext}
```

---

## 7. Python Integration Snippet

If you want to read back the embedded parameters in another script:

```python
from PIL import Image

img = Image.open("static/embedded_images/post_2_prompts01_An_old_weathered_iron_robotic_cyborg.png")

# Read standard PNG chunks
parameters = img.text.get("parameters")
comment = img.text.get("Comment")
date = img.text.get("Date")

print("Prompt & Parameters:\n", parameters)
print("Full Comment:\n", comment)
```
