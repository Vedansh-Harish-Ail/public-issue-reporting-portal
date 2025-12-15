<div align="center">

  <img src="static/image/banner_main.png" alt="Meri Panchayat Banner" width="100%" style="border-radius: 10px; margin-bottom: 20px;">

  <h1>🏛️ Meri Panchayat (Public Issue Reporting Portal)</h1>
  
  <p>
    <strong>Empowering Rural India through Digital Governance</strong>
  </p>

  <p>
    <a href="#features">Features</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#admin-access">Admin Access</a>
  </p>

  [![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-2.0%2B-green.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
  [![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
  [![Status](https://img.shields.io/badge/Status-Active-success.svg?style=for-the-badge)]()

</div>

---

## 📖 Overview

**Meri Panchayat** is a next-generation m-governance platform designed to bridge the gap between citizens and their local Gram Panchayat representatives. It provides a transparent, efficient, and user-friendly interface for reporting civic issues, tracking their resolution, and staying updated with government notices.

Aligned with the **Digital India** initiative, this portal ensures accountability and fosters community participation in local development.

---

## ✨ Key Features

### 👨‍👩‍👧‍👦 For Citizens
*   **Report Issues**: Easily lodge complaints about water, electricity, roads, and sanitation with location details.
*   **Real-time Tracking**: Monitor the status of reported issues (Pending, In Progress, Resolved).
*   **Public Notices**: Access latest circulars, schemes, and announcements from the Panchayat office.
*   **User-Friendly UI**: A clean, responsive interface optimized for all devices, featuring official government branding.

### 👮‍♂️ For Administrators (Panchayat Officials)
*   **Secure Dashboard**: Role-based access for officials to manage their jurisdiction.
*   **Issue Management**: View, update, and resolve citizen grievances efficiently.
*   **Notice Board**: Publish important announcements instantly to the public portal.
*   **Analytics**: View key metrics like total active issues and resolution rates.

---

## 🛠️ Tech Stack

*   **Backend**: Python, Flask (Web Framework)
*   **Database**: SQLite (Lightweight, Relational)
*   **Frontend**: HTML5, CSS3 (Custom Government-Standard Design System)
*   **Assets**: Google Fonts (Inter, Playfair Display), Custom Generated Imagery

---

## 🚀 Getting Started

Follow these steps to set up the project locally.

### Prerequisites
*   Python 3.x installed on your system.

### Installation

1.  **Clone the Repository** (if applicable) or navigate to the project directory:
    ```bash
    cd public-issue-reporting-portal
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize Database**:
    *   The application automatically initializes `panchayath.db` on the first run.

### Running the App

1.  **Start the Server**:
    ```bash
    python app.py
    ```

2.  **Access the Portal**:
    *   Open your browser and visit: `http://127.0.0.1:5000`

---

## 🔐 Admin Access

To access the official dashboard for testing purposes:

*   **URL**: `/admin/login` (or click "Official Login" in the nav)
*   **Username**: `admin`
*   **Password**: `admin123`

---

## 📂 Project Structure

```
public-issue-reporting-portal/
├── app.py                # Main application entry point
├── panchyath.db          # SQLite Database (auto-generated)
├── requirements.txt      # Project dependencies
├── static/
│   ├── css/              # Custom styling (style.css)
│   └── image/            # Assets (Logos, Banners)
└── templates/
    ├── base.html         # Base layout with Header/Footer
    ├── citizen/          # Public facing pages (Home, Report, Track)
    └── admin/            # Protected admin pages (Dashboard, Login)
```

---

<div align="center">
  <p>Designed & Developed with ❤️ for a specialized Government Use Case.</p>
</div>