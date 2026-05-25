"""SQLite 数据库操作"""

import sqlite3
from datetime import datetime
from typing import Optional

from src.config import load_config
from src.models import Device, ScanRecord


def get_db_path() -> str:
    return load_config().get("db_path", "devices.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """初始化数据库表"""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL UNIQUE,
                mac_address TEXT,
                hostname TEXT,
                vendor TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_online BOOLEAN DEFAULT 1,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS scan_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_online BOOLEAN,
                response_time_ms REAL,
                FOREIGN KEY (device_id) REFERENCES devices(id)
            );

            CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip_address);
            CREATE INDEX IF NOT EXISTS idx_devices_online ON devices(is_online);
            CREATE INDEX IF NOT EXISTS idx_scan_records_device
                ON scan_records(device_id);
            CREATE INDEX IF NOT EXISTS idx_scan_records_time
                ON scan_records(scan_time);
        """)
        conn.commit()
    finally:
        conn.close()


def upsert_device(
    ip_address: str,
    mac_address: Optional[str] = None,
    hostname: Optional[str] = None,
    vendor: Optional[str] = None,
    is_online: bool = True,
) -> int:
    """插入或更新设备信息，返回设备 ID"""
    conn = get_connection()
    now = datetime.now()
    try:
        existing = conn.execute(
            "SELECT id, mac_address, hostname, vendor FROM devices WHERE ip_address = ?",
            (ip_address,)
        ).fetchone()

        if existing:
            # 已有设备：更新最后在线时间和状态，补充空字段
            device_id = existing["id"]
            update_mac = mac_address or existing["mac_address"]
            update_hostname = hostname or existing["hostname"]
            update_vendor = vendor or existing["vendor"]
            conn.execute(
                """UPDATE devices
                   SET mac_address = ?, hostname = ?, vendor = ?,
                       is_online = ?, last_seen = ?
                   WHERE id = ?""",
                (update_mac, update_hostname, update_vendor, is_online, now, device_id)
            )
        else:
            # 新设备
            cursor = conn.execute(
                """INSERT INTO devices
                   (ip_address, mac_address, hostname, vendor, is_online, last_seen)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (ip_address, mac_address, hostname, vendor, is_online, now)
            )
            device_id = cursor.lastrowid

        conn.commit()
        return device_id
    finally:
        conn.close()


def insert_scan_record(
    device_id: int,
    is_online: bool,
    response_time_ms: Optional[float] = None,
) -> None:
    """插入一条扫描记录"""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO scan_records (device_id, is_online, response_time_ms)
               VALUES (?, ?, ?)""",
            (device_id, is_online, response_time_ms)
        )
        conn.commit()
    finally:
        conn.close()


def get_all_devices(online_only: bool = False) -> list[Device]:
    """获取所有设备"""
    conn = get_connection()
    try:
        query = "SELECT * FROM devices"
        if online_only:
            query += " WHERE is_online = 1"
        query += " ORDER BY id"
        rows = conn.execute(query).fetchall()
        return [_row_to_device(r) for r in rows]
    finally:
        conn.close()


def get_device_by_ip(ip_address: str) -> Optional[Device]:
    """根据 IP 获取设备"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM devices WHERE ip_address = ?", (ip_address,)
        ).fetchone()
        return _row_to_device(row) if row else None
    finally:
        conn.close()


def mark_offline_devices(online_ip_list: list[str]) -> list[str]:
    """将不在在线列表中的设备标记为离线，返回被标记的 IP 列表"""
    conn = get_connection()
    try:
        devices = conn.execute(
            "SELECT id, ip_address FROM devices WHERE is_online = 1"
        ).fetchall()

        offline_ids = []
        for row in devices:
            if row["ip_address"] not in online_ip_list:
                offline_ids.append(row["id"])

        placeholders = ",".join("?" * len(offline_ids))
        if offline_ids:
            conn.execute(
                f"""UPDATE devices SET is_online = 0
                    WHERE id IN ({placeholders})""",
                offline_ids
            )
            conn.commit()

        # 返回标记为离线的 IP
        offline_ips = [r["ip_address"] for r in devices if r["id"] in offline_ids]
        return offline_ips
    finally:
        conn.close()


def _row_to_device(row: sqlite3.Row) -> Device:
    return Device(
        id=row["id"],
        ip_address=row["ip_address"],
        mac_address=row["mac_address"],
        hostname=row["hostname"],
        vendor=row["vendor"],
        first_seen=datetime.fromisoformat(row["first_seen"]) if row["first_seen"] else None,
        last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
        is_online=bool(row["is_online"]),
        notes=row["notes"],
    )
