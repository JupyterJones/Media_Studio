#!/usr/bin/env python3
"""
get_lora_keywords.py - Instant LoRA Activation Keyword & Trigger Word Extractor
Reads the embedded JSON metadata from .safetensors LoRA files directly (without loading weights).
Discovers models across all configured storage drives.
"""

import os
import sys
import json
import struct
import argparse

MODELS_ROOTS = [
    "/media/jack/USB_USBSSD/models",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"),
    os.path.join(os.path.expanduser("~"), "Desktop", "Comfy-UI", "models"),
]

def find_lora_files():
    """Scans all root model directories for LoRA files."""
    found = {}
    for root in MODELS_ROOTS:
        lora_dir = os.path.join(root, "loras")
        if not os.path.exists(lora_dir):
            continue
        for r, _, files in os.walk(lora_dir):
            for f in sorted(files):
                if f.endswith(".safetensors"):
                    if f not in found:
                        found[f] = os.path.join(r, f)
    return found

def extract_lora_info(filepath):
    """
    Extracts embedded training metadata, activation keywords, and tags
    from a .safetensors file header in milliseconds.
    """
    info = {
        "filename": os.path.basename(filepath),
        "filepath": filepath,
        "trigger_phrases": [],
        "top_tags": [],
        "base_model": "Unknown",
        "output_name": "",
        "has_metadata": False
    }

    try:
        with open(filepath, "rb") as f:
            header_bytes = f.read(8)
            if len(header_bytes) < 8:
                return info
            header_len = struct.unpack("<Q", header_bytes)[0]
            # Safety check: header shouldn't be larger than 10MB
            if header_len > 10 * 1024 * 1024:
                return info

            header_json_bytes = f.read(header_len)
            header_json = json.loads(header_json_bytes.decode("utf-8", errors="ignore"))
            meta = header_json.get("__metadata__", {})

            if meta:
                info["has_metadata"] = True

            # 1. Official modelspec trigger phrase
            if "modelspec.trigger_phrase" in meta:
                info["trigger_phrases"].append(meta["modelspec.trigger_phrase"])

            # 2. Output name
            if "ss_output_name" in meta:
                info["output_name"] = str(meta["ss_output_name"]).strip()

            # 3. Base model architecture
            if "ss_sd_model_name" in meta:
                info["base_model"] = meta["ss_sd_model_name"]
            elif "ss_base_model_version" in meta:
                info["base_model"] = meta["ss_base_model_version"]

            # 4. Extract tags and frequencies
            tag_freq_raw = meta.get("ss_tag_frequency")
            if tag_freq_raw:
                if isinstance(tag_freq_raw, str):
                    try:
                        tag_freq = json.loads(tag_freq_raw)
                    except Exception:
                        tag_freq = {}
                else:
                    tag_freq = tag_freq_raw

                all_tags = {}
                for subset_name, tags_dict in tag_freq.items():
                    # Dataset folder names often have the trigger: e.g. "100_morriganda"
                    clean_folder = subset_name.split("_", 1)[-1] if "_" in subset_name else subset_name
                    if clean_folder and len(clean_folder) > 2 and not clean_folder.isdigit() and clean_folder.lower() not in ["img", "dataset"]:
                        if clean_folder not in info["trigger_phrases"]:
                            info["trigger_phrases"].append(clean_folder)

                    if isinstance(tags_dict, dict):
                        for tag, count in tags_dict.items():
                            all_tags[tag] = all_tags.get(tag, 0) + count

                sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
                info["top_tags"] = [t[0] for t in sorted_tags[:15]]

                # Often the most frequent tag in a custom dataset is the primary trigger word
                if sorted_tags and not info["trigger_phrases"]:
                    top_tag = sorted_tags[0][0]
                    if top_tag and len(top_tag) > 2:
                        info["trigger_phrases"].append(top_tag)

            # 5. Dataset dirs metadata
            dataset_dirs = meta.get("ss_dataset_dirs")
            if dataset_dirs:
                if isinstance(dataset_dirs, str):
                    try:
                        ds_dict = json.loads(dataset_dirs)
                        for d_name in ds_dict.keys():
                            clean = d_name.split("_", 1)[-1] if "_" in d_name else d_name
                            if clean and len(clean) > 2 and not clean.isdigit() and clean.lower() not in ["img", "dataset"]:
                                if clean not in info["trigger_phrases"]:
                                    info["trigger_phrases"].append(clean)
                    except Exception:
                        pass

    except Exception as e:
        info["error"] = str(e)

    # 6. Check companion .civitai.info or .txt file in same directory
    base_no_ext = os.path.splitext(filepath)[0]
    info_json = base_no_ext + ".civitai.info"
    if os.path.exists(info_json):
        try:
            with open(info_json, "r", encoding="utf-8") as f:
                c_data = json.load(f)
                trained_words = c_data.get("trainedWords", [])
                for tw in trained_words:
                    if tw not in info["trigger_phrases"]:
                        info["trigger_phrases"].append(tw)
        except Exception:
            pass

    companion_txt = base_no_ext + ".txt"
    if os.path.exists(companion_txt):
        try:
            with open(companion_txt, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                if lines:
                    info["companion_text_sample"] = lines[0]
        except Exception:
            pass

    return info

def print_lora_summary(info):
    print("=" * 65)
    print(f"📦 LoRA: {info['filename']}")
    print(f"📁 Path: {info['filepath']}")
    if info.get("base_model") and info["base_model"] != "Unknown":
        print(f"🎯 Base Model: {info['base_model']}")
    if info.get("output_name"):
        print(f"🏷️  Output Name: {info['output_name']}")

    triggers = info.get("trigger_phrases", [])
    if triggers:
        print(f"⚡ Activation Keywords: {', '.join(f'\"{t}\"' for t in triggers)}")
    else:
        print("⚡ Activation Keywords: [No dedicated trigger word needed / Style LoRA]")

    tags = info.get("top_tags", [])
    if tags:
        print(f"🏷️  Top Training Tags: {', '.join(tags[:8])}")

    if info.get("companion_text_sample"):
        print(f"📝 Prompt Sample: {info['companion_text_sample'][:120]}...")
    print("=" * 65)

def main():
    parser = argparse.ArgumentParser(description="Extract activation keywords from SD LoRAs")
    parser.add_argument("lora", nargs="?", help="LoRA filename or substring to search for")
    parser.add_argument("--all", action="store_true", help="List all discovered LoRAs and their keywords")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--save-remember", action="store_true", help="Save extracted keywords directly into REMEMBER.db")
    args = parser.parse_args()

    loras = find_lora_files()
    if not loras:
        print("[!] No LoRA files (.safetensors) found in any MODELS_ROOTS directories.")
        sys.exit(1)

    targets = []
    if args.lora:
        query = args.lora.lower()
        targets = [path for fn, path in loras.items() if query in fn.lower()]
        if not targets:
            print(f"[!] No LoRA found matching '{args.lora}'. Discovered {len(loras)} LoRAs:")
            for fn in sorted(loras.keys()):
                print(f"  - {fn}")
            sys.exit(1)
    else:
        targets = list(loras.values())

    results = []
    for path in targets:
        info = extract_lora_info(path)
        results.append(info)
        if not args.json:
            print_lora_summary(info)

    if args.json:
        print(json.dumps(results, indent=2))

    if args.save_remember:
        try:
            import sqlite3
            remember_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "REMEMBER.db")
            text_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "TEXT")
            os.makedirs(text_dir, exist_ok=True)

            if len(results) > 1 or args.all:
                # Compile ALL into ONE single clean master catalog entry!
                title = f"[LoRA Master Catalog] Complete Trigger Keywords Guide ({len(results)} Models)"
                md_content = f"# 🎨 LoRA Master Trigger Keywords Guide\n\n"
                md_content += f"**Total LoRAs:** {len(results)} | **Auto-generated by:** `get_lora_keywords.py`\n\n"
                md_content += "| LoRA Model | Activation Keywords | Base Architecture |\n"
                md_content += "| :--- | :--- | :--- |\n"

                for r in results:
                    triggers = ", ".join(f"`{t}`" for t in r["trigger_phrases"]) if r["trigger_phrases"] else "*None / Style*"
                    md_content += f"| **{r['filename']}** | {triggers} | {r.get('base_model', 'Unknown')} |\n"

                md_content += "\n---\n\n## 📋 Detailed Tags Breakdown\n\n"
                for r in results:
                    md_content += f"### 📦 `{r['filename']}`\n"
                    if r.get("output_name"):
                        md_content += f"- **Output Name:** `{r['output_name']}`\n"
                    triggers = ", ".join(f'"{t}"' for t in r["trigger_phrases"]) if r["trigger_phrases"] else "None (Style LoRA)"
                    md_content += f"- **⚡ Keywords:** {triggers}\n"
                    if r.get("top_tags"):
                        md_content += f"- **🏷️ Top Training Tags:** {', '.join(r['top_tags'][:10])}\n"
                    if r.get("companion_text_sample"):
                        md_content += f"- **📝 Prompt Sample:** {r['companion_text_sample'][:120]}...\n"
                    md_content += f"- **📁 File:** `{r['filepath']}`\n\n"

                if os.path.exists(remember_db):
                    conn = sqlite3.connect(remember_db)
                    c = conn.cursor()
                    c.execute("INSERT INTO post (title, content, image, video_filename, audio) VALUES (?, ?, NULL, NULL, NULL)", (title, md_content))
                    conn.commit()
                    conn.close()

                catalog_fn = os.path.join(text_dir, "lora_master_keywords_catalog.md")
                with open(catalog_fn, "w", encoding="utf-8") as f:
                    f.write(md_content)

                print(f"[✓] Successfully compiled and saved all {len(results)} LoRAs into ONE Master Entry in REMEMBER.db and static/TEXT/lora_master_keywords_catalog.md!")

            elif len(results) == 1:
                r = results[0]
                title = f"[LoRA Keywords] {r['filename']}"
                triggers = ", ".join(f'"{t}"' for t in r["trigger_phrases"]) if r["trigger_phrases"] else "Style LoRA (no keyword)"
                content = f"# LoRA: {r['filename']}\n\n**Keywords:** {triggers}\n\n**Top Tags:** {', '.join(r['top_tags'])}\n\n**Path:** `{r['filepath']}`\n"
                if os.path.exists(remember_db):
                    conn = sqlite3.connect(remember_db)
                    c = conn.cursor()
                    c.execute("INSERT INTO post (title, content, image, video_filename, audio) VALUES (?, ?, NULL, NULL, NULL)", (title, content))
                    conn.commit()
                    conn.close()
                print(f"[✓] Saved {r['filename']} keywords into REMEMBER.db!")
        except Exception as e:
            print(f"[!] Error saving to REMEMBER.db: {e}")

if __name__ == "__main__":
    main()
