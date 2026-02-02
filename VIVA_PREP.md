# 🎓 Viva Preparation - Technical "Cheat Sheet"

If the examiner asks how the portal works, use these simple, conversational explanations.

---

### 1. The Big Picture (How it talks)

**The Concept:** Local Area Network (LAN).
- **Explanation:** The PC acts as a **Local Server**. Since both the PC and the Phone are on the same Wi-Fi, they can talk to each other.
- **The Address:** The phone uses the PC's **Local IP Address** (e.g., `10.39.186.85:5000`) to request the website.

### 2. What is `0.0.0.0`? (CRITICAL QUESTION!)

In `app.py`, we use `app.run(host='0.0.0.0')`.
- **Question:** Why not use the default `127.0.0.1`?
- **Answer:** `127.0.0.1` (localhost) means "Only this computer." Setting it to `0.0.0.0` tells the computer to **"listen" for requests from any device** on the local network. Without this, your phone could never see the site.

### 3. Ports & Doors

- **Explanation:** A port is like a "door" on the computer. Flask uses **Port 5000** by default. When the phone connects, it's knocking on door 5000 to find the portal.

### 4. Why the Firewall fix?

- **Explanation:** Windows Firewall is a security guard. It blocks unknown devices from talking to your PC. By "Allowing Python through the Firewall," we gave the phone a "VIP Pass" to access the server.

### 5. Tech Stack (The Tools)

- **Backend:** Python & Flask (The engine and manager).
- **Frontend:** HTML, CSS, JavaScript (The face of the portal).
- **Database:** **SQLite3**. It's a "File-based" database, meaning the whole database lives in one file (`panchayath.db`). It's perfect for local office use.
- **Security:** `werkzeug.security` for password hashing (PBKDF2).
- **Communication:** `smtplib` for automated email notifications.

### 6. "Minute Details" (Hidden Tech)

- **Database Concurrency (WAL mode):** In `app.py`, we use `PRAGMA journal_mode=WAL;`. This allows multiple users to read the database while someone is writing to it, preventing "Database is Locked" errors.
- **Asynchronous Actions (Threading):** Emails are sent using `threading.Thread`. This sends emails in the background so the website doesn't freeze while waiting for the mail server.
- **Unique Tracking IDs:** We use `uuid4()` to generate short, unique IDs like `TRK-A1B2C3` so users can't guess other people's issue numbers.
- **Secure File Handling:** Uploaded photos are renamed with a timestamp and a "secure filename" to prevent duplicate names and malicious file uploads.
- **DB Integrity (Foreign Keys):** In `schema.sql`, we use `ON DELETE CASCADE`. This ensures that if a Panchayat is deleted, all associated admins and notices are automatically removed, keeping the data clean.
- **Advanced Flash Popups:** Instead of standard browser alerts, we integrated Flask's `flash()` system with a custom JavaScript `createPopup()` function in `base.html` for a modern, premium user experience.
- **Template Modularity (Macros):** We use **Jinja2 Macros** (in `macros.html`) for reusable components like the "Back Button," which makes the code cleaner and easier to maintain.
- **Strict Validation (Regex):** We use Regular Expressions (Regex) in `app.py` to enforce strict security:
    - **Mobile:** Must start with `+91` and follow Indian numbering standards.
    - **Password:** Must have 1 Uppercase, 1 Lowercase, 1 Number, and 1 Special Character.

### 7. Potential Viva Questions & Answers

**Q: Why use SQLite instead of MySQL?**
A: SQLite is serverless and lightweight. For a Panchayat office, it requires no setup, runs as a single file, and is extremely fast for this scale.

**Q: How do you handle multi-language (English/Kannada)?**
A: I use a `translations.py` dictionary and a Flask `context_processor` called `get_text`. It checks the user's session for the language preference and displays the correct text.

**Q: What is SQL Injection and how did you prevent it?**
A: It's when an attacker tries to run malicious SQL through input fields. I used **parameterized queries** (using `?` placeholders) which separates the SQL logic from the data, making it impossible to inject.

**Q: How does the "Other" category work?**
A: In the "Report Issue" page, if a user selects "Others," a JavaScript event listener dynamically unhides a text input. The backend then prioritizes this custom input over the dropdown value.

**Q: Is it on the Internet?**
A: It is a **Local Web App (Intranet)**. This is better for a Panchayat because it's private, secure, and works even if the main internet is slow, as long as the office Wi-Fi is on.

---
*Pro Tip: If they ask about security, mention that only people on the office Wi-Fi can access it (Physical Security) and passwords are saved as "hashes."*
