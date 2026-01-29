# 📖 Meri Panchayat Portal - Staff Guide
This guide explains how to set up and run the **Meri Panchayat Portal** on your office computer. Follow these simple steps to keep the portal running smoothly.
---
## 🛠️ Initial One-Time Setup
*Run these steps only if this is a brand-new computer.*

1.  **Install Python**: Download and install Python 3.x from [python.org](https://www.python.org/downloads/).
2.  **Install Packages**: 
    - Find `install_packages.bat` in this folder.
    - **Double-click** it and wait for the window to close.
---
## 🚀 Daily Launch Instructions
*Follow these steps every morning or whenever you need the portal.*

1.  **Start the Portal**: Double-click `LAUNCH_PORTAL.bat`.
2.  **Wait for the Browser**: Your web browser will open automatically.
3.  **Keep it Running**: A black terminal window will stay open—**do not close it**. This is the "engine" that runs the portal.
---


## 📱 Accessing from Mobile Phones
Other staff members can access the portal from their phones or other computers on the **same Wi-Fi**.

1.  Read the **Local Network Address** from the black terminal window (e.g., `http://192.168.1.5:5000`).
2.  Type that exact address into any phone's web browser.

> [!TIP]
> **No Setup Needed on Phones:** Your phone does **not** need these files. It only needs to be on the same Wi-Fi.
---
## 🛠️ Troubleshooting Mobile Access
If the link won't open on your phone, check these 3 common fixes on the **Main Computer**:

### 1. Same Wi-Fi
Ensure the phone and computer are on the **exact same Wi-Fi network**.

### 2. Network Profile (Private vs Public)
1. Go to **Settings > Network & Internet > Wi-Fi**.
2. Click your Wi-Fi name and ensure **Network Profile Type** is set to **Private**.

### 3. Windows Firewall (Python Access)
1. Search Windows for **"Allow an app through Windows Firewall"**.
2. Click **Change settings** (top right).
3. Find **"Python"** and ensure both **Private** and **Public** boxes are checked.
4. Click **OK**.
---
## 🛑 How to Stop or Restart
- **To Stop**: Simply close the black terminal window.
- **To Restart**: Close the black terminal window, then double-click `LAUNCH_PORTAL.bat` again.
---
*Developed for Meri Panchayat Portal Management.*
