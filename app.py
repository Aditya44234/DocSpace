from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import json
import os
import hashlib
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Simple user storage (in production, use a proper database)
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        users = load_users()
        
        # Check if user already exists
        if email in users:
            return jsonify({'success': False, 'message': 'User already exists'})
        
        # Create new user
        user_id = str(uuid.uuid4())
        users[email] = {
            'id': user_id,
            'name': name,
            'email': email,
            'password': hash_password(password),
            'created_at': datetime.now().isoformat(),
            'files': []
        }
        
        save_users(users)
        
        # Create user's upload directory
        user_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name
        
        return jsonify({'success': True, 'message': 'Account created successfully'})
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'})
        
        users = load_users()
        
        if email not in users:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
        
        user = users[email]
        if user['password'] != hash_password(password):
            return jsonify({'success': False, 'message': 'Invalid credentials'})
        
        session['user_id'] = user['id']
        session['user_email'] = email
        session['user_name'] = user['name']
        
        return jsonify({'success': True, 'message': 'Login successful'})
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    users = load_users()
    user = users.get(session['user_email'], {})
    files = user.get('files', [])
    
    return render_template('dashboard.html', user_name=session['user_name'], files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file:
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1]
        new_filename = f"{file_id}{file_extension}"
        
        user_dir = os.path.join(app.config['UPLOAD_FOLDER'], session['user_id'])
        file_path = os.path.join(user_dir, new_filename)
        
        file.save(file_path)
        
        # Update user's file list
        users = load_users()
        user = users[session['user_email']]
        user['files'].append({
            'id': file_id,
            'original_name': filename,
            'stored_name': new_filename,
            'size': os.path.getsize(file_path),
            'uploaded_at': datetime.now().isoformat()
        })
        
        save_users(users)
        
        return jsonify({'success': True, 'message': 'File uploaded successfully!'})

@app.route('/download/<file_id>')
def download_file(file_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    users = load_users()
    user = users.get(session['user_email'], {})
    
    file_info = None
    for f in user.get('files', []):
        if f['id'] == file_id:
            file_info = f
            break
    
    if not file_info:
        return "File not found", 404
    
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], session['user_id'])
    file_path = os.path.join(user_dir, file_info['stored_name'])
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    return send_file(file_path, as_attachment=True, download_name=file_info['original_name'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)