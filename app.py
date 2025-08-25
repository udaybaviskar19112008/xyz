# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, g
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename # For secure filename handling
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import re
import spacy
import pickle
import pdfplumber

app = Flask(__name__)
# IMPORTANT: Change this to a strong, random key!
app.secret_key = 'your_super_secret_key_here_for_real'

# Load AI model and tokenizer
MODEL_PATH = os.environ.get('MODEL_PATH', 'my_model.h5')
PKL_PATH = os.environ.get('PKL_PATH', 'tokenizer_new1.pkl')

try:
    with open(PKL_PATH, 'rb') as f:
        tokenizer = pickle.load(f)
    keras_model = load_model(MODEL_PATH)
    nlp = spacy.load('en_core_web_sm')
    print("AI model loaded successfully!")
except Exception as e:
    print(f"Error loading AI model: {e}")
    tokenizer = None
    keras_model = None
    nlp = None

# AI model constants
RESUME_LEN = 360
JOB_LEN = 462

# Database setup
DATABASE = 'users.db'

# Upload folder configuration
UPLOAD_FOLDER = 'resumes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# AI prediction helper functions
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    return text.strip()

def preprocessing(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.replace("\n", " ").strip()
    if nlp:
        text = [token.lemma_ for token in nlp(text) if not token.is_stop and not token.is_punct]
        return " ".join(text)
    return text

def shorting(tokens):
    keyword = "objective"
    tokens_lower = [t.lower() for t in tokens]
    if keyword in tokens_lower:
        index = tokens_lower.index(keyword)
        return tokens[index + 1:]
    return tokens

def text_to_vectors(text, max_len):
    if tokenizer:
        seq = tokenizer.texts_to_sequences([text])
        return pad_sequences(seq, maxlen=max_len, padding='pre')
    return None

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # This makes rows behave like dictionaries
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize database schema
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                major TEXT,
                status TEXT,
                resume_filename TEXT,     -- New: Stores the filename of the uploaded resume
                resume_upload_date TEXT   -- New: Stores the date of upload
            )
        ''')
        # Add a table for job descriptions associated with students if needed
        # For this example, we'll just have recruiters add description to a student's profile directly.
        db.commit()

# Call init_db once when the application starts
with app.app_context():
    init_db()

# --- Utility for Authentication Check ---
def login_required_student(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: # Assuming 'user_id' is for students
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_recruiter(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Placeholder for recruiter specific login check
        # For now, we'll use a dummy session variable for recruiters
        if 'recruiter_logged_in' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student-dashboard.html')
@login_required_student
def student_dashboard():
    return render_template('student-dashboard.html')

@app.route('/recruiter-dashboard.html')
@login_required_recruiter
def recruiter_dashboard():
    return render_template('recruiter-dashboard.html')


# --- API Endpoints for Student Authentication ---

@app.route('/api/register-student', methods=['POST'])
def register_student():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Account with this email already exists.'}), 409 # Conflict

        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, major, status) VALUES (?, ?, ?, ?, ?)",
            (name, email, hashed_password, "Not specified", "New User") # Default major/status
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Account created successfully!'}), 201 # Created
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Database error: Email might already exist.'}), 500
    except Exception as e:
        app.logger.error(f"Error during student registration: {e}") # Log errors
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@app.route('/api/login-student', methods=['POST'])
def login_student():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'success': False, 'message': 'Email and password are required.'}), 400

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT id, name, email, password_hash, major, status, resume_filename, resume_upload_date FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id'] # Store user ID in session
        # Return specific user data needed for dashboard
        return jsonify({
            'success': True,
            'message': 'Login successful!',
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'major': user['major'],
                'status': user['status'],
                'resume_filename': user['resume_filename'], # Include resume info
                'resume_upload_date': user['resume_upload_date']
            }
        }), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401 # Unauthorized

# --- API Endpoint for fetching student user profile data ---
@app.route('/api/get-profile', methods=['GET'])
@login_required_student
def get_profile():
    user_id = session.get('user_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name, email, major, status, resume_filename, resume_upload_date FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if user:
        return jsonify({
            'success': True,
            'profile': {
                'name': user['name'],
                'email': user['email'],
                'major': user['major'],
                'status': user['status'],
                'resume_filename': user['resume_filename'],
                'resume_upload_date': user['resume_upload_date']
            }
        }), 200
    else:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

# --- API Endpoint for updating student profile data ---
@app.route('/api/update-profile', methods=['POST'])
@login_required_student
def update_profile():
    user_id = session.get('user_id')
    data = request.json
    name = data.get('name')
    major = data.get('major')
    status = data.get('status')

    if not all([name, major, status]):
        return jsonify({'success': False, 'message': 'All profile fields are required.'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            "UPDATE users SET name = ?, major = ?, status = ? WHERE id = ?",
            (name, major, status, user_id)
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully!'}), 200
    except Exception as e:
        app.logger.error(f"Error during student profile update: {e}")
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

# --- API Endpoint for student resume upload ---
@app.route('/api/upload-resume', methods=['POST'])
@login_required_student
def upload_resume():
    user_id = session.get('user_id')

    if 'resume_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    file = request.files['resume_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)

            db = get_db()
            cursor = db.cursor()
            upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "UPDATE users SET resume_filename = ?, resume_upload_date = ? WHERE id = ?",
                (filename, upload_date, user_id)
            )
            db.commit()
            return jsonify({
                'success': True,
                'message': 'Resume uploaded successfully!',
                'filename': filename,
                'upload_date': upload_date
            }), 200
        except Exception as e:
            app.logger.error(f"Error during resume upload for user {user_id}: {e}")
            return jsonify({'success': False, 'message': f'File upload failed: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'Invalid file type or size. Allowed: pdf, doc, docx, txt. Max 16MB.'}), 400

# --- API Endpoint for serving resume files (for recruiters) ---
@app.route('/resumes/<filename>')
@login_required_recruiter # Only recruiters can access resumes directly
def serve_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- API Endpoints for Recruiter Functionality ---

@app.route('/api/login-recruiter', methods=['POST'])
def login_recruiter():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # For demonstration: Hardcoded recruiter credentials
    if email == 'recruiter@example.com' and password == 'recruiterpass':
        session['recruiter_logged_in'] = True # Set a session variable for recruiter
        return jsonify({'success': True, 'message': 'Recruiter login successful!'}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid recruiter credentials.'}), 401


@app.route('/api/get-students', methods=['GET'])
@login_required_recruiter
def get_students():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, email, major, status, resume_filename, resume_upload_date FROM users ORDER BY name")
    students = cursor.fetchall()

    student_list = []
    for s in students:
        student_list.append({
            'id': s['id'],
            'name': s['name'],
            'email': s['email'],
            'major': s['major'],
            'status': s['status'],
            'resume_filename': s['resume_filename'],
            'resume_upload_date': s['resume_upload_date'],
            'resume_url': url_for('serve_resume', filename=s['resume_filename'], _external=True) if s['resume_filename'] else None
        })
    return jsonify({'success': True, 'students': student_list}), 200

# --- AI Prediction Endpoint ---
@app.route('/predict', methods=['POST'])
def predict():
    try:
        if not keras_model or not tokenizer:
            return jsonify({'success': False, 'message': 'AI model not loaded properly'}), 500
        
        # Get job description from form or JSON
        job_description = request.form.get('job_description') or request.json.get('job_description')
        
        if not job_description:
            return jsonify({'success': False, 'message': 'Job description is required'}), 400
        
        # Get resume file
        resume_file = request.files.get('resume_file')
        if not resume_file:
            return jsonify({'success': False, 'message': 'Resume file is required'}), 400
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(resume_file)
        
        # Preprocess texts
        resume_clean = preprocessing(resume_text)
        resume_clean = shorting(resume_clean.split())
        job_clean = preprocessing(job_description)
        
        # Convert to vectors
        resume_vec = text_to_vectors(" ".join(resume_clean), RESUME_LEN)
        job_vec = text_to_vectors(job_clean, JOB_LEN)
        
        if resume_vec is None or job_vec is None:
            return jsonify({'success': False, 'message': 'Error processing text'}), 500
        
        # Make prediction
        prob = keras_model.predict([resume_vec, job_vec])[0][0]
        decision = "SELECT" if prob >= 0.5 else "REJECT"
        
        return jsonify({
            'success': True,
            'probability': round(prob * 100, 2),
            'decision': decision
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in AI prediction: {e}")
        return jsonify({'success': False, 'message': f'Prediction error: {str(e)}'}), 500

# --- Logout Route ---
@app.route('/logout')
def logout():
    session.pop('user_id', None) # Remove student user ID from session
    session.pop('recruiter_logged_in', None) # Remove recruiter session variable
    return redirect(url_for('index'))


# Ensure the database is initialized when the app starts
#if __name__ == '__main__':
    from flask import g # Import g for app context setup
    init_db() # Initialize the database tables
    app.run(debug=True) # debug=True restarts server on code changes and provides more info



