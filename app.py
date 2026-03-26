import os
import re
import json
import hmac
import hashlib
import secrets
import sqlite3
import base64
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

DATABASE_URL = os.environ.get("DATABASE_URL") # Provided by Render.com
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tuition.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

PBKDF2_ITERS = 260_000
SESSION_DAYS = 7

SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    username       TEXT     PRIMARY KEY,
    password_hash  TEXT     NOT NULL,
    role           TEXT     NOT NULL DEFAULT 'admin'
);

CREATE TABLE IF NOT EXISTS fee_structure (
    class_name     TEXT     PRIMARY KEY,
    monthly_fee    INTEGER  NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id             TEXT     PRIMARY KEY,
    name           TEXT     NOT NULL,
    school         TEXT     NOT NULL,
    class_name     TEXT     NOT NULL,
    phone          TEXT     NOT NULL,
    is_whatsapp    BOOLEAN  NOT NULL DEFAULT '0',
    photo_path     TEXT,
    joining_fee    INTEGER  NOT NULL DEFAULT 0,
    joining_fee_status  TEXT NOT NULL DEFAULT 'unpaid',
    joining_fee_date    TEXT,
    joining_fee_mode    TEXT,
    monthly_fee    INTEGER  NOT NULL DEFAULT 0,
    months         TEXT     NOT NULL DEFAULT '{}',
    assigned_tracks TEXT    NOT NULL DEFAULT '[]',
    created_at     TEXT     NOT NULL,
    updated_at     TEXT     NOT NULL
);

CREATE TABLE IF NOT EXISTS tracks (
    id             TEXT     PRIMARY KEY,
    title          TEXT     NOT NULL,
    level          TEXT     NOT NULL,
    skills         TEXT     NOT NULL
);

