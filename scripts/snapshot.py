#!/usr/bin/env python3
"""快照日期与路径的唯一来源。

通过环境变量 BOSS_DATE 指定快照目录（YYYY-MM-DD），缺省为当天日期。
各采集 / 清洗 / 分析 / 报告脚本统一从这里取路径，避免日期硬编码散落多处。
"""
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATE = os.environ.get("BOSS_DATE") or date.today().isoformat()

RAW = ROOT / "data" / "raw" / DATE
PROC = ROOT / "data" / "processed" / DATE
REPORT = ROOT / "reports" / DATE
BY_SOURCE = PROC / "by_source"
