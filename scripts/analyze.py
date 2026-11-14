#!/usr/bin/env python3
"""技能/关键词统计：读取详情底稿，输出岗位覆盖数与词频，分 tab 对比。

数据定位顺序：data/raw/<最新日期>/jobs_detail.json -> data/jobs_detail.json
词典来源：config/skills_dict.json
"""
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
DATA = ROOT / "data"


def load_dict():
    with open(CONFIG / "skills_dict.json", encoding="utf-8") as f:
        return json.load(f)


def locate_detail():
    raw = DATA / "raw"
    snapshots = sorted([p for p in raw.glob("*/jobs_detail.json")]) if raw.exists() else []
    if snapshots:
        return snapshots[-1]
    legacy = DATA / "jobs_detail.json"
    if legacy.exists():
        return legacy
    raise FileNotFoundError("未找到 jobs_detail.json 底稿")


def load_jobs():
    with open(locate_detail(), encoding="utf-8") as f:
        return json.load(f)


def norm(s):
    return (s or "").lower()


def analyze(jobs, dictionary):
    by_tab = defaultdict(list)
    for j in jobs:
        by_tab[j.get("tab", "unknown")].append(j)

    overall = {}
    for group, kws in dictionary.items():
        hit_jobs = 0
        kw_counter = Counter()
        for j in jobs:
            text = norm(j.get("desc", "") + " " + j.get("title", ""))
            if any(k in text for k in kws):
                hit_jobs += 1
            for k in kws:
                if k in text:
                    kw_counter[k.strip()] += 1
        overall[group] = {"hit_jobs": hit_jobs, "keywords": kw_counter.most_common(8)}

    per_tab = {}
    for tab, items in by_tab.items():
        cnt = Counter()
        for j in items:
            text = norm(j.get("desc", "") + " " + j.get("title", ""))
            for kws in dictionary.values():
                for k in kws:
                    if k in text:
                        cnt[k.strip()] += 1
        per_tab[tab] = {"n": len(items), "top": cnt.most_common(15)}

    return {"total": len(jobs), "by_tab": dict(by_tab), "overall": overall, "per_tab": per_tab}


def print_report(result):
    print(f"总岗位数: {result['total']}")
    for tab, items in result["by_tab"].items():
        print(f"  {tab}: {len(items)}")
    print("\n=== 分组技能命中（岗位覆盖数）===")
    for group, info in result["overall"].items():
        top = ", ".join(f"{k}:{v}" for k, v in info["keywords"])
        print(f"\n[{group}] 命中岗位 {info['hit_jobs']}")
        print(f"   {top}")
    print("\n=== 各 tab 高频技术词 TOP ===")
    for tab, info in result["per_tab"].items():
        print(f"\n--- {tab} (n={info['n']}) ---")
        for k, v in info["top"]:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    jobs = load_jobs()
    dictionary = load_dict()
    print_report(analyze(jobs, dictionary))
