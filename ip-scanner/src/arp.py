"""ARP 表查询与解析 — 支持通过 scapy 主动 ARP 探测"""

import socket
import struct

try:
    from scapy.all import Ether, ARP, srp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


def arp_scan(subnet: str, timeout: float = 2, progress_callback=None) -> dict[str, str]:
    """
    使用 scapy 进行 ARP 扫描，返回 {ip: mac} 映射。
    需要管理员/root 权限。
    """
    if not SCAPY_AVAILABLE:
        return {}

    try:
        ans, _ = srp(
            Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet),
            timeout=timeout,
            verbose=False,
        )
        result = {}
        total = len(ans)
        for i, (send, recv) in enumerate(ans, 1):
            result[recv.psrc] = recv.hwsrc.lower()
            if progress_callback:
                progress_callback(i, total)
        return result
    except Exception:
        return {}


def arp_table_lookup(ip_list: list[str]) -> dict[str, str]:
    """
    通过系统 ARP 表批量查询 MAC 地址。
    对于 Windows，执行 arp -a 一次然后解析全部条目，避免多次调用。
    """
    from src.scanner import resolve_mac_from_arp_table

    result = {}
    for ip in ip_list:
        mac = resolve_mac_from_arp_table(ip)
        if mac:
            result[ip] = mac
    return result


def resolve_hostname(ip: str, timeout: float = 1) -> str | None:
    """通过反向 DNS 解析主机名"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None
