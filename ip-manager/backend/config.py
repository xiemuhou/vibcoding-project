"""应用配置"""

import os
from pathlib import Path

# Excel 文件路径
EXCEL_PATH = os.environ.get(
    "IPMGR_EXCEL_PATH",
    r"C:\Users\haipeng1.tan\Desktop\IP地址信息汇总.xlsx",
)

# JWT 配置
JWT_SECRET = os.environ.get("IPMGR_JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# 数据库
DB_PATH = Path(__file__).parent / "ip_manager.db"

# 管理员初始账号（首次启动时创建）
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Excel 同步
EXCEL_RELOAD_INTERVAL = 300  # 定时检测 Excel 变化的间隔（秒）
WRITE_RETRY_COUNT = 3        # 写入失败重试次数
WRITE_RETRY_DELAY = 1.0      # 重试间隔（秒）

# Sheet 配置
READONLY_SHEETS = {"IP地址规划", "工厂监控"}  # 只读 Sheet
SKIP_SHEETS = {"IP地址规划"}  # 不纳入 IP 列表的 Sheet

# 10.10.128.0 双表布局：仅读取左侧列（A-H），忽略右侧英文表
DUAL_TABLE_SHEET = "10.10.128.0"
DUAL_TABLE_LEFT_COLS = 8  # A-H 列

# 设备类型选项
DEVICE_TYPES = [
    "台式电脑",
    "笔记本电脑",
    "打印机",
    "服务器",
    "网络设备",
    "监控设备",
    "其他",
]

# 部门选项（从 Excel 中提取的常见值，也可手动输入）
DEPARTMENTS = [
    "电算TEAM",
    "计算部",
    "管理部",
    "制造部",
    "品质部",
    "研发部",
    "人事部",
    "财务部",
    "营业部",
    "购买部",
]
