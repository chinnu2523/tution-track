import os
import sqlite3
import hashlib
import secrets

# Logic from app.py
PBKDF2_ITERS = 260_000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tuition.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    username       TEXT     PRIMARY KEY,
    password_hash  TEXT     NOT NULL,
    role           TEXT     NOT NULL DEFAULT 'admin'
);
"""

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERS)
    return f"{salt}${dk.hex()}"

def update_admin(username, password):
    # Initialize DB if needed
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    
    # Hash password
    pwd_hash = hash_password(password)
    
    # Check if admin exists
    row = db.execute("SELECT 1 FROM admins WHERE username=?", (username,)).fetchone()
    if row:
        db.execute("UPDATE admins SET password_hash = ? WHERE username = ?", (pwd_hash, username))
        print(f"Updated existing admin: {username}")
    else:
        db.execute("INSERT INTO admins (username, password_hash, role) VALUES (?, ?, ?)", (username, pwd_hash, "admin"))
        print(f"Created new admin: {username}")
    
    db.commit()
    db.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    update_admin("magi", "magi@1982")
