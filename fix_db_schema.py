import sqlite3
import os

db_paths = [
    '/Users/madarauchiha/Downloads/Project VMS_EduTech/vms_edutech.db',
    '/Users/madarauchiha/Project VMS_EduTech/vms_edutech.db'
]

for p in db_paths:
    if os.path.exists(p):
        print("Fixing schema in DB:", p)
        try:
            db = sqlite3.connect(p)
            db.execute("DROP TABLE IF EXISTS sessions")
            db.execute('''CREATE TABLE IF NOT EXISTS sessions (
                token       TEXT     PRIMARY KEY,
                role        TEXT     NOT NULL,
                user_id     TEXT     NOT NULL,
                expires_at  TEXT     NOT NULL
            )''')
            db.commit()
            print("Successfully fixed sessions table in", p)
        except Exception as e:
            print("Error fixing in", p, e)
