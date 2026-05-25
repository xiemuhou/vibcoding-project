"""命令行交互界面 — 基于 cmd 模块"""

import cmd
import sys
import threading
import time

from src.config import load_config, save_config
from src.scanner import scan_subnet, get_local_subnet, resolve_mac_from_arp_table
from src.arp import resolve_hostname
from src.vendor import lookup_vendor
from src.storage import (
    init_db, upsert_device, insert_scan_record, mark_offline_devices, get_all_devices
)
from src.export import export_csv, export_json, export_excel
from src.monitor import Monitor, get_monitor

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


if RICH_AVAILABLE:
    console = Console()
else:
    console = None


def _print_rich_table(devices: list) -> None:
    """使用 rich 打印设备表格"""
    if not RICH_AVAILABLE:
        _print_simple_table(devices)
        return

    table = Table(title="设备列表", show_lines=False)
    table.add_column("ID", justify="right", style="dim")
    table.add_column("IP 地址", style="cyan")
    table.add_column("MAC 地址", style="green")
    table.add_column("主机名", style="yellow")
    table.add_column("厂商", style="magenta")
    table.add_column("状态", justify="center")
    table.add_column("最后在线")

    for d in devices:
        status = "[green]在线[/green]" if d.is_online else "[red]离线[/red]"
        last_seen = d.last_seen.strftime("%m-%d %H:%M") if d.last_seen else "-"
        table.add_row(
            str(d.id), d.ip_address, d.mac_address or "-",
            d.hostname or "-", d.vendor or "-",
            status, last_seen,
        )
    console.print(table)


def _print_simple_table(devices: list) -> None:
    """不使用 rich 时的简单表格输出"""
    header = f"{'ID':>4}  {'IP地址':<15}  {'MAC地址':<17}  {'主机名':<20}  {'厂商':<20}  {'状态':<6}  {'最后在线'}"
    print(header)
    print("-" * len(header))
    for d in devices:
        status = "在线" if d.is_online else "离线"
        last_seen = d.last_seen.strftime("%m-%d %H:%M") if d.last_seen else "-"
        print(
            f"{d.id:>4}  {d.ip_address:<15}  {(d.mac_address or '-'):<17}  "
            f"{(d.hostname or '-')[:20]:<20}  {(d.vendor or '-')[:20]:<20}  "
            f"{status:<6}  {last_seen}"
        )


