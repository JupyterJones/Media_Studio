#!/usr/bin/env python3
import difflib
from icecream import ic
import sys
import os

# -------------------------------------------------------
# compare_files.py
# Create a unified diff report between two text files.
# Usage example:
#     python3 compare_files.py old.txt new.txt
# -------------------------------------------------------

def read_file(filepath):
    ic(f"Reading file: {filepath}")
    if not os.path.isfile(filepath):
        ic(f"File not found: {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return f.readlines()

def create_diff_report(old_file, new_file, output_file="diff_report.txt"):
    ic("Creating diff report")

    old_lines = read_file(old_file)
    new_lines = read_file(new_file)

    ic("Generating unified diff")

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=old_file,
        tofile=new_file,
        lineterm=""
    )

    diff_text = "\n".join(diff)
    #diff_text = " ".join(diff)
    ic(f"Writing diff to {output_file}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(diff_text)

    ic("Diff report complete")
    return output_file

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 compare_files.py old_file new_file")
        return

    old_file = sys.argv[1]
    new_file = sys.argv[2]

    ic(old_file, new_file)

    output = create_diff_report(old_file, new_file)
    print(f"Diff saved to: {output}")

if __name__ == "__main__":
    main()
