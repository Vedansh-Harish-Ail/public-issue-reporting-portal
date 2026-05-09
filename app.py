import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
import time
from datetime import datetime
from translations import TRANSLATIONS # Import translations
from email_templates import EMAIL_TEMPLATES # Import HTML templates
#---------------- EMAIL OTP IMPORT ------------------------
import smtplib
import random
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    psycopg2 = None
import requests
import urllib.parse

# Define Base Directory for Absolute Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CATEGORIES = [
    "Garbage Collection",
    "Water Supply",
    "Road Maintenance",
    "Street Lights",
    "Drainage",
    "Others"
]

app = Flask(__name__)

# ---------------- SECURITY CONFIGURATION -----------------
# Talisman adds security headers and enforces HTTPS
Talisman(app, content_security_policy=None) # CSP can be restrictive, set to None for MVP

# Limiter prevents brute-force attacks on sensitive routes
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# ---------------- EMAIL OTP CONFIGURATION -----------------

def generate_otp():
    return str(random.randint(100000, 999999))

def upload_to_blob(file_obj, filename):
    """Uploads a file to Vercel Blob and returns the public URL."""
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        return None
    
    # Clean filename for URL safety
    filename = urllib.parse.quote(filename)
    url = f"https://blob.vercel-storage.com?filename={filename}"
    headers = {"Authorization": f"Bearer {token}", "x-api-version": "7"}
    
    try:
        file_obj.seek(0)
        resp = requests.put(url, data=file_obj.read(), headers=headers)
        if resp.status_code in [200, 201]:
            return resp.json().get("url")
        print(f"Blob upload failed with status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Blob upload error: {e}")
    return None

def send_email(to_email, subject, body, content_type="plain"):
    """Generic function to send emails. Supports 'plain' and 'html'."""
    sender_email = os.environ.get("MAIL_USERNAME")
    app_password = os.environ.get("MAIL_PASSWORD")
    
    if not sender_email or not app_password:
        print("Error: EMAIL OTP credentials NOT FOUND.")
        print("Please set MAIL_USERNAME and MAIL_PASSWORD in your environment variables or .env file.")
        return False

    print(f"[{datetime.now()}] Attempting to send email to {to_email}...")
    
    if os.environ.get("DATABASE_URL") or os.environ.get("Panchayat_DATABASE_URL"):
        debug_file = os.path.join("/tmp", "debug_email.txt")
    else:
        debug_file = os.path.join(BASE_DIR, "debug_email.txt")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, content_type))

        # Debugging Email
        with open(debug_file, "a") as f:
            f.write(f"[{datetime.now()}] Sending {content_type} email to {to_email} with subject: {subject}\n")

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        
        with open(debug_file, "a") as f:
            f.write(f"[{datetime.now()}] SUCCESS: Email sent to {to_email}\n")
            
        print(f"[{datetime.now()}] Email sent successfully to {to_email}")
        return True
    except Exception as e:
        with open(debug_file, "a") as f:
            f.write(f"[{datetime.now()}] ERROR: {e}\n")
        print(f"[{datetime.now()}] Error sending email: {e}")
        return False

def send_email_otp(user_email, otp):
    """Sends OTP email using the templates from email_templates.py."""
    subject = _get_text("otp_email_subject")
    lang = session.get("lang", "en")
    
    # Grab the HTML template for the current language
    body_html_template = EMAIL_TEMPLATES.get(lang, EMAIL_TEMPLATES["en"])
    email_content = body_html_template.format(otp)
    content_type = "html"
        
    if send_email(user_email, subject, email_content, content_type=content_type):
        return True
    else:
        print(f"\n[FALLBACK] Email failed. Enter this OTP: {otp}\n")
        return True  # Return True to allow fallback manual entry if email fails

def send_status_update_email(user_email, user_name, tracking_id, issue_category, new_status, rejection_reason=None):
    """Sends an email notification when an issue status changes."""
    subject = _get_text("email_status_subject").format(tracking_id)
    
    body_template = _get_text("email_status_body")
    
    # Construct the status message
    status_msg = new_status
    if new_status == "Rejected" and rejection_reason:
        status_msg += f" (Reason: {rejection_reason})"
        
    try:
        body = body_template.format(user_name, issue_category, tracking_id, status_msg)
        # Run email sending in a separate thread
        threading.Thread(target=send_email, args=(user_email, subject, body)).start()
        return True
    except Exception as e:
        print(f"Error initiating email thread: {e}")
        return False

