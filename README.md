# Smart Notes Organizer

A full-featured notes management web app built with Python Flask, SQLite, and vanilla HTML/CSS/JS.

## Features
- User signup & login with hashed passwords
- Create, edit, delete, and view notes
- Pin important notes to the top
- Organize notes into color-coded categories/subjects
- Full-text search across note titles and content
- Live autocomplete search dropdown
- Responsive layout for mobile and desktop

## Project Structure

```
smart_notes/
├── app.py                  # Flask application & routes
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    ├── note_form.html
    ├── view_note.html
    └── categories.html
```

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Open your browser at **http://127.0.0.1:5000**

## Notes
- The SQLite database (`notes.db`) is created automatically on first run.
- Default categories (Personal, Work, Study, Ideas, Important) are added for each new user.
- Change `SECRET_KEY` in `app.py` before deploying to production.
