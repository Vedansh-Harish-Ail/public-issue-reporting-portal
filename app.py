import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
app = Flask(__name__)
# moment = Moment(app) # Removed as package install was cancelled
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

DB_NAME = "panchayath.db"

# ---------------- DATABASE CONNECTION ----------------

def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- SECURITY UTILS ----------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- INITIALIZE DATABASE ----------------

def init_db():
    conn = connect_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS panchayath (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        district TEXT,
        state TEXT
    );

    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        panchayath_id INTEGER,
        category TEXT,
        description TEXT,
        location TEXT,
        status TEXT DEFAULT 'Pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        panchayath_id INTEGER,
        title TEXT,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password_hash TEXT,
        panchayath_id INTEGER
    );
    """)
    conn.commit()
    conn.close()

# ---------------- SEED DEFAULT DATA ----------------

def seed_data():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM panchayath")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO panchayath (name, district, state)
            VALUES ('Demo Panchayath', 'Demo District', 'Demo State')
        """)

        cur.execute("""
            INSERT INTO admin (username, password_hash, panchayath_id)
            VALUES (?, ?, ?)
        """, ("admin", generate_password_hash("admin123"), 1))

    conn.commit()
    conn.close()

# ---------------- CITIZEN ROUTES ----------------

@app.route("/")
def home():
    conn = connect_db()
    panchayaths = conn.execute("SELECT * FROM panchayath").fetchall()
    conn.close()
    return render_template("citizen/index.html", panchayaths=panchayaths)

@app.route("/report", methods=["GET", "POST"])
def report_issue():
    conn = connect_db()

    if request.method == "POST":
        panchayath_id = request.form["panchayath_id"]
        category = request.form["category"]
        description = request.form["description"]
        location = request.form["location"]

        conn.execute("""
            INSERT INTO issues (panchayath_id, category, description, location)
            VALUES (?, ?, ?, ?)
        """, (panchayath_id, category, description, location))

        conn.commit()
        conn.close()
        flash("Issue reported successfully", "success")
        return redirect(url_for("track_issue"))

    panchayaths = conn.execute("SELECT * FROM panchayath").fetchall()
    conn.close()
    return render_template("citizen/report_issue.html", panchayaths=panchayaths)

@app.route("/track")
def track_issue():
    conn = connect_db()
    issues = conn.execute("""
        SELECT i.*, p.name AS panchayath_name
        FROM issues i
        JOIN panchayath p ON p.id = i.panchayath_id
        ORDER BY i.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("citizen/track_issue.html", issues=issues)

@app.route("/notices")
def notices():
    conn = connect_db()
    notices = conn.execute("""
        SELECT n.*, p.name AS panchayath_name
        FROM notices n
        JOIN panchayath p ON p.id = n.panchayath_id
        ORDER BY n.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("citizen/notices.html", notices=notices)

# ---------------- ADMIN ROUTES ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect_db()
        admin = conn.execute(
            "SELECT * FROM admin WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["panchayath_id"] = admin["panchayath_id"]
            return redirect(url_for("admin_dashboard"))

        flash("Invalid credentials", "danger")

    return render_template("admin/login.html")

@app.route("/admin")
@login_required
def admin_dashboard():
    # if "admin_id" not in session: check handled by decorator
    pid = session["panchayath_id"]
    conn = connect_db()

    issues = conn.execute("""
        SELECT * FROM issues
        WHERE panchayath_id = ?
        ORDER BY created_at DESC
    """, (pid,)).fetchall()

    conn.close()
    return render_template("admin/dashboard.html", issues=issues)

# ---------------- ADMIN NOTICES (FIXED PART) ----------------

@app.route("/admin/notices", methods=["GET", "POST"])
@login_required
def admin_notices():
    # if "admin_id" not in session: check handled by decorator
    pid = session["panchayath_id"]
    conn = connect_db()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        conn.execute("""
            INSERT INTO notices (panchayath_id, title, description)
            VALUES (?, ?, ?)
        """, (pid, title, description))
        conn.commit()
        flash("Notice published successfully", "success")

    notices = conn.execute("""
        SELECT * FROM notices
        WHERE panchayath_id = ?
        ORDER BY created_at DESC
    """, (pid,)).fetchall()

    conn.close()
    return render_template("admin/notices.html", notices=notices)

@app.route("/admin/issue/<int:issue_id>")
@login_required
def admin_issue_detail(issue_id):
    # Authorization check handled by decorator

    conn = connect_db()
    issue = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    conn.close()

    if not issue:
        flash("Issue not found", "danger")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/issue_detail.html", issue=issue)

@app.route("/admin/update/<int:issue_id>", methods=["POST"])
@login_required
def update_issue(issue_id):
    # Authorization check handled by decorator

    status = request.form["status"]
    conn = connect_db()
    conn.execute(
        "UPDATE issues SET status=? WHERE id=?",
        (status, issue_id)
    )
    conn.commit()
    conn.close()

    flash("Status updated", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

# ---------------- MAIN ----------------

if __name__ == "__main__":
    init_db()
    seed_data()
    app.run(debug=True)
