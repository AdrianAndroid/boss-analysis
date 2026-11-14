# BOSS 岗位分析

采集 BOSS 直聘「推荐 / 鸿蒙开发 / Android」等 tab 下的岗位 JD，拆解技能、统计热门关键词、输出带表格与趋势的分析结论，并为后续"技能 → 学习教程"沉淀映射结构。

## 目录

```
boss-analysis/
├── README.md               # 本文件
├── SPEC.md                 # 口径规范（身份键、去重、采集红线、schema）
├── PLAN.md                 # 工作计划与阶段进度
├── config/
│   ├── tabs.json           # 目标 tab、城市、采集上限、限速参数
│   └── skills_dict.json     # 技能/关键词词典
├── scripts/
│   ├── detail_store.py      # 详情落盘 / 断点队列 / job_key 生成
│   ├── clean.py              # 清洗结构化、单批去重、校验指标
│   ├── build_report.py       # 技能/关键词统计与 Markdown 报告生成
│   ├── build_curriculum.py   # 技能→教程映射清单生成
│   ├── analyze.py            # 旧版词频统计（兼容保留）
│   ├── collect.mjs          # Playwright 本地复采骨架（规划项，未启用）
│   └── lib/                  # Playwright 骨架复用的配置/身份键/存储模块
├── data/
│   ├── raw/<日期>/          # 每期原始快照（list / detail / companies）
│   └── processed/           # 清洗后结构化明细（CSV + JSON）
├── reports/<日期>/          # 每期分析报告（analysis.json + Markdown）
├── curriculum/              # 教程映射设计（schema + 待学清单）
└── progress/checkpoint.json # 断点续采进度记录
```

## 快速开始

```bash
# 1) 清洗去重：raw 底稿 -> processed 明细（含校验指标）
python3 scripts/clean.py

# 2) 技能/关键词分析 + 生成 Markdown 报告
python3 scripts/build_report.py

# 3) 生成技能→教程映射清单（不写教程正文）
python3 scripts/build_curriculum.py
```

> 本期采集走内置浏览器（已登录、免扫码、断点续采）；`collect.mjs` 为后续脱离内置浏览器的周期复采骨架，首次运行需人工扫码，其登录态目录 `auth/` 已被 gitignore。

## 数据口径（摘要，详见 SPEC.md）

- **身份键 `job_key`**：优先岗位编号；缺失时用「公司 + 标题 + 地点 + 经验」归一化哈希。
- **去重**：单批内按 `job_key` 去重；跨期全量保留，不做物理合并；同一岗位不同时间重发不算重复。
- **跨期状态**：持续在招 / 新发布 / 重新发布 / 已下架，分析层标注。

## 风控与合规

- 采集限速（间隔 ≥1.5s，带随机抖动），不并发刷量；遇风控/验证页即停，交人工处理。
- 不读取、不导出 cookie、token、登录态；`auth/` 等目录已在 `.gitignore`，禁止入库。
- 采集内容仅用于个人岗位分析，不二次公开传播。

## 周期迭代

每期数据独立存 `data/raw/<日期>/` 与 `reports/<日期>/`，历史不覆盖；第二期起可做跨期环比（上升/衰退/新词）。
