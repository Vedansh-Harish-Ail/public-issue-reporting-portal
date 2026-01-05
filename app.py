import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from translations import TRANSLATIONS # Import translations

app = Flask(__name__)
# moment = Moment(app) # Removed as package install was cancelled
app.secret_key = os.environ.get("SECRET_KEY", "new_secure_random_key_2025")

DB_NAME = "database/panchayath.db"

# ---------------- DATABASE CONNECTION ----------------

def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- I18N UTILS ----------------

@app.context_processor
def inject_get_text():
    def get_text(key):
        lang = session.get("lang", "en")
        return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    return dict(get_text=get_text)

@app.route("/set_language/<lang_code>")
def set_language(lang_code):
    if lang_code in TRANSLATIONS:
        session["lang"] = lang_code
    return redirect(request.referrer or url_for("home"))

# ---------------- SECURITY UTILS ----------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

def user_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.", "info")
            return redirect(url_for("user_login"))
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
        photo_path TEXT,
        status TEXT DEFAULT 'Pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS notices ( 
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        panchayath_id INTEGER,
        title TEXT,
        description TEXT,
        banner_path TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        mobile TEXT,
        password_hash TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password_hash TEXT,
        panchayath_id INTEGER
    );
    """)
    
    # Add user_id to issues table if it doesn't exist
    try:
        conn.execute("SELECT user_id FROM issues LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE issues ADD COLUMN user_id INTEGER")
        conn.commit()

    # Add banner_path to notices table if it doesn't exist
    try:
        conn.execute("SELECT banner_path FROM notices LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE notices ADD COLUMN banner_path TEXT")
        conn.commit()

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


# ---------------- CITIZEN ROUTES --------------

@app.route("/")
def home():
    conn = connect_db()
    panchayaths = conn.execute("SELECT * FROM panchayath").fetchall()
    
    # Fetch stats
    total_panchayaths = conn.execute("SELECT COUNT(*) FROM panchayath").fetchone()[0]
    total_issues = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
    resolved_issues = conn.execute("SELECT COUNT(*) FROM issues WHERE status = 'Completed'").fetchone()[0]
    
    resolution_rate = 0
    if total_issues > 0:
        resolution_rate = int((resolved_issues / total_issues) * 100)
    
    total_citizens = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    
    stats = {
        "panchayaths": total_panchayaths,
        "issues": total_issues,
        "resolution": resolution_rate,
        "citizens": f"{total_citizens}" if total_citizens > 0 else "0"
    }
    
    conn.close()
    return render_template("citizen/index.html", panchayaths=panchayaths, stats=stats)

@app.route("/report", methods=["GET", "POST"])
@user_login_required
def report_issue():
    # Admins can't report issues (already blocked but good to keep logic clear)
    if "admin_id" in session:
        flash("Admins cannot report issues. Please use the dashboard.", "warning")
        return redirect(url_for("admin_dashboard"))

    conn = connect_db()

    # Check/Add photo_path column if not exists (already handled in migration above but safe to keep)
    try:
        conn.execute("SELECT photo_path FROM issues LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE issues ADD COLUMN photo_path TEXT")
        conn.commit()

    if request.method == "POST":
        panchayath_id = request.form["panchayath_id"]
        category = request.form["category"]
        description = request.form["description"]
        location = request.form["location"]
        user_id = session["user_id"]
        
        image = request.files.get("image")
        image_filename = None
        
        if image and image.filename != "":
            upload_folder = os.path.join("static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            import time
            from werkzeug.utils import secure_filename
            ext = os.path.splitext(image.filename)[1]
            filename = f"issue_{int(time.time())}{ext}"
            image.save(os.path.join(upload_folder, filename))
            image_filename = f"uploads/{filename}"

        conn.execute("""
            INSERT INTO issues (panchayath_id, category, description, location, photo_path, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (panchayath_id, category, description, location, image_filename, user_id))

        conn.commit()
        conn.close()
        flash("Issue reported successfully", "success")
        return redirect(url_for("track_issue"))

    panchayaths = conn.execute("SELECT * FROM panchayath").fetchall()
    conn.close()
    return render_template("citizen/report_issue.html", panchayaths=panchayaths)

