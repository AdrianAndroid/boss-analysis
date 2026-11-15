# BOSS 岗位分析 v1 工作计划（PLAN）

> 本文件是执行计划与进度总表，与 `SPEC.md`（口径规范）配合使用。SPEC 定"规则"，PLAN 定"做什么、做到哪、怎么续作"。
> 版本：v0.1 ｜ 建立日期：2026-11-15 ｜ 状态：待确认决策项后开工

## 一、目标与范围

### 本轮目标
1. 「推荐 / 鸿蒙开发 / Android」三个 tab，每个 tab 拉取 **1000 条以内**岗位，字段尽量全。
2. 采集岗位与公司的详细信息：岗位标题、薪资、地点、经验、学历、技能标签、JD 全文；公司名、融资阶段、规模人数、行业。
3. 提取热门关键词，总结近期岗位所需技能/能力需求，输出带**表格和趋势**的分析结果。
4. 工程结构符合 GitHub 私有仓库上传要求；目录分类清晰；敏感信息不入库。
5. 预留周期性复采与跨期趋势对比能力；设计"技能 → 学习教程"的映射结构（本轮不写教程正文）。

### 本轮不做
- 教程正文编写（仅做映射 schema 与待学技能清单）。
- 自动投递、打招呼、刷量、绕过风控/验证码等账号动作。

## 二、现状盘点

| 已有产物 | 位置 | 说明 |
|---|---|---|
| 样本数据 | `data/jobs_list.json`、`data/jobs_detail.json` | 29 条去重岗位，旧 schema（按 URL 去重），阶段 3 回填 `job_key` |
| 分析脚本 | `analyze.py` | 技能词频统计雏形，词典待迁移到 `config/` |
| 首版报告 | `JD分析报告.md` | 关键词 TOP10 与信号结论 |
| 规范 | `SPEC.md`（v0.2）、`.gitignore` | 口径、身份键、采集红线、敏感信息排除 |

## 三、目标目录结构

```
boss-analysis/
├── README.md               # 项目说明、快速开始、数据口径（待补）
├── SPEC.md                 # 规范（已存在）
├── PLAN.md                 # 本计划 + 进度总表
├── .gitignore              # 已存在
├── config/
│   ├── tabs.json           # 目标 tab、关键词、城市、每批上限
│   └── skills_dict.json     # 技能/关键词词典（替代脚本内硬编码）
├── scripts/
│   ├── collect_list.py      # 列表分页采集
│   ├── collect_detail.py     # 详情全字段采集
│   ├── analyze.py            # 技能/关键词统计（由根目录迁入）
│   └── build_report.py       # 生成报告表格与趋势
├── data/
│   ├── raw/<日期>/           # 每期原始快照：jobs_list.json / jobs_detail.json
│   └── processed/            # 清洗后结构化明细（CSV + JSON）
├── reports/<日期>/           # 每期报告：关键词表、需求趋势表、明细 CSV
├── curriculum/                # 教程映射设计（本轮仅 schema + 待学清单）
│   └── skill_map.schema.json
└── progress/
    └── checkpoint.json        # 断点续采进度记录
```

## 四、采集字段清单（对齐 SPEC 3.2）

**岗位信息**：`job_key`、`tab`、`collected_at`、`source_url`、`title`、`salary`、`location`、`experience`、`education`、`tags[]`、`jd_desc`、`welfare[]`（可取则记）。

**公司信息**：`company.name`、`company.stage`（融资阶段）、`company.size`（规模人数）、`company.industry`（行业）。

**跨期状态**：`period_status`（持续在招 / 新发布 / 重新发布 / 已下架），分析层标注，采集期留空。

> 身份键 `job_key` 规则、单批去重与跨期保留口径，见 `SPEC.md` 3.3。

## 五、阶段任务与进度

状态枚举：`pending` 未开始 ｜ `in_progress` 进行中 ｜ `done` 完成 ｜ `blocked` 受阻

