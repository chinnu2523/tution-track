import sqlite3
import hashlib
import secrets

db_path = 'tuition.db'
username = 'magi'
new_pass = 'admin123'

salt = secrets.token_hex(16)
dk = hashlib.pbkdf2_hmac('sha256', new_pass.encode(), salt.encode(), 260000)
pwd_hash = f"{salt}${dk.hex()}"

db = sqlite3.connect(db_path)
db.execute("UPDATE admins SET password_hash=? WHERE username=?", (pwd_hash, username))
db.commit()
db.close()
print(f"Password for {username} reset to {new_pass}")
