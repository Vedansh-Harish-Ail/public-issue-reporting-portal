import sqlite3
import os

DB_PATH = 'database/panchayath.db'

if not os.path.exists(DB_PATH):
    print(f"Database file {DB_PATH} not found.")
else:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", [t['name'] for t in tables])
    
    for table in [t['name'] for t in tables]:
        print(f"\nSchema for {table}:")
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col['name']} ({col['type']})")
            
    conn.close()
