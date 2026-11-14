# BOSS直聘 三 Tab 岗位 JD 分析报告

- 采集时间：2026-11-14
- 样本口径：「推荐」「鸿蒙开发工程师(北京)」「Android(北京)」三个 tab 下最近岗位，去重后共 **29 个岗位**（推荐 12 / 鸿蒙 7 / Android 10），以北京为主，含少量上海及远程兼职岗。
- 数据底稿：`data/jobs_list.json`（列表元信息）、`data/jobs_detail.json`（完整 JD 描述）。
- 说明：薪资数字受站点字体反爬编码影响未纳入统计；技能与关键词均来自 JD 原文与职位标签。

---

## 一、样本概览

| Tab | 岗位数 | 方向特征 |
|---|---|---|
| 推荐 | 12 | 综合推荐，方向最杂：客户端 Android、Framework/Native、大数据架构、服务端全栈、座舱架构，以及采购总监、能源总经理、财务 BP、物流专家、知识工程咨询等非研发岗 |
| 鸿蒙 | 7 | 鸿蒙原生开发（ArkTS/ArkUI）为主，混跨端（RN/Flutter）与 AI 客户端；含 1 个鸿蒙质量/测试岗 |
| Android | 10 | Android 原生为基，叠加 Flutter/RN 跨端复用与 AI Coding；业务多出海、AI 对话/流式交互 |

> 关键观察：推荐 tab 里真正的一线研发岗约占一半，其余为资深管理、架构、解决方案与业务岗；看技术趋势应以鸿蒙、Android 两个 tab 为主样本。

---

## 二、JD 所需技能拆解

### 1. 编程语言与技术栈

| 语言/技术 | 主要出现场景 | 覆盖情况 |
|---|---|---|
| Kotlin | Android 客户端主力语言，协程/Flow、Compose | Android 岗高频 |
| Java | 传统 Android、后端/大数据架构 | 与 Kotlin 并列高频 |
| ArkTS / TypeScript | 鸿蒙原生应用开发、ArkUI 声明式 UI | 鸿蒙岗核心 |
| C / C++ | AOSP Native、Framework、HAL、座舱/嵌入式、音视频编解码 | 系统层/底层岗要求 |
| Dart / Flutter | 跨端 App 一套代码多端发布 | 跨端岗高频 |
| Objective-C / Swift | iOS 端，多为加分项 | 双端/跨端岗 |
| Python | 大数据分析、财务数据建模 | 少量后端/职能岗 |

### 2. Android 体系深度要求

**应用层**
- Jetpack、Jetpack Compose、Coroutines/Flow、ViewModel、状态管理
- 组件化、模块化、MVVM/MVC、依赖管理、导航与分层架构
- 网络通信、缓存、安全存储、推送与深链、生命周期与状态恢复

**系统层（Framework / Native，偏资深与车端）**
- AOSP 源码阅读/编译/裁剪、Android.bp/Android.mk、CMake、NDK 交叉编译
- Binder/AIDL、init 启动流程、SELinux、系统权限、SystemUI/Launcher/Settings
- AMS / WMS / PMS / IPackageManager 系统服务机制
- HAL / Vendor 层、Camera/Audio/Sensor/Wi-Fi/Radio/RIL 硬件适配

**性能与质量（几乎所有客户端岗的共性硬要求）**
- 性能优化：启动速度、渲染 FPS、内存占用、包体积、长列表渲染
- 稳定性治理：Crash / ANR / OOM / 卡顿 / 内存泄漏归因与闭环
- 兼容性：多机型、多系统版本、折叠屏/多窗口、三方依赖风险
- 工程质量：单元测试、UI 测试、自动化测试、CI/CD、监控与崩溃分析、代码审查

### 3. 鸿蒙生态技能

- 语言/UI：ArkTS、ArkUI、声明式 UI、状态管理
- 系统模型：Stage 模型、Ability / UIAbility / ExtensionAbility、生命周期、应用上下文
- 工程体系：DevEco Studio、Hvigor、HAP/HAR/HSP、签名打包、ArkWeb、分布式多设备协同
- 迁移能力：Android / iOS 向 HarmonyOS 迁移、一次开发多端部署
- 性能工具：DevEco Profiler、SmartPerf、HiTrace、性能基线与质量门禁

### 4. 跨端方案

- Flutter / Dart（含 Flutter Plugin、混合工程）
- React Native / React / TypeScript
- Kotlin Multiplatform、共享代码与平台专属代码组织
- 跨端接口与业务规则统一、双端构建/签名/分发/上架

### 5. AI / 大模型能力（本批样本最突出的新趋势）

**AI Coding 工具链**：Claude Code、Codex、Cursor、Manus 等被反复点名，部分岗位已把"深度使用 AI 编程工具"列为硬性要求。

**Agent 工程能力**
- 研发 Agent 建设：贯通编码、构建、模拟器/真机验证、自动化测试与日志反馈
- 多 Agent 编排：任务依赖、并发、交接与结果合并；规划 → 执行 → 观察 → 验证 → 纠错的开发 loop
- 上下文工程：Context、规则文件、Prompt 工程、记忆与状态管理、预算/幂等/中断恢复/失败回退
- MCP、自定义 Skill、工具接口设计与权限异常处理

