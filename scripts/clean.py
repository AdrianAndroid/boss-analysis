#!/usr/bin/env python3
"""阶段3：清洗结构化。

读取 data/raw/<日期>/jobs_detail.json，解析列表文本、回填 job_key，
输出 data/processed/<日期>/jobs_clean.json 与 jobs_clean.csv，并打印校验指标。
口径对齐 SPEC.md：身份键规则、单批去重、缺失值标记。
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "scripts"))
from detail_store import make_job_key  # noqa: E402

DATE = "2026-11-15"
RAW = ROOT / "data" / "raw" / DATE
PROC = ROOT / "data" / "processed" / DATE

EXP_RE = re.compile(r"(经验不限|应届|\d+\s*-\s*\d+\s*年|\d+\s*年以上|\d+\s*年)")
EDU_RE = re.compile(r"(博士|硕士|本科|大专|学历不限)")
LOC_RE = re.compile(r"北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|亦庄|望京|海淀|朝阳|昌平|丰台|大兴|东城|西城|上地|学院路|亚运村|万柳|苏州桥|回龙观|酒仙桥|大望路|清河|西二旗|中关村|太阳宫|霄云路|五棵松|善各庄|来广营|高碑店|安贞|交道口|西坝河|马连洼|西北旺|三里屯|什刹海")
SALARY_RE = re.compile(r"[Kk]·?\d*薪|元/月|\d+-\d+K")


def parse_list_text(text):
    parts = [p.strip() for p in (text or "").split("|") if p.strip()]
    title = parts[0] if parts else ""
    salary = ""
    exp = ""
    edu = ""
    location = ""
    company = ""
    tags = []
    rest = parts[1:] if len(parts) > 1 else []

    # 薪资段
    if rest and SALARY_RE.search(rest[0]):
        salary = rest.pop(0)

    for seg in rest:
        if not exp and EXP_RE.fullmatch(seg):
            exp = seg
        elif not edu and EDU_RE.fullmatch(seg):
            edu = seg
        elif LOC_RE.search(seg):
            location = seg
        else:
            tags.append(seg)

    # 公司：地点前一段（tags 末尾）；若无地点，取 tags 末尾
    if location and tags:
        company = tags.pop()
    elif not location and tags:
        company = tags.pop()

    return {"title": title, "salary": salary, "exp": exp, "edu": edu,
            "location": location, "company": company, "tags": tags}


def clean():
    detail = json.load(open(RAW / "jobs_detail.json", encoding="utf-8"))
    records = []
    seen_keys = {}
    first_by_key = {}
    for r in detail:
        parsed = parse_list_text(r.get("list_text", ""))
        title = r.get("title") or parsed["title"]
        company = r.get("company") or parsed["company"]
        location = parsed["location"]
        exp = parsed["exp"]
        job_key = make_job_key(title, company, location, exp)
        primary_tab = (r.get("tabs") or ["unknown"])[0]
        dup_of = None
        if job_key in first_by_key:
            dup_of = first_by_key[job_key]
        else:
            first_by_key[job_key] = r.get("url")
        rec = {
            "job_key": job_key,
            "primary_tab": primary_tab,
            "tabs": r.get("tabs", []),
            "url": r.get("url"),
            "title": title,
            "company": company,
            "salary": r.get("salary") or parsed["salary"],
            "location": location,
            "exp": exp,
            "edu": parsed["edu"],
            "tags": parsed["tags"],
            "company_stage": r.get("company_stage"),
            "company_size": r.get("company_size"),
            "company_industry": r.get("company_industry"),
            "desc": (r.get("desc") or "").strip(),
            "dup_of": dup_of,
            "period_status": None,
        }
        records.append(rec)
        seen_keys.setdefault(job_key, []).append(rec["url"])

    # 校验指标（口径：去重后样本）
    total = len(records)
    unique = [x for x in records if not x["dup_of"]]
    dup_keys = {k: v for k, v in seen_keys.items() if len(v) > 1}
    empty_desc = sum(1 for x in unique if not x["desc"])
    empty_company = sum(1 for x in unique if not x["company"])
    empty_title = sum(1 for x in unique if not x["title"])
    tab_dist = {}
    for x in unique:
        for t in x["tabs"] or [x["primary_tab"]]:
            tab_dist[t] = tab_dist.get(t, 0) + 1

    PROC.mkdir(parents=True, exist_ok=True)
    json.dump({"date": DATE, "count": len(unique), "raw_count": total,
               "duplicates": total - len(unique), "records": records},
              open(PROC / "jobs_clean.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    fields = ["job_key", "primary_tab", "tabs", "url", "title", "company",
              "salary", "location", "exp", "edu", "tags", "company_stage",
              "company_size", "company_industry", "desc", "dup_of", "period_status"]
    with open(PROC / "jobs_clean.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for x in records:
            row = dict(x)
            row["tabs"] = "/".join(x["tabs"])
            row["tags"] = "/".join(x["tags"])
            w.writerow(row)

    print(f"清洗完成: 原始 {total} | 去重后 {len(unique)} | 重复 {total - len(unique)} -> {PROC}")
    print(f"  job_key 重复组: {len(dup_keys)}")
    print(f"  空 JD: {empty_desc} | 空公司: {empty_company} | 空标题: {empty_title}")
    print(f"  公司完整度: {len(unique) - empty_company}/{len(unique)}")
    print(f"  tab 命中分布(多对多): {tab_dist}")
    if dup_keys:
        for k, v in list(dup_keys.items())[:5]:
            print(f"    重复 {k}: {v}")
    return records


if __name__ == "__main__":
    clean()
