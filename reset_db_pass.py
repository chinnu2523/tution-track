import sqlite3
import hashlib
import secrets
import os

db_paths = [
    '/Users/madarauchiha/Downloads/Project VMS_EduTech/vms_edutech.db',
    '/Users/madarauchiha/Downloads/Project VMS_EduTech/vms_edutech.sqlite',
    '/Users/madarauchiha/Project VMS_EduTech/vms_edutech.db',
    '/Users/madarauchiha/Project VMS_EduTech/vms_edutech.sqlite'
]

for p in db_paths:
    if os.path.exists(p):
        print("Found DB:", p)
        try:
            db = sqlite3.connect(p)
            salt = secrets.token_hex(16)
            dk = hashlib.pbkdf2_hmac('sha256', b'magi@1982', salt.encode(), 260000)
            pwd = f"{salt}${dk.hex()}"
            db.execute("UPDATE admins SET password_hash=? WHERE username='magi'", (pwd,))
            db.commit()
            print("Successfully reset to 'magi@1982' for user 'magi' in", p)
        except Exception as e:
            print("Error resetting in", p, e)
