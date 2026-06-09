from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
# SECRET_KEY: use environment variable in production, fallback for local dev
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smartnotes-dev-fallback-key')

# DATABASE: use DATABASE_URL env var on Render, fallback to local SQLite
database_url = os.environ.get('DATABASE_URL', 'sqlite:///notes.db')
# Render sets postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access your notes.'
login_manager.login_message_category = 'info'


# ─── Models ────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes      = db.relationship('Note',     backref='author', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='owner',  lazy=True, cascade='all, delete-orphan')


class Category(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(80),  nullable=False)
    color   = db.Column(db.String(20),  default='#6c757d')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes   = db.relationship('Note', backref='category', lazy=True)


class Note(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    content     = db.Column(db.Text,        nullable=False)
    is_pinned   = db.Column(db.Boolean,     default=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'),     nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Home ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# ─── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email',    '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('signup.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('signup.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('signup.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('signup.html')

        user = User(username=username, email=email,
                    password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        for name, color in [('Personal','#4f46e5'), ('Work','#0891b2'),
                             ('Study','#059669'),   ('Ideas','#d97706'),
                             ('Important','#dc2626')]:
            db.session.add(Category(name=name, color=color, user_id=user.id))
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password   = request.form.get('password', '')
        user = (User.query.filter_by(username=identifier).first() or
                User.query.filter_by(email=identifier).first())
        if user and check_password_hash(user.password, password):
            login_user(user, remember=request.form.get('remember') == 'on')
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    q           = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)

    query = Note.query.filter_by(user_id=current_user.id)
    if q:
        query = query.filter(db.or_(Note.title.ilike(f'%{q}%'),
                                    Note.content.ilike(f'%{q}%')))
    if category_id:
        query = query.filter_by(category_id=category_id)

    notes      = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    total      = Note.query.filter_by(user_id=current_user.id).count()

    return render_template('dashboard.html', notes=notes, categories=categories,
                           query=q, selected_category=category_id, total_notes=total)


# ─── Notes CRUD ────────────────────────────────────────────────────────────────

@app.route('/notes/new', methods=['GET', 'POST'])
@login_required
def new_note():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        content     = request.form.get('content', '').strip()
        category_id = request.form.get('category_id', type=int)
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return render_template('note_form.html', categories=categories, note=None)
        note = Note(title=title, content=content,
                    user_id=current_user.id, category_id=category_id or None)
        db.session.add(note)
        db.session.commit()
        flash('Note created!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('note_form.html', categories=categories, note=None)


@app.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note       = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        content     = request.form.get('content', '').strip()
        category_id = request.form.get('category_id', type=int)
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return render_template('note_form.html', categories=categories, note=note)
        note.title       = title
        note.content     = content
        note.category_id = category_id or None
        note.updated_at  = datetime.utcnow()
        db.session.commit()
        flash('Note updated!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('note_form.html', categories=categories, note=note)


@app.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted.', 'info')
    return redirect(url_for('dashboard'))


@app.route('/notes/<int:note_id>/pin', methods=['POST'])
@login_required
def pin_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    note.is_pinned = not note.is_pinned
    db.session.commit()
    return jsonify({'pinned': note.is_pinned})


@app.route('/notes/<int:note_id>/view')
@login_required
def view_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    return render_template('view_note.html', note=note)


# ─── Categories ────────────────────────────────────────────────────────────────

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        color = request.form.get('color', '#6c757d')
        if name:
            db.session.add(Category(name=name, color=color, user_id=current_user.id))
            db.session.commit()
            flash('Category added!', 'success')
        else:
            flash('Category name is required.', 'danger')
    cats = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories.html', categories=cats)


@app.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
def delete_category(cat_id):
    cat = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    Note.query.filter_by(category_id=cat_id).update({'category_id': None})
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'info')
    return redirect(url_for('categories'))


# ─── Search API ────────────────────────────────────────────────────────────────

@app.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    results = Note.query.filter(
        Note.user_id == current_user.id,
        db.or_(Note.title.ilike(f'%{q}%'), Note.content.ilike(f'%{q}%'))
    ).limit(6).all()
    return jsonify([{'id': n.id, 'title': n.title} for n in results])


# ─── Init DB + Run ─────────────────────────────────────────────────────────────

# Create tables when the app starts (works for both local and Render)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
