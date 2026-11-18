#!/usr/bin/env python3
"""阶段看板：汇总 analysis / skill_map / clean / trend_growth 生成单文件 HTML 看板。

输出 reports/<日期>/岗位技能看板.html（数据内联，本地 file:// 可直接打开，不依赖外网 CDN）。
复采刷新链路：clean.py -> build_report.py -> make_charts.py -> build_curriculum.py -> build_dashboard.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "scripts"))
from snapshot import DATE, REPORT, RAW, PROC  # noqa: E402
REPORT_DIR = REPORT
DATA_RAW = RAW
DATA_PROC = PROC

SALARY_NOISE = re.compile(r"薪|元/月|^\s*[-–—\dKk·\.\s]+$|\d+\s*-\s*\d+\s*K")
# 去除私有区字体字符/符号/数字/K 后为空，视为薪资或占位噪音标签
_NOISE_STRIP = re.compile(r"[\uE000-\uF8FF\-–—\dKk·\.\s/]")


def _noise_tag(t):
    if SALARY_NOISE.search(t):
        return True
    return _NOISE_STRIP.sub("", t) == ""


def load_json(path, default):
    if path.exists():
        return json.load(open(path, encoding="utf-8"))
    return default


def main():
    analysis = load_json(REPORT_DIR / "analysis.json", {})
    skill_map = load_json(ROOT / "curriculum" / "skill_map.json", {"skills": []})
    clean = load_json(DATA_PROC / "jobs_clean.json", {"records": []})
    growth = load_json(ROOT / "config" / "trend_growth.json", {"items": [], "extra": ""})

    result = analysis.get("result", {})
    overall = result.get("overall", {})

    # 大类覆盖 + 展开技能
    categories = []
    top_skills = []
    for cat, v in overall.items():
        kws = v.get("keywords", [])
        categories.append({
            "name": cat,
            "hit_jobs": v.get("hit_jobs", 0),
            "cover_rate": v.get("cover_rate", 0),
            "keywords": kws,
        })
        for k in kws:
            top_skills.append({
                "keyword": k["keyword"], "cover": k["cover"],
                "freq": k["freq"], "category": cat,
            })
    top_skills.sort(key=lambda x: x["cover"], reverse=True)

    # 高优待学清单（去重优先级取高）
    high = []
    seen = set()
    for s in skill_map.get("skills", []):
        if s.get("priority") != "高":
            continue
        if s["skill"] in seen:
            continue
        seen.add(s["skill"])
        high.append({
            "skill": s["skill"],
            "category": s.get("category", ""),
            "demand_count": s.get("demand_count", 0),
            "freq": s.get("freq", 0),
            "prerequisites": s.get("prerequisites", []),
        })
    high.sort(key=lambda x: x["demand_count"], reverse=True)

    # 移动端 -> AI Agent 差距对照（现状判定基于移动端背景；覆盖数取自本期 AI/Agent 组 JD 实测）
    gap = [
        {"skill": "C++ / Kotlin / Swift 工程", "cover": 40, "status": "已有", "gap": "低", "phase": "可迁移", "action": "类型安全、错误处理、接口封装思维直接复用"},
        {"skill": "性能优化 / 稳定性", "cover": 109, "status": "已有", "gap": "低", "phase": "可迁移", "action": "对应服务延迟、超时、降级与线上排障"},
        {"skill": "Python 工程化", "cover": 142, "status": "部分", "gap": "中", "phase": "阶段1", "action": "虚拟环境、包管理、异步、类型注解、脚本与服务"},
        {"skill": "大模型 / LLM 基础概念", "cover": 179, "status": "待补", "gap": "高", "phase": "阶段1", "action": "Token、上下文窗口、温度、流式、模型选型与成本"},
        {"skill": "Prompt 工程", "cover": 78, "status": "待补", "gap": "高", "phase": "阶段1", "action": "结构化模板、约束、Few-shot、输出解析与兜底"},
        {"skill": "Agent / 智能体编排", "cover": 173, "status": "待补", "gap": "高", "phase": "阶段2", "action": "规划→工具→记忆→多步流转与终止条件"},
        {"skill": "RAG 检索增强", "cover": 120, "status": "待补", "gap": "高", "phase": "阶段2", "action": "切分→Embedding→入库→检索→重排→生成全链路"},
        {"skill": "向量检索 / Embedding", "cover": 50, "status": "待补", "gap": "高", "phase": "阶段2", "action": "相似度召回、Top-K、阈值；上手 Chroma / Milvus"},
        {"skill": "Function Calling / 工具调用", "cover": 66, "status": "待补", "gap": "高", "phase": "阶段2", "action": "工具 schema、模型决策调用、结果回填再生成"},
        {"skill": "LangChain / LlamaIndex", "cover": 51, "status": "待补", "gap": "中", "phase": "阶段2", "action": "用框架串链路；知道何时用原生 SDK 更轻"},
        {"skill": "MCP 协议", "cover": 44, "status": "待补", "gap": "中", "phase": "阶段2", "action": "接入标准工具/数据源，理解标准工具接口形态"},
        {"skill": "多模态", "cover": 65, "status": "部分", "gap": "中", "phase": "阶段2", "action": "图文/语音接入方式与适用边界"},
        {"skill": "后端 API 服务（FastAPI）", "cover": 30, "status": "部分", "gap": "中", "phase": "阶段3", "action": "把 Agent 包成 HTTP 接口，含模型校验与流式返回"},
        {"skill": "数据库 / Redis 缓存", "cover": 58, "status": "部分", "gap": "中", "phase": "阶段3", "action": "会话历史、上下文与检索结果缓存落地"},
        {"skill": "分布式 / 稳定性", "cover": 68, "status": "部分", "gap": "中", "phase": "阶段3", "action": "异步、限流、降级、超时、日志与监控"},
        {"skill": "Docker 部署", "cover": 27, "status": "待补", "gap": "中", "phase": "阶段3", "action": "写 Dockerfile，本地容器化跑通服务"},
        {"skill": "Go 语言", "cover": 48, "status": "部分", "gap": "低", "phase": "阶段3", "action": "按目标 JD 选择性补，非首要主线"},
    ]

    # 岗位明细（仅去重后，剔除薪资噪音标签）
    jobs = []
    for r in clean.get("records", []):
        if r.get("dup_of") or r.get("dropped"):
            continue
        tags = [t for t in r.get("tags", []) if t and not _noise_tag(t)]
        jobs.append({
            "title": r.get("title", ""),
            "company": r.get("company", "") or "匿名",
            "salary": r.get("salary", "") or "—",
            "location": r.get("location", "") or "—",
            "tags": tags[:5],
            "tabs": r.get("tabs", []),
            "role": r.get("group_role", ""),
            "url": r.get("url", ""),
        })

    overview = {
        "date": analysis.get("date", DATE),
        "city": "北京",
        "sample": clean.get("count", len(jobs)),
        "skill_count": len(top_skills),
        "high_priority": len(high),
        "category_count": len(categories),
    }

    payload = {
        "overview": overview,
        "categories": categories,
        "top_skills": top_skills,
        "high": high,
        "gap": gap,
        "jobs": jobs,
        "growth": {"items": growth.get("items", []), "extra": growth.get("extra", "")},
    }

    data_js = json.dumps(payload, ensure_ascii=False)

    html = TEMPLATE.replace("/*__PAYLOAD__*/", data_js)
    out = REPORT_DIR / "岗位技能看板.html"
    out.write_text(html, encoding="utf-8")
    print(f"看板 -> {out}")
    print(f"  岗位 {overview['sample']} | 技能 {overview['skill_count']} | 高优 {overview['high_priority']} | 大类 {overview['category_count']}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>北京岗位技能需求看板</title>
<style>
:root{
  --bg:#F5F6F8; --card:#FFFFFF; --line:#E6E8EC; --line-soft:#EEF0F3;
  --ink:#1A1D23; --ink-2:#5B616B; --ink-3:#8A9099;
  --accent:#2563A8; --accent-soft:#E8F0F9; --amber:#B45309; --amber-soft:#FBF1E4;
  --green:#2F7D5B; --radius:12px;
  --shadow:0 1px 2px rgba(20,24,32,.06),0 4px 14px rgba(20,24,32,.05);
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;line-height:1.55;font-size:15px}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 64px}
header.masthead{margin-bottom:24px}
header.masthead h1{font-size:26px;font-weight:700;letter-spacing:.2px}
header.masthead .sub{margin-top:6px;color:var(--ink-2);font-size:14px}
.meta-pill{display:inline-flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:13px;color:var(--ink-2)}
/* 指标卡 */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow)}
.kpi .num{font-size:30px;font-weight:700;font-variant-numeric:tabular-nums}
.kpi .lbl{margin-top:4px;color:var(--ink-2);font-size:13px}
/* 区块 */
section{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);padding:22px;margin-bottom:22px}
section h2{font-size:17px;font-weight:600;margin-bottom:4px}
section .hint{color:var(--ink-3);font-size:13px;margin-bottom:16px}
/* 大类条形 */
.cat-row{display:grid;grid-template-columns:150px 1fr 92px;gap:12px;align-items:center;padding:9px 0;border-top:1px solid var(--line-soft)}
.cat-row:first-of-type{border-top:none}
.cat-name{font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cat-bar-track{background:var(--line-soft);border-radius:6px;height:18px;overflow:hidden}
.cat-bar{height:100%;background:var(--accent);border-radius:6px}
.cat-val{text-align:right;font-variant-numeric:tabular-nums;font-size:13px;color:var(--ink-2)}
.cat-val b{color:var(--ink)}
/* 工具条 */
.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px}
.toolbar input,.toolbar select{border:1px solid var(--line);border-radius:8px;padding:8px 11px;font-size:14px;background:var(--card);color:var(--ink);min-width:0}
.toolbar input{flex:1;min-width:160px}
.toolbar select{cursor:pointer}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{border:none;background:var(--card);padding:8px 13px;font-size:13px;cursor:pointer;color:var(--ink-2)}
.seg button.on{background:var(--accent);color:#fff}
/* 表格 */
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:10px 12px;text-align:left;border-top:1px solid var(--line-soft);vertical-align:middle}
th{color:var(--ink-2);font-weight:600;font-size:12.5px;background:#FAFBFC}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.rank{color:var(--ink-3);font-variant-numeric:tabular-nums;width:34px}
.tag{display:inline-block;background:var(--line-soft);border-radius:6px;padding:2px 8px;font-size:12px;color:var(--ink-2);margin:2px 4px 2px 0}
.tag.src{background:var(--accent-soft);color:var(--accent)}
.tag.core{background:var(--accent);color:#fff}
.tag.adj{background:transparent;border:1px solid var(--line-soft);color:var(--ink-2)}
.job-title{font-weight:600}
.job-company{color:var(--ink-2);font-size:13px}
a.job-link{color:var(--ink);text-decoration:none}
a.job-link:hover .job-title{color:var(--accent)}
.muted{color:var(--ink-3)}
/* 高优卡片 */
.high-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.high-card{border:1px solid var(--line);border-radius:10px;padding:15px 16px}
.high-card .top{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.high-card .skill{font-weight:600;font-size:15px}
.high-card .cat{font-size:12px;color:var(--accent);background:var(--accent-soft);border-radius:6px;padding:2px 8px;white-space:nowrap}
.high-card .stats{margin-top:8px;display:flex;gap:16px;font-size:13px;color:var(--ink-2)}
.high-card .stats b{color:var(--ink);font-variant-numeric:tabular-nums}
.high-card .pre{margin-top:8px;font-size:12.5px;color:var(--ink-3)}
/* 差距对照 */
.badge{display:inline-block;border-radius:6px;padding:2px 9px;font-size:12px;white-space:nowrap}
.badge.have{background:#E7F2EC;color:var(--green)}
.badge.part{background:var(--amber-soft);color:var(--amber)}
.badge.miss{background:#FBECEC;color:#B23A3A}
.badge.gap-high{background:#FBECEC;color:#B23A3A}
.badge.gap-mid{background:var(--amber-soft);color:var(--amber)}
.badge.gap-low{background:#E7F2EC;color:var(--green)}
.gap-phase{font-size:12px;color:var(--ink-3);white-space:nowrap}
.gap-action{color:var(--ink-2);font-size:13px}
.gap-summary{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:14px;font-size:13px;color:var(--ink-2)}
.gap-summary b{color:var(--ink);font-variant-numeric:tabular-nums}
/* 增速 */
.growth-row{display:grid;grid-template-columns:170px 1fr 110px;gap:12px;align-items:center;padding:9px 0;border-top:1px solid var(--line-soft)}
.growth-row:first-of-type{border-top:none}
.growth-bar-track{background:var(--line-soft);border-radius:6px;height:18px;overflow:hidden}
.growth-bar{height:100%;background:var(--amber);border-radius:6px}
.growth-src{font-size:12px;color:var(--ink-3);margin-top:3px}
.note{margin-top:14px;padding:12px 14px;background:var(--amber-soft);border-radius:10px;font-size:13px;color:var(--ink-2)}
.count-line{color:var(--ink-3);font-size:13px;margin-top:10px}
footer{margin-top:30px;color:var(--ink-3);font-size:12.5px;line-height:1.7}
@media(max-width:860px){
  .kpis{grid-template-columns:repeat(2,1fr)}
  .high-grid{grid-template-columns:repeat(2,1fr)}
  .cat-row{grid-template-columns:110px 1fr 80px}
}
@media(max-width:560px){
  .kpis{grid-template-columns:repeat(2,1fr)}
  .high-grid{grid-template-columns:1fr}
  .wrap{padding:18px 14px 48px}
  .hide-m{display:none}
}
</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <h1>北京岗位技能需求看板</h1>
    <div class="sub">基于本期在招岗位 JD 采集分析，用于定位近期高频技术要求与待学技能方向</div>
    <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
      <span class="meta-pill" id="meta-date"></span>
      <span class="meta-pill">口径：岗位覆盖数 / 词频分列</span>
    </div>
  </header>

  <div class="kpis" id="kpis"></div>

  <section>
    <h2>技能大类覆盖结构</h2>
    <div class="hint">该大类出现在多少个岗位（覆盖岗位数）及覆盖率；跨大类岗位重复计入。</div>
    <div id="cats"></div>
  </section>

  <section>
    <h2>技能需求排行</h2>
    <div class="hint">按岗位覆盖数或词频排序，可按大类筛选、关键词搜索。</div>
    <div class="toolbar">
      <input id="skill-search" type="text" placeholder="搜索技能词，如 agent / kotlin / 性能…">
      <select id="skill-cat"></select>
      <div class="seg" id="skill-sort">
        <button data-key="cover" class="on">按覆盖岗位</button>
        <button data-key="freq">按词频</button>
      </div>
    </div>
    <table>
      <colgroup><col style="width:40px"><col><col style="width:150px" class="hide-m"><col style="width:90px" class="num"><col style="width:90px" class="num"></colgroup>
      <thead><tr><th>#</th><th>技能</th><th class="hide-m">大类</th><th class="num">覆盖岗位</th><th class="num">词频</th></tr></thead>
      <tbody id="skill-rows"></tbody>
    </table>
    <div class="count-line" id="skill-count"></div>
  </section>

  <section>
    <h2>高优待学清单</h2>
    <div class="hint">需求度最高的优先技能，可作为学习路线起点；前置技能用于安排先后顺序。</div>
    <div class="high-grid" id="high-grid"></div>
  </section>

  <section>
    <h2>移动端 → AI Agent 差距对照</h2>
    <div class="hint">现状基于移动端开发背景判定；覆盖数为本期 AI/Agent 组 JD 实测命中岗位数；阶段对应路线文档 curriculum/ai_agent_transition_roadmap.md。</div>
    <div class="gap-summary" id="gap-summary"></div>
    <table>
      <colgroup><col><col style="width:90px" class="num"><col style="width:80px"><col style="width:70px"><col style="width:90px"><col></colgroup>
      <thead><tr><th>技能项</th><th class="num">覆盖岗位</th><th>现状</th><th>差距</th><th>阶段</th><th>补齐动作</th></tr></thead>
      <tbody id="gap-rows"></tbody>
    </table>
  </section>

  <section>
    <h2>岗位明细检索</h2>
    <div class="hint">点击标题跳转 BOSS 原岗位页；可按关键词或来源 tab 筛选。</div>
    <div class="toolbar">
      <input id="job-search" type="text" placeholder="搜索岗位标题 / 公司 / 标签…">
      <select id="job-src"></select>
    </div>
    <table>
      <colgroup><col><col style="width:150px" class="hide-m"><col style="width:100px"><col style="width:90px" class="hide-m"><col style="width:150px"></colgroup>
      <thead><tr><th>岗位</th><th class="hide-m">公司</th><th>薪资</th><th class="hide-m">地点</th><th>标签 / 来源</th></tr></thead>
      <tbody id="job-rows"></tbody>
    </table>
    <div class="count-line" id="job-count"></div>
  </section>

  <section>
    <h2>外部岗位增速对照</h2>
    <div class="hint">来自外部公开报告口径，来源与统计周期不同，仅反映方向与量级；本地为单期快照，不计算环比。</div>
    <div id="growth"></div>
    <div class="note" id="growth-extra"></div>
  </section>

  <footer>
    数据口径：身份键 job_key 单批去重，跨期全量保留；薪资受站点字体反爬影响仅原样记录。<br>
    本看板由 scripts/build_dashboard.py 从 reports/analysis.json、curriculum/skill_map.json、data/processed 明细与 config/trend_growth.json 生成；复采后重跑构建链路即可刷新。
  </footer>
</div>

<script>
const DATA = /*__PAYLOAD__*/;
const BOSS = "https://www.zhipin.com";
const fmt = n => (n||0).toLocaleString("zh-CN");

/* KPI */
(function(){
  const o=DATA.overview;
  document.getElementById("meta-date").textContent = `快照 ${o.date} · ${o.city}`;
  const k=[
    {num:fmt(o.sample),lbl:"有效岗位（去重后）"},
    {num:fmt(o.skill_count),lbl:"识别技能词"},
    {num:fmt(o.high_priority),lbl:"高优技能"},
    {num:fmt(o.category_count),lbl:"技能大类"},
  ];
  document.getElementById("kpis").innerHTML=k.map(x=>`<div class="kpi"><div class="num">${x.num}</div><div class="lbl">${x.lbl}</div></div>`).join("");
})();

/* 大类条形 */
(function(){
  const max=Math.max(...DATA.categories.map(c=>c.hit_jobs),1);
  document.getElementById("cats").innerHTML=DATA.categories.map(c=>{
    const w=(c.hit_jobs/max*100).toFixed(1);
    const rate=(c.cover_rate*100).toFixed(1);
    return `<div class="cat-row">
      <div class="cat-name" title="${c.name}">${c.name}</div>
      <div class="cat-bar-track"><div class="cat-bar" style="width:${w}%"></div></div>
      <div class="cat-val"><b>${fmt(c.hit_jobs)}</b> 岗 · ${rate}%</div>
    </div>`;
  }).join("");
})();

/* 技能排行 */
const skillState={q:"",cat:"all",sort:"cover"};
window.skillState=skillState;
(function(){
  const sel=document.getElementById("skill-cat");
  const cats=["all",...new Set(DATA.top_skills.map(s=>s.category))];
  sel.innerHTML=cats.map(c=>`<option value="${c}">${c==="all"?"全部大类":c}</option>`).join("");
  sel.addEventListener("change",()=>skillState.cat=sel.value);
  document.getElementById("skill-search").addEventListener("input",e=>skillState.q=e.target.value.trim().toLowerCase());
  document.getElementById("skill-sort").addEventListener("click",e=>{
    const b=e.target.closest("button"); if(!b)return;
    document.querySelectorAll("#skill-sort button").forEach(x=>x.classList.remove("on"));
    b.classList.add("on"); skillState.sort=b.dataset.key; renderSkills();
  });
  renderSkills();
})();
function renderSkills(){
  let rows=DATA.top_skills.filter(s=>{
    if(skillState.cat!=="all"&&s.category!==skillState.cat)return false;
    if(skillState.q&&!s.keyword.toLowerCase().includes(skillState.q))return false;
    return true;
  });
  rows.sort((a,b)=>b[skillState.sort]-a[skillState.sort]);
  const top=rows.slice(0,60);
  document.getElementById("skill-rows").innerHTML=top.map((s,i)=>`
    <tr>
      <td class="rank">${i+1}</td>
      <td class="job-title">${s.keyword}</td>
      <td class="hide-m job-company">${s.category}</td>
      <td class="num">${fmt(s.cover)}</td>
      <td class="num">${fmt(s.freq)}</td>
    </tr>`).join("") || `<tr><td colspan="5" class="muted">无匹配技能</td></tr>`;
  document.getElementById("skill-count").textContent=`共 ${rows.length} 个技能词，展示前 ${top.length} 个`;
}
window.renderSkills=renderSkills;

/* 高优清单 */
(function(){
  document.getElementById("high-grid").innerHTML=DATA.high.map(h=>`
    <div class="high-card">
      <div class="top"><span class="skill">${h.skill}</span><span class="cat">${h.category}</span></div>
      <div class="stats"><span>覆盖 <b>${fmt(h.demand_count)}</b> 岗</span><span>词频 <b>${fmt(h.freq)}</b></span></div>
      ${h.prerequisites&&h.prerequisites.length?`<div class="pre">前置：${h.prerequisites.join("、")}</div>`:""}
    </div>`).join("");
})();

/* 差距对照 */
(function(){
  const rows=DATA.gap||[];
  const stCls={"已有":"have","部分":"part","待补":"miss"};
  const gpCls={"高":"gap-high","中":"gap-mid","低":"gap-low"};
  const cnt=s=>rows.filter(r=>r.status===s).length;
  const high=rows.filter(r=>r.gap==="高").length;
  document.getElementById("gap-summary").innerHTML=
    `<span>已有可迁移 <b>${cnt("已有")}</b></span><span>部分具备 <b>${cnt("部分")}</b></span><span>待补 <b>${cnt("待补")}</b></span><span>高差距项 <b>${high}</b></span>`;
  document.getElementById("gap-rows").innerHTML=rows.map(r=>`
    <tr>
      <td class="job-title">${r.skill}</td>
      <td class="num">${fmt(r.cover)}</td>
      <td><span class="badge ${stCls[r.status]||"part"}">${r.status}</span></td>
      <td><span class="badge ${gpCls[r.gap]||"gap-mid"}">${r.gap}</span></td>
      <td class="gap-phase">${r.phase}</td>
      <td class="gap-action">${r.action}</td>
    </tr>`).join("");
})();

/* 岗位明细 */
const jobState={q:"",src:"all"};
window.jobState=jobState;
(function(){
  const sel=document.getElementById("job-src");
  const srcs=["all",...new Set(DATA.jobs.flatMap(j=>j.tabs))];
  sel.innerHTML=srcs.map(s=>`<option value="${s}">${s==="all"?"全部来源":s}</option>`).join("");
  sel.addEventListener("change",()=>jobState.src=sel.value);
  document.getElementById("job-search").addEventListener("input",e=>jobState.q=e.target.value.trim().toLowerCase());
  renderJobs();
})();
function renderJobs(){
  let rows=DATA.jobs.filter(j=>{
    if(jobState.src!=="all"&&!j.tabs.includes(jobState.src))return false;
    if(jobState.q){
      const hay=(j.title+" "+j.company+" "+j.tags.join(" ")).toLowerCase();
      if(!hay.includes(jobState.q))return false;
    }
    return true;
  });
  const shown=rows.slice(0,80);
  document.getElementById("job-rows").innerHTML=shown.map(j=>{
    const tags=j.tags.map(t=>`<span class="tag">${t}</span>`).join("");
    const srcs=j.tabs.map(t=>`<span class="tag src">${t}</span>`).join("");
    const roleTag=j.role==="fde_core"?`<span class="tag core">核心FDE</span>`:(j.role==="fde_adjacent"?`<span class="tag adj">相邻交付</span>`:"");
    const href=BOSS+j.url;
    return `<tr>
      <td><a class="job-link" href="${href}" target="_blank" rel="noopener"><div class="job-title">${j.title||"—"}</div></a></td>
      <td class="hide-m job-company">${j.company}</td>
      <td>${j.salary}</td>
      <td class="hide-m muted">${j.location}</td>
      <td>${tags}${srcs}${roleTag}</td>
    </tr>`;
  }).join("") || `<tr><td colspan="5" class="muted">无匹配岗位</td></tr>`;
  document.getElementById("job-count").textContent=`共 ${rows.length} 个岗位，展示前 ${shown.length} 个`;
}
window.renderJobs=renderJobs;

/* 增速 */
(function(){
  const items=DATA.growth.items;
  const max=Math.max(...items.map(i=>i.growth_pct),1);
  document.getElementById("growth").innerHTML=items.map(i=>{
    const w=(i.growth_pct/max*100).toFixed(1);
    return `<div class="growth-row">
      <div><div>${i.direction}</div><div class="growth-src">${i.source}</div></div>
      <div class="growth-bar-track"><div class="growth-bar" style="width:${w}%"></div></div>
      <div class="cat-val"><b>+${i.growth_pct}%</b></div>
    </div>`;
  }).join("");
  document.getElementById("growth-extra").textContent=DATA.growth.extra||"";
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
