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
- **Database:** **SQLite3**. It's a "File-based" database, meaning the whole database lives in one file (`database.db`). It's perfect for local office use.



### 6. Is it on the Internet?

- **Answer:** It is a **Local Web App (Intranet)**. This is actually better for a Panchayat because it's **private and secure**. It works even if the main internet connection is slow, as long as the office Wi-Fi is working.



---
*Pro Tip: If they ask about security, mention that only people on the office Wi-Fi can access it (Physical Security).*
