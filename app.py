from flask import (
    Flask, render_template, request, jsonify, session,
    redirect, url_for, send_file
)
import json, os, hashlib, uuid
from datetime import datetime
from werkzeug.utils import secure_filename

# ── NEW: Google‑OAuth imports ────────────────────────────────────────────
from flask_dance.contrib.google import make_google_blueprint, google
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
# ─────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-key')

# ── Google OAuth client creds (set as env‑vars in Render) ────────────────
app.config["GOOGLE_OAUTH_CLIENT_ID"]     = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

google_bp = make_google_blueprint(
    scope=["profile", "email"],
    redirect_url="/google_login"
)
app.register_blueprint(google_bp, url_prefix="/login")
# ─────────────────────────────────────────────────────────────────────────

app.config['UPLOAD_FOLDER']      = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

# ─────────────────── ROUTES ──────────────────────────────────────────────
@app.route('/')
def index():
    # if already logged‑in (session) → dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')   # plain landing page

# ---------- Google OAuth callback ----------
@app.route('/google_login')
def google_login():
    """
    Handles the redirect from Google's OAuth flow.
    Creates a user entry (if first time) and logs the user in.
    """
    if not google.authorized:
        # First hop: send user to Google's consent screen
        return redirect(url_for("google.login"))

    # Second hop: we have an access‑token; get profile
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return f"Failed to fetch user info: {resp.text}", 400

    data  = resp.json()
    email = data["email"]
    name  = data.get("name", email.split("@")[0])

    users = load_users()
    if email not in users:
        # first‑time Google login → create a user “row”
        user_id = str(uuid.uuid4())
        users[email] = {
            "id": user_id,
            "name": name,
            "email": email,
            "password": None,              # no local password
            "created_at": datetime.now().isoformat(),
            "files": []
        }
        save_users(users)

        # personal folder
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], user_id), exist_ok=True)

    # set session
    user = users[email]
    session['user_id']    = user['id']
    session['user_email'] = email
    session['user_name']  = user['name']
    return redirect(url_for('dashboard'))
# -------------------------------------------

@app.route('/signup', methods=['GET','POST'])
def signup():

    if request.method == 'GET':
        return render_template('signup.html')  # ✅ Add this
    data = request.get_json()
    name, email, password = data.get('name'), data.get('email'), data.get('password')

    if not all([name, email, password]):
        return jsonify(success=False, message="All fields are required")

    users = load_users()
    if email in users:
        return jsonify(success=False, message="User already exists")

    user_id = str(uuid.uuid4())
    users[email] = {
        "id": user_id,
        "name": name,
        "email": email,
        "password": hash_password(password),
        "created_at": datetime.now().isoformat(),
        "files": []
    }
    save_users(users)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], user_id), exist_ok=True)

    session.update(user_id=user_id, user_email=email, user_name=name)
    return jsonify(success=True, message="Account created successfully")

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ── 1️⃣  serve the login page on GET ─────────────────
    if request.method == 'GET':
        return render_template('login.html')   # show your form / page

    # ── 2️⃣  handle the form or fetch POST ───────────────
    # If sent via fetch() → JSON; if <form> → request.form
    data = request.get_json(silent=True) or request.form

    email    = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify(success=False,
                       message="Email and password are required")

    users = load_users()
    user  = users.get(email)
    if not user or user['password'] != hash_password(password):
        return jsonify(success=False, message="Invalid credentials")

    session.update(user_id=user['id'],
                   user_email=email,
                   user_name=user['name'])
    return jsonify(success=True, message="Login successful")


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    users = load_users()
    user  = users.get(session['user_email'], {})
    return render_template('dashboard.html',
                           user_name=session['user_name'],
                           files=user.get('files', []))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify(success=False, message="Not authenticated")

    file = request.files.get('file')
    if not file or not file.filename or file.filename == '':
        return jsonify(success=False, message='No file selected')

    filename       = secure_filename(file.filename)
    file_id        = str(uuid.uuid4())
    ext            = os.path.splitext(filename)[1]
    new_filename   = f"{file_id}{ext}"

    user_dir  = os.path.join(app.config['UPLOAD_FOLDER'], session['user_id'])
    file_path = os.path.join(user_dir, new_filename)
    os.makedirs(user_dir, exist_ok=True)
    file.save(file_path)

    users = load_users()
    user  = users[session['user_email']]
    user['files'].append({
        "id": file_id,
        "original_name": filename,
        "stored_name": new_filename,
        "size": os.path.getsize(file_path),
        "uploaded_at": datetime.now().isoformat()
    })
    save_users(users)
    return jsonify(success=True, message="File uploaded successfully!")

@app.route('/download/<file_id>')
def download_file(file_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    users = load_users()
    user  = users.get(session['user_email'], {})
    file  = next((f for f in user.get('files', []) if f['id'] == file_id), None)
    if not file:
        return "File not found", 404

    path = os.path.join(app.config['UPLOAD_FOLDER'], session['user_id'], file['stored_name'])
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True, download_name=file['original_name'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
