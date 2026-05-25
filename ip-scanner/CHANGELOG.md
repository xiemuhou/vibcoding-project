# Changelog

本文件记录项目重要变更，格式遵循 Keep a Changelog，并优先维护 `[Unreleased]`。

## [Unreleased]

## [1.1.0] - 2026-05-25

### Added（新增）

- Web 服务端 (`web_server.py`)：基于 Flask，监听 3000 端口
- Web 管理页面 (`templates/index.html`)：深色主题仪表盘，展示设备列表、状态统计、扫描进度
- REST API：设备查询、扫描控制、数据导出、监控管理、配置读写
- `start.bat`：自动安装依赖并打开浏览器访问 Web 页面

## [1.0.0] - 2026-05-25

### Added（新增）

- 初始化 AI 项目指令文件：生成 `AGENTS.md`、`CLAUDE.md`、`README.md`、`CHANGELOG.md` 与 `.gitignore`
- 配置项目工程原则、工作流和变更记录规范
- 定位项目为 Python 设备IP采集程序，支持局域网设备发现、IP状态监控、数据存储与导出
- CLI 交互命令行 (`main.py`)：scan / list / export / monitor / config 命令
- 核心模块：scanner.py、arp.py、vendor.py、storage.py、export.py、monitor.py、config.py、models.py

### Changed（变更）

### Fixed（修复）

---

## 记录规则

- 必须记录影响项目行为、结构、工作流、工程原则、指令文件或关键配置的变更
- 记录应说明改了什么、为什么改，以及影响范围
- 版本号遵循 SemVer：bug fix 递增修订号，新功能递增次版本号，破坏性变更递增主版本号

```markdown
## [版本号] - YYYY-MM-DD

### Added（新增）
- 新增了 XXX：用途是 YYY

### Changed（变更）
- 修改了 XXX：原因是 YYY，影响是 ZZZ

### Fixed（修复）
- 修复了 XXX：表现是 YYY，修复方式是 ZZZ
```
