#!/usr/bin/env python3

"""
sudo_search.py

Incremental locate-style indexer without FTS.
- Works on any Python 3.6+
- Indexes / and /mnt
- Tracks deleted files
- Supports filters: size, days (mtime), extension
- Uses os only
"""

import os
import sys
import sqlite3
import time

# -------------------------------
# CONFIG
# -------------------------------

DB_NAME = "/home/jack/databases/superlocate2.db"


# -------------------------------
# DATABASE
# -------------------------------

def init_db():
    print("Initializing database...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Use regular table instead of FTS for this use case
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            filename TEXT,
            directory TEXT,
            size INTEGER,
            mtime REAL,
            extension TEXT
        )
    """)

    # Indexes for faster search
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_filename ON files(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_directory ON files(directory)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mtime ON files(mtime)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_size ON files(size)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extension ON files(extension)")

    conn.commit()
    conn.close()
    print("Database ready.")


# -------------------------------
# INDEXING (INCREMENTAL)
# -------------------------------

def index_filesystem(paths=None):
    if paths is None:
        paths = ["/"]

    print(f"Starting incremental index for: {paths}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    indexed_paths = set()
    file_count = 0
    start_time = time.time()

    for base in paths:
        for root, dirs, files in os.walk(base, topdown=True):
            for name in files:
                full_path = os.path.join(root, name)

                try:
                    stat = os.stat(full_path)
                    size = stat.st_size
                    mtime = stat.st_mtime
                    extension = os.path.splitext(name)[1].lower()

                    indexed_paths.add(full_path)

                    cursor.execute("SELECT mtime FROM files WHERE path=?", (full_path,))
                    row = cursor.fetchone()

                    if row:
                        if row[0] != mtime:
                            print(f"Updating: {full_path}")
                            cursor.execute("""
                                UPDATE files
                                SET size=?, mtime=?, extension=?
                                WHERE path=?
                            """, (size, mtime, extension, full_path))
                    else:
                        print(f"New file: {full_path}")
                        cursor.execute("""
                            INSERT INTO files (path, filename, directory, size, mtime, extension)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (full_path, name, root, size, mtime, extension))

                    file_count += 1
                    if file_count % 5000 == 0:
                        print(f"Processed {file_count} files...")
                        conn.commit()

                except Exception as e:
                    continue

    # Remove deleted files
    print("Removing deleted files from database...")
    cursor.execute("SELECT path FROM files")
    all_db_paths = {row[0] for row in cursor.fetchall()}
    deleted = all_db_paths - indexed_paths

    for path in deleted:
        print(f"Removing deleted: {path}")
        cursor.execute("DELETE FROM files WHERE path=?", (path,))

    conn.commit()
    conn.close()
    elapsed = time.time() - start_time
    print(f"Index complete. {file_count} files processed in {elapsed:.2f}s.")


# -------------------------------
# SEARCH WITH FILTERS
# -------------------------------

def search(query, min_size=None, max_size=None, days=None, ext=None):
    print(f"Searching for: {query}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    sql = "SELECT path, size, mtime FROM files WHERE filename LIKE ? OR path LIKE ?"
    params = [f"%{query}%", f"%{query}%"]

    if min_size is not None:
        sql += " AND size >= ?"
        params.append(min_size)

    if max_size is not None:
        sql += " AND size <= ?"
        params.append(max_size)

    if days is not None:
        cutoff = time.time() - (days * 86400)
        sql += " AND mtime >= ?"
        params.append(cutoff)

    if ext is not None:
        sql += " AND extension = ?"
        params.append(ext.lower())

    sql += " LIMIT 500"

    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()

    print(f"{len(results)} results found.")
    for path, size, mtime in results:
        readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
        print(f"{path} | {size} bytes | {readable_time}")


# -------------------------------
# MAIN
# -------------------------------

def main():
    if len(sys.argv) < 2:
        print("""
Usage:
  sudo python ./sudo_search.py index        # Incremental system-wide index
  python ./sudo_search.py search QUERY     # Search files with optional filters
        """)
        return

    command = sys.argv[1]
    init_db()

    if command == "index":
        paths_to_index = ["/", "/mnt"]
        index_filesystem(paths_to_index)

    elif command == "search":
        if len(sys.argv) < 3:
            print("Provide search term")
            return
        search(sys.argv[2])

    else:
        print("Unknown command")


if __name__ == "__main__":
    main()