| 阶段 | 任务 | 产出 | 状态 | 进度记录要点 |
|---|---|---|---|---|
| 0 | 工程化与规范对齐：建目录、补 README、词典迁入 config、SPEC 补全字段与周期口径 | 目录骨架、config、README | done | 各目录就绪；词典 9 组 |
| 1 | 列表采集：三 tab 分页滚动，提取标题/链接/标签/地点，按 `job_key` 单批去重 | `data/raw/<日期>/lists/<来源>.json`、`list_merged.json` | done | 推荐 385 / 鸿蒙 450 / Android 450；URL 去重 1063 |
| 2 | 详情采集：逐个打开详情，采全岗位 + 公司字段，限速访问，断点续采 | `data/raw/<日期>/jobs_detail.json`、`companies.json` | in_progress | 97/1063；JD/公司/薪资齐全；公司主页待补阶段/规模/行业 |
| 3 | 清洗结构化：文本清洗、字段拆分、缺失值标记、旧样本回填 `job_key`；校验条数/空字段率/重复率 | `data/processed/` 明细 CSV/JSON | pending | 校验指标、异常记录 |
| 4 | 技能与关键词分析：岗位覆盖数 + 词频，分 tab 对比，分组统计 | 分析中间结果 | pending | 词典命中覆盖、分组结果 |
| 5 | 趋势与需求总结：当期基线表、近期高频硬技能、增量新趋势、稀缺方向、岗位分层；预留跨期环比列 | `reports/<日期>/` 报告（表格） | pending | 报告章节完成度、表格清单 |
| 6 | 教程映射设计：定义 skill_map schema，从 JD 抽取待学技能清单填入；不写教程正文 | `curriculum/` 映射表 | pending | 待学技能数、优先级分布 |
| 7 | Git 归档：init、首次提交、核对无敏感文件、关联私有仓库并推送 | 私有仓库远端 | pending | 提交记录、入库文件清单核对 |
| 8 | AI/FDE 检索组调研：实测站内关键词检索 URL、关键词召回与噪声；固化配置与口径 | `config/search_groups.json`、`docs/ai_fde_research.md` | done | URL 规则已验证；FDE/Agent 岗位可见 |
| 9 | AI/FDE 检索组全量采集与去噪：列表+详情采集，按 drop_rules 剔噪，FDE 分核心/相邻两层 | `data/raw/2026-11-15/lists/{ai_agent,fde}.json`、`data/processed/` | done | ai_agent 110、fde 148（核心 15 + 相邻 132）；空 JD/标题 0 |

## 六、进度记录机制（断点续作）

- `progress/checkpoint.json` 字段：
  - `plan_version`、`updated_at`、`current_phase`
  - 每阶段：`status`、`started_at`、`finished_at`、`note`
  - 采集进度：各 tab `collected` / `target`、`batch`、`last_url`、`failed[]`、`skipped[]`
  - 数据校验：`total`、`duplicates`、`empty_fields`、`company_complete_rate`
- 脚本启动先读 checkpoint，从断点继续，已采 URL/`job_key` 自动跳过，不重复访问。
- 对话内任务清单与 checkpoint 保持同步；每完成一阶段更新状态与时间戳。

## 七、周期性迭代设计（需求 7、8）

- 每期数据独立存 `data/raw/<日期>/`、报告存 `reports/<日期>/`，历史不覆盖。
- 趋势脚本跨期聚合：技能占比变化、新增/衰退关键词、岗位量与薪资区间变化。
- 第一期只建基线；第二期起算环比（上升/衰退/新词），报告表格先留环比列。
- 复采节奏（每周 / 每两周）参数化日期即可重复跑。

### 本期已验证的复采流程（下次照此续作）

