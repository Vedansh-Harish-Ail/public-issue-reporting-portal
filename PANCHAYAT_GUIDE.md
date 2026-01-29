# 📖 Quick Start Guide for Panchayat Staff

This guide explains how to set up and run the **Meri Panchayat Portal** on your office computer without needing any technical software like VS Code.

## 🛠️ Initial One-Time Setup
Before running the portal for the first time, you must install the necessary components:

1.  **Install Python**: Ensure Python 3.x is installed on the computer. (Download from [python.org](https://www.python.org/downloads/)).
2.  **Install Project Packages**:
    - Locate the file `install_packages.bat` in this folder.
    - **Double-click** it.
    - Wait for the black window to finish and then press any key to close it.

---

## 🚀 How to Launch the Portal
Every morning (or whenever you need to use the system), simply:

1.  Locate the file `LAUNCH_PORTAL.bat`.
2.  **Double-click** it.
3.  **What happens next?**
    - Your web browser will automatically open to the portal.
    - A black terminal window will stay open in the background—**do not close this window**, as it is the "engine" running the portal.

---

## 📱 Accessing from Other Computers (LAN)
Since this portal is set up for office use, other staff on the **same Wi-Fi or Local Network** can also access it:

1.  When you run `LAUNCH_PORTAL.bat`, look at the black terminal window. 
2.  It will display a line: **"Your Local Network Address is: http://192.168.x.x:5000"**.
3.  On any other computer or phone connected to the office Wi-Fi, type that exact address into the browser.
4.  The portal will open just like it does on the main computer!

> [!TIP]
> **No Files Needed on Phone:** Your phone (or other computers) does **not** need any of these project files. Only the main "Server" computer needs the files. Your phone just uses its web browser to look at the portal running on the main computer.


---

## 🛑 How to Stop
To turn off the portal, simply close the black terminal window that says "Starting Meri Panchayat Portal".
