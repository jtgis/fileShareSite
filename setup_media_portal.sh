#!/usr/bin/env bash
set -e

PROJECT_DIR="${PROJECT_DIR:-$HOME/media_portal}"

echo "Rebuilding File Share Site in: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

mkdir -p templates static collections

#######################################
# app.py
#######################################
cat > app.py << 'EOF'
#!/usr/bin/env python3
import os
import sqlite3
from functools import wraps
from flask import (
    Flask, g, render_template, request, redirect,
    url_for, session, flash, send_from_directory, abort
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import safe_join

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "site.db")
MEDIA_ROOT = os.path.join(BASE_DIR, "collections")

VIDEO_EXTS = {"mp4", "webm", "ogg", "m4v"}
AUDIO_EXTS = {"mp3", "wav", "ogg", "flac", "m4a"}  # mp3 supported
IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp"}
PDF_EXTS = {"pdf"}


def ensure_db_schema():
    """Create or upgrade the collections table (adds is_admin if missing)."""
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            directory TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    cur.execute("PRAGMA table_info(collections)")
    cols = [row[1] for row in cur.fetchall()]
    if "is_admin" not in cols:
        cur.execute(
            "ALTER TABLE collections ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"
        )
    conn.commit()
    conn.close()


ensure_db_schema()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-production")
    os.makedirs(MEDIA_ROOT, exist_ok=True)

    # ---------- DB helpers ----------

    def get_db():
        if "db" not in g:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            g.db = conn
        return g.db

    @app.teardown_appcontext
    def close_db(exception=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def get_collection_by_id(collection_id):
        db = get_db()
        cur = db.execute("SELECT * FROM collections WHERE id = ?", (collection_id,))
        return cur.fetchone()

    def get_collection_root(collection):
        directory = collection["directory"]
        return os.path.join(MEDIA_ROOT, directory)

    def get_file_category(ext):
        ext = ext.lower()
        if ext in VIDEO_EXTS:
            return "video"
        if ext in AUDIO_EXTS:
            return "audio"
        if ext in IMAGE_EXTS:
            return "image"
        if ext in PDF_EXTS:
            return "pdf"
        return "other"

    def format_bytes(size):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def list_files_for_collection(collection):
        root = get_collection_root(collection)
        files = []
        if not os.path.isdir(root):
            return files

        for dirpath, dirnames, filenames in os.walk(root):
            for fname in filenames:
                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, root)
                ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
                category = get_file_category(ext)
                size = os.path.getsize(full_path)
                files.append(
                    {
                        "name": fname,
                        "rel_path": rel_path.replace("\\", "/"),
                        "ext": ext,
                        "category": category,
                        "size": format_bytes(size),
                    }
                )
        files.sort(key=lambda f: f["rel_path"])
        return files

    # ---------- Auth helpers ----------

    def current_collection():
        cid = session.get("collection_id")
        if not cid:
            return None
        return get_collection_by_id(cid)

    def login_required(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if "collection_id" not in session:
                return redirect(url_for("login", next=request.path))
            return view(**kwargs)

        return wrapped_view

    def admin_required(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if "collection_id" not in session or not session.get("is_admin"):
                abort(403)
            return view(**kwargs)

        return wrapped_view

    # ---------- User-facing routes ----------

    @app.route("/")
    @login_required
    def index():
        collection = current_collection()
        if not collection:
            session.clear()
            return redirect(url_for("login"))

        # Admin accounts are admin-only: no personal collection view
        if collection["is_admin"]:
            return redirect(url_for("admin_dashboard"))

        files = list_files_for_collection(collection)
        return render_template(
            "dashboard.html",
            collection=collection,
            files=files,
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            db = get_db()
            cur = db.execute(
                "SELECT * FROM collections WHERE username = ?", (username,)
            )
            row = cur.fetchone()

            if row and check_password_hash(row["password_hash"], password):
                session.clear()
                session["collection_id"] = row["id"]
                session["is_admin"] = bool(row["is_admin"])
                flash("Logged in successfully.", "success")

                # Admin: always go to admin dashboard (admin-only account)
                if session["is_admin"]:
                    return redirect(url_for("admin_dashboard"))

                next_url = request.args.get("next")
                return redirect(next_url or url_for("index"))
            else:
                flash("Invalid username or password.", "danger")

        # hide_header makes login page even more minimal
        return render_template("login.html", hide_header=True)

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    @app.route("/media/<path:filepath>")
    @login_required
    def serve_media(filepath):
        collection = current_collection()
        if not collection:
            abort(403)

        # Admin should not have a personal media collection
        if collection["is_admin"]:
            abort(403)

        root = get_collection_root(collection)
        full_path = safe_join(root, filepath)
        if full_path is None or not os.path.isfile(full_path):
            abort(404)

        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        return send_from_directory(directory, filename, as_attachment=False)

    @app.route("/download/<path:filepath>")
    @login_required
    def download_file(filepath):
        collection = current_collection()
        if not collection:
            abort(403)

        if collection["is_admin"]:
            abort(403)

        root = get_collection_root(collection)
        full_path = safe_join(root, filepath)
        if full_path is None or not os.path.isfile(full_path):
            abort(404)

        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        return send_from_directory(directory, filename, as_attachment=True)

    @app.route("/view/<path:filepath>")
    @login_required
    def view_file(filepath):
        collection = current_collection()
        if not collection:
            abort(403)

        if collection["is_admin"]:
            abort(403)

        root = get_collection_root(collection)
        full_path = safe_join(root, filepath)
        if full_path is None or not os.path.isfile(full_path):
            abort(404)

        filename = os.path.basename(full_path)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        category = get_file_category(ext)

        return render_template(
            "view_file.html",
            collection=collection,
            filepath=filepath,
            filename=filename,
            category=category,
        )

    # ---------- Admin routes ----------

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        db = get_db()
        rows = db.execute(
            "SELECT id, username, display_name, directory, is_admin FROM collections ORDER BY id"
        ).fetchall()
        return render_template("admin_dashboard.html", collections=rows)

    @app.route("/admin/collections/new", methods=["GET", "POST"])
    @admin_required
    def admin_new_collection():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            display_name = request.form.get("display_name", "").strip()
            directory = request.form.get("directory", "").strip()
            password = request.form.get("password", "")
            is_admin = 1 if request.form.get("is_admin") == "on" else 0

            if not username or not password:
                flash("Username and password are required.", "danger")
                return redirect(url_for("admin_new_collection"))

            # For admin-only accounts, directory can be a dummy name (not used)
            if not directory:
                if is_admin:
                    directory = f"admin_{username}"
                else:
                    flash("Directory is required for non-admin users.", "danger")
                    return redirect(url_for("admin_new_collection"))

            password_hash = generate_password_hash(password)

            if not is_admin:
                collection_path = os.path.join(MEDIA_ROOT, directory)
                os.makedirs(collection_path, exist_ok=True)

            db = get_db()
            try:
                db.execute(
                    """
                    INSERT INTO collections (
                        username, password_hash, display_name, directory, is_admin
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, password_hash, display_name or username, directory, is_admin),
                )
                db.commit()
                role = "admin" if is_admin else "user"
                flash(f"{role.title()} account created successfully.", "success")
                return redirect(url_for("admin_dashboard"))
            except sqlite3.IntegrityError:
                flash("Username already exists.", "danger")

        return render_template("admin_new_collection.html")

    @app.route("/admin/collections/<int:collection_id>/reset_password", methods=["GET", "POST"])
    @admin_required
    def admin_reset_password(collection_id):
        db = get_db()
        collection = get_collection_by_id(collection_id)
        if not collection:
            abort(404)

        if request.method == "POST":
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            if not password:
                flash("Password is required.", "danger")
                return redirect(url_for("admin_reset_password", collection_id=collection_id))
            if password != confirm:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("admin_reset_password", collection_id=collection_id))

            password_hash = generate_password_hash(password)
            db.execute(
                "UPDATE collections SET password_hash = ? WHERE id = ?",
                (password_hash, collection_id),
            )
            db.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_reset_password.html", collection=collection)

    @app.route("/admin/collections/<int:collection_id>/delete", methods=["POST"])
    @admin_required
    def admin_delete_collection(collection_id):
        db = get_db()
        collection = get_collection_by_id(collection_id)
        if not collection:
            abort(404)

        if collection["is_admin"]:
            admin_count = db.execute(
                "SELECT COUNT(*) FROM collections WHERE is_admin = 1"
            ).fetchone()[0]
            if admin_count <= 1:
                flash("Cannot delete the last admin account.", "danger")
                return redirect(url_for("admin_dashboard"))

        db.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        db.commit()
        flash("Account deleted from database. Files on disk remain.", "info")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/collections/<int:collection_id>/files")
    @admin_required
    def admin_collection_files(collection_id):
        collection = get_collection_by_id(collection_id)
        if not collection:
            abort(404)

        if collection["is_admin"]:
            flash("Admin accounts do not have a media collection.", "info")
            return redirect(url_for("admin_dashboard"))

        files = list_files_for_collection(collection)
        return render_template(
            "admin_files.html",
            collection=collection,
            files=files,
        )

    @app.route("/admin/collections/<int:collection_id>/files/delete", methods=["POST"])
    @admin_required
    def admin_delete_file(collection_id):
        collection = get_collection_by_id(collection_id)
        if not collection:
            abort(404)

        if collection["is_admin"]:
            flash("Admin accounts do not have media files.", "danger")
            return redirect(url_for("admin_dashboard"))

        rel_path = request.form.get("rel_path", "")
        if not rel_path:
            flash("No file specified.", "danger")
            return redirect(url_for("admin_collection_files", collection_id=collection_id))

        root = get_collection_root(collection)
        full_path = safe_join(root, rel_path)
        if full_path is None or not os.path.isfile(full_path):
            flash("File not found.", "danger")
        else:
            try:
                os.remove(full_path)
                flash("File deleted.", "success")
            except OSError as e:
                flash(f"Error deleting file: {e}", "danger")

        return redirect(url_for("admin_collection_files", collection_id=collection_id))

    @app.route("/admin/collections/<int:collection_id>/view/<path:filepath>")
    @admin_required
    def admin_view_file(collection_id, filepath):
        """
        Admin 'view as user' – resolve paths using the target collection.
        """
        collection = get_collection_by_id(collection_id)
        if not collection:
            abort(404)

        root = get_collection_root(collection)
        full_path = safe_join(root, filepath)
        if full_path is None or not os.path.isfile(full_path):
            abort(404)

        filename = os.path.basename(full_path)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        category = get_file_category(ext)

        return render_template(
            "view_file.html",
            collection=collection,
            filepath=filepath,
            filename=filename,
            category=category,
        )

    @app.route("/help")
    def help_page():
        """Public help page with basic info."""
        return render_template("help.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
EOF

#######################################
# db_init.py
#######################################
cat > db_init.py << 'EOF'
#!/usr/bin/env python3
import os
import sqlite3
import getpass

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "site.db")
MEDIA_ROOT = os.path.join(BASE_DIR, "collections")


def init_db():
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            directory TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        );
        """
    )

    cur.execute("PRAGMA table_info(collections)")
    cols = [row[1] for row in cur.fetchall()]
    if "is_admin" not in cols:
        cur.execute(
            "ALTER TABLE collections ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"
        )

    conn.commit()
    return conn


def add_collection(conn):
    print("\n=== Add a new account ===")
    username = input("Username (for login): ").strip()
    display_name = input("Display name (for collections, optional): ").strip() or username
    directory = input(
        "Directory under 'collections/' (blank for admin-only): "
    ).strip()
    admin_flag = input("Is this user an admin? [y/N]: ").strip().lower()
    is_admin = 1 if admin_flag == "y" else 0

    if not username:
        print("Username is required.")
        return

    if not directory:
        if is_admin:
            directory = f"admin_{username}"
            print(f"(Admin-only account; using dummy directory: {directory})")
        else:
            print("Directory is required for non-admin users.")
            return

    password = getpass.getpass("Password: ")
    password2 = getpass.getpass("Confirm password: ")
    if password != password2:
        print("Passwords do not match.")
        return

    password_hash = generate_password_hash(password)

    if not is_admin:
        collection_path = os.path.join(MEDIA_ROOT, directory)
        os.makedirs(collection_path, exist_ok=True)
    else:
        collection_path = "(admin-only; no media folder is required)"

    try:
        conn.execute(
            """
            INSERT INTO collections (
                username, password_hash, display_name, directory, is_admin
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, password_hash, display_name, directory, is_admin),
        )
        conn.commit()
        role = "admin" if is_admin else "user"
        print(
            f"Account '{display_name}' ({role}) created. "
            f"Media directory: {collection_path}"
        )
    except sqlite3.IntegrityError:
        print("Error: username already exists.")


if __name__ == "__main__":
    conn = init_db()
    print("Database initialized at:", DB_PATH)

    while True:
        choice = input("\nAdd an account? [y/N]: ").strip().lower()
        if choice == "y":
            add_collection(conn)
        else:
            break

    conn.close()
    print("Done.")
EOF

#######################################
# requirements, install, run, service
#######################################
cat > requirements.txt << 'EOF'
Flask
Werkzeug
EOF

cat > install.sh << 'EOF'
#!/usr/bin/env bash
set -e

sudo apt update
sudo apt install -y python3-venv python3-pip sqlite3

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python db_init.py

echo
echo "Installation complete."
echo "To run the app: ./run.sh"
EOF

cat > run.sh << 'EOF'
#!/usr/bin/env bash
set -e

source venv/bin/activate

export SECRET_KEY="change-this-to-a-long-random-string"
export FLASK_APP=app.py
export FLASK_ENV=production

flask run --host=0.0.0.0 --port=8000
EOF

cat > media_portal.service << 'EOF'
[Unit]
Description=File Share Site
After=network.target

[Service]
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/path/to/media_portal
Environment="SECRET_KEY=change-this-to-a-long-random-string"
Environment="FLASK_APP=app.py"
Environment="FLASK_ENV=production"
ExecStart=/path/to/media_portal/venv/bin/flask run --host=0.0.0.0 --port=8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

#######################################
# Templates
#######################################
cat > templates/base.html << 'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{% block title %}File Share Site{% endblock %}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link
      rel="stylesheet"
      href="{{ url_for('static', filename='style.css') }}"
    />
  </head>
  <body>
    {% if not hide_header %}
    <header class="topbar">
      <div class="topbar-inner">
        <div class="logo">
          <a href="{{ url_for('index') }}">File Share Site</a>
        </div>
        <nav class="nav">
          {% if session.get("is_admin") %}
          <a href="{{ url_for('admin_dashboard') }}">Admin</a>
          {% endif %}
          {% if session.collection_id %}
          <a href="{{ url_for('logout') }}">Logout</a>
          {% endif %}
        </nav>
      </div>
    </header>
    {% endif %}

    <main class="main">
      {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
      <div class="flashes">
        {% for category, message in messages %}
        <div class="flash flash-{{ category }}">{{ message }}</div>
        {% endfor %}
      </div>
      {% endif %}
      {% endwith %}

      {% block content %}{% endblock %}

      {% if session.collection_id and not session.get("is_admin") %}
      <footer class="site-footer">
        If you have any issues, please see our
        <a href="{{ url_for('help_page') }}">help guide</a>
        or contact
        <a href="mailto:EMAIL@gmail.com">EMAIL@gmail.com</a>.
      </footer>
      {% endif %}
    </main>
  </body>
</html>
EOF

cat > templates/login.html << 'EOF'
{% extends "base.html" %}
{% block title %}Login - File Share Site{% endblock %}
{% block content %}
<div class="card card-login">
  <form method="post" class="form form-login">
    <input
      type="text"
      name="username"
      placeholder="Username"
      autocomplete="username"
      required
    />
    <input
      type="password"
      name="password"
      placeholder="Password"
      autocomplete="current-password"
      required
    />
    <button type="submit">Log in</button>
  </form>
</div>
{% endblock %}
EOF

cat > templates/dashboard.html << 'EOF'
{% extends "base.html" %}
{% block title %}Collections - File Share Site{% endblock %}
{% block content %}
<div class="card">
  <h1>
    Welcome to the {{ collection["display_name"] or collection["username"] }} media collection
  </h1>
  <p>Here are the files in this collection.</p>

  {% if files %}
  <div class="table-wrapper">
    <table class="file-table">
      <thead>
        <tr>
          <th>File name</th>
          <th>Type</th>
          <th>Size</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for f in files %}
        <tr>
          <td data-label="File name">{{ f.name }}</td>
          <td data-label="Type" class="file-type">
            {% if f.category == "video" %}
            🎥 Video
            {% elif f.category == "audio" %}
            🎵 Audio
            {% elif f.category == "image" %}
            🖼️ Image
            {% elif f.category == "pdf" %}
            📄 PDF
            {% else %}
            📁 Other
            {% endif %}
          </td>
          <td data-label="Size">{{ f.size }}</td>
          <td data-label="Actions">
            {% if f.category != "other" %}
            <a href="{{ url_for('view_file', filepath=f.rel_path) }}">View</a>
            {% endif %}
            <a href="{{ url_for('download_file', filepath=f.rel_path) }}"
              >Download</a
            >
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <p>No files found. Upload or copy files into this collection's directory on the server.</p>
  {% endif %}
</div>
{% endblock %}
EOF

cat > templates/view_file.html << 'EOF'
{% extends "base.html" %}
{% block title %}View {{ filename }} - File Share Site{% endblock %}
{% block content %}
<div class="card">
  <h1 class="file-title">{{ filename }}</h1>
  <p>
    <a href="{{ url_for('download_file', filepath=filepath) }}">Download</a> |
    <a href="{{ url_for('index') }}">Back to files</a>
  </p>

  {% if category == "video" %}
  <video
    controls
    style="max-width: 100%; height: auto;"
    src="{{ url_for('serve_media', filepath=filepath) }}"
  >
    Your browser does not support the video tag.
  </video>

  {% elif category == "audio" %}
  <audio controls style="width: 100%;">
    <source src="{{ url_for('serve_media', filepath=filepath) }}" />
    Your browser does not support the audio element.
  </audio>

  {% elif category == "image" %}
  <img
    src="{{ url_for('serve_media', filepath=filepath) }}"
    alt="{{ filename }}"
    style="max-width: 100%; height: auto;"
  />

  {% elif category == "pdf" %}
  <iframe
    src="{{ url_for('serve_media', filepath=filepath) }}"
    style="width: 100%; height: 80vh; border: 1px solid #ccc;"
  >
  </iframe>

  {% else %}
  <p>This file type cannot be previewed. Please download it.</p>
  {% endif %}
</div>
{% endblock %}
EOF

cat > templates/admin_dashboard.html << 'EOF'
{% extends "base.html" %}
{% block title %}Admin - File Share Site{% endblock %}
{% block content %}
<div class="card">
  <h1>Admin Dashboard</h1>
  <p>Manage user collections and media content.</p>

  <p>
    <a href="{{ url_for('admin_new_collection') }}">Add new account</a>
  </p>

  <div class="table-wrapper">
    <table class="file-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Display Name</th>
          <th>Directory</th>
          <th>Role</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for c in collections %}
        <tr>
          <td data-label="ID">{{ c.id }}</td>
          <td data-label="Username">{{ c.username }}</td>
          <td data-label="Display Name">{{ c.display_name or c.username }}</td>
          <td data-label="Directory">{{ c.directory }}</td>
          <td data-label="Role">{{ "Admin" if c.is_admin else "User" }}</td>
          <td data-label="Actions">
            {% if not c.is_admin %}
            <a href="{{ url_for('admin_collection_files', collection_id=c.id) }}">Files</a>
            {% endif %}
            <a href="{{ url_for('admin_reset_password', collection_id=c.id) }}">Reset password</a>
            <form
              method="post"
              action="{{ url_for('admin_delete_collection', collection_id=c.id) }}"
              style="display:inline;"
              onsubmit="return confirm('Delete this account from the database? Files on disk will remain.');"
            >
              <button type="submit" class="link-button">Delete</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
EOF

cat > templates/admin_new_collection.html << 'EOF'
{% extends "base.html" %}
{% block title %}New Account - File Share Site{% endblock %}
{% block content %}
<div class="card">
  <h1>Add New Account</h1>
  <form method="post" class="form">
    <label>
      Username
      <input type="text" name="username" required />
    </label>
    <label>
      Display name
      <input type="text" name="display_name" />
    </label>
    <label>
      Directory under "collections/" (for non-admin users)
      <input
        type="text"
        name="directory"
        placeholder="e.g. family_a (leave blank for admin-only)"
      />
    </label>
    <label>
      Password
      <input type="password" name="password" required />
    </label>
    <label class="checkbox-label">
      <input type="checkbox" name="is_admin" />
      Make this user an admin (admin-only account if directory left blank)
    </label>
    <button type="submit">Create account</button>
  </form>
</div>
{% endblock %}
EOF

cat > templates/admin_reset_password.html << 'EOF'
{% extends "base.html" %}
{% block title %}Reset Password - File Share Site{% endblock %}
{% block content %}
<div class="card">
  <h1>Reset Password</h1>
  <p>For user: <strong>{{ collection["username"] }}</strong></p>
  <form method="post" class="form">
    <label>
      New password
      <input type="password" name="password" required />
    </label>
    <label>
      Confirm new password
      <input type="password" name="confirm_password" required />
    </label>
    <button type="submit">Update password</button>
  </form>
</div>
{% endblock %}
EOF

cat > templates/admin_files.html << 'EOF'
{% extends "base.html" %}
{% block title %}Files - {{ collection["display_name"] or collection["username"] }}{% endblock %}
{% block content %}
<div class="card">
  <h1>Files for {{ collection["display_name"] or collection["username"] }}</h1>
  <p>Directory: <code>{{ collection["directory"] }}</code></p>

  {% if files %}
  <div class="table-wrapper">
    <table class="file-table">
      <thead>
        <tr>
          <th>File name</th>
          <th>Type</th>
          <th>Size</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for f in files %}
        <tr>
          <td data-label="File name">{{ f.name }}</td>
          <td data-label="Type" class="file-type">
            {% if f.category == "video" %}
            🎥 Video
            {% elif f.category == "audio" %}
            🎵 Audio
            {% elif f.category == "image" %}
            🖼️ Image
            {% elif f.category == "pdf" %}
            📄 PDF
            {% else %}
            📁 Other
            {% endif %}
          </td>
          <td data-label="Size">{{ f.size }}</td>
          <td data-label="Actions">
            <a href="{{ url_for('admin_view_file', collection_id=collection['id'], filepath=f.rel_path) }}">View as user</a>
            <form
              method="post"
              action="{{ url_for('admin_delete_file', collection_id=collection['id']) }}"
              style="display:inline;"
              onsubmit="return confirm('Delete this file permanently?');"
            >
              <input type="hidden" name="rel_path" value="{{ f.rel_path }}" />
              <button type="submit" class="link-button">Delete file</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <p>No files found in this collection.</p>
  {% endif %}
</div>
{% endblock %}
EOF

cat > templates/help.html << 'EOF'
{% extends "base.html" %}
{% block title %}Help - File Share Site{% endblock %}
{% block content %}
<div class="card">
  <h1>Help &amp; Information</h1>

  <h2>What is this site?</h2>
  <p>
    This site is a private File Share Site where you can securely access and
    download files that have been shared with you.
  </p>

  <h2>Logging in</h2>
  <ul>
    <li>Use the username and password that were provided to you.</li>
    <li>If you forget your password, contact the site administrator.</li>
  </ul>

  <h2>Viewing and downloading files</h2>
  <ul>
    <li>After logging in, you will see a list of files in your collection.</li>
    <li>Use <strong>View</strong> to open supported files (video, audio, images, PDF).</li>
    <li>Use <strong>Download</strong> to save a copy of any file to your device.</li>
  </ul>

  <h2>Need more help?</h2>
  <p>
    If you run into any problems or have questions, please contact
    <a href="mailto:EMAIL@gmail.com">EMAIL@gmail.com</a>.
  </p>
</div>
{% endblock %}
EOF

#######################################
# static/style.css
#######################################
cat > static/style.css << 'EOF'
body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;
  background: #f4f5f7;
}

.topbar {
  background: #1f2933;
  color: #fff;
  padding: 0.5rem 1.5rem;
}

.topbar-inner {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo a {
  color: #fff;
  text-decoration: none;
  font-weight: 600;
}

.nav a {
  color: #fff;
  text-decoration: none;
  margin-left: 1rem;
}

.main {
  max-width: 960px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(15, 23, 42, 0.1);
}

.card h1 {
  margin-top: 0;
}

.form label {
  display: block;
  margin-bottom: 1rem;
}

.form input[type="text"],
.form input[type="password"] {
  width: 100%;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #cbd2d9;
  margin-top: 0.25rem;
  box-sizing: border-box;
}

.form button {
  background: #2563eb;
  border: none;
  color: #fff;
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  cursor: pointer;
}

.form button:hover {
  background: #1d4ed8;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.flashes {
  margin-bottom: 1rem;
}

.flash {
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.flash-success {
  background: #dcfce7;
  color: #14532d;
}

.flash-danger {
  background: #fee2e2;
  color: #7f1d1d;
}

.flash-info {
  background: #e0f2fe;
  color: #0c4a6e;
}

.file-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.file-table th,
.file-table td {
  padding: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.file-table th {
  text-align: left;
  background: #f9fafb;
}

.file-table tr:hover {
  background: #f3f4f6;
}

.file-table a {
  color: #2563eb;
  text-decoration: none;
  margin-right: 0.5rem;
}

.file-table a:hover {
  text-decoration: underline;
}

.link-button {
  background: none;
  border: none;
  color: #dc2626;
  cursor: pointer;
  padding: 0;
  font-size: 0.9rem;
}

.link-button:hover {
  text-decoration: underline;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
}

/* Login page - super minimal */
.card-login {
  max-width: 360px;
  margin: 5rem auto;
}

.form-login {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-login input[type="text"],
.form-login input[type="password"] {
  width: 100%;
  padding: 0.7rem;
  border-radius: 6px;
  border: 1px solid #cbd2d9;
  box-sizing: border-box;
  font-size: 0.95rem;
}

.form-login button {
  width: 100%;
}

/* Long filenames on view page */
.file-title {
  word-wrap: break-word;
  overflow-wrap: anywhere;
  word-break: break-word;
}

/* Footer message for logged-in users */
.site-footer {
  margin-top: 2rem;
  font-size: 0.85rem;
  color: #6b7280;
}

/* Mobile-friendly: turn table into stacked cards */
@media (max-width: 600px) {
  .main {
    margin: 1.5rem auto;
    padding: 0 0.75rem;
  }

  .card {
    padding: 1.25rem;
  }

  .topbar-inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .nav a {
    margin-left: 0;
    margin-right: 1rem;
  }

  .card-login {
    margin: 3rem auto;
  }

  .file-table {
    border: 0;
  }

  .file-table thead {
    border: 0;
    clip: rect(0 0 0 0);
    height: 1px;
    margin: -1px;
    overflow: hidden;
    padding: 0;
    position: absolute;
    width: 1px;
  }

  .file-table,
  .file-table tbody,
  .file-table tr,
  .file-table td {
    display: block;
    width: 100%;
  }

  .file-table tr {
    margin-bottom: 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: #fff;
  }

  .file-table td {
    border-bottom: 1px solid #e5e7eb;
    padding: 0.4rem 0.6rem;
    font-size: 0.85rem;
  }

  .file-table td:last-child {
    border-bottom: 0;
  }

  .file-table td::before {
    content: attr(data-label);
    font-weight: 600;
    display: block;
    margin-bottom: 0.15rem;
    font-size: 0.75rem;
    text-transform: uppercase;
    color: #6b7280;
  }

  .file-title {
    font-size: 1rem;
  }
}
EOF

#######################################
# Permissions + summary
#######################################
chmod +x install.sh run.sh db_init.py app.py

echo
echo "======================================"
echo " File Share Site code created/updated in:"
echo "   $PROJECT_DIR"
echo "--------------------------------------"
echo "Next steps:"
echo "  cd \"$PROJECT_DIR\""
echo "  ./install.sh      # install deps and add accounts (mark at least one as admin)"
echo "  ./run.sh          # start the server on port 8000"
echo "======================================"
