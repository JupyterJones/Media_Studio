#!/usr/bin/env python3
"""
embed_post_image.py

Extracts images and their creation parameters / content from static/blog4.db,
embeds all post text (title, parameters, video, date, and custom comments)
directly into the image's metadata (PNG chunks & EXIF), and saves it to
static/embedded_images/.

Usage:
  # Interactive mode:
  python3 embed_post_image.py

  # Specific post ID:
  python3 embed_post_image.py -i 2
  python3 embed_post_image.py -i 2 -c "My additional notes" -d "2026-09-15"

  # List all posts with images:
  python3 embed_post_image.py --list

  # Process all posts with images:
  python3 embed_post_image.py --all

  # View embedded metadata of an existing image:
  python3 embed_post_image.py --view static/embedded_images/post_2.png
"""

import os
import sys
import re
import io
import base64
import sqlite3
import argparse
from datetime import datetime
from PIL import Image, PngImagePlugin, ExifTags


DEFAULT_DB_PATH = "static/blog4.db"
DEFAULT_OUTPUT_DIR = "static/embedded_images"


def get_db_connection(db_path=DEFAULT_DB_PATH):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def list_posts_with_images(db_path=DEFAULT_DB_PATH):
    """Retrieve list of all posts that contain image data."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, video_filename,
               substr(content, 1, 80) AS content_preview,
               length(image) AS img_len
        FROM post
        WHERE image IS NOT NULL AND length(image) > 0
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_post(post_id, db_path=DEFAULT_DB_PATH):
    """Fetch a single post by ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, content, video_filename, image
        FROM post
        WHERE id = ?
    """, (post_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def decode_image_data(raw_data):
    """Decode image data whether it is stored as base64 string or binary bytes."""
    if not raw_data:
        return None
    if isinstance(raw_data, str):
        # Handle data:image/xxx;base64,... URI
        if "," in raw_data and "base64" in raw_data[:60]:
            raw_data = raw_data.split(",", 1)[1]
        return base64.b64decode(raw_data.strip())
    elif isinstance(raw_data, (bytes, bytearray)):
        # Check if bytes are ascii base64 characters
        if raw_data.startswith(b"iVBORw0") or raw_data.startswith(b"/9j/") or raw_data.startswith(b"UklGR"):
            try:
                return base64.b64decode(raw_data)
            except Exception:
                pass
        return bytes(raw_data)
    return None


def sanitize_filename(title, post_id, ext):
    """Generate a clean, filesystem-safe filename."""
    if title:
        clean = re.sub(r'[^a-zA-Z0-9_-]+', '_', title).strip('_')
        # Limit length to avoid overly long filenames
        clean = clean[:60].rstrip('_')
        if clean:
            return f"post_{post_id}_{clean}.{ext}"
    return f"post_{post_id}.{ext}"


def embed_and_save(post_id, custom_comment=None, custom_date=None,
                   db_path=DEFAULT_DB_PATH, output_dir=DEFAULT_OUTPUT_DIR):
    """
    Reads post row from DB, embeds parameters, date, and comments into
    the image, and saves it in output_dir.
    """
    row = fetch_post(post_id, db_path)
    if not row:
        print(f"[-] Error: Post with ID {post_id} not found in {db_path}.")
        return None

    if not row["image"]:
        print(f"[-] Error: Post ID {post_id} does not contain an image.")
        return None

    img_bytes = decode_image_data(row["image"])
    if not img_bytes:
        print(f"[-] Error: Failed to decode image for post ID {post_id}.")
        return None

    # Open image
    img = Image.open(io.BytesIO(img_bytes))
    orig_format = img.format or "PNG"
    ext = orig_format.lower()
    if ext == "jpeg":
        ext = "jpg"

    # Prepare dates
    now = datetime.now()
    if custom_date and custom_date.strip():
        date_str = custom_date.strip()
    else:
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Exif date format is YYYY:MM:DD HH:MM:SS
    try:
        dt_parsed = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        exif_date_str = dt_parsed.strftime("%Y:%m:%d %H:%M:%S")
    except Exception:
        exif_date_str = now.strftime("%Y:%m:%d %H:%M:%S")

    title = row["title"] or ""
    content = row["content"] or ""
    video = row["video_filename"] or ""

    # Build the complete comment text
    comment_blocks = []
    comment_blocks.append(f"Post ID: {post_id}")
    if title:
        comment_blocks.append(f"Title: {title}")
    comment_blocks.append(f"Date: {date_str}")
    if video:
        comment_blocks.append(f"Video: {video}")
    if custom_comment and custom_comment.strip():
        comment_blocks.append(f"Comment / Notes: {custom_comment.strip()}")

    comment_blocks.append("\nParameters / Content:\n" + content)
    full_comment = "\n".join(comment_blocks)

    # Setup EXIF metadata
    try:
        exif = img.getexif()
    except Exception:
        exif = Image.Exif()

    exif[ExifTags.Base.ImageDescription] = full_comment
    exif[ExifTags.Base.DateTime] = exif_date_str
    exif[ExifTags.Base.Software] = "Media Studio"

    # Make output directory
    os.makedirs(output_dir, exist_ok=True)
    filename = sanitize_filename(title, post_id, ext)
    out_path = os.path.join(output_dir, filename)

    # Embed format-specific metadata
    if orig_format.upper() == "PNG":
        png_info = PngImagePlugin.PngInfo()
        # "parameters" is standard for Stable Diffusion, Automatic1111, ComfyUI, etc.
        png_info.add_text("parameters", content)
        png_info.add_text("Title", title)
        png_info.add_text("Comment", full_comment)
        png_info.add_text("Date", date_str)
        if custom_comment and custom_comment.strip():
            png_info.add_text("UserNotes", custom_comment.strip())
        if video:
            png_info.add_text("VideoFilename", video)
        png_info.add_text("Software", "Media Studio")

        img.save(out_path, format="PNG", pnginfo=png_info, exif=exif)
    elif orig_format.upper() in ("JPEG", "JPG"):
        img.save(out_path, format="JPEG", comment=full_comment.encode("utf-8", errors="replace"), exif=exif)
    elif orig_format.upper() == "WEBP":
        img.save(out_path, format="WEBP", exif=exif)
    else:
        # Generic fallback
        img.save(out_path, format=orig_format, exif=exif)

    file_size_kb = os.path.getsize(out_path) / 1024
    print(f"\n[+] Successfully embedded metadata and saved image!")
    print(f"    File: {out_path}")
    print(f"    Format: {orig_format} ({img.width}x{img.height})")
    print(f"    Size: {file_size_kb:.1f} KB")
    print(f"    Post ID: {post_id}")
    print(f"    Title: {title}")
    print(f"    Date: {date_str}")
    if custom_comment and custom_comment.strip():
        print(f"    User Comment: {custom_comment.strip()}")
    print("-" * 60)
    print("Embedded Comment Preview:")
    print("-" * 60)
    print(full_comment[:400] + ("..." if len(full_comment) > 400 else ""))
    print("-" * 60)
    return out_path


def view_image_metadata(image_path):
    """Inspect and print all embedded metadata in an image file."""
    if not os.path.exists(image_path):
        print(f"[-] File not found: {image_path}")
        return

    print(f"\n{'='*60}")
    print(f"Inspecting Metadata: {image_path}")
    print(f"{'='*60}")

    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"[-] Could not open image: {e}")
        return

    print(f"Format: {img.format}")
    print(f"Dimensions: {img.size[0]} x {img.size[1]}")
    print(f"Mode: {img.mode}")

    # PNG Text chunks
    if hasattr(img, "text") and img.text:
        print(f"\n--- PNG Text Chunks ({len(img.text)}) ---")
        for k, v in img.text.items():
            print(f"\n[{k}]:\n{v}")

    # EXIF tags
    try:
        exif = img.getexif()
        if exif:
            print(f"\n--- EXIF Tags ({len(exif)}) ---")
            for tag_id, val in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                print(f"\n[{tag_name}]:\n{val}")
    except Exception as e:
        print(f"[-] Error reading EXIF: {e}")


def interactive_menu(db_path=DEFAULT_DB_PATH, output_dir=DEFAULT_OUTPUT_DIR):
    """Run an interactive CLI session."""
    print("=" * 60)
    print("   Media Studio - Image Metadata Embedder")
    print("=" * 60)

    rows = list_posts_with_images(db_path)
    if not rows:
        print(f"No posts with images found in {db_path}.")
        return

    print(f"\nAvailable posts with images in '{db_path}':")
    print(f"{'ID':<6} | {'Title':<35} | {'Content Snippet'}")
    print("-" * 75)
    for r in rows:
        title_str = (r['title'] or 'Untitled')[:33]
        snippet = (r['content_preview'] or '').replace('\r', ' ').replace('\n', ' ')[:32]
        print(f"{r['id']:<6} | {title_str:<35} | {snippet}...")
    print("-" * 75)

    # Prompt user for ID
    while True:
        choice = input("\nEnter Post ID to embed (or 'q' to quit): ").strip()
        if choice.lower() in ('q', 'quit', 'exit'):
            print("Exiting.")
            return
        if choice.isdigit():
            post_id = int(choice)
            break
        print("Please enter a valid numeric ID.")

    # Prompt for optional user comment
    custom_comment = input("Enter any additional comment or notes (press Enter to skip): ").strip()

    # Prompt for optional date
    default_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    custom_date = input(f"Enter date [default: {default_date}]: ").strip()
    if not custom_date:
        custom_date = default_date

    # Run embedding
    embed_and_save(
        post_id=post_id,
        custom_comment=custom_comment,
        custom_date=custom_date,
        db_path=db_path,
        output_dir=output_dir
    )


def main():
    parser = argparse.ArgumentParser(
        description="Embed post parameters, title, date, and comments into image files."
    )
    parser.add_argument("-i", "--id", type=int, help="Post ID to extract and embed")
    parser.add_argument("-l", "--list", action="store_true", help="List all posts with images")
    parser.add_argument("-a", "--all", action="store_true", help="Embed images for all posts with images")
    parser.add_argument("-c", "--comment", type=str, default=None, help="Additional custom comment to embed")
    parser.add_argument("-d", "--date", type=str, default=None, help="Custom date (e.g. '2026-09-15' or 'YYYY-MM-DD HH:MM:SS')")
    parser.add_argument("-v", "--view", type=str, help="View metadata of an existing image file")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH, help=f"Path to SQLite DB (default: {DEFAULT_DB_PATH})")
    parser.add_argument("--outdir", type=str, default=DEFAULT_OUTPUT_DIR, help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")

    args = parser.parse_args()

    if args.view:
        view_image_metadata(args.view)
    elif args.list:
        rows = list_posts_with_images(args.db)
        print(f"Posts with images in {args.db}:")
        for r in rows:
            print(f"ID {r['id']}: {r['title']}")
    elif args.all:
        rows = list_posts_with_images(args.db)
        for r in rows:
            embed_and_save(r['id'], custom_comment=args.comment, custom_date=args.date, db_path=args.db, output_dir=args.outdir)
    elif args.id is not None:
        embed_and_save(args.id, custom_comment=args.comment, custom_date=args.date, db_path=args.db, output_dir=args.outdir)
    else:
        # Interactive mode
        interactive_menu(db_path=args.db, output_dir=args.outdir)


if __name__ == "__main__":
    main()
