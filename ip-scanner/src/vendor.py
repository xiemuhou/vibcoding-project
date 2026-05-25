"""MAC 厂商识别 — 基于 OUI 数据库"""

import os

try:
    from manuf import manuf
    MANUF_AVAILABLE = True
except ImportError:
    MANUF_AVAILABLE = False

_mac_to_vendor_cache: dict[str, str | None] = {}


def lookup_vendor(mac_address: str) -> str | None:
    """根据 MAC 地址查询厂商名称"""
    if not mac_address:
        return None

    mac = mac_address.lower().strip()
    if mac in _mac_to_vendor_cache:
        return _mac_to_vendor_cache[mac]

    vendor = None
    if MANUF_AVAILABLE:
        try:
            parser = manuf.MacParser()
            vendor = parser.get_manuf(mac) or parser.get_comment(mac)
        except Exception:
            pass

    _mac_to_vendor_cache[mac] = vendor
    return vendor


def batch_lookup_vendors(mac_map: dict[str, str]) -> dict[str, str | None]:
    """批量查询厂商，返回 {ip: vendor_name}"""
    result = {}
    for ip, mac in mac_map.items():
        result[ip] = lookup_vendor(mac)
    return result
