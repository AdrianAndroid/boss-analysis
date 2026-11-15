#!/usr/bin/env python3
"""阶段4-5：技能/关键词分析与报告生成。

读取 data/processed/<日期>/jobs_clean.json（去重样本），按 config/skills_dict.json
统计岗位覆盖数与词频，分 tab 多对多对比，输出：
  - reports/<日期>/analysis.json   机器可读中间结果
  - reports/<日期>/岗位技能分析报告.md  带表格的基线报告
口径对齐 SPEC 第 5 节；首期为基线，环比列保留但标注无历史可比。
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATE = "2026-11-15"
PROC = ROOT / "data" / "processed" / DATE
REP = ROOT / "reports" / DATE

# 纯 ASCII 短词需词边界匹配，避免子串误命中（go/c/ai 等）
BOUNDARY_WORDS = {"go", "c", "ai", "r", "sdk", "ndk", "rtc", "hal", "mcu", "qnx"}


def load_clean():
    data = json.load(open(PROC / "jobs_clean.json", encoding="utf-8"))
    return [r for r in data["records"] if not r.get("dup_of") and not r.get("dropped")]


def load_dict():
    return json.load(open(ROOT / "config" / "skills_dict.json", encoding="utf-8"))


def load_growth():
    return json.load(open(ROOT / "config" / "trend_growth.json", encoding="utf-8"))


def hit(keyword, text):
    kw = keyword.lower().strip()
    if not kw:
        return False
    if kw in BOUNDARY_WORDS or re.fullmatch(r"[a-z0-9/+#.-]+", kw):
        return re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", text) is not None
    return kw in text


def analyze(jobs, dictionary):
    # 预处理文本
    for j in jobs:
        j["_text"] = " ".join([
            j.get("title", ""), j.get("desc", ""),
            " ".join(j.get("tags", []) or []),
        ]).lower()

    # 总体：分组覆盖 + 关键词词频
    overall = {}
    for group, kws in dictionary.items():
        hit_jobs = 0
        kw_counter = Counter()
        kw_cover = Counter()
        for j in jobs:
            text = j["_text"]
            group_hit = False
            for k in kws:
                if hit(k, text):
                    group_hit = True
                    kw_counter[k.strip()] += text.count(k.lower().strip())
                    kw_cover[k.strip()] += 1
            if group_hit:
                hit_jobs += 1
        overall[group] = {
            "hit_jobs": hit_jobs,
            "cover_rate": round(hit_jobs / len(jobs), 3) if jobs else 0,
            "keywords": [
                {"keyword": k, "cover": kw_cover[k], "freq": kw_counter[k]}
                for k in kw_counter
            ],
        }
        overall[group]["keywords"].sort(key=lambda x: (-x["cover"], -x["freq"]))

    # 分 tab（多对多归属）
    per_tab = defaultdict(list)
    for j in jobs:
        for t in j.get("tabs") or [j.get("primary_tab", "unknown")]:
            per_tab[t].append(j)

    tab_result = {}
    for tab, items in per_tab.items():
        cnt = Counter()
        cover = Counter()
        for j in items:
            for kws in dictionary.values():
                for k in kws:
                    if hit(k, j["_text"]):
                        cnt[k.strip()] += j["_text"].count(k.lower().strip())
                        cover[k.strip()] += 1
        tab_result[tab] = {
            "n": len(items),
            "top": [
                {"keyword": k, "cover": cover[k], "freq": cnt[k]}
                for k in cnt
            ],
        }
        tab_result[tab]["top"].sort(key=lambda x: (-x["cover"], -x["freq"]))

    # 全量高频关键词 TOP（跨分组合并）
    all_cover = Counter()
    all_freq = Counter()
    for j in jobs:
        for kws in dictionary.values():
            for k in kws:
                if hit(k, j["_text"]):
                    all_cover[k.strip()] += 1
                    all_freq[k.strip()] += j["_text"].count(k.lower().strip())
    overall_top = [
        {"keyword": k, "cover": all_cover[k], "freq": all_freq[k]}
        for k in all_cover
    ]
    overall_top.sort(key=lambda x: (-x["cover"], -x["freq"]))

    return {"overall": overall, "per_tab": tab_result, "overall_top": overall_top}


def render_markdown(jobs, dictionary, result, growth):
    n = len(jobs)
    tab_n = {t: v["n"] for t, v in result["per_tab"].items()}
    lines = []
    lines.append("# 岗位技能与需求分析报告（基线期）\n")
    lines.append(f"- 采集日期：{DATE}　|　城市口径：北京　|　样本：去重后 **{n}** 个岗位")
    lines.append(f"- tab 命中（多对多）：" + "，".join(f"{k} {v}" for k, v in tab_n.items()))
    lines.append("- 说明：本期为第一期基线，尚无历史期可比，环比/上升衰退列保留待第二期回填；薪资受字体反爬影响未纳入统计。")
    lines.append(f"- 采集状态：三 tab（recommend/harmonyos/android）与两个检索组（ai_agent/fde）合并采集，清洗去噪后 **{n}** 个唯一岗位。")
    lines.append("- 检索组口径：ai_agent 为 AI/大模型/Agent 研发岗；fde 分「核心 FDE」（标题含 FDE/前沿·前线部署）与「相邻交付/解决方案/部署岗」两层，纯销售、投资出版、芯片/FPGA 原型验证、纯客户成功商务岗已剔除。")
    lines.append("- 口径：关键词区分「岗位覆盖数」（命中岗位数）与「词频」（出现次数）；纯英文短词按词边界匹配。\n")

    # 总体分组覆盖表
    lines.append("## 一、技能分组岗位覆盖\n")
    lines.append("| 技能分组 | 命中岗位数 | 覆盖率 | 代表关键词（覆盖:词频） |")
    lines.append("|---|---|---|---|")
    for group, info in result["overall"].items():
        reps = "、".join(f"{k['keyword']}({k['cover']}:{k['freq']})" for k in info["keywords"][:5])
        lines.append(f"| {group} | {info['hit_jobs']} | {info['cover_rate']*100:.1f}% | {reps} |")

    # 本地存量结构图
    lines.append("\n### 本地样本技能大类覆盖结构\n")
    lines.append("![本地样本技能大类覆盖结构](chart_structure.png)\n")

    # 外部增速对比（公开口径）
    lines.append("### 外部岗位招聘需求增速（公开报告口径）\n")
    lines.append(f"> {growth['note']}\n")
    lines.append("![岗位增速对比](chart_growth.png)\n")
    lines.append("| 方向 | 同比增速 | 来源与周期 |")
    lines.append("|---|---|---|")
    for g in sorted(growth["items"], key=lambda x: -x["growth_pct"]):
        lines.append(f"| {g['direction']} | +{g['growth_pct']:g}% | {g['source']} |")
    lines.append(f"\n> {growth['extra']}\n")

    # 全量高频 TOP20
    lines.append("\n## 二、全量高频关键词 TOP 20\n")
    lines.append("| 排名 | 关键词 | 覆盖岗位数 | 词频 | 覆盖率 |")
    lines.append("|---|---|---|---|---|")
    for i, k in enumerate(result["overall_top"][:20], 1):
        rate = f"{k['cover']/n*100:.1f}%" if n else "-"
        lines.append(f"| {i} | {k['keyword']} | {k['cover']} | {k['freq']} | {rate} |")

    # 分 tab TOP
    lines.append("\n## 三、分 tab 高频关键词\n")
    for tab, info in result["per_tab"].items():
        lines.append(f"### {tab}（n={info['n']}）\n")
        lines.append("| 关键词 | 覆盖岗位数 | 词频 |")
        lines.append("|---|---|---|")
        for k in info["top"][:15]:
            lines.append(f"| {k['keyword']} | {k['cover']} | {k['freq']} |")
        lines.append("")

    # 需求趋势观察（基于本期样本，结论可回溯 desc）
    lines.append("## 四、本期需求观察（基线）\n")
    top = result["overall_top"][:10]
    lines.append("本期样本中覆盖度靠前的方向：" + "、".join(f"{k['keyword']}" for k in top) + "。")
    lines.append("- Android/鸿蒙客户端主线扎实：Java、Kotlin、ArkTS、Jetpack、Framework、性能与稳定性仍是硬门槛；跨端（Flutter、React Native、跨平台）与 AI/大模型（Agent、大模型、LLM、Prompt）渗透明显。")
    lines.append("- 推荐页偏综合与协作：团队协作、解决方案、团队管理、成本与跨部门沟通出现频次高，反映该 tab 混入资深/管理与复合岗。")
    lines.append("\n> 注：趋势判断需结合第二期数据做环比；本期为首期全量基线。\n")
    return "\n".join(lines)


def main():
    jobs = load_clean()
    dictionary = load_dict()
    growth = load_growth()
    result = analyze(jobs, dictionary)

    REP.mkdir(parents=True, exist_ok=True)
    json.dump({"date": DATE, "sample": len(jobs), "result": result},
              open(REP / "analysis.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    md = render_markdown(jobs, dictionary, result, growth)
    open(REP / "岗位技能分析报告.md", "w", encoding="utf-8").write(md)

    print(f"分析完成: {len(jobs)} 岗位")
    print("总体 TOP10:", [(k["keyword"], k["cover"]) for k in result["overall_top"][:10]])
    print(f"报告 -> {REP / '岗位技能分析报告.md'}")


if __name__ == "__main__":
    main()
