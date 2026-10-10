import os
from flask import Flask, render_template_string, url_for, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gallery.db"
db = SQLAlchemy(app)

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
SKIP_DIRS = set()            # folder names to ignore, e.g. {"masks", "temp"}
SKIP_NAME_CONTAINS = ("mask",)  # skip files whose name contains any of these
                                # (binary_mask.png, greyscale_mask.png, ...)


# --------------------------------------------------
# MODEL
# --------------------------------------------------
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False, unique=True)  # path relative to static/
    title = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(500), nullable=False, default="")

    @property
    def full_path(self):
        # Computed, not stored: survives moving the project folder.
        return os.path.join(app.static_folder, self.image)


# --------------------------------------------------
# FOLDER -> DB SYNC
# --------------------------------------------------
def sync_images():
    """Make the DB mirror static/: add new files, remove rows whose file is gone."""
    on_disk = {}
    for root, dirs, files in os.walk(app.static_folder):
        # Mutate in place so os.walk actually skips these directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            stem, ext = os.path.splitext(name)
            if ext.lower() not in IMAGE_EXTS:
                continue
            if any(s in name.lower() for s in SKIP_NAME_CONTAINS):
                continue
            rel = os.path.relpath(os.path.join(root, name), app.static_folder)
            rel = rel.replace(os.sep, "/")  # URLs always use forward slashes
            on_disk[rel] = (stem, os.path.dirname(rel))

    known = {row.image: row for row in Image.query.all()}

    for rel, (stem, folder) in on_disk.items():
        if rel not in known:
            db.session.add(Image(image=rel, title=stem, caption=folder))

    for rel, row in known.items():
        if rel not in on_disk:
            db.session.delete(row)

    db.session.commit()


with app.app_context():
    db.create_all()
    sync_images()


# --------------------------------------------------
# TEMPLATES (move to templates/*.html + render_template() when it grows)
# --------------------------------------------------
GALLERY = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Gallery</title>
  <style>
    body { font-family: sans-serif; margin: 1rem 2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }
    figure { margin: 0; }
    img { width: 100%; height: 220px; object-fit: cover; border-radius: 6px; }
    figcaption { font-size: .75rem; word-break: break-all; }
    code { cursor: pointer; color: #555; }
  </style>
</head>
<body>
  <h1>Gallery ({{ images|length }})</h1>
  <div class="grid">
    {% for img in images %}
      <figure>
        <a href="{{ url_for('show_image', id=img.id) }}">
          <img src="{{ url_for('static', filename=img.image) }}"
               alt="{{ img.title }}" loading="lazy">
        </a>
        <figcaption>
          <strong>{{ img.title }}</strong><br>
          <code title="Click to copy"
                onclick="navigator.clipboard.writeText('{{ img.full_path|e }}')">{{ img.full_path }}</code>
        </figcaption>
      </figure>
    {% endfor %}
  </div>
</body>
</html>
"""

DETAIL = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{ img.title }}</title>
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <style>
    body { font-family: sans-serif; margin: 1rem 2rem; }
    .nav { display: flex; justify-content: space-between; margin: 1rem 0; }
    code { background: #eee; padding: 2px 5px; border-radius: 4px; }
  </style>
</head>
<body>
  <p><a href="{{ url_for('static_images') }}">&larr; Back to gallery</a></p>
  <h2>{{ img.title }}</h2>
  <img src="{{ url_for('static', filename=img.image) }}" style="max-width:100%;">
  <p><strong>File:</strong> <code>{{ img.full_path }}</code></p>
  <p><strong>URL:</strong> <code>{{ url_for('static', filename=img.image) }}</code></p>
  <div class="nav">
    <span>
      {% if prev_id %}
        <a href="{{ url_for('show_image', id=prev_id) }}"><i class="fas fa-angle-left"></i> Prev</a>
      {% endif %}
    </span>
    <span>
      {% if next_id %}
        <a href="{{ url_for('show_image', id=next_id) }}">Next <i class="fas fa-angle-right"></i></a>
      {% endif %}
    </span>
  </div>
</body>
</html>
"""


# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.route("/")
def home():
    return static_images()


@app.route("/static_images")
def static_images():
    sync_images()  # picks up new/removed files without a restart
    images = Image.query.order_by(Image.image).all()
    return render_template_string(GALLERY, images=images)


@app.route("/static_images/<int:id>")
def show_image(id):
    img = db.get_or_404(Image, id)
    # Same ordering as the grid (by path), so Prev/Next matches what you see
    prev_img = (Image.query.filter(Image.image < img.image)
                .order_by(Image.image.desc()).first())
    next_img = (Image.query.filter(Image.image > img.image)
                .order_by(Image.image).first())
    return render_template_string(
        DETAIL,
        img=img,
        prev_id=prev_img.id if prev_img else None,
        next_id=next_img.id if next_img else None,
    )


# --------------------------------------------------
# MAIN
# --------------------------------------------------
if __name__ == "__main__":
    # 127.0.0.1 because debug=True exposes the Werkzeug debugger (remote code execution)
    app.run(debug=True, host="127.0.0.1", port=5400)