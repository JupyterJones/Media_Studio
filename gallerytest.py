import os
from flask import Flask, render_template_string, url_for, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gallery.db"
db = SQLAlchemy(app)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False, unique=True)  # path relative to static/
    title = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(500), nullable=False, default="")


def sync_images():
    """Scan static/ recursively and add a row for every image not yet in the DB."""
    known = {row.image for row in Image.query.with_entities(Image.image)}
    for root, _dirs, files in os.walk(app.static_folder):
        for name in sorted(files):
            stem, ext = os.path.splitext(name)
            if ext.lower() not in IMAGE_EXTS:
                continue
            # Path relative to static/, with forward slashes (URLs are not OS paths)
            rel = os.path.relpath(os.path.join(root, name), app.static_folder)
            rel = rel.replace(os.sep, "/")
            if rel not in known:
                db.session.add(Image(image=rel, title=stem, caption=os.path.dirname(rel)))
    db.session.commit()


with app.app_context():
    db.create_all()
    sync_images()


GALLERY = """
<!doctype html>
<html>
<head>
  <title>Gallery</title>
  <style>
    body { font-family: sans-serif; margin: 1rem 2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }
    figure { margin: 0; }
    img { width: 100%; height: 220px; object-fit: cover; border-radius: 6px; }
    figcaption { font-size: .8rem; word-break: break-all; }
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
        <figcaption><strong>{{ img.title }}</strong><br>{{ img.caption }}</figcaption>
      </figure>
    {% endfor %}
  </div>
</body>
</html>
"""

DETAIL = """
<!doctype html>
<html>
<head><title>{{ img.title }}</title></head>
<body style="font-family: sans-serif; margin: 1rem 2rem;">
  <p><a href="{{ url_for('index') }}">&larr; Back to gallery</a></p>
  <h2>{{ img.title }}</h2>
  <img src="{{ url_for('static', filename=img.image) }}" style="max-width:100%;">
  <p>{{ img.caption }}</p>
</body>
</html>
"""


@app.route("/images")
def index():
    sync_images()  # picks up new files without restarting the server
    images = Image.query.order_by(Image.image).all()
    return render_template_string(GALLERY, images=images)


@app.route("/images/<int:id>")
def show_image(id):
    img = db.get_or_404(Image, id)
    return render_template_string(DETAIL, img=img)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5400)