import sqlite3
from flask import Flask, render_template, request, jsonify
import os
from flask import Flask, request, jsonify
import os, sqlite3
from flask import send_from_directory
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")



def get_db():
    return sqlite3.connect("database.db")



@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.json
        email = data["email"].strip()
        password = data["password"].strip()

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT
        )
        """)

        cur.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, password)
        )

        conn.commit()
        conn.close()

        print("SIGNUP SUCCESS:", email)
        return jsonify({"success": True})

    except Exception as e:
        print("SIGNUP ERROR:", e)
        return jsonify({"success": False, "msg": "User already exists"}), 400

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data["email"].strip()
        password = data["password"].strip()

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cur.fetchone()
        conn.close()

        print("LOGIN ATTEMPT:", email, "FOUND:", bool(user))

        return jsonify({"success": True if user else False})

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"success": False}), 500
    

@app.route("/save_resume", methods=["POST"])
def save_resume():
    data = request.json

    name = data["name"]
    phone = data["phone"]
    email = data["email"]
    degree = data["degree"]
    cgpa = data["cgpa"]
    skills = data["skills"]
    projects = data["projects"]

    # -------- Resume Text --------
    resume_text = f"""
{name.upper()}
--------------------------------------------------
{degree} | CGPA: {cgpa}

CONTACT
Phone : {phone}
Email : {email}

SKILLS
--------------------------------------------------
"""

    for s in skills.split(","):
        resume_text += f"- {s.strip()}\n"

    resume_text += f"""

PROJECTS
--------------------------------------------------
{projects}
"""

    # -------- Save as TXT --------
    os.makedirs("resumes", exist_ok=True)
    file_path = f"resumes/{name.replace(' ', '_')}.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(resume_text)

    # -------- SAVE TO DATABASE --------
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        name TEXT,
        phone TEXT,
        email TEXT,
        degree TEXT,
        cgpa TEXT,
        skills TEXT,
        projects TEXT,
        file_path TEXT
    )
    """)

    cur.execute("""INSERT INTO resumes ( name, phone, email, degree, cgpa, skills, projects, file_path) VALUES (?,?,?,?,?,?,?,?)""", (
        name, phone, email, degree,
        cgpa, skills, projects, file_path
    ))

    conn.commit()
    conn.close()

    print("RESUME SAVED TO DATABASE")

    return jsonify({
        "success": True,
        "resume_text": resume_text
    })


ADMIN_EMAIL = "admin@placement.com"
ADMIN_PASSWORD = "admin123"

@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.json
    if data["email"] == ADMIN_EMAIL and data["password"] == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/admin_dashboard")
def admin_dashboard():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT email FROM users")
    users = cur.fetchall()

    cur.execute("SELECT name, email, degree, cgpa, file_path FROM resumes")
    resumes = cur.fetchall()

    conn.close()

    return render_template("admin.html", users=users, resumes=resumes)




@app.route("/download/<filename>")
def download_resume(filename):
    resume_dir = os.path.join(os.getcwd(), "resumes")
    return send_from_directory(
        resume_dir,
        filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)
