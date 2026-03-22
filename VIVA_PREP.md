# 🎓 Viva Preparation - Complete Technical "Cheat Sheet"

If the examiner asks how the portal works, use these simple, conversational explanations. This sheet covers everything from the most basic concepts to the highly advanced features woven into your project.

---

## 🟢 SECTION 1: The Basics (What & Why)

**Q: What is the main objective of your project?**
A: To provide a localized, simple-to-use digital portal for citizens to report civic issues directly to their Panchayat office without needing an active internet connection.

**Q: What technologies did you use (Tech Stack) and why?**
A: 
- **Backend:** Python + Flask (Lightweight, readable, perfect for setting up a local server quickly).
- **Frontend:** HTML5, CSS3, JavaScript (Responsive, modern design).
- **Database:** SQLite3 (Serverless, file-based, meaning it requires zero installation or heavy MySQL server processes on Panchayat office PCs).

**Q: Can anyone on the Internet see this website?**
A: No. It operates on a **Local Area Network (LAN) / Intranet**. It is completely private. Both the user (phone) and the admin (PC) must be connected to the same Wi-Fi router. 

**Q: What is the difference between Frontend and Backend in your project?**
A: The Frontend is the face (the buttons, form fields, and colors users see). The Backend is the brain (the Python logic that processes logins, validates data, talks to the database, and sends OTP emails).

---

## 🟡 SECTION 2: Networking & Connectivity (CRITICAL)

**Q: In your code, you use `app.run(host='0.0.0.0')`. What does this mean? Why not `127.0.0.1`?** *(Highly likely question)*
A: `127.0.0.1` (localhost) strictly means "only allow connections from THIS computer." Setting the host to `0.0.0.0` tells the Flask server to open up and **"listen" for incoming connections from ANY device** on the local Wi-Fi network. Without `0.0.0.0`, mobile phones could not access the portal.

**Q: What is a Port? Why use Port 5000?**
A: An IP address points to a computer, but a Port points to a specific "door" or service on that computer. Flask uses Port 5000 by default. So, when the phone types `192.168.1.10:5000`, it says "Go to this PC, and enter through Door 5000" where our Python app is waiting.

**Q: Why did we have to configure the Windows Firewall?**
A: Windows Firewall acts as a strict security guard that blocks external devices from pinging the PC. We had to add a rule to allow Python through the Firewall so that citizens' phones are granted a "VIP Pass" to communicate with the Flask server.

**Q: How does the `LAUNCH_PORTAL.bat` file work?**
A: It's an automation script. It automatically strictly enforces the Python environment, checks for dependencies (via `requirements.txt`), uses `route print` to dynamically magically find the PC's Local IP address, spits out the link for phones to use, and starts the server.

---

## 🟠 SECTION 3: Database & Architecture

**Q: How is data stored in SQLite?**
A: It is file-based. The entire database is stored inside a single file named `panchayath.db`.

**Q: What is `PRAGMA journal_mode=WAL;` and why did you use it?** *(Advanced)*
A: WAL stands for **Write-Ahead Logging**. By default, SQLite completely locks the entire database when one person writes to it, causing crashes if a second person tries to read/write. WAL mode enables **Concurrency**, allowing multiple citizens to read and write to the database simultaneously without getting "Database is Locked" errors.

**Q: What is `ON DELETE CASCADE` in your `schema.sql`?**
A: It maintains Data Integrity. If an admin deletes a "Panchayath" from the master list, the database will automatically CASCADE and delete all admins, activities, and notices linked to that Panchayath so we aren't left with orphaned "junk" data.

**Q: How did you implement Database Migrations when you added new features?** *(Advanced)*
A: In `init_db()`, instead of dropping the tables, I used `try/except sqlite3.OperationalError` blocks. The system attempts to read a new column; if it fails, it executes an `ALTER TABLE` query to append the new column on-the-fly without destroying existing citizen data.

---

