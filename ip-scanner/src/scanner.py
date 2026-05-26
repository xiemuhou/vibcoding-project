"""网络扫描引擎 — 多线程 ping + ARP 扫描"""

import ipaddress
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from ping3 import ping

from src.config import load_config
from src.models import ScanResult


def get_local_subnet() -> str:
    """自动获取本机所在网段（CIDR 格式）"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        # 假设 /24 子网掩码
        parts = local_ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    except Exception:
        return "192.168.1.0/24"


def get_subnet_hosts(subnet: str) -> list[str]:
    """返回网段内所有主机 IP 列表（排除网络地址和广播地址）"""
    net = ipaddress.ip_network(subnet, strict=False)
    return [str(ip) for ip in net.hosts()]


def ping_host(ip: str, timeout: float = 1) -> tuple[str, bool, float | None]:
    """ping 单个主机，返回 (ip, 是否在线, 响应时间毫秒)"""
    try:
        response = ping(ip, timeout=timeout)
        if response is not None:
            return (ip, True, response * 1000)
        return (ip, False, None)
    except Exception:
        return (ip, False, None)


def scan_subnet(
    subnet: str | None = None,
    progress_callback=None,
    stop_event=None,
) -> list[ScanResult]:
    """扫描整个子网，返回在线设备列表"""
    config = load_config()
    if not subnet:
        subnet = config.get("default_subnet") or get_local_subnet()

    hosts = get_subnet_hosts(subnet)
    max_threads = config.get("max_threads", 50)
    timeout = config.get("ping_timeout", 1)
    results: list[ScanResult] = []
    total = len(hosts)

    executor = ThreadPoolExecutor(max_workers=max_threads)
    futures = {executor.submit(ping_host, ip, timeout): ip for ip in hosts}

    try:
        for i, future in enumerate(as_completed(futures), 1):
            if stop_event and stop_event.is_set():
                break

            ip, online, response_ms = future.result()
            if online:
                results.append(ScanResult(
                    ip_address=ip,
                    is_online=True,
                    response_time_ms=response_ms,
                ))
            if progress_callback:
                progress_callback(i, total)
    finally:
        if stop_event and stop_event.is_set():
            for future in futures:
                future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
        else:
            executor.shutdown(wait=True)

    return results


def resolve_mac_from_arp_table(ip: str) -> str | None:
    """从系统 ARP 表获取 MAC 地址"""
    system = sys.platform

    try:
        if system == "win32":
            output = subprocess.check_output(
                f'arp -a {ip}', shell=True, text=True,
                stderr=subprocess.DEVNULL
            )
            for line in output.splitlines():
                if ip in line:
                    parts = line.split()
                    for p in parts:
                        p = p.replace("-", ":").strip()
                        if len(p) == 17 and p.count(":") == 5:
                            return p.lower()
        else:
            # Linux / macOS
            output = subprocess.check_output(
                f"arp -n {ip}", shell=True, text=True,
                stderr=subprocess.DEVNULL
            )
            for line in output.splitlines():
                if ip in line:
                    parts = line.split()
                    for p in parts:
                        if ":" in p and len(p) >= 17:
                            return p.lower()
    except Exception:
        pass

    return None
