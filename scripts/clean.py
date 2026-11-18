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
from snapshot import DATE, RAW, PROC, BY_SOURCE  # noqa: E402

# 已知来源（tab / 检索组）；AI/FDE 目录待首次采集时由数据自动补入
KNOWN_SOURCES = ["recommend", "harmonyos", "android", "ai_agent", "fde"]

NOISE_RE = re.compile(r"BOSS直聘|BOSS|boss|Boss|直聘|kanzhun", re.I)


def clean_desc(text):
    """去除详情页混入的水印/遮挡文本（BOSS直聘/boss/直聘/kanzhun），还原被插断的词。"""
    if not text:
        return ""
    t = NOISE_RE.sub("", text)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


FIELDS = ["job_key", "primary_tab", "tabs", "url", "title", "company",
          "salary", "location", "exp", "edu", "tags", "company_stage",
          "company_size", "company_industry", "desc", "dup_of", "group_role",
          "dropped", "period_status"]

EXP_RE = re.compile(r"(经验不限|应届|\d+\s*-\s*\d+\s*年|\d+\s*年以上|\d+\s*年)")
EDU_RE = re.compile(r"(博士|硕士|本科|大专|学历不限)")
LOC_RE = re.compile(r"北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|亦庄|望京|海淀|朝阳|昌平|丰台|大兴|东城|西城|上地|学院路|亚运村|万柳|苏州桥|回龙观|酒仙桥|大望路|清河|西二旗|中关村|太阳宫|霄云路|五棵松|善各庄|来广营|高碑店|安贞|交道口|西坝河|马连洼|西北旺|三里屯|什刹海")
SALARY_RE = re.compile(r"[Kk]·?\d*薪|元/月|\d+-\d+K")


# 纯站点标识/占位符（不能作为公司名；注意“BOSS直聘”本身是合法雇主名，不在此列）
INVALID_COMPANY = {"kanzhun", "BOSS直聘招聘"}

# ---- 检索组（ai_agent / fde）噪声剔除与角色分层，口径对齐 config/search_groups.json ----
# 标题命中即剔除的强噪声（销售/商务/投资/出版/芯片FPGA/纯商务客户成功/管理岗/标注评测等）
_DROP_TITLE = re.compile(
    r"销售|商务|渠道|大客户经理|客户经理|投资|出版|主编|门店|店长|客服|标注|质检|训练师|"
    r"美工|助理|专员|FPGA|原型验证|芯片|SOC原型|视频生成|创作师|设计师|增长|市场|"
    r"管培|招聘|讲师|培训业务|内容创作|运营|交付经理|交付总监|项目交付经理|"
    r"客户成功经理|客户成功总监|客户成功专员|交付运维|运维交付"
)
# AI 研发 / 技术兜底词：标题或正文须命中其一，否则视为误召回剔除
_AI_TECH = re.compile(
    r"agent|智能体|llm|大模型|rag|多模态|aigc|模型|算法|推理|向量|embedding|微调|"
    r"预训练|后训练|nlp|知识图谱|深度学习|机器学习|语音|架构|开发|工程|研发|全栈|"
    r"后端|平台|infra|研究员|gpt|transformer|prompt|智能助手", re.I
)
# FDE 核心岗：标题直接出现 FDE / 前沿·前线·前置·前向部署 / Forward Deployed
_FDE_CORE = re.compile(r"fde|forward deployed|前沿部署|前线部署|前置部署|前向部署", re.I)
# FDE 相邻岗：交付 / 解决方案 / 售前 / 客户成功 / 部署落地类
_FDE_ADJ = re.compile(r"交付|解决方案|售前|客户成功|部署|落地|原型交付", re.I)


def classify_group(rec):
    """返回 (role, dropped)。role: core/adjacent/ai/None；dropped=True 不进分析口径。"""
    tabs = rec.get("tabs") or []
    title = rec.get("title") or ""
    desc = rec.get("desc") or ""
    if "ai_agent" in tabs:
        if _DROP_TITLE.search(title):
            return "dropped", True
        if not (_AI_TECH.search(title) or _AI_TECH.search(desc)):
            return "dropped", True
        return "ai", False
    if "fde" in tabs:
        if _DROP_TITLE.search(title):
            return "dropped", True
        if _FDE_CORE.search(title):
            return "fde_core", False
        if _FDE_ADJ.search(title):
            return "fde_adjacent", False
        # 标题既非核心也非相邻，需正文有研发/AI 内容才保留
        if _AI_TECH.search(desc):
            return "fde_adjacent", False
        return "dropped", True
    return None, False


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


def _source_of(rec):
    return rec.get("tabs") or [rec.get("primary_tab") or "unknown"]


def export_by_source(unique):
    """按来源导出视图到 processed/<日期>/by_source/<source>.{json,csv}。

    跨来源岗位在每个归属视图各出现一次；全量明细仍以 jobs_clean.* 为准。
    """
    BY_SOURCE.mkdir(parents=True, exist_ok=True)
    groups = {}
    for rec in unique:
        for src in _source_of(rec):
            groups.setdefault(src, []).append(rec)

    ordered = [s for s in KNOWN_SOURCES if s in groups]
    ordered += [s for s in groups if s not in KNOWN_SOURCES]

    for src in ordered:
        recs = groups[src]
        json.dump({"date": DATE, "source": src, "count": len(recs), "records": recs},
                  open(BY_SOURCE / f"{src}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        with open(BY_SOURCE / f"{src}.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for x in recs:
                row = dict(x)
                row["tabs"] = "/".join(x["tabs"])
                row["tags"] = "/".join(x["tags"])
                w.writerow(row)
        print(f"  来源视图 {src}: {len(recs)} 岗")


def clean():
    detail = json.load(open(RAW / "jobs_detail.json", encoding="utf-8"))
    records = []
    seen_keys = {}
    first_by_key = {}
    for r in detail:
        parsed = parse_list_text(r.get("list_text", ""))
        title = r.get("title") or parsed["title"]
        raw_co = (r.get("company") or "").strip()
        company = parsed["company"] if (not raw_co or raw_co in INVALID_COMPANY) else raw_co
        location = parsed["location"]
        exp = parsed["exp"]
        job_key = make_job_key(title, company, location, exp)
        primary_tab = (r.get("tabs") or ["unknown"])[0]
        group_role, dropped = classify_group(r)
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
            "desc": clean_desc(r.get("desc")),
            "dup_of": dup_of,
            "group_role": group_role,
            "dropped": dropped,
            "period_status": None,
        }
        records.append(rec)
        seen_keys.setdefault(job_key, []).append(rec["url"])

    # 校验指标（口径：去重后样本）
    total = len(records)
    unique = [x for x in records if not x["dup_of"] and not x.get("dropped")]
    dropped_n = sum(1 for x in records if x.get("dropped"))
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

    with open(PROC / "jobs_clean.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for x in records:
            row = dict(x)
            row["tabs"] = "/".join(x["tabs"])
            row["tags"] = "/".join(x["tags"])
            w.writerow(row)

    # 按来源（tab / 检索组）导出视图：跨来源岗位在各视图各留一份，归属以 tabs/groups 为准
    export_by_source(unique)

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
