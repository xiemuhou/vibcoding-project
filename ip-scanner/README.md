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

- Python 3.10+
- pip

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd vibcoding-project

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 使用

```bash
# 启动IP采集
python main.py
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