## 🔴 SECTION 4: Security & Authentication

**Q: How is user and admin password data protected?**
A: Passwords are NEVER saved as plain text. I used `werkzeug.security` to generate a **Password Hash** using the PBKDF2 algorithm. It turns "admin123" into an unreadable string (`pbkdf2:sha256:260000$...`) that cannot be reverse-engineered.

**Q: What is SQL Injection and how did you prevent it?**
A: SQL Injection is a hack where users type malicious SQL commands into form boxes (like `DROP TABLE users;`). I prevented this by using **Parameterized Queries** (using `?` placeholders like `execute("SELECT FROM users WHERE email=?", (email,))`). This forces the database to treat inputs strictly as text data, not as executable code.

**Q: How did you implement user access control?**
A: I built custom Python decorators (`@login_required` and `@user_login_required`) using `functools.wraps`. They intercept page requests, check if the `session["user_id"]` exists, and if not, boot the user out to the login screen.

---

## 🟣 SECTION 5: Email OTP & Multi-Threading

**Q: How are OTPs generated and sent?**
A: OTPs are generated using Python's `random.randint`. Emails are sent via Google's SMTP server using the `smtplib` and `email.mime` libraries to send properly formatted HTML emails.

**Q: Why did you use `threading.Thread` to send the emails?** *(Advanced - Guaranteed to impress)*
A: Connecting to Gmail's server takes 2 to 3 seconds. If I fired the email on the main timeline, the user's browser would "freeze" and spin until the email was sent. By using Python's `threading.Thread`, I pass the email-sending task to a **background process**, allowing the web page to load instantly for the user.

**Q: How does the OTP expiration logic work?**
A: When OTP is sent, I save Python's `time.time()` into the session limit. When the user submits the OTP, I calculate `time.time() - session['otp_time']`. If the difference is > 120 seconds, the OTP is rejected.

---

## 🔵 SECTION 6: File Uploads & UI Logic

**Q: How does the server know the user is uploading a file instead of normal text?**
A: In the HTML form tag, I added `enctype="multipart/form-data"`. This splits the form payload into multiple structural chunks so images can travel safely.

**Q: How do you handle duplicate file uploads securely?**
A: Users might upload pictures with the exact same name (e.g. `image1.jpg`). To prevent overriding, the Python backend intercepts the upload and appends a `time.time()` integer timestamp to the filename (e.g. `issue_170284455.jpg`).

**Q: Explain your Form Validations. Are they Client-Side or Server-Side?**
A: Both. I use HTML `required` attributes (Client). However, I also rigorously check inputs in Python (Server) using **Regex (Regular Expressions)** for mobile numbers (`^\+91[6-9]\d{9}$`) and strict password checks to prevent intelligent hackers who bypass browser constraints.

**Q: How did you build the modern popup messages?**
A: By binding Flask's built-in `flash()` variables with a custom JavaScript function `createPopup()`. When Python flashes an error, JS intercepts it and builds a beautiful floating HTML element automatically rather than an ugly browser `alert()`.

**Q: How do you handle multi-language (English/Kannada)?**
A: I use a centralized `translations.py` dictionary. I attached a Flask `@app.context_processor` which automatically injects an `_get_text()` translating function into all HTML templates. 

**Q: How is the 'Tracking ID' created?**
A: Using Python's `uuid4()`. It guarantees an untraceable, mathematically random alphanumeric shortcode (e.g., `TRK-A1B2C3`) so users cannot spy on other people's complaints by guessing numbers like `Issue 1`, `Issue 2`, etc.

---

## 🟢 SECTION 7: Master List of All Features (Big & Small)

If asked "What features does your portal have?", start with the major ones and drop in the micro-features to show incredible attention to detail.

