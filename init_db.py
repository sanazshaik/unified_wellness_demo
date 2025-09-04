import sqlite3
import os

# Always point to root users.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Expanded schema with profile info
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        age INTEGER,
        height_in REAL,
        weight_lb REAL,
        devices TEXT
    )
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH} with extended schema")

if __name__ == "__main__":
    init_db()
