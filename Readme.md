# ip-scanner — 用户使用指南与交付汇总

本 README 面向**使用者**：如何在 Windows 电脑上直接运行 `ip-scanner`，以及如何使用扫描、停止扫描、导出等核心功能。

项目源码位于：`D:\vibcoding-project\ip-scanner`

## 快速开始

### 推荐用法：Windows 直接运行

```text
请运行 ip-scanner 工具
输入：双击 ip-scanner 目录下的 start.bat
输出：自动安装依赖、启动 Web 服务，并打开 http://localhost:3000
```

你只需要在 Windows 电脑上双击：

```bat
ip-scanner\start.bat
```

首次运行时，脚本会自动完成：

1. 检查 Python 3.10 或更高版本
2. 创建 `.venv` 虚拟环境
3. 安装核心依赖
4. 启动 Web 服务
5. 打开浏览器访问 `http://localhost:3000`

## 功能概述

`ip-scanner` 是一个局域网设备 IP 扫描工具，适合在 Windows 电脑上快速查看当前网段内的在线设备。

| 你的需求 | 使用位置 | 结果 |
|---|---|---|
| 扫描局域网设备 | Web 页面点击“开始扫描” | 发现在线 IP、MAC、主机名等信息 |
| 中途取消扫描 | Web 页面点击“停止扫描” | 停止当前扫描任务 |
| 开始新一轮扫描 | 再次点击“开始扫描” | 自动清空上一轮历史数据 |
| 导出结果 | 点击 CSV / JSON / Excel 导出 | 生成扫描结果文件 |
| 定时监控 | 点击“启动监控” | 后台周期性扫描 |

## 本次优化内容

### 1. Windows 启动更稳定

已优化 `start.bat`：

- 自动创建 `.venv`
- 自动安装核心依赖
- 自动检测损坏或从其他电脑复制来的 `.venv`
- 检测到无效 `.venv` 时自动删除并重建
- 使用英文 ASCII 提示，避免 Windows 代码页乱码导致批处理执行异常

### 2. 依赖安装更轻量

核心依赖保留在：

```text
ip-scanner\requirements.txt
```

包含：

| 依赖 | 用途 |
|---|---|
| `flask` | Web 服务 |
| `ping3` | IP 探测 |
| `rich` | 命令行展示 |
| `openpyxl` | Excel 导出 |

可选增强依赖放在：

```text
ip-scanner\requirements-optional.txt
```

包含：

| 依赖 | 用途 |
|---|---|
| `scapy` | 主动 ARP 探测 |
| `manuf` | MAC 厂商识别 |

基础扫描不依赖可选增强包，所以普通 Windows 电脑更容易直接运行。

### 3. 扫描控制增强

Web 页面已新增：

- “停止扫描”按钮
- `POST /api/scan/stop` 停止扫描接口
- 新一轮扫描开始前自动清空设备和扫描记录
- 扫描状态支持 `stopping` / `cancelled`

## 常见问题

### Q：其他电脑运行时报 `did not find executable at 'D:\Program Files\Python314\python.exe'` 怎么办？

A：这是因为 `.venv` 虚拟环境从另一台电脑复制过去了。`.venv` 会记录原电脑的 Python 路径，换电脑后路径失效。

新版 `start.bat` 会自动检测并重建无效 `.venv`。也可以手动删除：

```bat
ip-scanner\.venv
```

然后重新双击 `start.bat`。

### Q：复制项目到其他电脑时要带 `.venv` 吗？

A：不要带。复制这些即可：

- `src`
- `templates`
- `web_server.py`
- `main.py`
- `start.bat`
- `requirements.txt`
- `requirements-optional.txt`
- `README.md`
- `config.json`

`.venv`、`__pycache__`、临时文件都不需要复制。

### Q：依赖安装失败怎么办？

A：优先检查：

1. 是否安装了 Python 3.10 或更高版本
2. Python 安装时是否勾选了 `Add python.exe to PATH`
3. 当前网络是否能访问 PyPI
4. 公司代理或杀毒软件是否拦截 pip 下载

可以手动尝试：

```bat
cd ip-scanner
.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.org/simple
```

### Q：需要安装 Npcap 吗？

A：基础扫描不需要。只有你要使用 `scapy` 主动 ARP 探测时，Windows 上通常才需要管理员权限和 Npcap。

## 文件位置

| 文件 | 说明 |
|---|---|
| `ip-scanner\start.bat` | Windows 一键启动脚本 |
| `ip-scanner\requirements.txt` | 核心依赖 |
| `ip-scanner\requirements-optional.txt` | 可选增强依赖 |
| `ip-scanner\web_server.py` | Web 服务与 API |
| `ip-scanner\templates\index.html` | Web 页面 |
| `ip-scanner\src\scanner.py` | 扫描引擎 |
| `ip-scanner\src\storage.py` | SQLite 数据存储 |

## 推荐交付方式

把 `ip-scanner` 文件夹复制给其他 Windows 电脑时，建议先删除以下内容：

```text
ip-scanner\.venv
ip-scanner\src\__pycache__
ip-scanner\devices.db-shm
ip-scanner\devices.db-wal
```

然后让使用者双击 `start.bat`。程序会在目标电脑上重新创建自己的运行环境。
