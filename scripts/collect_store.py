#!/usr/bin/env python3
"""列表采集落盘与合并（内置浏览器采集路线）。

- 按来源组写 data/raw/<日期>/lists/<source>.json
- 合并所有组到 list_merged.json：同一 URL 命中多组时 tabs 多对多累加
- URL 规范化为相对路径 /job_detail/<id>.html，剔除无编号坏链接

用法（浏览器提取后把 JSON 写到临时文件，再调用）：
  python3 collect_store.py list <source> <items.json>
  python3 collect_store.py merge
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "scripts"))
from snapshot import DATE, RAW  # noqa: E402

LISTS_DIR = RAW / "lists"
MERGED_PATH = RAW / "list_merged.json"
DETAIL_RE = re.compile(r"/job_detail/([A-Za-z0-9_-]+\.html)")


def norm_url(href):
    """规范化为相对 detail 路径；非详情链接返回 None。"""
    if not href:
        return None
    m = DETAIL_RE.search(href)
    if not m:
        return None
    return "/job_detail/" + m.group(1)


def _read_json(path, default):
    if path.exists():
        return json.load(open(path, encoding="utf-8"))
    return default


def save_source_list(source, items):
    """items: [{url, text, tabs?}]。写 lists/<source>.json，返回去重后条数。"""
    LISTS_DIR.mkdir(parents=True, exist_ok=True)
    seen = {}
    for it in items:
        url = norm_url(it.get("url") or "")
        if not url:
            continue
        text = (it.get("text") or "").strip()
        if not text:
            continue
        tabs = it.get("tabs") or [source]
        if url in seen:
            for t in tabs:
                if t not in seen[url]["tabs"]:
                    seen[url]["tabs"].append(t)
        else:
            seen[url] = {"url": url, "text": text, "tabs": list(dict.fromkeys(tabs))}
    records = list(seen.values())
    payload = {"tab": source, "collected_at": datetime.now().isoformat(timespec="seconds"),
               "count": len(records), "items": records}
    json.dump(payload, open(LISTS_DIR / f"{source}.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    return len(records)


def merge_merged():
    """合并 lists/*.json 到 list_merged.json，tabs 累加去重。"""
    LISTS_DIR.mkdir(parents=True, exist_ok=True)
    merged = {}
    for f in sorted(LISTS_DIR.glob("*.json")):
        data = _read_json(f, {"items": []})
        for it in data.get("items", []):
            url = it["url"]
            if url in merged:
                for t in it.get("tabs", []):
                    if t not in merged[url]["tabs"]:
                        merged[url]["tabs"].append(t)
            else:
                merged[url] = {"url": url, "text": it.get("text", ""),
                                "tabs": list(dict.fromkeys(it.get("tabs", [])))}
    records = list(merged.values())
    payload = {"collected_at": datetime.now().isoformat(timespec="seconds"),
               "count": len(records), "items": records}
    json.dump(payload, open(MERGED_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    return len(records)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "list":
        source, fpath = sys.argv[2], sys.argv[3]
        items = json.load(open(fpath, encoding="utf-8"))
        n = save_source_list(source, items)
        print(f"list {source}: {n} 条 -> {LISTS_DIR / (source + '.json')}")
    elif len(sys.argv) >= 2 and sys.argv[1] == "merge":
        n = merge_merged()
        print(f"merged: {n} 条 -> {MERGED_PATH}")
    else:
        print(__doc__)
