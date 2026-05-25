# 设备IP采集程序 — 需求规格

## 项目概述

开发一个 **设备IP采集程序**，用于自动扫描局域网内所有在线设备，采集 IP 地址、MAC 地址、主机名、厂商信息等，支持定时扫描、状态监控与数据导出。

## 核心功能

### 1. 局域网设备扫描
- 自动检测本机所在网段（如 192.168.1.0/24）
- 支持手动指定 IP 段范围进行扫描
- 多线程并发 ping 扫描，提升扫描速度
- 通过 ARP 表获取设备 MAC 地址
- 通过 MAC 地址 OUI 前缀识别设备厂商（内置或查询 IEEE 数据库）

### 2. 设备信息采集
- 采集字段：IP 地址、MAC 地址、主机名、厂商、首次发现时间、最后在线时间、在线状态
- 支持通过 mDNS / NetBIOS 额外解析设备主机名
- 支持自定义备注（如"网关"、"打印机"、"服务器"）

### 3. IP 状态监控
- 后台定时扫描（可配间隔，默认 5 分钟）
- 设备上线/下线状态变更通知
- 新设备接入告警（未知 MAC 地址出现时提醒）
- IP 冲突检测

### 4. 数据存储
- 本地 SQLite 数据库存储，无需额外部署
- 保留历史扫描记录，支持按时间范围查询
- 设备信息支持增删改查

### 5. 数据导出
- 导出格式：CSV、JSON、Excel
- 支持导出当前在线设备列表
- 支持导出历史扫描报告

### 6. 命令行交互界面
- 交互式菜单：扫描、查看、导出、设置
- 实时展示扫描进度和结果表格
- 彩色终端输出，提升可读性

## 技术栈

| 层 | 技术选型 |
|----|---------|
| 语言 | Python 3.10+ |
| 数据库 | SQLite（内置 `sqlite3`） |
| 网络扫描 | `scapy`（ARP）/ `ping3`（ICMP）/ 系统 ARP 表 |
| 并发 | `concurrent.futures`（线程池） |
| OUI 厂商查询 | `manuf` 库 或 内置私有 OUI 数据库 |
| 表格输出 | `rich` 库（终端美化） |
| 数据导出 | `csv`（内置）/ `openpyxl`（Excel） |
| CLI 框架 | `argparse` + `cmd` 或 `click` |

## 目录结构

```
src/
├── __init__.py
├── scanner.py        # 网络扫描引擎（ping + ARP）
├── arp.py            # ARP 表查询与解析
├── vendor.py         # MAC 厂商识别
├── monitor.py        # 定时监控调度
├── storage.py        # SQLite 数据库操作
├── models.py         # 数据模型定义
├── export.py         # 数据导出（CSV/JSON/Excel）
├── cli.py            # 命令行交互界面
└── config.py         # 配置管理

main.py               # 程序入口
requirements.txt      # 依赖清单
```

## 命令行接口

```
设备IP采集程序 v1.0

可用命令:
  scan           立即扫描当前网段
  scan -r <段>    扫描指定IP段（如 192.168.1.0/24）
  list           查看所有已发现设备
  list --online  仅查看在线设备
  export csv     导出为 CSV 文件
  export json    导出为 JSON 文件
  export excel   导出为 Excel 文件
  monitor start  启动后台监控
  monitor stop   停止后台监控
  monitor status 查看监控状态
  config         查看/修改配置
  help           显示帮助
  exit           退出程序
```

## 数据库设计

```sql
-- 设备表
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    mac_address TEXT,
    hostname TEXT,
    vendor TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_online BOOLEAN DEFAULT 1,
    notes TEXT
);

-- 扫描记录表
CREATE TABLE scan_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER,
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_online BOOLEAN,
    response_time_ms REAL,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);
```

## 开发阶段

### 阶段一：基础扫描
- 实现 ping 扫描（多线程）
- ARP 表查询获取 MAC 地址
- 基础 CLI 菜单

### 阶段二：数据持久化
- SQLite 数据库建表与 CRUD
- 扫描结果自动入库
- 设备列表查询展示

### 阶段三：厂商识别与导出
- MAC OUI 厂商查询
- CSV / JSON / Excel 导出

### 阶段四：监控与告警
- 定时后台扫描
- 设备上下线检测
- 新设备告警

### 阶段五：优化完善
- 终端表格美化（rich）
- 配置持久化
- 错误处理与日志

## 验收标准

1. 能在 30 秒内完成 /24 网段的全量扫描
2. 正确识别设备 MAC 地址和常见厂商
3. 设备上下线变更能在 2 个扫描周期内检测到
4. 导出文件格式正确、内容完整
5. SQLite 数据库文件可被外部工具正常打开
