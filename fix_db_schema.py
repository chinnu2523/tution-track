import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tuition.db")

def fix_schema():
    if not os.path.exists(DB_PATH):
        print("Database not found. app.py will create it on first run.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Add expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT     NOT NULL,
                amount      INTEGER  NOT NULL,
                category    TEXT,
                date        TEXT     NOT NULL,
                mode        TEXT     NOT NULL,
                remarks     TEXT
            )
        ''')
        print("Ensured 'expenses' table exists.")

        # Check if 'attendance' table exists (it should, but just in case)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  TEXT     NOT NULL,
                date        TEXT     NOT NULL,
                status      TEXT     NOT NULL,
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        ''')
        print("Ensured 'attendance' table exists.")

        conn.commit()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()
