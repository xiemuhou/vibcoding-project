"""设备IP采集程序 — Web 服务端"""

import os
import sys
import threading

from flask import Flask, jsonify, render_template, request, send_file

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import load_config, save_config
from src.scanner import scan_subnet, get_local_subnet, resolve_mac_from_arp_table
from src.arp import resolve_hostname
from src.vendor import lookup_vendor
from src.storage import (
    init_db, upsert_device, insert_scan_record,
    mark_offline_devices, get_all_devices, clear_scan_data,
)
from src.export import export_csv, export_json, export_excel
from src.monitor import get_monitor, Monitor

app = Flask(__name__)
init_db()

_scanning = threading.Lock()
_scan_stop_event = threading.Event()
_scan_status: dict = {
    "running": False,
    "progress": 0,
    "total": 0,
    "online": 0,
    "stopping": False,
    "cancelled": False,
}


# ===== 页面路由 =====

@app.route("/")
def index():
    return render_template("index.html")


# ===== 设备 API =====

@app.route("/api/devices")
def api_devices():
    online_only = request.args.get("online_only", "0") == "1"
    devices = get_all_devices(online_only=online_only)
    return jsonify([d.to_dict() for d in devices])


@app.route("/api/devices/count")
def api_devices_count():
    devices = get_all_devices()
    online = sum(1 for d in devices if d.is_online)
    return jsonify({"total": len(devices), "online": online, "offline": len(devices) - online})


# ===== 扫描 API =====

@app.route("/api/scan", methods=["POST"])
def api_scan():
    global _scan_status
    if _scan_status["running"]:
        return jsonify({"error": "扫描正在进行中"}), 409

    # 支持自定义网段
    body = request.get_json(silent=True) or {}
    subnet = body.get("subnet", "").strip() or get_local_subnet()
    _scan_stop_event.clear()
    clear_scan_data()
    _scan_status = {
        "running": True,
        "progress": 0,
        "total": 0,
        "online": 0,
        "stopping": False,
        "cancelled": False,
    }

    def _do_scan(subnet):
        global _scan_status
        with _scanning:
            def progress(current, total):
                _scan_status["progress"] = current
                _scan_status["total"] = total

            results = scan_subnet(
                subnet,
                progress_callback=progress,
                stop_event=_scan_stop_event,
            )
            if _scan_stop_event.is_set():
                _scan_status = {
                    "running": False,
                    "progress": _scan_status["progress"],
                    "total": _scan_status["total"],
                    "online": 0,
                    "stopping": False,
                    "cancelled": True,
                }
                return

            online_results = [r for r in results if r.is_online]

            for r in online_results:
                if _scan_stop_event.is_set():
                    _scan_status = {
                        "running": False,
                        "progress": _scan_status["progress"],
                        "total": _scan_status["total"],
                        "online": 0,
                        "stopping": False,
                        "cancelled": True,
                    }
                    return

                r.mac_address = resolve_mac_from_arp_table(r.ip_address)
                r.hostname = resolve_hostname(r.ip_address)
                vendor = lookup_vendor(r.mac_address) if r.mac_address else None
                if _scan_stop_event.is_set():
                    _scan_status = {
                        "running": False,
                        "progress": _scan_status["progress"],
                        "total": _scan_status["total"],
                        "online": 0,
                        "stopping": False,
                        "cancelled": True,
                    }
                    return

                device_id = upsert_device(
                    ip_address=r.ip_address,
                    mac_address=r.mac_address,
                    hostname=r.hostname,
                    vendor=vendor,
                    is_online=True,
                )
                insert_scan_record(device_id, True, r.response_time_ms)

            online_ips = [r.ip_address for r in online_results]
            mark_offline_devices(online_ips)
            _scan_status = {
                "running": False, "progress": _scan_status["total"],
                "total": _scan_status["total"], "online": len(online_results),
                "stopping": False, "cancelled": False,
            }

    thread = threading.Thread(target=_do_scan, args=(subnet,), daemon=True)
    thread.start()
    return jsonify({"message": "扫描已启动", "subnet": subnet})


@app.route("/api/scan/status")
def api_scan_status():
    return jsonify(_scan_status)


@app.route("/api/scan/stop", methods=["POST"])
def api_scan_stop():
    if not _scan_status["running"]:
        return jsonify({"message": "当前没有正在进行的扫描", "running": False})

    _scan_stop_event.set()
    _scan_status["stopping"] = True
    return jsonify({"message": "正在停止扫描", "running": True})


# ===== 导出 API =====

@app.route("/api/export/<fmt>")
def api_export(fmt):
    if fmt == "csv":
        path = export_csv()
    elif fmt == "json":
        path = export_json()
    elif fmt == "excel":
        path = export_excel()
    else:
        return jsonify({"error": f"不支持的格式: {fmt}"}), 400
    return send_file(
        os.path.abspath(path), as_attachment=True,
        download_name=os.path.basename(path)
    )


# ===== 监控 API =====

@app.route("/api/monitor/start", methods=["POST"])
def api_monitor_start():
    config = load_config()
    monitor = get_monitor(interval=config.get("scan_interval", 300))
    if monitor.is_running:
        return jsonify({"message": "监控已在运行中"})
    monitor.start()
    return jsonify({"message": "监控已启动", "subnet": monitor.subnet, "interval": monitor.interval})


@app.route("/api/monitor/stop", methods=["POST"])
def api_monitor_stop():
    monitor = get_monitor()
    if monitor.is_running:
        monitor.stop()
        return jsonify({"message": "监控已停止"})
    return jsonify({"message": "监控未在运行"})


@app.route("/api/monitor/status")
def api_monitor_status():
    monitor = get_monitor()
    return jsonify({"running": monitor.is_running, "subnet": monitor.subnet})


# ===== 配置 API =====

@app.route("/api/config")
def api_config():
    return jsonify(load_config())


@app.route("/api/config", methods=["PUT"])
def api_config_update():
    data = request.get_json()
    config = load_config()
    for key in data:
        if key in config:
            config[key] = type(config[key])(data[key])
    save_config(config)
    return jsonify(config)


# ===== 启动 =====

def main():
    print("设备IP采集程序 Web 服务端 v1.0.0")
    print(f"访问地址: http://localhost:3000")
    app.run(host="0.0.0.0", port=3000, debug=False)


if __name__ == "__main__":
    main()
