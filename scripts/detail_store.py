#!/usr/bin/env python3
"""阶段2 详情采集的本地落盘与断点管理（内置浏览器采集路线）。

- 读取 data/raw/<日期>/list_merged.json 作为待采队列
- 详情记录追加写入同目录 jobs_detail.json，按 url 去重
- 公司主页链接缓存到 companies.json，供阶段2B 补充融资/规模/行业
- job_key 规则对齐 SPEC 3.3：编号优先，缺失走 公司+标题+地点+经验 md5 前12位
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATE = "2026-11-15"
RAW = ROOT / "data" / "raw" / DATE

LIST_PATH = RAW / "list_merged.json"
DETAIL_PATH = RAW / "jobs_detail.json"
COMPANY_PATH = RAW / "companies.json"

JOB_NO_RE = re.compile(r"[A-Za-z]{2}\d{5,}")


def _read_json(path, default):
    if path.exists():
        return json.load(open(path, encoding="utf-8"))
    return default


def load_merged():
    return _read_json(LIST_PATH, {"items": []})["items"]


def load_detail():
    return _read_json(DETAIL_PATH, [])


def save_detail(records):
    json.dump(records, open(DETAIL_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)


def pending(limit=None):
    merged = load_merged()
    done = {d["url"] for d in load_detail()}
    todo = [x for x in merged if x["url"] not in done]
    return todo[:limit] if limit else todo


def norm_key(s):
    return re.sub(r"\s+", "", (s or "").lower())


def make_job_key(title, company, location, exp):
    m = JOB_NO_RE.search(title or "")
    if m:
        return m.group(0)
    seed = "|".join(norm_key(x) for x in (company, title, location, exp))
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:12]


def add_record(rec):
    """合并写入：按 url 去重，已存在则更新。返回 (records, index)。"""
    records = load_detail()
    idx = next((i for i, r in enumerate(records) if r["url"] == rec["url"]), None)
    if idx is None:
        records.append(rec)
    else:
        records[idx].update(rec)
    save_detail(records)
    return records, idx


def load_companies():
    return _read_json(COMPANY_PATH, {"companies": []})


def upsert_company(href, name):
    if not href:
        return
    data = load_companies()
    if not any(c["href"] == href for c in data["companies"]):
        data["companies"].append({"href": href, "name": name,
                                  "stage": None, "size": None, "industry": None})
        json.dump(data, open(COMPANY_PATH, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)


if __name__ == "__main__":
    det = load_detail()
    print(f"已采详情: {len(det)} / 待采队列: {len(load_merged())}")
