#!/usr/bin/env python3
"""阶段6：生成 技能->教程映射清单（不写教程正文）。

读取 reports/<日期>/analysis.json 与 processed/<日期>/jobs_clean.json，
按分组汇总硬技能关键词，评定优先级，回填来源岗位留痕，输出
curriculum/skill_map.json。Schema 见 curriculum/skill_map.schema.json。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATE = "2026-11-15"
REP = ROOT / "reports" / DATE
PROC = ROOT / "data" / "processed" / DATE
CUR = ROOT / "curriculum"

# 软技能/业务分组不进入硬技能教程主线，单独低优先级保留
SOFT_GROUP = "业务/管理/行业"
BOUNDARY_WORDS = {"go", "c", "ai", "r", "sdk", "ndk", "rtc", "hal", "mcu", "qnx"}


def hit(keyword, text):
    kw = keyword.lower().strip()
    if kw in BOUNDARY_WORDS or re.fullmatch(r"[a-z0-9/+#.-]+", kw):
        return re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", text) is not None
    return kw in text


def priority(cover):
    if cover >= 40:
        return "高"
    if cover >= 20:
        return "中"
    return "低"


def main():
    analysis = json.load(open(REP / "analysis.json", encoding="utf-8"))["result"]
    jobs = json.load(open(PROC / "jobs_clean.json", encoding="utf-8"))["records"]
    jobs = [j for j in jobs if not j.get("dup_of")]

    # 预计算每条文本
    texts = []
    for j in jobs:
        t = " ".join([j.get("title", ""), j.get("desc", ""), " ".join(j.get("tags", []) or [])]).lower()
        texts.append((j["url"], t))

    skills = []
    for group, info in analysis["overall"].items():
        for kw in info["keywords"]:
            name = kw["keyword"]
            cover = kw["cover"]
            freq = kw["freq"]
            sources = [url for url, t in texts if hit(name, t)]
            prio = priority(cover) if group != SOFT_GROUP else "低"
            skills.append({
                "skill": name,
                "category": group,
                "demand_count": cover,
                "freq": freq,
                "priority": prio,
                "prerequisites": [],
                "outline_placeholder": "",
                "resource_status": "todo",
                "source_jobs": sources,
            })

    # 排序：硬技能在前，按优先级、覆盖数
    rank = {"高": 0, "中": 1, "低": 2}
    skills.sort(key=lambda s: (rank[s["priority"]], -s["demand_count"], s["category"]))

    out = {
        "version": "v0.1",
        "date": DATE,
        "note": "本期仅生成映射清单与优先级，教程正文待后续按 priority 由高到低补写；prerequisites 待人工/规则补全。",
        "skills": skills,
    }
    CUR.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(CUR / "skill_map.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    high = [s["skill"] for s in skills if s["priority"] == "高"]
    print(f"映射技能 {len(skills)} 个 | 高优先级 {len(high)}")
    print("高优先级:", high)


if __name__ == "__main__":
    main()
