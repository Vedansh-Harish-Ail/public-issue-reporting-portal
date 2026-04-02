import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

def migrate():
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not db_url:
        print("Error: DATABASE_URL or POSTGRES_URL not found in environment variables.")
        return

    print("Connecting to Vercel Postgres/Supabase...")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Read schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if not os.path.exists(schema_path):
            print(f"Error: {schema_path} not found.")
            return

        with open(schema_path, "r") as f:
            sql_script = f.read()

        def add_column_if_missing(table, column, type_def):
            cur.execute(f"""
                SELECT count(*) FROM information_schema.columns 
                WHERE table_name='{table}' AND column_name='{column}';
            """)
            if cur.fetchone()[0] == 0:
                print(f"Adding column {column} to {table}...")
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def};")

        # 1. Ensure new tables exist
        print("Ensuring all tables exist...")
        # (Running the updated schema.sql with "IF NOT EXISTS" handles this safely)
        statements = sql_script.split(";")
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                cur.execute(stmt)

        # 2. Add missing columns to existing tables
        print("Checking for missing columns in existing tables...")
        add_column_if_missing("issues", "tracking_id", "TEXT UNIQUE")
        add_column_if_missing("issues", "rejection_reason", "TEXT")
        add_column_if_missing("issues", "reporter_name", "TEXT")
        add_column_if_missing("notices", "banner_path", "TEXT")
        add_column_if_missing("notices", "expiry_date", "TIMESTAMP")
        
        conn.commit()
        
        # Seed default data
        print("Seeding default data...")
        from werkzeug.security import generate_password_hash
        
        # Add Demo Panchayath
        cur.execute("SELECT COUNT(*) FROM panchayath")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO panchayath (name, district, state)
                VALUES ('Demo Panchayath', 'Demo District', 'Demo State')
            """)
            
            # Add Admin
            cur.execute("""
                INSERT INTO admin (username, password_hash, panchayath_id)
                VALUES (%s, %s, %s)
            """, ("admin", generate_password_hash("admin123"), 1))
            
        conn.commit()
        print("Migration and Seeding successful!")
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