**大模型与应用层**
- LLM 基本特性与边界：上下文窗口、幻觉、工具调用、不确定性、上下文污染
- 要求能审查 AI 生成代码，识别幻觉、过度设计、隐性缺陷
- AI 对话、流式输出（SSE）、Markdown/代码块渲染、多模态内容；RAG、知识图谱、本体建模（知识工程岗）

### 6. 音视频 / 实时通信（垂直方向）

- WebRTC：PeerConnection、DataChannel、ICE、STUN/TURN、DTLS/SRTP、RTP/RTCP、SDP
- 编解码：H.264/H.265、Opus/PCM、YUV、NALU、软硬编解码适配
- 传输与弱网：TCP/UDP、KCP、FEC、NACK、拥塞控制、码率自适应、卡顿/延迟/花屏处理
- 蓝牙 / BLE / Wi-Fi；SSE / WebSocket 长连接

### 7. 后端 / 大数据 / 云

- 分布式系统、实时计算、流批一体、湖仓一体（Hudi/Iceberg/Delta Lake）
- Spark / Flink / Hadoop / HBase、实时数仓、OLAP 引擎
- AWS 云；MySQL / PostgreSQL / MongoDB / Redis / 消息队列
- 高可用、高稳定、可观测平台、数据质量体系与 SLA

### 8. 汽车 / 座舱 / 嵌入式

- 智能座舱：安卓应用层（车控、空调氛围灯、蓝牙电话、语音、地图、手机互联、OTA、仪表 HMI、3D/SR 引擎）
- 中间层：QNX / Linux、安卓 Framework（音视频/调度/车控/通信/蓝牙 WIFI）、HAL、MCU-SWC、AutoSAR
- 算法方向：视觉算法、音频算法；传感器、Radar

### 9. 通用软技能与行业背景

- 通用：团队管理、跨部门/跨团队协作、方案设计、沟通推进、抗压与自驱、文档与规范沉淀
- 行业：金融、能源、物流/供应链、电商、出海商业化、订阅支付/广告、AI 产品

---

## 三、最近最火的关键词（按岗位覆盖度 + 趋势权重）

### TOP 榜

| 排名 | 关键词 | 热度解读 |
|---|---|---|
| 1 | **性能优化 / 稳定性治理** | 覆盖绝大多数客户端岗，启动、内存、渲染、Crash/ANR/OOM、兼容性是标配要求 |
| 2 | **架构设计（组件化/模块化/分层）** | 中高级岗的分水岭，强调架构演进、技术选型与工程体系 |
| 3 | **AI Coding / Agent / 大模型** | 本批最明显的增量趋势：从"用 AI 补全代码"升级到"编排研发 Agent、审查 AI 产出"，鸿蒙与 Android 岗均有体现 |
| 4 | **Kotlin / Java** | Android 双语言底座，Kotlin 占比上升 |
| 5 | **跨端（Flutter / React Native）** | 一套代码覆盖 iOS/Android/鸿蒙，跨端复用是降本主线 |
| 6 | **鸿蒙 HarmonyOS / ArkTS** | 原生生态岗位成型，ArkUI、Stage 模型、DevEco 工具链成为明确门槛 |
| 7 | **团队协作 / 跨部门沟通** | 通用软技能，资深与管理岗权重更高 |
| 8 | **兼容性适配** | 多机型、多版本、折叠屏、弱网与后台切换场景 |
| 9 | **自动化测试 / CI/CD** | 与 AI 研发闭环绑定，强调测试先行、质量门禁与发布自动化 |
| 10 | **音视频 / WebRTC** | 垂直高热方向，集中在系统层、车端、直播连麦/云手机场景 |

### 分 tab 热点

- **推荐**：架构、性能、团队管理与解决方案能力权重高；AI 主要出现在架构师、技术 leader、知识工程等岗位；技术广度优先于单一深度。
- **鸿蒙**：ArkTS/ArkUI 原生能力 + AI Agent 工作流 + 性能稳定性三件套；质量岗也要求鸿蒙原生理解与自动化框架建设。
- **Android**：Kotlin/Java 原生打底，Flutter/RN 跨端复用；AI Coding 成为常见加分乃至硬性要求；业务热点是出海应用、AI 对话与流式交互、多模态内容。

### 值得关注的信号

1. **"AI 原生开发者"正在成为新岗位画像**：不只要求会用 AI 工具，更要求能设计 Agent 工作流、管理上下文与工具调用、并对 AI 生成代码做质量把关。
2. **跨端 + 鸿蒙并行**：企业既在用 Flutter/RN 做跨端降本，也在单独储备鸿蒙原生迁移能力，两条线同时招人。
3. **性能与稳定性是长期硬通货**：无论原生、跨端还是鸿蒙，启动/内存/渲染/崩溃治理都是高频硬性条款。
4. **系统层/车端岗位门槛高**：AOSP、Framework、HAL、C/C++、音视频协议栈等要求集中在资深与智能座舱方向，竞争相对小、技术壁垒高。

---

## 四、后续可扩展方向

- 扩大样本量（每 tab 翻 2–3 页）并按薪资、年限、学历做交叉统计；
- 对 JD 做技能标签结构化抽取，沉淀为可复用的岗位技能库；
- 结合你的技术栈（Android/Kotlin、跨端、AI 工程）输出岗位匹配度与差距清单。
