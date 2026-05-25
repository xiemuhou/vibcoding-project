"""数据导出模块 — CSV / JSON / Excel"""

import csv
import json
import os
from datetime import datetime

from src.config import load_config
from src.storage import get_all_devices


def _ensure_export_dir() -> str:
    export_dir = load_config().get("export_dir", "exports")
    os.makedirs(export_dir, exist_ok=True)
    return export_dir


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def export_csv(devices=None) -> str:
    """导出为 CSV，返回文件路径"""
    if devices is None:
        devices = get_all_devices()
    export_dir = _ensure_export_dir()
    filename = os.path.join(export_dir, f"devices_{_timestamp()}.csv")

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "IP地址", "MAC地址", "主机名", "厂商",
            "首次发现", "最后在线", "在线状态", "备注"
        ])
        for d in devices:
            writer.writerow([
                d.id, d.ip_address, d.mac_address or "", d.hostname or "",
                d.vendor or "",
                d.first_seen.strftime("%Y-%m-%d %H:%M:%S") if d.first_seen else "",
                d.last_seen.strftime("%Y-%m-%d %H:%M:%S") if d.last_seen else "",
                "在线" if d.is_online else "离线",
                d.notes or "",
            ])
    return filename


def export_json(devices=None) -> str:
    """导出为 JSON，返回文件路径"""
    if devices is None:
        devices = get_all_devices()
    export_dir = _ensure_export_dir()
    filename = os.path.join(export_dir, f"devices_{_timestamp()}.json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump([d.to_dict() for d in devices], f, ensure_ascii=False, indent=2)
    return filename


def export_excel(devices=None) -> str:
    """导出为 Excel，返回文件路径"""
    try:
        from openpyxl import Workbook
    except ImportError:
        raise ImportError("请安装 openpyxl：pip install openpyxl")

    if devices is None:
        devices = get_all_devices()
    export_dir = _ensure_export_dir()
    filename = os.path.join(export_dir, f"devices_{_timestamp()}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "设备列表"

    headers = ["ID", "IP地址", "MAC地址", "主机名", "厂商",
               "首次发现", "最后在线", "在线状态", "备注"]
    ws.append(headers)

    for d in devices:
        ws.append([
            d.id, d.ip_address, d.mac_address or "", d.hostname or "",
            d.vendor or "",
            d.first_seen.strftime("%Y-%m-%d %H:%M:%S") if d.first_seen else "",
            d.last_seen.strftime("%Y-%m-%d %H:%M:%S") if d.last_seen else "",
            "在线" if d.is_online else "离线",
            d.notes or "",
        ])

    # 调整列宽
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    wb.save(filename)
    return filename
