import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(r"c:\panchayath_project\Final_public-issue-reporting-portal 2\public-issue-reporting-portal", "database")
DB_NAME = os.path.join(DB_DIR, "panchayath.db")

def check_db():
    if not os.path.exists(DB_NAME):
        print(f"Database not found at {DB_NAME}")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if activities table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities';")
    table = cursor.fetchone()
    if table:
        print("PASS: activities table exists.")
        
        # Check columns
        cursor.execute("PRAGMA table_info(activities);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_columns = ['id', 'panchayath_id', 'title', 'description', 'image_path', 'created_at']
        for col in expected_columns:
            if col in columns:
                print(f"PASS: Column '{col}' exists in activities table.")
            else:
                print(f"FAIL: Column '{col}' missing from activities table.")
    else:
        print("FAIL: activities table missing.")
        
    conn.close()

if __name__ == "__main__":
    check_db()
