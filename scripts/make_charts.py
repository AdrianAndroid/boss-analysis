#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成岗位增速对比图与本地样本存量结构图。

- 图1 外部增速：来自脉脉高聘 / Indeed / LinkedIn 等公开报告，口径与周期在图内标注；
  本地为单期快照(2026-11-15)，无法计算环比/同比增速，故增速数据均为外部公开口径。
- 图2 本地结构：读取 reports/.../analysis.json 的分组岗位覆盖占比。
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Hiragino Sans GB", "STHeiti", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "scripts"))
from snapshot import DATE, REPORT  # noqa: E402
REPORT_DIR = str(REPORT)
ANALYSIS = os.path.join(REPORT_DIR, "analysis.json")
GROWTH_CFG = os.path.join(ROOT, "config", "trend_growth.json")

# --- 外部公开增速（口径不同，仅作方向参照，不可跨口径精确比较）---
with open(GROWTH_CFG, encoding="utf-8") as f:
    _growth_cfg = json.load(f)
GROWTH = [(g["direction"], g["growth_pct"], g["source"]) for g in _growth_cfg["items"]]


def chart_growth():
    rows = sorted(GROWTH, key=lambda r: r[1])
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    notes = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(12, 6.6))
    colors = plt.cm.YlOrRd([0.35 + 0.55 * v / max(vals) for v in vals])
    bars = ax.barh(labels, vals, color=colors, edgecolor="white")

    pad = max(vals) * 0.012
    for bar, v, note in zip(bars, vals, notes):
        y = bar.get_y() + bar.get_height() / 2
        ax.text(bar.get_width() + pad, y, f"+{v:g}%", va="center", ha="left",
                fontsize=10, fontweight="bold", color="#222")
        ax.text(bar.get_width() + pad, y - 0.30, note, va="center", ha="left",
                fontsize=7.2, color="#666")

    ax.set_xlabel("招聘需求同比增速（%，外部公开口径）")
    ax.set_title("2026 热门技术岗位招聘需求增速对比（外部公开报告）", fontsize=13, fontweight="bold")
    ax.set_xlim(0, max(vals) * 1.55)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "注：各数据来源与统计周期不同，仅反映方向与量级；FDE 供需比约 0.28（猎聘 2026.9，每 3.5 岗抢 1 人）。",
             fontsize=7.5, color="#555")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    out = os.path.join(REPORT_DIR, "chart_growth.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def chart_structure():
    data = json.load(open(ANALYSIS, encoding="utf-8"))
    overall = data["result"]["overall"]
    sample = data.get("sample", len(overall))
    rows = sorted(overall.items(), key=lambda kv: kv[1]["cover_rate"])
    labels = [k for k, _ in rows]
    vals = [v["cover_rate"] * 100 for _, v in rows]

    fig, ax = plt.subplots(figsize=(11, 6.2))
    colors = plt.cm.Blues([0.35 + 0.55 * v / 100 for v in vals])
    bars = ax.barh(labels, vals, color=colors, edgecolor="white")

    for bar, v in zip(bars, vals):
        ax.text(bar.get_width() + 1.2, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", ha="left", fontsize=10, fontweight="bold")

    ax.set_xlabel("岗位覆盖占比（%，样本内出现该技能组的岗位比例）")
    ax.set_title(f"本地样本技能大类覆盖结构（北京 {sample} 岗 · {DATE}）", fontsize=13, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = os.path.join(REPORT_DIR, "chart_structure.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


if __name__ == "__main__":
    g = chart_growth()
    s = chart_structure()
    print("growth ->", g)
    print("structure ->", s)