def send_issue_confirmation_email(user_email, user_name, tracking_id, category, description, location):
    """Sends an appealing HTML email confirmation on issue reporting."""
    subject = _get_text("email_report_subject").format(tracking_id)
    
    # Simple HTML Template with inline CSS for broad compatibility
    body_html = _get_text("email_report_body_html").format(
        user_name=user_name,
        tracking_id=tracking_id,
        category=category,
        location=location,
        description=description,
        date=datetime.now().strftime("%d %b %Y, %I:%M %p")
    )
    
    # Run email sending in a separate thread
    threading.Thread(target=send_email, args=(user_email, subject, body_html), kwargs={"content_type": "html"}).start()
    return True

# ---------------- CONFIGURATION ----------------
app.secret_key = os.environ.get("SECRET_KEY", "new_secure_random_key_2025")

# Ensure the database directory exists (Only if using SQLite/Local)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_NAME = os.path.join(DB_DIR, "panchayath.db")

if not any(os.environ.get(k) for k in ["Panchayat_DATABASE_URL", "Panchayat_POSTGRES_URL", "DATABASE_URL", "POSTGRES_URL"]):
    try:
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
    except Exception as e:
        print(f"Skipping DB_DIR creation: {e}")

# ---------------- DATABASE CONNECTION ----------------

def connect_db():
    # Check for Postgres (Production) or SQLite (Local)
    # Priority order: Panchayat_... (user's specific name), DATABASE_URL (Standard), POSTGRES_URL (Vercel)
    db_url = (
        os.environ.get("Panchayat_DATABASE_URL") or 
        os.environ.get("Panchayat_POSTGRES_URL") or 
        os.environ.get("DATABASE_URL") or 
        os.environ.get("POSTGRES_URL")
    )
    
    if db_url and db_url.startswith("postgres"):
        if psycopg2 is None:
            print("CRITICAL ERROR: 'psycopg2-binary' is missing but DATABASE_URL is set to Postgres.")
            raise ImportError("psycopg2-binary is required for Postgres connection. Run: pip install psycopg2-binary")
        # Handle "postgres://" vs "postgresql://" for SQLAlchemy compatibility if needed
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        conn = psycopg2.connect(db_url)
        # Make Postgres behave like sqlite3.Row (DictCursor supports both index and name)
        conn.autocommit = True
        # Overwrite cursor to return DictRow objects
        original_cursor = conn.cursor
        def compat_cursor(*args, **kwargs):
            cursor = original_cursor(*args, cursor_factory=DictCursor, **kwargs)
            original_execute = cursor.execute
            def wrapped_execute(query, params=None):
                if params and isinstance(query, str):
                    query = query.replace("?", "%s")
                return original_execute(query, params)
            cursor.execute = wrapped_execute
            return cursor
        conn.cursor = compat_cursor
        
        # Also need a top-level execute for conn.execute calls
        def conn_execute(query, params=None):
            cur = conn.cursor()
            cur.execute(query, params)
            return cur
        conn.execute = conn_execute
        return conn
    else:
        # Fallback to local SQLite
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
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
    
    # Check if we are on Postgres to handle syntax differences
    is_postgres = False
    try:
        import psycopg2
        # If it's our wrapped psycopg2 connection, it has 'cursor_factory' or we check type
        if hasattr(conn, 'autocommit'):
            is_postgres = True
    except Exception:
        pass

    sql_script = """
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
        expiry_date DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        panchayath_id INTEGER,
        title TEXT,
        description TEXT,
        image_path TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (panchayath_id) REFERENCES panchayath(id) ON DELETE CASCADE
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
    """

    if is_postgres:
        # Transform SQLite syntax to Postgres for compatibility
        sql_script = sql_script.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        sql_script = sql_script.replace("DATETIME", "TIMESTAMP")

    conn.executescript(sql_script)
    
    # Helper to check if column exists
    def column_exists(table, column):
        try:
            conn.execute(f"SELECT {column} FROM {table} LIMIT 1")
            return True
        except Exception:
            return False

    if not column_exists("issues", "user_id"):
        conn.execute("ALTER TABLE issues ADD COLUMN user_id INTEGER")
        conn.commit()

    if not column_exists("issues", "tracking_id"):
        conn.execute("ALTER TABLE issues ADD COLUMN tracking_id TEXT")
        conn.commit()

    if not column_exists("issues", "reporter_name"):
        conn.execute("ALTER TABLE issues ADD COLUMN reporter_name TEXT")
        conn.commit()
        # Backfill existing names from users table
        try:
            conn.execute("""
                UPDATE issues 
                SET reporter_name = (SELECT name FROM users WHERE users.id = issues.user_id)
                WHERE reporter_name IS NULL
            """)
            conn.commit()
        except Exception:
            pass

    if not column_exists("notices", "banner_path"):
        conn.execute("ALTER TABLE notices ADD COLUMN banner_path TEXT")
        conn.commit()

    if not column_exists("notices", "expiry_date"):
        conn.execute("ALTER TABLE notices ADD COLUMN expiry_date DATETIME")
        conn.commit()

    conn.commit()
    conn.close()

