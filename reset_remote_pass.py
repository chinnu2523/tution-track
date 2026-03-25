import sqlite3
import hashlib
import secrets

# Logic matches app.py
PBKDF2_ITERS = 260_000
# Remote path for PythonAnywhere
DB_PATH = '/home/chinnu2523/tution-track/tuition.db'

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERS)
    return f"{salt}${dk.hex()}"

SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    username       TEXT     PRIMARY KEY,
    password_hash  TEXT     NOT NULL,
    role           TEXT     NOT NULL DEFAULT 'admin'
);
"""

def update_admin(username, password):
    try:
        db = sqlite3.connect(DB_PATH)
        db.executescript(SCHEMA) # Ensure table exists
        pwd_hash = hash_password(password)
        
        row = db.execute("SELECT 1 FROM admins WHERE username=?", (username,)).fetchone()
        if row:
            db.execute("UPDATE admins SET password_hash = ? WHERE username = ?", (pwd_hash, username))
            print(f"Successfully UPDATED password for user '{username}'.")
        else:
            db.execute("INSERT INTO admins (username, password_hash, role) VALUES (?, ?, ?)", (username, pwd_hash, "admin"))
            print(f"Successfully CREATED user '{username}' with new password.")
        
        db.commit()
        db.close()
    except Exception as e:
        print(f"INTERNAL ERROR: {e}")

if __name__ == "__main__":
    update_admin("magi", "magi@1982")
