import sqlite3
import psycopg2
import os

pg_url = "postgresql://neondb_owner:npg_wQMgbOChFl96@ep-bold-recipe-a1jbvds6-pooler.ap-southeast-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

def migrate():
    print("Connecting to SQLite...")
    sqlite_conn = sqlite3.connect('database/panchayath.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    print("Connecting to Postgres...")
    pg_conn = psycopg2.connect(pg_url)
    pg_cur = pg_conn.cursor()

    tables = ['panchayath', 'admin', 'users', 'notices', 'activities', 'issues']

    print("Clearing target tables...")
    for t in reversed(tables):
        pg_cur.execute(f"TRUNCATE TABLE {t} CASCADE;")
        
    for t in tables:
        sqlite_cur.execute(f"SELECT * FROM {t}")
        rows = sqlite_cur.fetchall()
        if not rows:
            print(f"Skipping {t}, no data.")
            continue
            
        print(f"Migrating {len(rows)} rows to {t}...")
        cols = rows[0].keys()
        col_str = ", ".join(cols)
        val_str = ", ".join(["%s"] * len(cols))
        
        insert_query = f"INSERT INTO {t} ({col_str}) VALUES ({val_str})"
        
        for r in rows:
            pg_cur.execute(insert_query, tuple(r))
            
        # Reset sequence
        try:
            pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE((SELECT MAX(id) FROM {t}), 0) + 1, false);")
        except Exception as e:
            pg_conn.rollback()
            print(f"Sequence reset failed for {t}: {e}")
            
    pg_conn.commit()
    print("Data Migration Complete!")

migrate()
