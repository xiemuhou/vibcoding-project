#!/usr/bin/env python3
"""设备IP采集程序 — 程序入口"""

import sys

from src.cli import IPCollectorCLI


def main():
    """启动交互式 CLI"""
    cli = IPCollectorCLI()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n再见！")
        sys.exit(0)


if __name__ == "__main__":
    main()
