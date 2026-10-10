#!/usr/bin/env python3
"""
Test which 'io' module Python is importing.
This script is SAFE and does not touch your Flask app.
"""

import io
from io import BytesIO

print("=" * 50)
print("Testing Python IO module")
print("=" * 50)

print("io module object:", io)

# Some modules (built-ins) don't have __file__
io_file = getattr(io, "__file__", "BUILT-IN")
print("io module file:", io_file)

print("Does io have BytesIO?", hasattr(io, "BytesIO"))
print("BytesIO object:", BytesIO)

# Try actually using it
try:
    buf = io.BytesIO()
    buf.write(b"test")
    print("BytesIO write/read SUCCESS:", buf.getvalue())
except Exception as e:
    print("BytesIO FAILED:", e)

print("=" * 50)
