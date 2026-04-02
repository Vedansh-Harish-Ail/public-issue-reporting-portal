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

        # TRANSFORM SQLITE TO POSTGRES
        print("Transforming SQLite schema to Postgres...")
        # 1. PRIMARY KEY AUTOINCREMENT -> SERIAL PRIMARY KEY
        sql_script = sql_script.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        # 2. DATETIME -> TIMESTAMP
        sql_script = sql_script.replace("DATETIME", "TIMESTAMP")
        # 3. Handle multiple statements (split by semicolon)
        statements = sql_script.split(";")

        print("Executing schema...")
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    cur.execute(stmt)
                except Exception as e:
                    # Ignore "Already exists" errors for safe re-runs
                    if "already exists" not in str(e).lower():
                        raise e
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
