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
│   ├── analyze.py           # 技能/关键词统计（覆盖数 + 词频，分 tab）
│   ├── collect_list.py      # 列表采集（待实现）
│   ├── collect_detail.py     # 详情采集（待实现）
│   └── build_report.py       # 报告生成（待实现）
├── data/
│   ├── raw/<日期>/          # 每期原始快照（list / detail）
│   └── processed/           # 清洗后结构化明细（CSV + JSON）
├── reports/<日期>/          # 每期分析报告
├── curriculum/              # 教程映射设计（schema + 待学清单）
└── progress/checkpoint.json # 断点续采进度记录
```

## 快速开始

```bash
# 统计现有底稿（读取 data/raw 最新快照，回退 data/jobs_detail.json）
python3 scripts/analyze.py
```

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
