"""数据模型定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Device:
    """设备信息模型"""
    ip_address: str
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    is_online: bool = True
    notes: Optional[str] = None
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "is_online": self.is_online,
            "notes": self.notes,
        }


@dataclass
class ScanRecord:
    """扫描记录模型"""
    device_id: int
    is_online: bool
    response_time_ms: Optional[float] = None
    scan_time: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class ScanResult:
    """单次扫描结果"""
    ip_address: str
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    is_online: bool = False
    response_time_ms: Optional[float] = None
