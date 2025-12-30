from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management # Change this to a secure secret key

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create test user if not exists
    test_email = "test@example.com"
    cursor.execute("SELECT id FROM users WHERE email = ?", (test_email,))
    if not cursor.fetchone():
        hashed_password = generate_password_hash("Test@123")
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
            ("Test", "User", test_email, hashed_password)
        )
        print("Created test user: test@example.com / Test@123")
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    # Handle POST request
    try:
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        # Validate required fields
        if not all([first_name, last_name, email, password]):
            return jsonify({
                "error": "All fields are required"
            }), 400

        # Validate email format
        if '@' not in email:
            return jsonify({
                "error": "Please enter a valid email address"
            }), 400

        # Validate password strength
        if len(password) < 8:
            return jsonify({
                "error": "Password must be at least 8 characters long"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return jsonify({
                    "error": "Email already exists"
                }), 400

            # Hash the password
            hashed_password = generate_password_hash(password)

            # Insert new user
            cursor.execute(
                "INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                (first_name, last_name, email, hashed_password)
            )
            user_id = cursor.lastrowid
            
            # Commit changes
            conn.commit()

            # Set session
            session['user_id'] = user_id
            session['email'] = email

            return jsonify({
                "success": True,
                "redirect": url_for('home')
            })

        except sqlite3.IntegrityError:
            return jsonify({
                "error": "Email already exists"
            }), 400
        finally:
            conn.close()

    except Exception as e:
        print(f"Error in signup: {str(e)}")
        return jsonify({
            "error": "An error occurred during registration. Please try again."
        }), 500

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Handle sign-in form submission
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            return jsonify({
                'success': True,
                'redirect': url_for('home')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
    else:
        # For GET request, just render the template
        return render_template('index.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

# Existing routes
@app.route("/save_resume", methods=["POST"])
def save_resume():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        required_fields = ['name', 'phone', 'email', 'degree', 'cgpa', 'skills', 'projects']
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        # Create resume text
        resume_text = f"""
{data['name'].upper()}
--------------------------------------------------
{data['degree']} | CGPA: {data['cgpa']}

CONTACT
Phone : {data['phone']}
Email : {data['email']}

SKILLS
--------------------------------------------------
{data['skills']}

PROJECTS
--------------------------------------------------
{data['projects']}
"""

        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create resumes table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            degree TEXT NOT NULL,
            cgpa TEXT NOT NULL,
            skills TEXT NOT NULL,
            projects TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Insert resume data
        cursor.execute('''
        INSERT INTO resumes (user_id, name, phone, email, degree, cgpa, skills, projects)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data['name'],
            data['phone'],
            data['email'],
            data['degree'],
            data['cgpa'],
            data['skills'],
            data['projects']
        ))
        
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Resume saved successfully",
            "resume_text": resume_text
        })

    except Exception as e:
        print(f"Error saving resume: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"An error occurred while saving the resume: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True)