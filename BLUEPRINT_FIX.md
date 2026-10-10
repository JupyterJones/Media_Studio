# Blueprint Fix Summary: Flask BuildError Resolution

## 1. Problem Overview

When navigating to `/static_images`, Flask threw a 500 Internal Server Error:

```text
werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'show_image' with values ['id']. Did you mean 'sound2_image' instead?
127.0.0.1 - - [10/Oct/2026 09:39:15] "GET /static_images HTTP/1.1" 500 -
```

---

## 2. Root Cause Analysis

1. **Blueprint Namespace Requirement**:
   In `gallery2.py`, routes were registered on a Flask Blueprint:
   ```python
   gallery_bp = Blueprint("gallery", __name__)
   ```
   When routes belong to a blueprint, Flask automatically namespaces their endpoints with `<blueprint_name>.<endpoint>`.
   - The route `@gallery_bp.route("/static_images/<int:id>") def show_image(id):` is named `gallery.show_image`.
   - The template strings `GALLERY` and `DETAIL` called `url_for('show_image', id=img.id)` without the blueprint prefix.
   - Flask looked for an un-namespaced `show_image` on the root app, couldn't find it, and failed with `BuildError`.

2. **Root Route Collision**:
   `gallery2.py` previously declared `@gallery_bp.route("/") def home(): return static_images()`. Because `gallery_bp` is registered without a URL prefix in `MediaStudioSD2.py`, this blueprint route intercepted requests to `/`, conflicting with `MediaStudioSD2.py`'s homepage route (`index()`) and triggering redirect loops with the `ensure_index_page` session guard.

3. **Session Check Whitelist**:
   `MediaStudioSD2.py` uses `@app.before_request def ensure_index_page()` to redirect new sessions to the index page unless the requested URL is explicitly exempted. `/static_images` was not listed.

---

## 3. Changes Applied

### A. `gallery2.py`
- **Updated `GALLERY` template**:
  - Changed `url_for('show_image', id=img.id)` to `url_for('gallery.show_image', id=img.id)`.
- **Updated `DETAIL` template**:
  - Changed `url_for('index')` to `url_for('gallery.static_images')` for the "Back to gallery" link.
  - Changed `url_for('show_image', id=prev_id)` to `url_for('gallery.show_image', id=prev_id)`.
  - Changed `url_for('show_image', id=next_id)` to `url_for('gallery.show_image', id=next_id)`.
- **Removed Root Route Collision**:
  - Removed `@gallery_bp.route("/")` so the root path `/` remains exclusively assigned to `MediaStudioSD2.py`'s `index()` handler.

### B. `MediaStudioSD2.py`
- In `ensure_index_page()` (`@app.before_request`), added `/static_images` to the whitelist:
  ```python
  and not request.path.startswith("/static_images")
  ```
  This allows direct navigation to `/static_images` without forcing an unwanted redirect to the index page on fresh browser sessions.

### C. `lone_gallery.py`
- Fixed `url_for('index')` and `return index()` to reference `static_images` so the standalone utility script operates without errors if executed independently.

---

## 4. Verification

After restarting the unified server via `start_studio.sh`, the following routes were tested and confirmed operational:

- **Root Homepage**: `http://localhost:5200/` &rarr; `HTTP 200 OK`
- **Gallery Grid**: `http://localhost:5200/static_images` &rarr; `HTTP 200 OK`
- **Gallery Item Detail**: `http://localhost:5200/static_images/<id>` &rarr; `HTTP 200 OK`
