# 📁 DocSpace

DocSpace is a secure, minimal web application where users can sign up, upload important documents (like Aadhaar, certificates, etc.), and access them from any device. Built with **Flask**, **HTML5**, **CSS**, and **JavaScript**, it offers simple authentication and per-user storage using a local JSON-based system.

---

## 🚀 Features

- 🔐 User Authentication (Sign Up / Log In)
- 📤 Upload and store personal documents (up to 16MB)
- 📥 Download documents anytime
- 📁 Per-user isolated upload folders
- 🗂 Dashboard view of uploaded files
- 🔑 Secure password storage with SHA-256 hashing
- 💾 Lightweight backend using `users.json` (swap for real DB in production)

---

## 🛠️ Tech Stack

- **Backend:** Python + Flask
- **Frontend:** HTML5, CSS3, JavaScript
- **Storage:** Local file system (`/uploads`)
- **Session Management:** Flask sessions
- **Authentication:** Email + Password (SHA-256 hash)

---

## 📂 Folder Structure

```
DocSpace/
│
├── app.py                 # Flask app logic
├── users.json             # Simple file-based user data
├── requirements.txt       # Python dependencies
│
├── templates/             # HTML templates (Jinja2)
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   └── dashboard.html
│
├── static/                # Your CSS/JS assets
└── uploads/               # Per-user upload folders (auto-created)
```

---

## ⚙️ Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/docspace.git
cd docspace
```

### 2. Set up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the App
```bash
python app.py
```

Visit **http://localhost:5000** in your browser to start using DocSpace.

---

## 🔒 Important Notes

- In production:
  - Replace `secret_key` with a strong, secure environment variable.
  - Move `users.json` and `uploads/` outside public directories.
  - Implement proper database and authentication mechanisms.
  - Use HTTPS for secure file transfer.

---

## 🔮 Future Improvements

- 🔍 Add search and filter by document name or date
- 🧾 PDF/Image preview in browser
- 🗃️ Tagging system for organizing files
- 🔄 Version history / file recovery
- 📱 Progressive Web App (PWA) support
- ☁️ Cloud storage with AWS S3 or Firebase
- 🔑 OAuth login (Google/GitHub)

---

## 🤝 Contributing

This project is open for contributions!  
If you'd like to build a proper backend or implement database/cloud support, feel free to fork the repo and submit a pull request.

---

## 📃 License

This project is licensed under the [MIT License](LICENSE).

---

### 🙏 Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [Werkzeug](https://werkzeug.palletsprojects.com/)
- The open-source community

> _“Your documents. Your space. Anywhere.”_ – **DocSpace**