class IPCollectorCLI(cmd.Cmd):
    prompt = "ip-collector> "
    intro = """
========================================
      设备IP采集程序  v1.0.0
  输入 help 查看可用命令
========================================
"""

    def __init__(self):
        super().__init__()
        self.use_rawinput = False  # 使用 readline，跨平台兼容更好
        init_db()
        self._monitor: Monitor | None = None

    def default(self, line: str) -> bool:
        if line.strip() in ("exit", "EOF"):
            return True
        return super().default(line)

    def emptyline(self) -> bool:
        """空行不执行任何操作（也不重复上一条命令）"""
        return False

    # ===== scan 命令 =====
    def do_scan(self, arg: str) -> None:
        """scan [-r <网段>]  —  扫描局域网设备
        scan                 自动检测本机网段扫描
        scan -r 192.168.1.0/24  扫描指定网段
        """
        subnet = None
        if "-r" in arg:
            parts = arg.split()
            if len(parts) > 1:
                subnet = parts[-1]
            else:
                print("请指定网段，如: scan -r 192.168.1.0/24")
                return

        target = subnet or get_local_subnet()
        print(f"正在扫描 {target} ...")

        results = scan_subnet(target, progress_callback=self._scan_progress)
        online_results = [r for r in results if r.is_online]
        print(f"\n扫描完成: 发现 {len(online_results)} 台在线设备")

        # 获取 MAC 地址
        for r in online_results:
            r.mac_address = resolve_mac_from_arp_table(r.ip_address)
            r.hostname = resolve_hostname(r.ip_address)

        # 存入数据库
        for r in online_results:
            vendor = lookup_vendor(r.mac_address) if r.mac_address else None
            device_id = upsert_device(
                ip_address=r.ip_address,
                mac_address=r.mac_address,
                hostname=r.hostname,
                vendor=vendor,
                is_online=True,
            )
            insert_scan_record(device_id, True, r.response_time_ms)

        # 标记离线
        online_ips = [r.ip_address for r in online_results]
        offline = mark_offline_devices(online_ips)
        if offline:
            print(f"标记离线: {len(offline)} 台设备")

        devices = get_all_devices(online_only=True)
        _print_rich_table(devices)

    @staticmethod
    def _scan_progress(current: int, total: int) -> None:
        if current % 20 == 0 or current == total:
            print(f"\r扫描进度: {current}/{total}", end="", flush=True)

    # ===== list 命令 =====
    def do_list(self, arg: str) -> None:
        """list [--online]  —  查看设备列表
        list              查看所有设备
        list --online     仅查看在线设备
        """
        online_only = "--online" in arg
        devices = get_all_devices(online_only=online_only)
        if not devices:
            print("暂无设备记录")
            return
        _print_rich_table(devices)
        print(f"\n共 {len(devices)} 台设备")

    # ===== export 命令 =====
    def do_export(self, arg: str) -> None:
        """export <格式>  —  导出设备数据
        export csv      导出为 CSV
        export json     导出为 JSON
        export excel    导出为 Excel
        """
        fmt = arg.strip().lower()
        devices = get_all_devices()
        if not devices:
            print("暂无设备数据可导出")
            return

        try:
            if fmt == "csv":
                path = export_csv(devices)
            elif fmt == "json":
                path = export_json(devices)
            elif fmt == "excel":
                path = export_excel(devices)
            else:
                print("请指定导出格式: csv / json / excel")
                return
            print(f"已导出到: {path}")
        except ImportError as e:
            print(f"导出失败: {e}")

    # ===== monitor 命令 =====
    def do_monitor(self, arg: str) -> None:
        """monitor <start|stop|status>  —  后台监控管理
        monitor start    启动后台监控
        monitor stop     停止后台监控
        monitor status   查看监控状态
        """
        cmd = arg.strip().lower()

        if cmd == "start":
            if self._monitor and self._monitor.is_running:
                print("监控已在运行中")
                return
            config = load_config()
            self._monitor = get_monitor(interval=config.get("scan_interval", 300))
            self._monitor.on_event(lambda t, d: print(f"  [{t}] {d['ip_address']}"))
            self._monitor.start()
            print(f"后台监控已启动 (间隔: {self._monitor.interval}s, 网段: {self._monitor.subnet})")

        elif cmd == "stop":
            if self._monitor:
                self._monitor.stop()
                print("后台监控已停止")
            else:
                print("监控未在运行")

        elif cmd == "status":
            if self._monitor and self._monitor.is_running:
                print(f"监控运行中 (间隔: {self._monitor.interval}s, 网段: {self._monitor.subnet})")
            else:
                print("监控未在运行")

        else:
            print("用法: monitor <start|stop|status>")

    # ===== config 命令 =====
    def do_config(self, arg: str) -> None:
        """config [key] [value]  —  查看或修改配置
        config                   查看所有配置
        config scan_interval 60  设置扫描间隔为 60 秒
        """
        parts = arg.strip().split()
        config = load_config()

        if not parts:
            print("当前配置:")
            for k, v in config.items():
                print(f"  {k} = {v}")
            return

        if len(parts) == 2:
            key, val = parts[0], parts[1]
            if key in config:
                orig_type = type(config[key])
                config[key] = orig_type(val)
                save_config(config)
                print(f"已更新: {key} = {val}")
            else:
                print(f"未知配置项: {key}")
        elif len(parts) == 1:
            key = parts[0]
            if key in config:
                print(f"{key} = {config[key]}")
            else:
                print(f"未知配置项: {key}")

    # ===== 退出 =====
    def do_exit(self, arg: str) -> bool:
        """退出程序"""
        if self._monitor:
            self._monitor.stop()
        print("再见！")
        return True

    def do_help(self, arg: str) -> None:
        """显示帮助"""
        if arg:
            cmd.Cmd.do_help(self, arg)
            return
        print("""
可用命令:
  scan                扫描局域网设备
  scan -r <网段>       扫描指定网段（如 192.168.1.0/24）
  list                查看所有设备
  list --online       仅查看在线设备
  export csv|json|excel  导出数据
  monitor start|stop|status  后台监控管理
  config              查看/修改配置
  help                显示帮助
  exit                退出程序
""")

    def emptyline(self) -> bool:
        return False
