#!/usr/bin/env python3
"""列表层预筛：在详情采集前剔除明显误召回噪声，压缩详情队列。

规则与 clean.py 的检索组判定对齐（标题/标签文本可判部分）；被剔记录不物理删除，
写入 list_dropped.json 留痕，lists/<source>.json 仍保留全量召回。
三 tab（recommend/harmonyos/android）为基线对照，全量保留。
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "scripts"))
from snapshot import RAW  # noqa: E402
from clean import _DROP_TITLE, _AI_TECH, _FDE_CORE, _FDE_ADJ  # noqa: E402

MERGED = RAW / "list_merged.json"
DROPPED = RAW / "list_dropped.json"


def _title(text):
    return (text.split("|")[0] or "").strip()


def keep(it):
    tabs = it.get("tabs") or []
    title = _title(it.get("text", ""))
    text = it.get("text", "")
    if "ai_agent" in tabs:
        if _DROP_TITLE.search(title):
            return False, "drop_title"
        if not (_AI_TECH.search(title) or _AI_TECH.search(text)):
            return False, "no_ai_tech"
    if "fde" in tabs:
        if _DROP_TITLE.search(title):
            return False, "drop_title"
        if not (_FDE_CORE.search(title) or _FDE_ADJ.search(title) or _AI_TECH.search(text)):
            return False, "no_fde_role"
    return True, None


def main():
    data = json.load(open(MERGED, encoding="utf-8"))
    keep_items, drop_items = [], []
    for it in data["items"]:
        ok, reason = keep(it)
        if ok:
            keep_items.append(it)
        else:
            drop_items.append({**it, "drop_reason": reason})
    payload = {"collected_at": datetime.now().isoformat(timespec="seconds"),
               "count": len(keep_items), "items": keep_items}
    json.dump(payload, open(MERGED, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump({"collected_at": datetime.now().isoformat(timespec="seconds"),
               "count": len(drop_items), "items": drop_items},
              open(DROPPED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"预筛: 保留 {len(keep_items)} | 剔除 {len(drop_items)} -> {MERGED.name} / {DROPPED.name}")


if __name__ == "__main__":
    main()
