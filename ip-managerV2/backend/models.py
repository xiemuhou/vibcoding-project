import sqlite3
import os

RESERVED_SUFFIXES = {1, 254, 255}


def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path):
    conn = get_db(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS subnets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cidr        TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            sort_order  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ip_addresses (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            subnet_id    INTEGER NOT NULL REFERENCES subnets(id),
            ip_address   TEXT NOT NULL UNIQUE,
            ip_suffix    INTEGER NOT NULL,
            status       TEXT NOT NULL DEFAULT 'free',
            department   TEXT DEFAULT '',
            username     TEXT DEFAULT '',
            device       TEXT DEFAULT '',
            device_model TEXT DEFAULT '',
            mac_address  TEXT DEFAULT '',
            location     TEXT DEFAULT '',
            remark       TEXT DEFAULT '',
            updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_ip_subnet ON ip_addresses(subnet_id);
        CREATE INDEX IF NOT EXISTS idx_ip_status ON ip_addresses(status);
    """)
    conn.close()


def db_exists(db_path):
    if not os.path.exists(db_path):
        return False
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='ip_addresses'")
    exists = cursor.fetchone()[0] > 0
    conn.close()
    return exists
