"""
modules/database.py
All database operations: init, auth, sessions, tokens, activity logging.
Supports SQLite (default) and PostgreSQL (see POSTGRES GUIDE in app.py).
"""

import sqlite3, hashlib, json, uuid, os
import datetime

DB_PATH = os.environ.get("DATALYZE_DB_PATH", "datalyze.db")


# ── Connection ────────────────────────────────────────────────────────────────
def _connect():
    """SQLite connection. Swap with psycopg2.connect() for Postgres."""
    return sqlite3.connect(DB_PATH)


# ── Schema ────────────────────────────────────────────────────────────────────
def init_db():
    conn = _connect()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_name TEXT NOT NULL,
        file_name TEXT,
        rows_count INTEGER,
        cols_count INTEGER,
        analysis_types TEXT,
        charts_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id INTEGER,
        action_type TEXT NOT NULL,
        action_detail TEXT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS login_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL)""")
    conn.commit()
    conn.close()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


# ── Activity Log ──────────────────────────────────────────────────────────────
def log_activity(user_id, action_type, detail="", session_id=None):
    """Record any user action. Never raises — logging must not crash the app."""
    try:
        conn = _connect()
        conn.execute(
            "INSERT INTO user_activity (user_id, session_id, action_type, action_detail) VALUES (?,?,?,?)",
            (user_id, session_id, action_type, str(detail)[:1000]))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── Auth ──────────────────────────────────────────────────────────────────────
def register_user(username, email, password):
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
            (username, email, _hash(password)))
        conn.commit()
        return True, "Account created!"
    except sqlite3.IntegrityError as e:
        msg = "Username already taken." if "username" in str(e) else "Email already registered."
        return False, msg
    finally:
        conn.close()


def login_user(username, password):
    conn = _connect()
    c = conn.cursor()
    c.execute(
        "SELECT id, username FROM users WHERE username=? AND password_hash=?",
        (username, _hash(password)))
    user = c.fetchone()
    conn.close()
    return user


# ── Persistent Login Tokens ───────────────────────────────────────────────────
def create_token(user_id, username):
    token = str(uuid.uuid4()).replace("-", "")
    expires = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO login_tokens (token, user_id, username, expires_at) VALUES (?,?,?,?)",
        (token, user_id, username, expires))
    conn.commit()
    conn.close()
    return token


def validate_token(token):
    if not token:
        return None
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT user_id, username, expires_at FROM login_tokens WHERE token=?", (token,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    if datetime.datetime.utcnow().isoformat() > row[2]:
        return None  # expired
    return row[0], row[1]


def revoke_token(token):
    conn = _connect()
    conn.execute("DELETE FROM login_tokens WHERE token=?", (token,))
    conn.commit()
    conn.close()


# ── Sessions CRUD ─────────────────────────────────────────────────────────────
def save_session_db(user_id, session_name, file_name, rows, cols, analysis_types, charts_json):
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """INSERT INTO sessions
           (user_id,session_name,file_name,rows_count,cols_count,analysis_types,charts_json)
           VALUES (?,?,?,?,?,?,?)""",
        (user_id, session_name, file_name, rows, cols, json.dumps(analysis_types), charts_json))
    conn.commit()
    sid = c.lastrowid
    conn.close()
    log_activity(user_id, "dashboard_saved", f"session='{session_name}' file='{file_name}'", sid)
    return sid


def rename_session_db(session_id, new_name):
    conn = _connect()
    conn.execute("UPDATE sessions SET session_name=? WHERE id=?", (new_name, session_id))
    conn.commit()
    conn.close()


def delete_session_db(session_id, user_id):
    conn = _connect()
    conn.execute("DELETE FROM sessions WHERE id=? AND user_id=?", (session_id, user_id))
    conn.commit()
    conn.close()
    log_activity(user_id, "session_deleted", f"session_id={session_id}")


def update_session_db(session_id, session_name, charts_json, analysis_types, user_id):
    conn = _connect()
    conn.execute(
        "UPDATE sessions SET session_name=?, charts_json=?, analysis_types=? WHERE id=? AND user_id=?",
        (session_name, charts_json, json.dumps(analysis_types), session_id, user_id))
    conn.commit()
    conn.close()
    log_activity(user_id, "session_updated", f"session_id={session_id} name='{session_name}'")


def get_user_sessions(user_id):
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """SELECT id, session_name, file_name, rows_count, cols_count, analysis_types, created_at
           FROM sessions WHERE user_id=? ORDER BY created_at DESC LIMIT 20""",
        (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_session_charts(session_id):
    import plotly.io as pio
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT charts_json FROM sessions WHERE id=?", (session_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        charts = []
        for item in json.loads(row[0]):
            try:
                uid  = item.get("uid", str(uuid.uuid4())[:8])
                desc = item.get("desc", "")
                charts.append((uid, item["title"], pio.from_json(item["fig_json"]), desc))
            except Exception:
                pass
        return charts
    return []