CREATE TABLE IF NOT EXISTS progress (
    student_id     TEXT     NOT NULL,
    track_id       TEXT     NOT NULL,
    skill          TEXT     NOT NULL,
    done_at        TEXT     NOT NULL,
    PRIMARY KEY(student_id, track_id, skill),
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY(track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS batches (
    id             TEXT     PRIMARY KEY,
    name           TEXT     NOT NULL,
    time           TEXT     NOT NULL,
    days           TEXT     NOT NULL,
    subject        TEXT     NOT NULL,
    teacher        TEXT     NOT NULL,
    room           TEXT
);

CREATE TABLE IF NOT EXISTS batch_students (
    batch_id       TEXT     NOT NULL,
    student_id     TEXT     NOT NULL,
    PRIMARY KEY(batch_id, student_id),
    FOREIGN KEY(batch_id) REFERENCES batches(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exams (
    id             SERIAL PRIMARY KEY,
    title          TEXT     NOT NULL,
    max_marks      INTEGER  NOT NULL,
    date           TEXT     NOT NULL,
    class_name     TEXT
);

CREATE TABLE IF NOT EXISTS marks (
    exam_id        INTEGER  NOT NULL,
    student_id     TEXT     NOT NULL,
    marks_obtained INTEGER  NOT NULL,
    PRIMARY KEY(exam_id, student_id),
    FOREIGN KEY(exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS enquiries (
    id             SERIAL PRIMARY KEY,
    name           TEXT     NOT NULL,
    phone          TEXT     NOT NULL,
    grade          TEXT,
    school         TEXT,
    status         TEXT     NOT NULL DEFAULT 'New',
    notes          TEXT,
    created_at     TEXT     NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token       TEXT     PRIMARY KEY,
    role        TEXT     NOT NULL,
    user_id     TEXT     NOT NULL,
    expires_at  TEXT     NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL PRIMARY KEY,
    timestamp   TEXT     NOT NULL,
    admin_id    TEXT     NOT NULL,
    action      TEXT     NOT NULL,
    details     TEXT     NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    id          SERIAL PRIMARY KEY,
    student_id  TEXT     NOT NULL,
    date        TEXT     NOT NULL,
    status      TEXT     NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id          SERIAL PRIMARY KEY,
    student_id  TEXT     NOT NULL,
    month       TEXT     NOT NULL,
    amount      INTEGER  NOT NULL,
    mode        TEXT     NOT NULL,
    remarks     TEXT,
    paid_at     TEXT     NOT NULL,
    receipt_id  TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expenses (
    id          SERIAL PRIMARY KEY,
    title       TEXT     NOT NULL,
    amount      INTEGER  NOT NULL,
    category    TEXT,
    date        TEXT     NOT NULL,
    mode        TEXT     NOT NULL,
    remarks     TEXT
);
"""
# Note: In SQLite, SERIAL and SERIAL PRIMARY KEY are not keywords, we need a slight adjustment.
if not DATABASE_URL:
    SCHEMA = SCHEMA.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")

def get_db():
    if "db" not in g:
        if DATABASE_URL:
            g.db = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def db_exec(query, params=()):
    db = get_db()
    if DATABASE_URL:
        query = query.replace("?", "%s")
        cur = db.cursor()
        cur.execute(query, params)
        return cur
    else:
        return db.execute(query, params)

def db_upsert(table, pk_col, data):
    """Helper for INSERT OR REPLACE (SQLite) vs ON CONFLICT (Postgres)"""
    keys = list(data.keys())
    values = list(data.values())
    
    if DATABASE_URL:
        # Postgres ON CONFLICT
        cols = ", ".join(keys)
        placeholders = ", ".join(["%s"] * len(keys))
        updates = ", ".join([f"{k} = EXCLUDED.{k}" for k in keys if k != pk_col])
        query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) ON CONFLICT ({pk_col}) DO UPDATE SET {updates}"
        db_exec(query, tuple(values))
    else:
        # SQLite INSERT OR REPLACE
        cols = ", ".join(keys)
        placeholders = ", ".join(["?"] * len(keys))
        query = f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
        db_exec(query, tuple(values))

def db_commit():
    if "db" in g:
        g.db.commit()

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db:
        db.close()

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERS)
    return f"{salt}${dk.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hash_hex = stored_hash.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERS)
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False

def init_db():
    with app.app_context():
        db = get_db()
        if DATABASE_URL:
            cur = db.cursor()
            cur.execute(SCHEMA)
            db.commit()
            cur.execute("SELECT 1 FROM admins WHERE username='magi'")
            if not cur.fetchone():
                cur.execute("INSERT INTO admins (username, password_hash, role) VALUES (%s,%s,%s)", 
                           ("magi", hash_password("magi@1982"), "admin"))
                db.commit()
        else:
            db.executescript(SCHEMA)
            row = db.execute("SELECT 1 FROM admins WHERE username='magi'").fetchone()
            if not row:
                db.execute("INSERT INTO admins (username, password_hash, role) VALUES (?,?,?)", 
                           ("magi", hash_password("magi@1982"), "admin"))
            db.commit()

def log_action(admin_id, action, details):
    db_exec(
        "INSERT INTO audit_logs (timestamp, admin_id, action, details) VALUES (?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), admin_id, action, details)
    )
    db_commit()

def create_session(role: str, user_id: str) -> str:
    token = secrets.token_urlsafe(48)
    expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat()
    db = get_db()
    db_exec(
        "INSERT INTO sessions (token, role, user_id, expires_at) VALUES (?,?,?,?)",
        (token, role, user_id, expires)
    )
    db_commit()
    return token

def resolve_token():
    cookie = request.cookies.get("tt_session")
    if cookie: return cookie
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "): return auth[7:]
    return None

def get_current_user():
    token = resolve_token()
    if not token: return None
    db = get_db()
    # Use ISO string comparison for expiry (works in both SQLite and Postgres)
    now_iso = datetime.now(timezone.utc).isoformat()
    row = db_exec("SELECT role, user_id FROM sessions WHERE token=? AND expires_at > ?", (token, now_iso)).fetchone()
    if row: return dict(row)
    return None

def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user["role"] != "admin":
            return jsonify({"ok": False, "error": "Admin access required."}), 401
        g.admin = user["user_id"]
        return fn(*args, **kwargs)
    return wrapper

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"ok": False, "error": "Auth required."}), 401
        g.user = user
        return fn(*args, **kwargs)
    return wrapper

# API ROUTES

@app.route("/api/admin/change_pwd", methods=["POST"])
@require_admin
def change_pwd():
    data = request.get_json(silent=True) or {}
    cur = data.get("current")
    new_p = data.get("new")
    db = get_db()
    row = db_exec("SELECT password_hash FROM admins WHERE username=?", (g.admin,)).fetchone()
    if row and verify_password(cur, row["password_hash"]):
        db_exec("UPDATE admins SET password_hash=? WHERE username=?", (hash_password(new_p), g.admin))
        db_commit()
        log_action(g.admin, "PWD_CHANGE", "Password changed")
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Invalid current password"}), 400
# Helper for student data alignment
def format_student(row):
    d = dict(row)
    if "class_name" in d: d["class"] = d.pop("class_name")
    if "monthly_fee" in d: d["monthlyFee"] = d.pop("monthly_fee")
    if "joining_fee" in d: d["joiningFee"] = d.pop("joining_fee")
    if "months" in d: d["months"] = json.loads(d["months"]) if d["months"] else {}
    if "assigned_tracks" in d: d["assigned_tracks"] = json.loads(d["assigned_tracks"]) if d["assigned_tracks"] else []
    return d

@app.route("/api/login/admin", methods=["POST"])
def login_admin():
    data = request.get_json(silent=True) or {}
    un = data.get("username", "")
    pw = data.get("password", "")
    db = get_db()
    row = db_exec("SELECT password_hash, role FROM admins WHERE username=?", (un,)).fetchone()
    if row and verify_password(pw, row["password_hash"]):
        token = create_session(row["role"], un)
        resp = jsonify({"ok": True, "token": token, "user": un, "role": row["role"]})
        resp.set_cookie("tt_session", token, httponly=True, samesite="Lax", max_age=SESSION_DAYS*86400, path="/")
        log_action(un, "LOGIN", f"{row['role'].capitalize()} logged in")
        return resp
    return jsonify({"ok": False, "error": "Invalid admin credentials."}), 401

@app.route("/api/login/student", methods=["POST"])
def login_student():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip().lower()
    phone = re.sub(r"\D", "", data.get("phone", ""))
    
    db = get_db()
    # Optimized SQL query instead of Python loop
    if DATABASE_URL:
        # Postgres ilike or LOWER
        row = db_exec("SELECT * FROM students WHERE LOWER(name) = %s AND REPLACE(phone, ' ', '') = %s", (name, phone)).fetchone()
    else:
        # SQLite LOWER and custom sanitization logic is harder in SQL, 
        # but we can do a basic match and verify in Python for robustness.
        row = db_exec("SELECT * FROM students WHERE LOWER(name) = ? AND phone LIKE ?", (name, f"%{phone}%")).fetchone()
    
    if row:
        s_data = format_student(row)
        # Final sanity check for phone (handles varying formats in DB)
        if re.sub(r"\D", "", s_data["phone"]) == phone:
            token = create_session("student", row["id"])
            resp = jsonify({"ok": True, "token": token, "student": s_data, "role": "student"})
            resp.set_cookie("tt_session", token, httponly=True, samesite="Lax", max_age=SESSION_DAYS*86400, path="/")
            return resp
            
    return jsonify({"ok": False, "error": "Student not found."}), 401

@app.route("/api/student/me", methods=["GET"])
@require_auth
def get_student_me():
    if g.user["role"] != "student": return jsonify({"ok": False}), 403
    db = get_db()
    row = db_exec("SELECT * FROM students WHERE id=?", (g.user["user_id"],)).fetchone()
    if not row: return jsonify({"ok": False}), 404
    s = format_student(row)
    
    # Total Paid
    total_paid = db_exec("SELECT SUM(amount) FROM payments WHERE student_id=?", (g.user["user_id"],)).fetchone()[0] or 0
    s["totalPaid"] = total_paid
    
    return jsonify({"ok": True, "student": s})

@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    user = get_current_user()
    if user: return jsonify({"ok": True, "user": user})
    return jsonify({"ok": False}), 401

@app.route("/api/logout", methods=["POST"])
def api_logout():
    token = resolve_token()
    if token:
        db = get_db()
        user = get_current_user()
        if user and user["role"] in ["admin", "staff"]:
            log_action(user["user_id"], "LOGOUT", "User logged out")
        db_exec("DELETE FROM sessions WHERE token=?", (token,))
        db_commit()
    resp = jsonify({"ok": True})
    resp.delete_cookie("tt_session", path="/")
    return resp

# Fee Structure
@app.route("/api/settings/fee-structure", methods=["GET"])
@require_auth
def get_fee_structure():
    rows = db_exec("SELECT * FROM fee_structure").fetchall()
    return jsonify({"ok": True, "fee_structure": [dict(r) for r in rows]})

@app.route("/api/settings/fee-structure", methods=["POST"])
@require_admin
def update_fee_structure():
    data = request.get_json(silent=True) or {}
    class_name = data.get("class_name")
    fee = data.get("monthly_fee")
    db_upsert("fee_structure", "class_name", {"class_name": class_name, "monthly_fee": fee})
    db_commit()
    log_action(g.admin, "FEE_STRUCTURE_UPDATE", f"Set {class_name} fee to {fee}")
    return jsonify({"ok": True})

# Students
@app.route("/api/students", methods=["GET"])
@require_auth
def get_students():
    rows = db_exec("SELECT * FROM students").fetchall()
    return jsonify({"ok": True, "students": [format_student(r) for r in rows]})

@app.route("/api/students", methods=["POST"])
@require_auth
def create_student():
    data = request.get_json(silent=True) or {}
    sid = "st_" + str(int(datetime.now().timestamp() * 1000)) + "_" + secrets.token_hex(2)
    
    db = get_db()
    db_exec('''INSERT INTO students 
        (id, name, school, class_name, phone, is_whatsapp, photo_path, joining_fee, joining_fee_status, joining_fee_date, joining_fee_mode, monthly_fee, months, assigned_tracks, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (sid, data.get("name"), data.get("school", ""), data.get("class", ""), data.get("phone", ""),
         data.get("is_whatsapp", 0), data.get("photo_path"), data.get("joiningFee", 0), 
         data.get("joining_fee_status", "unpaid"), data.get("joining_fee_date"), data.get("joining_fee_mode"),
         data.get("monthlyFee", 0), json.dumps(data.get("months", {})), json.dumps(data.get("assigned_tracks", [])),
         datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat())
    )
    db_commit()
    
    # If joining fee is paid, record it in payments table
    if data.get("joining_fee_status") == 'paid' and data.get("joiningFee", 0) > 0:
        receipt_id = "RCT-J-" + secrets.token_hex(4).upper()
        db_exec("INSERT INTO payments (student_id, month, amount, mode, remarks, paid_at, receipt_id) VALUES (?,?,?,?,?,?,?)",
               (sid, "Joining Fee", data.get("joiningFee"), data.get("joining_fee_mode", "Cash"), "Initial Joining Fee", datetime.now(timezone.utc).isoformat(), receipt_id))
        db_commit()
        
    log_action(g.user["user_id"], "STUDENT_ADDED", f"Added student: {data.get('name')} ({sid})")
    return jsonify({"ok": True, "id": sid})

@app.route("/api/students/<sid>", methods=["PUT"])
@require_auth
def update_student(sid):
    data = request.get_json(silent=True) or {}
    db = get_db()
    db_exec('''UPDATE students 
        SET name=?, school=?, class_name=?, phone=?, is_whatsapp=?, photo_path=?, joining_fee=?, joining_fee_status=?, joining_fee_date=?, joining_fee_mode=?, monthly_fee=?, months=?, assigned_tracks=?, updated_at=?
        WHERE id=?''',
        (data.get("name"), data.get("school",""), data.get("class",""), data.get("phone",""), 
         data.get("is_whatsapp", 0), data.get("photo_path"), 
         data.get("joiningFee", 0), data.get("joining_fee_status", "unpaid"), 
         data.get("joining_fee_date"), data.get("joining_fee_mode"),
         data.get("monthlyFee", 0), json.dumps(data.get("months", {})), json.dumps(data.get("assigned_tracks", [])),
         datetime.now(timezone.utc).isoformat(), sid)
    )
    db_commit()
    log_action(g.user["user_id"], "STUDENT_UPDATED", f"Updated student profile: {data.get('name')} ({sid})")
    return jsonify({"ok": True})

@app.route("/api/students/<sid>", methods=["DELETE"])
@require_admin
def delete_student(sid):
    db = get_db()
    db_exec("DELETE FROM students WHERE id=?", (sid,))
    db_commit()
    log_action(g.admin, "STUDENT_DELETED", f"Deleted student: {sid}")
    return jsonify({"ok": True})

# Payments Expansion
@app.route("/api/students/<sid>/pay", methods=["POST"])
@require_auth
def pay_fee(sid):
    data = request.get_json(silent=True) or {}
    month = data.get("month")
    amount = data.get("amount")
    mode = data.get("mode", "Cash")
    remarks = data.get("remarks", "")
    
    db = get_db()
    receipt_id = "RCT-" + secrets.token_hex(4).upper()
    db_exec("INSERT INTO payments (student_id, month, amount, mode, remarks, paid_at, receipt_id) VALUES (?,?,?,?,?,?,?)",
               (sid, month, amount, mode, remarks, datetime.now(timezone.utc).isoformat(), receipt_id))
    
    # Update student months
    st = db_exec("SELECT months FROM students WHERE id=?", (sid,)).fetchone()
    months = json.loads(st["months"]) if st else {}
    months[month] = True
    db_exec("UPDATE students SET months=? WHERE id=?", (json.dumps(months), sid))
    db_commit()
    log_action(g.user["user_id"], "FEE_PAID", f"Payment for {month} received for student {sid}")
    return jsonify({"ok": True, "receipt_id": receipt_id})

@app.route("/api/students/<sid>/details", methods=["GET"])
@require_auth
def get_student_details(sid):
    db = get_db()
    st = db_exec("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    if not st: return jsonify({"ok": False, "error": "Not found"}), 404
    
    s = format_student(st)
    
    att = db_exec("SELECT date, status FROM attendance WHERE student_id=? ORDER BY date DESC LIMIT 30", (sid,)).fetchall()
    pay = db_exec("SELECT * FROM payments WHERE student_id=? ORDER BY paid_at DESC", (sid,)).fetchall()
    
    # Progress for student
    prog = db_exec("SELECT track_id, skill FROM progress WHERE student_id=?", (sid,)).fetchall()
    # Exams and Marks for student
    exams_marks = db_exec("SELECT e.title, e.max_marks, e.date, m.marks_obtained FROM exams e JOIN marks m ON e.id = m.exam_id WHERE m.student_id=?", (sid,)).fetchall()
    
    return jsonify({
        "ok": True,
        "student": s,
        "attendance": [dict(a) for a in att],
        "payments": [dict(p) for p in pay],
        "progress": [dict(pr) for pr in prog],
        "exam_results": [dict(em) for em in exams_marks]
    })

# LMS Portal Endpoints
@app.route("/api/lms/tracks", methods=["GET"])
@require_auth
def get_tracks():
    rows = db_exec("SELECT * FROM tracks").fetchall()
    res = []
    for r in rows:
        d = dict(r)
        d["skills"] = json.loads(d["skills"])
        res.append(d)
    return jsonify({"ok": True, "tracks": res})

@app.route("/api/lms/tracks", methods=["POST"])
@require_admin
def create_track():
    data = request.get_json()
    tid = data.get("id") or "tr_" + secrets.token_hex(4)
    db_upsert("tracks", "id", {"id": tid, "title": data["title"], "level": data["level"], "skills": json.dumps(data["skills"])})
    db_commit()
    return jsonify({"ok": True, "id": tid})

@app.route("/api/lms/progress/toggle", methods=["POST"])
@require_auth
def toggle_progress():
    data = request.get_json()
    sid = g.user["user_id"] if g.user["role"] == "student" else data.get("student_id")
    tid = data["track_id"]
    skill = data["skill"]
    
    db = get_db()
    row = db_exec("SELECT 1 FROM progress WHERE student_id=? AND track_id=? AND skill=?", (sid, tid, skill)).fetchone()
    if row:
        db_exec("DELETE FROM progress WHERE student_id=? AND track_id=? AND skill=?", (sid, tid, skill))
        action = "REMOVED"
    else:
        db_exec("INSERT INTO progress (student_id, track_id, skill, done_at) VALUES (?,?,?,?)",
                   (sid, tid, skill, datetime.now(timezone.utc).isoformat()))
        action = "COMPLETED"
    
    db_commit()
    return jsonify({"ok": True, "status": action})

# Batches & Scheduling
@app.route("/api/batches", methods=["GET"])
@require_auth
def get_batches():
    rows = db_exec("SELECT * FROM batches").fetchall()
    return jsonify({"ok": True, "batches": [dict(r) for r in rows]})

@app.route("/api/batches", methods=["POST"])
@require_admin
def create_batch():
    data = request.get_json()
    bid = data.get("id") or "bt_" + secrets.token_hex(4)
    db_upsert("batches", "id", {
        "id": bid, "name": data["name"], "time": data["time"], 
        "days": data["days"], "subject": data["subject"], 
        "teacher": data["teacher"], "room": data.get("room")
    })
    db_commit()
    return jsonify({"ok": True, "id": bid})

@app.route("/api/batches/<bid>/assign", methods=["POST"])
@require_admin
def assign_batch_students(bid):
    data = request.get_json()
    student_ids = data.get("student_ids", [])
    db = get_db()
    db_exec("DELETE FROM batch_students WHERE batch_id=?", (bid,))
    for sid in student_ids:
        db_exec("INSERT INTO batch_students (batch_id, student_id) VALUES (?,?)", (bid, sid))
    db_commit()
    return jsonify({"ok": True})

@app.route("/api/students/<sid>/batches", methods=["GET"])
@require_auth
def get_student_batches(sid):
    db = get_db()
    rows = db_exec("SELECT b.* FROM batches b JOIN batch_students bs ON b.id = bs.batch_id WHERE bs.student_id=?", (sid,)).fetchall()
    return jsonify({"ok": True, "batches": [dict(r) for r in rows]})

# Exams & Marks
@app.route("/api/exams", methods=["GET"])
@require_auth
def get_exams():
    rows = db_exec("SELECT * FROM exams ORDER BY date DESC").fetchall()
    return jsonify({"ok": True, "exams": [dict(r) for r in rows]})

@app.route("/api/exams", methods=["POST"])
@require_admin
def create_exam():
    data = request.get_json()
    db = get_db()
    db_exec("INSERT INTO exams (title, max_marks, date, class_name) VALUES (?,?,?,?)",
               (data["title"], data["max_marks"], data["date"], data.get("class_name")))
    db_commit()
    return jsonify({"ok": True})

@app.route("/api/exams/<eid>/marks", methods=["GET"])
@require_auth
def get_exam_marks(eid):
    db = get_db()
    rows = db_exec("SELECT m.*, s.name FROM marks m JOIN students s ON m.student_id = s.id WHERE m.exam_id=?", (eid,)).fetchall()
    return jsonify({"ok": True, "marks": [dict(r) for r in rows]})

@app.route("/api/exams/<eid>/marks", methods=["POST"])
@require_admin
def update_marks(eid):
    data = request.get_json()
    marks_list = data.get("marks", []) # list of {student_id, marks_obtained}
    for m in marks_list:
        db_upsert("marks", "exam_id, student_id", {
            "exam_id": eid, "student_id": m["student_id"], "marks_obtained": m["marks_obtained"]
        })
    db_commit()
    return jsonify({"ok": True})

# Enquiries
@app.route("/api/enquiries", methods=["GET"])
@require_admin
def get_enquiries():
    rows = db_exec("SELECT * FROM enquiries ORDER BY created_at DESC").fetchall()
    return jsonify({"ok": True, "enquiries": [dict(r) for r in rows]})

@app.route("/api/enquiries", methods=["POST"])
@require_admin
def create_enquiry():
    data = request.get_json()
    db = get_db()
    db_exec("INSERT INTO enquiries (name, phone, grade, school, notes, created_at) VALUES (?,?,?,?,?,?)",
               (data["name"], data["phone"], data.get("grade"), data.get("school"), data.get("notes"), datetime.now(timezone.utc).isoformat()))
    db_commit()
    return jsonify({"ok": True})

@app.route("/api/enquiries/<eid>/status", methods=["PUT"])
@require_admin
def update_enquiry_status(eid):
    data = request.get_json()
    db = get_db()
    db_exec("UPDATE enquiries SET status=? WHERE id=?", (data["status"], eid))
    db_commit()
    return jsonify({"ok": True})

# Dashboard Stats
@app.route("/api/dashboard/stats", methods=["GET"])
@require_auth
def dashboard_stats():
    db = get_db()
    total_students = db_exec("SELECT COUNT(*) FROM students").fetchone()[0]
    
    now = datetime.now(timezone.utc)
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    monthly_collection = db_exec("SELECT SUM(amount) FROM payments WHERE paid_at >= ?", (this_month_start,)).fetchone()[0] or 0
    
    pending_fee_students = 0
    overdue_list = []
    # Simplified overdue: Check current month in 'months' JSON
    curr_m = now.strftime("%b")
    rows = db_exec("SELECT id, name, months, phone, monthly_fee FROM students").fetchall()
    for r in rows:
        ms = json.loads(r["months"])
        if not ms.get(curr_m):
            pending_fee_students += 1
            overdue_list.append({"id": r["id"], "name": r["name"], "phone": r["phone"], "amount": r["monthly_fee"]})
            
    recent_payments = db_exec("SELECT p.*, s.name FROM payments p JOIN students s ON p.student_id = s.id ORDER BY p.paid_at DESC LIMIT 5").fetchall()
    
    # Expense stats
    this_month_expenses = db_exec("SELECT SUM(amount) FROM expenses WHERE date >= ?", (this_month_start[:10],)).fetchone()[0] or 0
    
    return jsonify({
        "ok": True,
        "total_students": total_students,
        "monthly_collection": monthly_collection,
        "monthly_expenses": this_month_expenses,
        "net_profit": monthly_collection - this_month_expenses,
        "pending_fee_students": pending_fee_students,
        "overdue_list": overdue_list[:10],
        "recent_payments": [dict(rp) for rp in recent_payments]
    })

# Photo Upload
@app.route("/api/upload-photo", methods=["POST"])
@require_auth
def upload_photo():
    if 'photo' not in request.files: return jsonify({"ok": False, "error": "No file"}), 400
    file = request.files['photo']
    if file.filename == '': return jsonify({"ok": False, "error": "No selection"}), 400
    
    filename = secure_filename(secrets.token_hex(8) + "_" + file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    return jsonify({"ok": True, "photo_path": "/uploads/" + filename})

@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Attendance
@app.route("/api/attendance", methods=["GET"])
@require_auth
def get_attendance():
    date = request.args.get("date")
    if not date: return jsonify({"ok": False, "error": "Date required"}), 400
    db = get_db()
    rows = db_exec("SELECT * FROM attendance WHERE date=?", (date,)).fetchall()
    return jsonify({"ok": True, "attendance": [dict(r) for r in rows]})

@app.route("/api/attendance", methods=["POST"])
@require_auth
def mark_attendance():
    data = request.get_json()
    sid = data.get("student_id")
    date = data.get("date")
    status = data.get("status")
    db = get_db()
    db_exec("DELETE FROM attendance WHERE student_id=? AND date=?", (sid, date))
    db_exec("INSERT INTO attendance (student_id, date, status) VALUES (?,?,?)", (sid, date, status))
    db_commit()
    return jsonify({"ok": True})

@app.route("/api/attendance/bulk", methods=["POST"])
@require_auth
def bulk_attendance():
    data = request.get_json()
    date = data.get("date")
    records = data.get("records", []) # list of {student_id, status}
    db = get_db()
    for r in records:
        db_exec("DELETE FROM attendance WHERE student_id=? AND date=?", (r["student_id"], date))
        db_exec("INSERT INTO attendance (student_id, date, status) VALUES (?,?,?)", (r["student_id"], date, r["status"]))
    db_commit()
    return jsonify({"ok": True})

# Expenses
@app.route("/api/expenses", methods=["GET"])
@require_admin
def get_expenses():
    db = get_db()
    rows = db_exec("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    return jsonify({"ok": True, "expenses": [dict(r) for r in rows]})

@app.route("/api/expenses", methods=["POST"])
@require_admin
def create_expense():
    data = request.get_json()
    db = get_db()
    db_exec("INSERT INTO expenses (title, amount, category, date, mode, remarks) VALUES (?,?,?,?,?,?)",
               (data["title"], data["amount"], data.get("category"), data["date"], data.get("mode", "Cash"), data.get("remarks", "")))
    db_commit()
    log_action(g.admin, "EXPENSE_ADDED", f"Added expense: {data['title']} (Rs.{data['amount']})")
    return jsonify({"ok": True})

@app.route("/api/expenses/<eid>", methods=["DELETE"])
@require_admin
def delete_expense(eid):
    db = get_db()
    db_exec("DELETE FROM expenses WHERE id=?", (eid,))
    db_commit()
    log_action(g.admin, "EXPENSE_DELETED", f"Deleted expense ID: {eid}")
    return jsonify({"ok": True})

# Backup
@app.route("/api/admin/backup", methods=["GET"])
@require_admin
def backup_db():
    return send_file(DB_PATH, as_attachment=True, download_name=f"tuition_backup_{datetime.now().strftime('%Y%m%d')}.db")

# Serve Frontend
@app.route("/")
def serve_index():
    return send_from_directory(BASE_DIR, "tuition-center.html")

init_db()

if __name__ == "__main__":
    # Support dynamic port for platforms like Render
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