@app.route("/track")
@user_login_required
def track_issue():
    user_id = session["user_id"]
    conn = connect_db()
    issues = conn.execute("""
        SELECT i.*, p.name AS panchayath_name
        FROM issues i
        JOIN panchayath p ON p.id = i.panchayath_id
        WHERE i.user_id = ?
        ORDER BY i.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return render_template("citizen/track_issue.html", issues=issues, title="My Reported Issues")

@app.route("/public-track")
def public_track():
    conn = connect_db()
    issues = conn.execute("""
        SELECT i.*, p.name AS panchayath_name, u.name AS user_name
        FROM issues i
        JOIN panchayath p ON p.id = i.panchayath_id
        LEFT JOIN users u ON u.id = i.user_id
        ORDER BY i.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("citizen/track_issue.html", issues=issues, title="Public Issue Tracker", is_public=True)

@app.route("/about")
def about():
    return render_template("citizen/about.html")

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

# ---------------- USER AUTH ROUTES ----------------

@app.route("/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        password = request.form["password"]
        
        hashed_password = generate_password_hash(password)
        
        conn = connect_db()
        try:
            conn.execute("""
                INSERT INTO users (name, email, mobile, password_hash)
                VALUES (?, ?, ?, ?)
            """, (name, email, mobile, hashed_password))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("user_login"))
        except sqlite3.IntegrityError:
            flash("Email already exists. Please use a different one.", "danger")
        finally:
            conn.close()
            
    return render_template("citizen/register.html")

@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        conn = connect_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("home"))
        
        flash("Invalid email or password.", "danger")
        
    return render_template("citizen/login.html")

@app.route("/logout")
def user_logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

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
        SELECT i.*, u.name as reporter_name 
        FROM issues i
        LEFT JOIN users u ON i.user_id = u.id
        WHERE i.panchayath_id = ?
        ORDER BY i.created_at DESC
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
        
        banner = request.files.get("banner")
        banner_filename = None
        
        if banner and banner.filename != "":
            upload_folder = os.path.join("static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            import time
            ext = os.path.splitext(banner.filename)[1]
            filename = f"notice_{int(time.time())}{ext}"
            banner.save(os.path.join(upload_folder, filename))
            banner_filename = f"uploads/{filename}"

        conn.execute("""
            INSERT INTO notices (panchayath_id, title, description, banner_path)
            VALUES (?, ?, ?, ?)
        """, (pid, title, description, banner_filename))
        conn.commit()
        flash("Notice published successfully", "success")

    notices = conn.execute("""
        SELECT * FROM notices
        WHERE panchayath_id = ?
        ORDER BY created_at DESC
    """, (pid,)).fetchall()

    conn.close()
    return render_template("admin/notices.html", notices=notices)

@app.route("/admin/notices/delete/<int:notice_id>")
@login_required
def delete_notice(notice_id):
    pid = session["panchayath_id"]
    conn = connect_db()
    
    # Ensure the notice belongs to this panchayath
    notice = conn.execute("SELECT * FROM notices WHERE id = ? AND panchayath_id = ?", (notice_id, pid)).fetchone()
    
    if notice:
        conn.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
        conn.commit()
        flash("Notice deleted successfully", "success")
    else:
        flash("Notice not found or unauthorized", "danger")
        
    conn.close()
    return redirect(url_for("admin_notices"))

@app.route("/profile")
@user_login_required
def user_profile():
    user_id = session["user_id"]
    conn = connect_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("home"))
        
    return render_template("citizen/profile.html", user=user)

@app.route("/admin/issue/<int:issue_id>")
@login_required
def admin_issue_detail(issue_id):
    # Authorization check handled by decorator

    conn = connect_db()
    issue = conn.execute("""
        SELECT i.*, u.name as reporter_name, u.email as reporter_email, u.mobile as reporter_mobile
        FROM issues i
        LEFT JOIN users u ON i.user_id = u.id
        WHERE i.id = ?
    """, (issue_id,)).fetchone()
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