def process_expired_notices():
    conn = connect_db()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get expired notices
    try:
        conn.row_factory = sqlite3.Row
        expired_notices = conn.execute("""
            SELECT * FROM notices 
            WHERE expiry_date IS NOT NULL AND expiry_date <= ?
        """, (current_time,)).fetchall()
        
        for notice in expired_notices:
            # Move to activities
            conn.execute("""
                INSERT INTO activities (panchayath_id, title, description, image_path, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (notice['panchayath_id'], notice['title'], "", notice['banner_path'], notice['created_at']))
            
            # Delete from notices
            conn.execute("DELETE FROM notices WHERE id = ?", (notice['id'],))
        
        conn.commit()
    except sqlite3.OperationalError:
        pass # Column might not exist yet
    finally:
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

# ---------------- INITIALIZE AT STARTUP (For Vercel/Production) ----------------
try:
    init_db()
    seed_data()
except Exception as e:
    print(f"Startup Database Error: {e}")

# ---------------- HELPERS ----------------
def generate_tracking_id():
    import uuid
    # Generate a short unique ID (e.g., TRK-1A2B3C)
    return "TRK-" + str(uuid.uuid4())[:8].upper()


@app.context_processor
def utility_processor():
    def get_image_url(path):
        if not path:
            return ""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        from flask import url_for
        return url_for('static', filename=path)
    return dict(get_image_url=get_image_url)

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
        location = request.form.get("location", "").strip()
        
        # If "Others" is selected, use the custom name provided
        if category == "Others":
            other_cat = request.form.get("other_category_name", "").strip()
            if other_cat:
                category = other_cat
        
        # 1. Basic Cleaning & Content Check
        description = request.form["description"].strip()
        desc_len = len(description)
        words = description.split()
        word_count = len(words)
        
        # 2. Junk Check: Prevent repeating characters (e.g., "hhhhhh")
        # Blocks 5 or more identical characters in a row
        if re.search(r'(.)\1{4,}', description):
            flash(_get_text("flash_description_junk"), "danger")
            return redirect(url_for("report_issue"))

        # 3. Absolute Minimum: 10 words
        if word_count < 10:
            flash(_get_text("flash_description_words"), "danger")
            return redirect(url_for("report_issue"))
            
        # 4. Max Length: 500 chars
        if desc_len > 500:
            flash(_get_text("flash_description_len"), "danger")
            return redirect(url_for("report_issue"))
        
        image = request.files.get("image")
        
        # Restore: Conditional photo requirement: if words < 15 OR chars < 30, image is mandatory
        if (word_count < 15 or desc_len < 30) and (not image or image.filename == ""):
            if word_count < 15:
                flash(_get_text("flash_photo_required_words"), "danger")
            else:
                flash(_get_text("flash_photo_required_refined"), "danger")
            return redirect(url_for("report_issue"))

        image_filename = None
        tracking_id = generate_tracking_id()
        
        if image and image.filename != "":
            # Try Vercel Blob
            blob_url = upload_to_blob(image, f"issue_{tracking_id}_{image.filename}")
            if blob_url:
                image_filename = blob_url
            else:
                # Fallback
                upload_folder = os.path.join(BASE_DIR, "static", "uploads")
                if not os.environ.get("DATABASE_URL") and not os.environ.get("Panchayat_DATABASE_URL"):
                     os.makedirs(upload_folder, exist_ok=True)
                ext = os.path.splitext(image.filename)[1]
                filename = f"issue_{tracking_id}{ext}"
                try:
                    image.save(os.path.join(upload_folder, filename))
                    image_filename = f"uploads/{filename}"
                except:
                    image_filename = None

        user_name = session.get("user_name", "Anonymous")

        conn.execute("""
            INSERT INTO issues (panchayath_id, category, description, location, photo_path, user_id, tracking_id, reporter_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (panchayath_id, category, description, location, image_filename, user_id, tracking_id, user_name))

        conn.commit()
        
        # Fetch user email for notification
        user = conn.execute("SELECT email, name FROM users WHERE id = ?", (user_id,)).fetchone()
        
        if user:
            send_issue_confirmation_email(
                user_email=user["email"],
                user_name=user["name"],
                tracking_id=tracking_id,
                category=category,
                description=description,
                location=location
            )
            
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
        SELECT i.*, p.name AS panchayath_name, COALESCE(i.reporter_name, u.name, 'Anonymous') AS user_name
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
    process_expired_notices()
    conn = connect_db()
    notices = conn.execute("""
        SELECT n.*, p.name AS panchayath_name
        FROM notices n
        JOIN panchayath p ON p.id = n.panchayath_id
        ORDER BY n.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("citizen/notices.html", notices=notices)

@app.route("/activities")
def activities():
    process_expired_notices()
    conn = connect_db()
    activities = conn.execute("""
        SELECT a.*, p.name AS panchayath_name
        FROM activities a
        JOIN panchayath p ON p.id = a.panchayath_id
        ORDER BY a.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("citizen/activities.html", activities=activities)


# ---------------- USER AUTH ROUTES ----------------

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per hour")
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

        # Check if user already exists BEFORE sending OTP
        conn = connect_db()
        existing_user = conn.execute("SELECT * FROM users WHERE email = ? OR mobile = ?", (email, mobile)).fetchone()
        conn.close()
        
        if existing_user:
            flash(_get_text("flash_user_exists"), "danger")
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
@limiter.limit("10 per hour")
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
@limiter.limit("3 per hour")
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
@limiter.limit("10 per hour")
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
@limiter.limit("10 per hour")
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
    pid = session.get("panchayath_id")
    print(f"DEBUG ADMIN DASHBOARD: Session PID = {pid}")
    conn = connect_db()

    issues_rows = conn.execute("""
        SELECT i.*, COALESCE(i.reporter_name, u.name, 'Anonymous') as reporter_name 
        FROM issues i
        LEFT JOIN users u ON i.user_id = u.id
        WHERE i.panchayath_id = ? AND i.status != 'Completed' AND i.status != 'Rejected'
        ORDER BY i.created_at DESC
    """, (pid,)).fetchall()
    
    print(f"DEBUG ADMIN DASHBOARD: Found {len(issues_rows)} active rows in DB for PID {pid}")
    
    issues = [dict(row) for row in issues_rows]

    # Pre-group issues by category for robust template rendering
    grouped_issues = {cat: [] for cat in CATEGORIES}
    for issue in issues:
        cat = issue.get('category')
        print(f"DEBUG ADMIN DASHBOARD: Processing issue {issue['id']} with category '{cat}'")
        if cat in grouped_issues:
            grouped_issues[cat].append(issue)
        else:
            print(f"DEBUG ADMIN DASHBOARD: Category '{cat}' not found in CATEGORIES list!")
            grouped_issues.setdefault("Others", []).append(issue)

    # Calculate stats for dashboard cards
    stats = {
        "total": conn.execute("SELECT COUNT(*) FROM issues WHERE panchayath_id = ?", (pid,)).fetchone()[0],
        "resolved": conn.execute("SELECT COUNT(*) FROM issues WHERE panchayath_id = ? AND status = 'Completed'", (pid,)).fetchone()[0],
        "pending": conn.execute("SELECT COUNT(*) FROM issues WHERE panchayath_id = ? AND status = 'Pending'", (pid,)).fetchone()[0],
        "under_review": conn.execute("SELECT COUNT(*) FROM issues WHERE panchayath_id = ? AND status = 'Under Review'", (pid,)).fetchone()[0],
        "rejected": conn.execute("SELECT COUNT(*) FROM issues WHERE panchayath_id = ? AND status = 'Rejected'", (pid,)).fetchone()[0]
    }

    conn.close()
    return render_template("admin/dashboard.html", issues_by_category=grouped_issues, stats=stats)

@app.route("/admin/completed_issues")
@login_required
def admin_completed_issues():
    pid = session["panchayath_id"]
    conn = connect_db()

    issues = conn.execute("""
        SELECT i.*, COALESCE(i.reporter_name, u.name, 'Anonymous') as reporter_name 
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
        SELECT i.*, COALESCE(i.reporter_name, u.name, 'Anonymous') as reporter_name 
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
        process_expired_notices()
        title = request.form["title"]
        description = request.form["description"]
        expiry_date = request.form.get("expiry_date")
        if expiry_date:
            # Check if expiry_date (YYYY-MM-DD) is in the past
            current_date = datetime.now().strftime("%Y-%m-%d")
            if expiry_date < current_date:
                flash(_get_text("flash_expiry_past"), "danger")
                return redirect(url_for("admin_notices"))
            
            # Save as end of day for database consistency
            expiry_date = expiry_date + " 23:59:59"
        else:
            expiry_date = None
        
        banner = request.files.get("banner")
        banner_filename = None
        
        if banner and banner.filename != "":
            blob_url = upload_to_blob(banner, f"notice_{int(time.time())}_{banner.filename}")
            if blob_url:
                banner_filename = blob_url
            else:
                upload_folder = os.path.join(BASE_DIR, "static", "uploads")
                if not os.environ.get("DATABASE_URL") and not os.environ.get("Panchayat_DATABASE_URL"):
                    os.makedirs(upload_folder, exist_ok=True)
                ext = os.path.splitext(banner.filename)[1]
                filename = f"notice_{int(time.time())}{ext}"
                try:
                    banner.save(os.path.join(upload_folder, filename))
                    banner_filename = f"uploads/{filename}"
                except:
                    banner_filename = None

        conn.execute("""
            INSERT INTO notices (panchayath_id, title, description, banner_path, expiry_date)
            VALUES (?, ?, ?, ?, ?)
        """, (pid, title, description, banner_filename, expiry_date))
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
        # Delete the physical file if it exists
        if notice['banner_path']:
            file_path = os.path.join(BASE_DIR, "static", notice['banner_path'])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        conn.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
        conn.commit()
        flash(_get_text("flash_notice_deleted"), "success")
    else:
        flash(_get_text("flash_notice_unauthorized"), "danger")
        
    conn.close()
    return redirect(url_for("admin_notices"))

@app.route("/admin/activities", methods=["GET", "POST"])
@login_required
def admin_activities():
    pid = session["panchayath_id"]
    conn = connect_db()

    if request.method == "POST":
        title = request.form["title"]
        description = ""
        
        image = request.files.get("image")
        image_filename = None
        
        if image and image.filename != "":
            blob_url = upload_to_blob(image, f"activity_{int(time.time())}_{image.filename}")
            if blob_url:
                image_filename = blob_url
            else:
                upload_folder = os.path.join(BASE_DIR, "static", "uploads")
                if not os.environ.get("DATABASE_URL") and not os.environ.get("Panchayat_DATABASE_URL"):
                    os.makedirs(upload_folder, exist_ok=True)
                ext = os.path.splitext(image.filename)[1]
                filename = f"activity_{int(time.time())}{ext}"
                try:
                    image.save(os.path.join(upload_folder, filename))
                    image_filename = f"uploads/{filename}"
                except:
                    image_filename = None

        conn.execute("""
            INSERT INTO activities (panchayath_id, title, description, image_path)
            VALUES (?, ?, ?, ?)
        """, (pid, title, description, image_filename))
        conn.commit()
        flash(_get_text("flash_activity_published"), "success")

    activities = conn.execute("""
        SELECT * FROM activities
        WHERE panchayath_id = ?
        ORDER BY created_at DESC
    """, (pid,)).fetchall()

    conn.close()
    return render_template("admin/activities.html", activities=activities)

@app.route("/admin/activities/delete/<int:activity_id>")
@login_required
def delete_activity(activity_id):
    pid = session["panchayath_id"]
    conn = connect_db()
    
    activity = conn.execute("SELECT * FROM activities WHERE id = ? AND panchayath_id = ?", (activity_id, pid)).fetchone()
    
    if activity:
        if activity['image_path']:
            file_path = os.path.join(BASE_DIR, "static", activity['image_path'])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        conn.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        conn.commit()
        flash(_get_text("flash_activity_deleted"), "success")
    else:
        flash(_get_text("flash_notice_unauthorized"), "danger")
        
    conn.close()
    return redirect(url_for("admin_activities"))


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

@app.route("/admin/issue/view/<int:issue_id>")
@login_required
def admin_issue_detail(issue_id):
    pid = session["panchayath_id"]
    conn = connect_db()
    issue = conn.execute("""
        SELECT i.*, COALESCE(i.reporter_name, u.name, 'Anonymous') as reporter_name, u.email as reporter_email, u.mobile as reporter_mobile, p.name as panchayath_name
        FROM issues i
        LEFT JOIN users u ON i.user_id = u.id
        JOIN panchayath p ON i.panchayath_id = p.id
        WHERE i.id = ? AND i.panchayath_id = ?
    """, (issue_id, pid)).fetchone()
    conn.close()
    if not issue:
        flash(_get_text("flash_issue_not_found"), "danger")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/issue_detail.html", issue=issue)

@app.route("/admin/issue/delete/<int:issue_id>")
@login_required
def delete_issue(issue_id):
    pid = session["panchayath_id"]
    conn = connect_db()
    
    # Ensure the issue belongs to this panchayath
    issue = conn.execute("SELECT * FROM issues WHERE id = ? AND panchayath_id = ?", (issue_id, pid)).fetchone()
    
    if issue:
        # Delete the physical file if it exists
        if issue['photo_path']:
            file_path = os.path.join(BASE_DIR, "static", issue['photo_path'])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        conn.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
        conn.commit()
        flash(_get_text("flash_issue_deleted"), "success")
    else:
        flash(_get_text("flash_issue_unauthorized"), "danger")
        
    conn.close()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/update/<int:issue_id>", methods=["POST"])
@login_required
def update_issue(issue_id):
    # Authorization check handled by decorator

    status = request.form["status"]
    rejection_reason = request.form.get("rejection_reason") if status == "Rejected" else None
    
    conn = connect_db()
    
    # Fetch issue and user details BEFORE updating
    issue = conn.execute("""
        SELECT i.*, u.email, u.name as user_name, p.name as panchayath_name
        FROM issues i
        LEFT JOIN users u ON i.user_id = u.id
        JOIN panchayath p ON i.panchayath_id = p.id
        WHERE i.id = ?
    """, (issue_id,)).fetchone()
    
    conn.execute(
        "UPDATE issues SET status=?, rejection_reason=? WHERE id=?",
        (status, rejection_reason, issue_id)
    )
    conn.commit()
    conn.close()

    if issue and issue["email"]:
        # Send email notification
        send_status_update_email(
            user_email=issue["email"],
            user_name=issue["user_name"],
            tracking_id=issue["tracking_id"],
            issue_category=issue["category"],
            new_status=status,
            rejection_reason=rejection_reason
        )

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
    # Host '0.0.0.0' allows external access on the local network
    app.run(debug=True, host='0.0.0.0')

