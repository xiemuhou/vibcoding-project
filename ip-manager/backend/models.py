"""数据库模型 - SQLite (用户 + 操作日志)"""

import sqlite3
from contextlib import contextmanager
from config import DB_PATH, ADMIN_USERNAME, ADMIN_PASSWORD


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password_hash TEXT   NOT NULL,
            display_name TEXT   DEFAULT '',
            is_admin    INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    DEFAULT (datetime('now','localtime')),
            username    TEXT    NOT NULL,
            action      TEXT    NOT NULL,
            sheet_name  TEXT    NOT NULL,
            row_index   INTEGER NOT NULL,
            ip_address  TEXT    NOT NULL,
            detail      TEXT    DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_logs_time ON audit_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_users_name ON users(username);
    """)
    conn.commit()
    conn.close()


@contextmanager
def get_db():
    conn = _get_conn()
    try:
        yield conn
    finally:
        conn.close()


def init_admin():
    """初始化管理员账号。"""
    import bcrypt
    with get_db() as db:
        row = db.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,)).fetchone()
        if row is None:
            pw_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            db.execute(
                "INSERT INTO users (username, password_hash, display_name, is_admin) VALUES (?,?,?,1)",
                (ADMIN_USERNAME, pw_hash, "管理员"),
            )
            db.commit()
