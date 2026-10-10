import os
import shutil
from icecream import ic

# Destination directory
dest_dir = "/mnt/HDD500/all_mp3s"
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)
    ic(f"Created destination directory: {dest_dir}")

# Base directory to start scanning (root)
base_dir = "/"  # change to "/" to scan whole system, or "/home/jack" for user folder

# Function to safely copy files without overwriting
def safe_copy(src_path, dest_folder):
    filename = os.path.basename(src_path)
    dest_path = os.path.join(dest_folder, filename)
    base, ext = os.path.splitext(filename)
    counter = 1

    while os.path.exists(dest_path):
        dest_path = os.path.join(dest_folder, f"{base}_{counter}{ext}")
        counter += 1

    shutil.copy2(src_path, dest_path)
    ic(f"Copied: {src_path} -> {dest_path}")

# Walk through directories
for root, dirs, files in os.walk(base_dir):
    # Skip certain system directories to avoid permission issues
    skip_dirs = ["/proc", "/sys", "/mnt/HDD500/docker","/dev", "/run", "/tmp", "/mnt/HDD500/all_mp3s"]
    if any(root.startswith(skip) for skip in skip_dirs):
        continue

    for file in files:
        if file.lower().endswith(".mp3"):
            try:
                src_file = os.path.join(root, file)
                safe_copy(src_file, dest_dir)
            except Exception as e:
                ic(f"Failed to copy {src_file}: {e}")

ic("All MP3 files scanned and copied.")
