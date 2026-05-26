# 设备IP采集程序

用于自动扫描和采集网络内设备的IP地址信息，支持局域网设备发现、IP状态监控、数据存储与导出。

## 特性

- 局域网设备自动发现与扫描
- IP地址状态实时监控
- 设备信息采集与存储
- 数据导出（CSV / JSON）
- 命令行交互界面

## 快速开始

### 环境要求

- Windows 10/11
- Python 3.10+（推荐 3.11 或 3.12）

### Windows 直接运行

双击项目目录下的 `start.bat` 即可启动。

首次运行时脚本会自动：

1. 创建 `.venv` 虚拟环境
2. 安装核心依赖
3. 打开浏览器访问 `http://localhost:3000`

如果安装依赖失败，优先确认：

- 已安装 Python 3.10/3.11/3.12/3.13
- 安装 Python 时已勾选 `Add python.exe to PATH`
- 当前网络能访问 PyPI，或配置了公司代理

如果是从另一台电脑复制过来的项目，请不要复制 `.venv` 目录。`.venv` 里记录了原电脑的 Python 安装路径，换电脑后可能出现类似 `did not find executable at 'D:\Program Files\Python314\python.exe'` 的错误。新版 `start.bat` 会自动检测并重建无效的 `.venv`；也可以手动删除 `.venv` 后重新双击 `start.bat`。

### 手动安装

```bash
# 进入项目目录
cd ip-scanner

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 可选增强依赖

基础扫描不需要安装可选依赖。若需要主动 ARP 探测或更完整的 MAC 厂商识别，可额外安装：

```bash
pip install -r requirements-optional.txt
```

在 Windows 上，主动 ARP 探测通常还需要管理员权限和 Npcap 支持；即使不安装这些可选依赖，Web 程序也可以正常启动和扫描。

### 使用

```bash
# 启动 Web 页面
python web_server.py
```

## 目录结构

```
vibcoding project/
├── main.py              # 程序入口
├── requirements.txt     # 项目依赖
├── src/                 # 源代码
├── tests/               # 测试文件
├── docs/                # 文档
│   └── plans/           # 计划文档
├── tmp/                 # 临时文件
├── AGENTS.md            # 跨平台 AI 指令
├── CLAUDE.md            # Claude Code 指令
├── README.md            # 项目说明
├── CHANGELOG.md         # 变更记录
└── .gitignore           # Git 忽略规则
```

## AI 辅助开发

本项目配置了 AI 辅助开发支持，可以使用以下工具进行智能开发：

### Claude Code

使用 `CLAUDE.md` 作为项目指令。

```bash
# 在项目目录启动 Claude Code
claude

# Claude Code 会自动读取 CLAUDE.md 理解项目上下文
```

### OpenAI Codex CLI

使用 `AGENTS.md` 作为项目指令。

```bash
# 在项目目录启动 Codex CLI
codex

# Codex 会自动读取 AGENTS.md 理解项目上下文
```

### AI 开发最佳实践

1. **新功能开发**：描述需求，AI 会按照项目工作流进行开发
2. **代码审查**：请求 AI 审查代码，它会按照工程原则给出建议
3. **文档更新**：AI 会自动同步更新相关文档
4. **问题排查**：描述问题现象，AI 会分析并给出解决方案
5. **变更记录**：**重要** - 凡是项目的更新，都要统一在 `CHANGELOG.md` 文件里记录。

## 贡献

欢迎提交 Issue 和 Pull Request。

## 许可证

MIT License