### 🌟 Core Features (Major)
1. **Multi-Language Support (i18n):** Users can toggle the entire portal between English and Kannada instantly without reloading the page logic. This is built using a custom dictionary (`translations.py`) and a Flask `context_processor`.
2. **"Others" Dynamic Issue Category:** If a citizen selects the "Others" category, a hidden text box seamlessly appears via JavaScript. The backend Python code dynamically catches this text and overrides the standard dropdown value.
3. **Automated Notice Expiry & Archiving System:** Instead of admins manually deleting old notices, a custom Python function (`process_expired_notices()`) activates on every page load to check expiry dates. If a notice holds an expired date, the system automatically moves it from the `notices` table directly into the `activities` table so past events are never permanently lost.
4. **Real-Time Dynamic Dashboard Analytics:** The admin dashboard calculates live statistics natively from the database—calculating Total Issues, Resolved Issues, Pending issues, and the exact Resolution Rate Percentage instantly.
5. **Dual Issue Tracking Systems:** 
   - **Private Tracker:** Citizens who are logged in can securely view their personal reports using their private User ID.
   - **Public Tracker:** Anyone can view a public transparency board that displays all issues raised by everyone (with names attached or set to 'Anonymous'), building civic trust.

### 🛡️ Smart Validation Features (Intermediate)
6. **Strict Submission Integrity Checker:** If someone writes gibberish like *"hhhhhhh"*, the server uses Regex `r'(.)\1{4,}'` to detect and block repeating junk characters instantly.
7. **Adaptive Minimum Text Validation:** The backend strictly checks that an issue description contains an absolute minimum of 10 words, and limits it to exactly 500 characters.
8. **Conditional Photo upload Logic:** If a user submits a very short description (less than 15 words or <30 characters), the Python logic adapts and makes uploading an image **strictly mandatory**. If they write a long essay, the image is optional.

### 📧 Email & Notification Features 
9. **Event-Triggered System Emails:** 
   - **OTP Authentication:** For secure registration, an OTP is emailed to verify identity. If the email fails, the system safely falls back to a manual override OTP flow.
   - **Change of Status Alerts:** Any time the Admin changes an issue status (e.g., from "Pending" to "Rejected"), a custom HTML email is shot out to the user instantly. If rejected, the exact rejection reason is included in the email.
   - **Instant Registration Receipt:** As soon as an issue is filed, an HTML-formatted receipt with their exact `Tracking ID` is automatically sent in the background.

### 🔬 "Micro-Features" Built for Polish (The Small Details)
10. **Modern Flash Popups:** Bypassed the nasty default browser `alert()` popups. Built a custom JavaScript system (`createPopup()`) that intercepts Python `flash()` messages and generates beautiful, animated floating snackbars based on error severity (success, warning, info, danger).
11. **Secure Filename Collision Prevention:** If two users upload an image named `pothole.jpg`, the server automatically retrieves the UNIX timestamp `time.time()`, renames the file to `issue_17034455.jpg` and uses `secure_filename` so files are never accidentally overwritten.
12. **Background Multithreaded Processing:** Used Python's `threading.Thread` so the massive delay of connecting to Gmail's SMTP servers happens invisibly in the background, keeping the portal lightning fast for the citizen.
13. **Local Deployment Script (`LAUNCH_PORTAL.bat`):** Created a custom batch script that automatically sets paths, installs missing Python `pip` packages silently, intelligently pings the PC router IP to find the Intranet address, and skips Windows firewalls.
14. **Database Self-Healing Migrations:** Instead of dropping the database whenever a new column is added, `init_db()` tries pushing columns dynamically and quietly handles SQLite errors without crashing.

---
💡 **PRO TIPS for the Viva:**
- If they ask about "Scalability", mention that SQLite is perfect for local offices, but the Flask logic is built modularly, making it incredibly easy to swap out SQLite for a cloud PostgreSQL instance in the future.
- If they inquire about a feature, try to trace the workflow: *"First the HTML form takes the data, JS validates it briefly, then Flask catches it via POST, runs Regex verification, executes a Parameterized query on the SQLite DB, and finally fires a Flash message."*