1. **列表**：内置浏览器登录后进入 `/web/geek/jobs`，依次切「推荐 / 鸿蒙开发工程师(北京) / Android(北京)」或按检索组 URL 取词，滚动触顶后页面内规范化提取卡片（URL 去 query、过滤 footer/相似职位链接），按来源落 `data/raw/<日期>/lists/<来源>.json`。
2. **合并去重**：本地脚本按 URL 合并三 tab 为 `list_merged.json`，记录每条出现的 `tabs[]`；跨 tab 同岗位详情只采一次。
3. **详情断点续采**：`scripts/detail_store.py` 维护待采队列与已采记录，按 URL 跳过；每条间隔 1.2–1.8s 随机抖动、不并发；遇登录/验证 URL 即停并交人工。详情取标题/公司/薪资/JD 全文；公司主页链接入 `companies.json`。
4. **公司补充字段**：按公司主页去重访问，回填融资阶段/规模人数/行业；匿名岗无主页链接则留空，不编造。
5. **跨期对比**：新一期快照独立目录；分析层按 `job_key`（辅以公司+标题+地点+JD 相似度）关联历史，标注 `持续在招 / 新发布 / 重新发布 / 已下架`，不物理合并历史底稿。
6. **复采前置**：若内置浏览器登录态失效，先扫码登录；不导出/不入库 cookie 与会话。Playwright 本地脚本骨架保留，作为后续脱离内置浏览器的复采工具。

## 八、教程映射设计（需求 9，本轮不写正文）

`curriculum/skill_map.schema.json` 字段：

| 字段 | 说明 |
|---|---|
| `skill` | 技能/技术名 |
| `category` | 分组（语言/框架/系统层/AI/音视频…） |
| `demand_count` | 本期出现岗位数 |
| `priority` | 高/中/低（按需求度 + 与现有技术栈差距） |
| `prerequisites` | 前置技能 |
| `outline_placeholder` | 教程大纲占位（本轮空） |
| `resource_status` | `todo / drafting / done` |
| `source_jobs` | 来源岗位链接留痕 |

## 九、风控与合规红线（详见 SPEC 第 4 节）

- 限速访问（间隔 ≥1.5s，可随机化），不并发刷量；遇风控/验证页即停，交人工处理。
- 不读取/导出 cookie、token、登录态；`auth/` 等目录禁止入库。
- 不绕过人机校验、不伪造指纹；采集内容仅个人分析使用，不二次公开传播。

## 十、风险与取舍

1. **1000 条/tab 是上限目标**：列表翻页深度与风控可能达不到，实际以可翻到的上限为准；触顶或拦截时安全停下并记录。
2. **全字段采集耗时较长**：详情逐条访问，分批跑，靠 checkpoint 断点续采，不要求一次跑完。
3. **趋势第一期仅基线**：环比/上升衰退词需第二期数据，本期表格先留列。
4. **公司字段可能缺失**：外包/兼职岗常缺规模/行业，按缺失值标记，不编造。
5. **薪资字体反爬**：文本原样记录，不做解码统计；如需解码另立方法说明。

## 十一、待确认决策项（开工前需拍板）

| # | 决策点 | 候选 | 结论 |
|---|---|---|---|
| 1 | 采集/分析脚本技术栈 | A. Node 22 + Playwright（采集）+ Python（分析）；B. 全 Python | **本期：内置浏览器采集 + Python 分析**；Playwright 骨架留作后续周期复采工具 |
| 2 | 报告形态 | Markdown 表格 / 追加 Excel / HTML | 默认 Markdown 表格；是否加 Excel/HTML 待补 |
| 3 | 触顶与风控策略 | 保留已采部分继续 / 立即全停 | 保留已采部分继续；遇真实验证/登录拦截即停交人工 |
| 4 | Git 归档时机 | 工程初始化后先推一版 / 分析完成后再推 | 分析完成后统一归档私有仓库 |

## 十二、变更记录

| 日期 | 版本 | 变更内容 |
|---|---|---|
| 2026-11-15 | v0.1 | 初版工作计划：阶段任务、目录、字段、进度机制、周期与教程映射设计 |
