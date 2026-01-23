import os
import sqlite3
from urllib import response
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
from translations import TRANSLATIONS # Import translations
#---------------- SMS OTP IMPORT ----------------
import requests
import random
import time
#---------------- EMAIL OTP IMPORT ------------------
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
#---------------- SMS OTP CONFIGURATION ----------------



#---------------- EMAIL OTP CONFIGURATION ----------------

def generate_otp():
    return str(random.randint(100000, 999999))

def send_email_otp(user_email, otp):
    # Use provided credentials as defaults if env vars are missing
    sender_email = os.environ.get("MAIL_USERNAME", "panchayatseva1@gmail.com")
    # REPLACE THE STRING BELOW WITH YOUR 16-CHARACTER GOOGLE APP PASSWORD
    app_password = os.environ.get("MAIL_PASSWORD", "tkao zyic hwog dxnd")
    
    if not sender_email or not app_password:
        print("Error: Email credentials not found in environment variables.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = user_email
        msg['Subject'] = "Your Verification OTP"

        body = f"Your OTP is: {otp}\n\nThis OTP is valid for 2 minutes.\nDo not share this with anyone."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        # Even if email fails, print to console so user can still test
        print(f"\n[FALLBACK] Email failed. Enter this OTP: {otp}\n")
        return True

# ---------------- CONFIGURATION ----------------
app.secret_key = os.environ.get("SECRET_KEY", "new_secure_random_key_2025")

DB_NAME = "database/panchayath.db"

# ---------------- DATABASE CONNECTION ----------------

def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- I18N UTILS ----------------

def _get_text(key):
    lang = session.get("lang", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

@app.context_processor
def inject_get_text():
    return dict(get_text=_get_text)

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
            flash(_get_text("flash_login_required"), "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

def user_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash(_get_text("flash_login_required"), "info")
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
        tracking_id TEXT UNIQUE,
        panchayath_id INTEGER,
        category TEXT,
        description TEXT,
        location TEXT,
        photo_path TEXT,
        status TEXT DEFAULT 'Pending',
        rejection_reason TEXT,
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

    # Add tracking_id to issues table if it doesn't exist
    try:
        conn.execute("SELECT tracking_id FROM issues LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE issues ADD COLUMN tracking_id TEXT")
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

# ---------------- HELPERS ----------------
def generate_tracking_id():
    import uuid
    # Generate a short unique ID (e.g., TRK-1A2B3C)
    return "TRK-" + str(uuid.uuid4())[:8].upper()

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
        flash(_get_text("flash_admin_no_report"), "warning")
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

        tracking_id = generate_tracking_id()

        conn.execute("""
            INSERT INTO issues (panchayath_id, category, description, location, photo_path, user_id, tracking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (panchayath_id, category, description, location, image_filename, user_id, tracking_id))

        conn.commit()
        conn.close()
        flash(_get_text("flash_report_success").format(tracking_id), "success")
        return redirect(url_for("track_issue", new_tracking_id=tracking_id))

    panchayaths = conn.execute("SELECT * FROM panchayath").fetchall()
    conn.close()
    return render_template("citizen/report_issue.html", panchayaths=panchayaths)

@app.route("/track")
@user_login_required
def track_issue():
    user_id = session["user_id"]
    search_id = request.args.get("search_id")
    # Helper to highlight specific tracking ID if redirected from report
    new_tracking_id = request.args.get("new_tracking_id") 
    
    conn = connect_db()
    
    if search_id:
        issues = conn.execute("""
            SELECT i.*, p.name AS panchayath_name
            FROM issues i
            JOIN panchayath p ON p.id = i.panchayath_id
            WHERE i.tracking_id = ? AND i.user_id = ?
        """, (search_id.strip(), user_id)).fetchall()
        
        if not issues:
            flash(_get_text("flash_no_issue_found"), "warning")
            # Fallback to showing all
            issues = conn.execute("""
                SELECT i.*, p.name AS panchayath_name
                FROM issues i
                JOIN panchayath p ON p.id = i.panchayath_id
                WHERE i.user_id = ?
                ORDER BY i.created_at DESC
            """, (user_id,)).fetchall()
    else:
        issues = conn.execute("""
            SELECT i.*, p.name AS panchayath_name
            FROM issues i
            JOIN panchayath p ON p.id = i.panchayath_id
            WHERE i.user_id = ?
            ORDER BY i.created_at DESC
        """, (user_id,)).fetchall()
        
    conn.close()
    return render_template("citizen/track_issue.html", issues=issues, title="My Reported Issues", new_tracking_id=new_tracking_id, search_id=search_id)

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

        # Server-side Validation
        # Mobile: +91 followed by 10 digits (6-9)
        if not re.match(r"^\+91[6-9]\d{9}$", mobile):
            flash(_get_text("flash_invalid_mobile"), "danger")
            return redirect(url_for("user_register"))

        # Password: 8+ chars, 1 Upper, 1 Lower, 1 Number, 1 Special
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
            flash(_get_text("flash_password_weak"), "danger")
            return redirect(url_for("user_register"))

        # store data temporarily
        session["temp_user"] = {
            "name": name,
            "email": email,
            "mobile": mobile,
            "password": generate_password_hash(password)
        }

        otp = generate_otp()
        session["otp"] = otp
        session["otp_time"] = time.time()
        
        # Send OTP via Email
        if send_email_otp(email, otp):
            flash(_get_text("flash_otp_sent").format(email), "info")
            return redirect(url_for("verify_otp"))
        else:
            flash(_get_text("flash_otp_failed"), "danger")
            return redirect(url_for("user_register"))

    return render_template("citizen/register.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]

        # OTP expiry: 2 minutes
        if time.time() - session.get("otp_time", 0) > 120:
            flash(_get_text("flash_otp_expired"), "danger")
            return redirect(url_for("verify_otp"))

        if entered_otp == session.get("otp"):
            user = session.get("temp_user")

            conn = connect_db()
            try:
                conn.execute("""
                    INSERT INTO users (name, email, mobile, password_hash)
                    VALUES (?, ?, ?, ?)
                """, (
                    user["name"],
                    user["email"],
                    user["mobile"],
                    user["password"]
                )) 
                conn.commit()
            except sqlite3.IntegrityError:
                flash(_get_text("flash_user_exists"), "danger")
                return redirect(url_for("user_register"))
            finally:
                conn.close()

            # Clear session
            session.pop("otp", None)
            session.pop("otp_time", None)
            session.pop("temp_user", None)

            flash(_get_text("flash_reg_success"), "success")
            return redirect(url_for("user_login"))

        flash(_get_text("flash_invalid_otp"), "danger")

    return render_template("citizen/verify_otp.html")

@app.route("/resend-otp")
def resend_otp():
    if "temp_user" not in session:
        flash(_get_text("flash_session_expired"), "warning")
        return redirect(url_for("user_register"))
    
    otp = generate_otp()
    session["otp"] = otp
    session["otp_time"] = time.time()
    
    email = session["temp_user"]["email"]
    
    if send_email_otp(email, otp):
        flash(_get_text("flash_otp_sent").format(email), "info")
    else:
        flash(_get_text("flash_otp_failed"), "danger")
        
    return redirect(url_for("verify_otp"))

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
            flash(_get_text("flash_welcome_user").format(user['name']), "success")
            return redirect(url_for("home"))
        
        flash(_get_text("flash_invalid_login"), "danger")
        
    return render_template("citizen/login.html")

@app.route("/logout")
def user_logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    flash(_get_text("flash_logged_out"), "success")
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
            flash(_get_text("flash_admin_welcome").format(admin['username']), "success")
            return redirect(url_for("admin_dashboard"))

        flash(_get_text("flash_invalid_login"), "danger")

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
        WHERE i.panchayath_id = ? AND i.status != 'Completed' AND i.status != 'Rejected'
        ORDER BY i.created_at DESC
    """, (pid,)).fetchall()

    # Calculate stats for dashboard cards
    stats = {
        "total": conn.execute("SELECT COUNT(*) FROM issues WHERE panchayath_id = ?", (pid,)).fetchone()[0],
        "resolved": conn.execute("SELECT COUNT(*) FROM issues WHERE panchayath_id = ? AND status = 'Completed'", (pid,)).fetchone()[0],
        "pending": conn.execute("SELECT COUNT(*) FROM issues WHERE panchayath_id = ? AND status = 'Pending'", (pid,)).fetchone()[0],
        "rejected": conn.execute("SELECT COUNT(*) FROM issues WHERE panchayath_id = ? AND status = 'Rejected'", (pid,)).fetchone()[0]
    }

    conn.close()
    return render_template("admin/dashboard.html", issues=issues, stats=stats)

@app.route("/admin/completed_issues")
@login_required
def admin_completed_issues():
    pid = session["panchayath_id"]
    conn = connect_db()

    issues = conn.execute("""
        SELECT i.*, u.name as reporter_name 
        FROM issues i
        LEFT JOIN users u ON i.user_id = u.id
        WHERE i.panchayath_id = ? AND i.status = 'Completed'
        ORDER BY i.created_at DESC
    """, (pid,)).fetchall()

    conn.close()
    return render_template("admin/completed_issues.html", issues=issues)

@app.route("/admin/rejected_issues")
@login_required
def admin_rejected_issues():
    pid = session["panchayath_id"]
    conn = connect_db()

    issues = conn.execute("""
        SELECT i.*, u.name as reporter_name 
        FROM issues i
        LEFT JOIN users u ON i.user_id = u.id
        WHERE i.panchayath_id = ? AND i.status = 'Rejected'
        ORDER BY i.created_at DESC
    """, (pid,)).fetchall()

    conn.close()
    return render_template("admin/rejected_issues.html", issues=issues)

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
        flash(_get_text("flash_notice_published"), "success")

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
        flash(_get_text("flash_notice_deleted"), "success")
    else:
        flash(_get_text("flash_notice_unauthorized"), "danger")
        
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
        flash(_get_text("flash_user_not_found"), "danger")
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
        flash(_get_text("flash_issue_not_found"), "danger")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/issue_detail.html", issue=issue)

@app.route("/admin/update/<int:issue_id>", methods=["POST"])
@login_required
def update_issue(issue_id):
    # Authorization check handled by decorator

    status = request.form["status"]
    rejection_reason = request.form.get("rejection_reason") if status == "Rejected" else None
    
    conn = connect_db()
    conn.execute(
        "UPDATE issues SET status=?, rejection_reason=? WHERE id=?",
        (status, rejection_reason, issue_id)
    )
    conn.commit()
    conn.close()

    flash(_get_text("flash_status_updated"), "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash(_get_text("flash_admin_logout"), "success")
    return redirect(url_for("admin_login"))

# ---------------- MAIN ----------------

if __name__ == "__main__":
    init_db()
    seed_data()
    app.run(debug=True)

