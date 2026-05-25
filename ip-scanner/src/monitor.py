"""定时监控调度 — 后台定时扫描与变更检测"""

import threading
import time
from datetime import datetime

from src.scanner import scan_subnet, get_local_subnet, resolve_mac_from_arp_table
from src.arp import resolve_hostname
from src.vendor import lookup_vendor
from src.storage import (
    upsert_device, insert_scan_record, mark_offline_devices, get_all_devices
)


class Monitor:
    """后台监控器"""

    def __init__(self, subnet: str | None = None, interval: int = 300):
        self.subnet = subnet or get_local_subnet()
        self.interval = interval
        self._running = False
        self._thread: threading.Thread | None = None
        self.callbacks: list = []  # 事件回调列表，每个回调接收 (event_type, data)

    def on_event(self, callback) -> None:
        """注册事件回调。event_type: "device_online" | "device_offline" | "new_device" """
        self.callbacks.append(callback)

    def _emit(self, event_type: str, data: dict) -> None:
        for cb in self.callbacks:
            cb(event_type, data)

    def start(self) -> None:
        """启动后台监控"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止后台监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    @property
    def is_running(self) -> bool:
        return self._running

    def _loop(self) -> None:
        """监控主循环"""
        while self._running:
            try:
                self.scan_once()
            except Exception as e:
                self._emit("error", {"message": str(e)})
            # 分段 sleep 以响应 stop
            for _ in range(min(self.interval, 5)):
                if not self._running:
                    return
                time.sleep(1)

    def scan_once(self) -> dict:
        """执行一次完整扫描，返回统计信息"""
        # 获取扫描前已知设备
        before_devices = {d.ip_address for d in get_all_devices()}

        # ping 扫描
        results = scan_subnet(self.subnet)
        online_ips = [r.ip_address for r in results]

        # 获取 MAC 和主机名
        for r in results:
            r.mac_address = resolve_mac_from_arp_table(r.ip_address)
            r.hostname = resolve_hostname(r.ip_address)

        # 存入数据库
        for r in results:
            vendor = lookup_vendor(r.mac_address) if r.mac_address else None
            device_id = upsert_device(
                ip_address=r.ip_address,
                mac_address=r.mac_address,
                hostname=r.hostname,
                vendor=vendor,
                is_online=True,
            )
            if r.response_time_ms is not None:
                insert_scan_record(device_id, True, r.response_time_ms)

        # 标记离线设备
        offline_ips = mark_offline_devices(online_ips)

        # 检测新设备和状态变化
        after_devices = {d.ip_address for d in get_all_devices()}
        new_devices = after_devices - before_devices

        for ip in new_devices:
            self._emit("new_device", {"ip_address": ip})
        for ip in offline_ips:
            self._emit("device_offline", {"ip_address": ip})

        return {
            "total_scanned": len(results),
            "online": len([r for r in results if r.is_online]),
            "offline_marked": len(offline_ips),
            "new_devices": len(new_devices),
            "subnet": self.subnet,
            "time": datetime.now().isoformat(),
        }


# 全局单例
_monitor_instance: Monitor | None = None


def get_monitor(subnet: str | None = None, interval: int = 300) -> Monitor:
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = Monitor(subnet=subnet, interval=interval)
    return _monitor_instance
