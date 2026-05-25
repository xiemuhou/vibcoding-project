"""配置管理模块"""

import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "scan_interval": 300,  # 定时扫描间隔（秒），默认 5 分钟
    "ping_timeout": 1,     # ping 超时（秒）
    "max_threads": 50,     # 最大并发线程数
    "default_subnet": "",  # 默认扫描网段，为空则自动检测
    "export_dir": "exports",  # 导出文件目录
    "db_path": "devices.db",  # SQLite 数据库路径
}


def load_config() -> dict:
    """加载配置，如配置文件不存在则使用默认配置并自动创建"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    save_config(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """保存配置到文件"""
    os.makedirs(os.path.dirname(CONFIG_FILE) or ".", exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
