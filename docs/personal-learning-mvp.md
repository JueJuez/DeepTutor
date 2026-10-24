# PDF / EPUB 个人学习助手：验证与开发计划

更新：2026-10-25。状态：O0 完成；O1/O2/O3 有界交付；R1 事务快照与自动补偿已实施并补完整合验证（1344 passed，见执行记录 13）；**R2 持久预算门禁、R3 底层 HTTP 计量、R4 旧辅助条件未知语义已实施并离线验证（见执行记录 13）**。预算门禁覆盖 factory 与 agentic 两个入口、默认关闭，未覆盖入口与费用估算边界逐项列明；O3 范围外项保留。B0/B1 真实模型闭环、B3 语义审核、B4 未覆盖项及 B5 延迟试用仍待验，不代表整体 MVP 完成。开发分支为 `codex/learning-offline`，本地隔离 worktree 为 `C:\Users\O1830\.codex\worktrees\learning-offline\DeepTutor`；R1–R4 改动（含测试与本文）已按用户指令提交并推送至 fork，提交与远端 SHA 以实际 Git 核对及 `fork/codex/learning-offline` tracking ref 为准，接手先核对、不重置或覆盖。原工作区数据和未提交计划保留。

本文是本地个人学习扩展的需求、任务状态与新会话交接真源，由项目使用者和后续开发会话共同维护。每批结束更新本文中的证据、缺口和下一步；不另起重复任务清单。

## 1. 目标与方向

目标：从书籍学习中形成可核对的理解、独立应用和延迟保持证据，而不仅是摘要、聊天记录或模型给出的掌握分。

需求来自关联会话「梳理 PDF 和 EPUB MVP 欠项」（`01a16c1c-8a3d-7170-907b-54e62462a4f6`）。用户现已拉取 DeepTutor，希望在此沉淀计划并由新会话继续开发。

当前工作方向是**优先验证 DeepTutor，再在既有模块中补缺口**。克隆仓库不等于已经确认其适配全部需求；B0/B1 若发现关键阻碍，应记录证据、修复成本与替代方案，再与用户讨论基准选择。

此前 Open Notebook 的 `docs/7-DEVELOPMENT/personal-learning-mvp.md` 是需求历史来源。本文承接其学习质量与数据保护要求；其 SurrealDB、worker、Source 扩展和安装命令不适用于此仓库，不作为本项目执行步骤。旧文档留在旧仓库，无需迁移代码或数据库。

### 本期边界

- 个人本机使用、云端模型 API；优先中文学习交互。
- 必须覆盖文字型 PDF 和无 DRM EPUB。PDF 区分物理页与印刷页；EPUB 按 spine 顺序定位章节、段落，不虚构固定页码。
- 先贯通一本书的一个小单元，再完成 PDF/EPUB 两种输入的全链验证。
- 扫描/混合页、复杂公式图表或双栏抽取不可靠时，提示并阻止受影响单元进入出题评估。OCR 与完整多模态理解后续再做。
- 加密、损坏、DRM 文件明确失败；暂不新增 MOBI/AZW、网页、课程、视频、手机推送、多用户功能。
- 采用原书阅读与 Mastery Path；不要求先用 Books 重新生成整本教材，不批量重写书籍。

## 2. 当前基线与证据强度

初始基线为 `a31d8262`（提交说明 `release: v1.6.15`）；初建计划时只做了关联会话阅读和有限源码核对。下表保留该次初始证据，不代表后续没有实施。当前交接基线为 `cfb3e8d1`，实际修复与验证见第 8 节，下一阶段任务见第 9 节；新会话须重新核对现场。这些本地快照不代表上游最新版本。

| 现有入口 | 本地证据 | 初始核对时的结论 |
|---|---|---|
| 原书阅读与引用 | [reading/models.py](../deeptutor/reading/models.py)、[extract.py](../deeptutor/reading/extract.py)、[reading API](../deeptutor/api/routers/reading.py) | 已有统一 locator 和 PDF/EPUB 数据模型；顺序、段落定位、重抽取稳定性及浏览器跳转待验证 |
| 学习路径与评估 | [learning/models.py](../deeptutor/learning/models.py)、[semantic_assessment.py](../deeptutor/learning/semantic_assessment.py)、[mastery API](../deeptutor/api/routers/mastery_path.py) | 已有实现入口；不能列为全部待新建，也不能据此宣称评分可靠 |
| 作答与复习状态 | [assessment.py](../deeptutor/learning/assessment.py)、[scheduler.py](../deeptutor/learning/scheduler.py)、[storage.py](../deeptutor/learning/storage.py) | 已有持久评估事件、调度和队列结构；答案保存、覆核重算、并发幂等、重启恢复待专项核验 |
| 学习与阅读界面 | `web/components/reading/`、`web/components/space/learning/`、`web/lib/mastery-session.ts` | 应复用现有界面；完整用户流程待浏览器验证 |
| 配置与费用 | [runtime_settings.py](../deeptutor/services/config/runtime_settings.py)、根 AGENTS.md | 使用 JSON settings 与现有调用链；usage 不等于已具备预算硬限制 |
| 已有测试 | `tests/reading/`、`tests/capabilities/test_mastery_semantic_assessment.py`、`deeptutor/learning/tests/`、`web/tests/` | 测试文件存在；本次未执行，不能报告通过 |

后续状态统一使用：未核验／已有实现待验证／确认缺口／修复中／离线通过／真实调用通过／语义审核通过／用户试用通过。不把这些状态合并为一个“完成”。

## 3. 核验优先级与最小行为契约

以下均是验收要求，**并非已经确认 DeepTutor 缺失**。B1 逐项给出现有代码、测试、实际行为和差距；已有能力通过后直接复用。

| 核验项 | 必须观察到的行为 |
|---|---|
| 来源与版本 | PDF 页、EPUB 章节路径与片段可回到原文；重抽取后旧题和旧作答仍有可追溯证据，不混用不同版本文本 |
| 抽取质量 | 可预览内容与单元边界；空文本、乱序、缺页和上下文截断明确可见；不依据残缺材料评价完整单元 |
| 教学目标 | 学习目标可编辑，关联概念、条件、反例或步骤；概念知识不能因“不适合做方法卡”而漏掉 |
| 练习答案隔离 | 独立作答前不向客户端下发参考答案、评分要点或正确选项标记；检查网络响应与状态存储，不能只隐藏界面 |
| 作答证据 | 保存原始回答、题目版本、目标、来源、时间、提示/看答案等辅助条件与评估版本；刷新、重启后能恢复 |
| 评分与覆核 | 基于原文和题目要求接受合理等价表达；错误、自信表述、提示后修正不能冒充独立掌握；用户更正保留原评估、理由与采用版本 |
| 掌握展示 | 分开呈现理解、应用、辅助作答和延迟证据；阅读完成、聊天轮数、自评“掌握”不能替代独立作答证据 |
| 复习一致性 | 失败、浏览、重复提交不推进日程；同一作答事件最多生效一次；覆核能重算状态与日程；显示真实间隔 |
| 费用与失败 | 单元按需生成、上下文/输出/并发/重试有上限；未知 usage 不填 0；超预算暂停新调用；超时保留可能计费的不确定性 |
| 数据生命周期 | 导出含原始作答、评估、版本和引用；删除范围明确；升级前备份且能恢复，不覆盖已有配置或学习记录 |

### 教学与复习建议

每单元先少量目标与题目，包含自己的话解释和至少一个新情境应用任务；不先建整本题库。即时后测与延迟复测用同目标的不同题，并保留全部原始输出供检查。

“初步掌握”至少需要无提示解释和新情境应用均达到该目标的具体要求；“有延迟保持证据”还需要至少 7 天后的不同任务。提示后答对属于巩固证据，不能追记为独立通过。闭卷依赖用户遵守和自报，应用无法证明用户没有在别处查阅。

此前候选量表为 0–4 分、候选复习间隔为 1/3/7/14 天，都是产品启发式，不是已确认的最优规则。**先核对现有 scheduler 与掌握策略，不为套旧方案重写算法。** 若现有规则满足证据、可解释性与幂等要求即可沿用，并在本文记录实际规则；存在冲突时提出最小调整及数据兼容方案。

## 4. 技术实施约束

1. 先读 [AGENTS.md](../AGENTS.md)、[CONTRIBUTING.md](../CONTRIBUTING.md) 和改动模块的约定，重新核对分支、提交和未提交修改。功能开发按仓库约定隔离工作区，保护本计划等已有改动。
2. 复用 `deeptutor/reading`、`deeptutor/learning`、既有 capability、API、前端与持久化层；先核对真实 storage/schema，再决定增量字段与迁移，不另建学习引擎或引入 Open Notebook 的数据库方案。
3. CLI、WebSocket、SDK 沿用 durable turn application service；不通过新直连调用绕开事件持久化、现有模型配置和 UsageTracker。
4. 运行设置在 `data/user/settings/*.json`，项目根 `.env` 被忽略；按现有设置入口配置，禁止照搬旧项目 `.env` 启动方式。密钥不写本文、测试 fixture 或公开日志。
5. 新状态优先建在现有事件与投影上；版本、幂等键和覆核关联需真实存储测试，不能只在提示词中约束。外部模型调用不能承诺恰好执行一次。
6. 保留失败分类和已有有效结果，数据库保存失败不自动重调模型；自动重试次数先核对现状再设明确上限，鉴权/配置错误不盲重试，不静默换模型。
7. 涉及新增用户文案遵循现有 i18n；改契约时沿用项目生成流程，不手写第二份接口定义。
8. 借鉴本地 `D:\Code\Skills\cangjie-skill` 的方法卡与覆盖审计时重新核对实现。本期只按需借鉴原文、解释、应用、步骤、边界结构，不安装整套蒸馏管线，不把 Agent 会用当作学习者学会。

## 5. 分批实施与放行

| 批次 | 工作与交付物 | 放行证据 | 当前状态 |
|---|---|---|---|
| B0 本机运行基线 | 检查 Python/Node/包管理器、端口、已有配置与数据；按本仓库安装启动；配置一个主模型；导入一个 PDF 和一个 EPUB | 原书可读，一次小范围模型交互可用；记录运行命令、依赖障碍、usage/未知项和原有缺陷 | 部分完成：安装启动、自制样本及真实 PDF/EPUB 导入定位已验证；主模型与真实交互待额度恢复 |
| B1 现成闭环与差距核验 | 各选一个单元，走阅读→学习路径→独立回答→应用反馈→到期复习；逐项填第 3 节证据；读 scheduler、存储与相关测试 | 每项明确“复用／需修复／未知”；有实际复现和最小修复范围，不能仅引用 README | O1 已做真实 SQLite、接口和跨进程专项；R1 新记录自动补偿已实施，无快照历史记录仍有边界，真实单元闭环待模型就绪 |
| B2 来源与作答可信链 | 仅修复已确认的定位、版本、异常材料、答案隔离和原始作答保存问题 | 一个单元引用可靠；提交前网络响应无答案；刷新/重启恢复；错误与缺证据不能升级掌握 | 既有三项修复保留；O1 追加修复 reading 答案键隔离，恢复与并发专项离线通过；真实流程待验 |
| B3 反馈、掌握与复习 | 补齐实际缺失的语义评估边界、辅助条件、覆核、事件幂等和日程一致性 | 正确/错误/部分正确/等价表达/不知道均经审核；并发与重复提交、覆核重算、时区测试通过 | O1 修复并发初始化、辅助条件投影并验证重复覆核；R1 覆核自动补偿已实施；R4 将旧记录辅助条件收紧为显式"未知"、不被刷新/重试升级为独立通过。语义质量待真实闭环 |
| B4 费用与数据保护 | 补齐预算检查、失败恢复、导出删除、备份恢复和升级兼容中的实际缺口 | 已支出加在途预留约束新任务；重试有界；未知费用可见；恢复能找回作答与引用 | O2 修复无关图片降级重调与通用摘要未知价格；O3 提供选定存储恢复。R2 已实现可配置的持久预算门禁（请求/Token/费用上限+在途预留+保守结算，默认关闭，覆盖 factory 与 agentic 入口，见执行记录 13）；R3 记录底层 HTTP 尝试数。未覆盖入口（fetch_models 等）、费用估算依赖静态价格表、全部导出删除/升级兼容仍未完成 |
| B5 综合验收与个人试用 | 扩展样本，执行完整浏览器/接口流程、语义审核和真实延迟复测 | 技术、语义和个人试用分别给证据；未到至少 7 天复测日期保留待验证 | 未开始 |

B0/B1 发现可小范围修复的启动问题可在当前批处理并记录，不必停下来逐项请求许可；涉及更换方向、明显扩大范围或增加未约定付费服务时再讨论。没有真实材料、模型或预算时继续源码审计、自制样本与离线检查，真实调用保留待验证，不用 mock 冒充。

### B0 的具体起步顺序

1. 记录实际版本与数据位置，检查现有服务和依赖；不删除、不重置，不默认克隆后没有旧数据。
2. 按当前 README、CONTRIBUTING、`pyproject.toml` 与 `web/package.json` 选择最低必要安装集合。仅为书籍学习不应无条件安装 Manim、视频或全部可选项。
3. 在隔离环境安装源码依赖并启动后端和前端，记录实际成功命令；根 AGENTS.md 的 `deeptutor start` 是候选入口，不代表本机已启动成功。
4. 通过现有设置配置云端主模型；先核验沉浸阅读能否不建整书向量库完成本单元学习，仅需 RAG 时才配置 embedding 并记录费用。
5. 导入小型 PDF、EPUB，核对阅读顺序与各 3 处定位，再开始有限模型试用；记录从阅读转到 Mastery Path 时来源是否保留。
6. 更新本文证据与差距，再确定 B2 的第一项可验收修改。

## 6. 样本、测试与完成标准

### 样本

起步：一份有权使用的文字型 PDF、一个学习目标和一个单元，随后加入 EPUB。综合验收：2 份文字型 PDF（概念类、方法类）和 1 份 EPUB，每份至少 2 个单元；每单元人工核对至少 3 处引用和全部练习的可答性。异常样本用小型自制文件覆盖扫描/空文本、损坏、长文、目录缺失与乱序风险。

每个目标保留已知正确、部分正确、错误、合理等价表达和“不知道”的答案。题目是否可答、评分是否符合原文由人工语义审核；保留争议与失败，不能反复生成直到满意后只留下成功例。

真实书籍、个人回答、凭据和原始费用记录不进 Git。使用已有忽略的数据目录，写入前用 `git check-ignore` 核对；提交的测试 fixture 应为自制或许可明确的小材料。

### 检查层次

- 确定性测试：定位版本、答案字段隔离、辅助条件、失败状态、并发幂等、覆核重算、冻结时间与时区边界。
- 真实存储与运行集成：保存/重启、迁移、事件回放、重复请求、备份恢复、导出删除；mock 不能替代。
- 浏览器：PDF 与 EPUB 各走完整流程，检查网络响应、刷新恢复、错误提示和窄屏操作。
- 真实模型：引用支持结论、题目可答、反馈与评分正确、中文表达可用；程序通过不代表语义通过。
- 个人试用：前测、无提示变式后测、至少 7 天后的无提示复测，记录真实日期、辅助条件与失败目标。小样本不能证明普遍学习效果。

开发时先执行改动相关测试与仓库规定检查；后端依据当前 Python 测试/ruff 配置，前端依据 [package.json](../web/package.json) 的 `typecheck`、`test:node`、`test:unit`、`lint`、`build` 及契约/i18n/架构检查。综合交付再覆盖受影响完整链路；不要照搬旧仓库不存在的 `test:coverage` 或 mypy 要求。最初计划会话仅修改文档；功能实现的实际检查见第 8 节最新执行记录。

### 完成标准

技术闭环：两种格式均能完成原书定位→目标→独立解释与新情境应用→可覆核反馈→到期复习；原始证据持久化，版本不混淆，重复请求不重复推进，失败可见，预算与数据保护检查通过，受影响原有功能无回归。

语义验收：选定单元全部练习可答、引用成立、反馈可核对，明确误判已修复或停用受影响内容。个人学习验收另需实际延迟复测；允许报告“技术闭环完成，延迟保持待验证”，不能提前标整体完成。

## 7. 需要用户提供的信息

1. 一份试用书籍的本地路径、选定单元及“学完希望能做什么”；稍后补 EPUB 和综合样本。
2. 可用服务商与模型、单次试用和月度预算。密钥在现有设置中本地填写，不必发到聊天。
3. 是否有旧 DeepTutor 配置、书籍或学习记录需要保留；开发侧仍应自行检查实际数据位置。
4. 参与题目/反馈审核、独立应用和至少 7 天后的复测。

模型价格在实际选定服务商后查官方价格并记录日期；预算未知时不运行整书付费生成。应用预算只覆盖本应用可记录的调用，不保证覆盖同密钥其他客户端或延迟账单。

## 8. 交接与执行记录

当前交付：既有本机安装、PDF/EPUB 导入定位和三项 B2 修复保留；O0–O3 离线实施与缺口见执行记录 6–10；R1 事务快照/自动补偿见执行记录 12；R2 预算门禁、R3 底层计量、R4 旧辅助条件未知语义及 R1 整合补完见执行记录 13。代码、离线契约、真实调用、语义审核与个人试用分别记账；真实模型闭环和延迟试用未通过验收。第 9 节持续维护实施状态；以下早期记录中的“未提交”“仍运行旧代码”等描述是当时快照，接手时重新核对。

### 执行记录 2026-10-24（B0 会话）

- 基线：`a31d8262`（release: v1.6.15），分支 main 与 origin/main 同步；未提交修改仅 `.gitignore`、`AGENTS.md` 与本文。无旧数据目录（`data/` 本次新建，已被 `.gitignore` 覆盖）。
- 环境：Windows 11、Node 24.3.0、npm 11.4.2、uv 0.11.25。Anaconda base Python 3.11.5。
- **依赖障碍（已修复）**：用 Anaconda 3.11.5 解释器建 venv 时，PyMuPDF 在导入 PDF 时以 0xC0000005 访问违例崩溃（后端进程直接退出）。改用 `uv venv .venv --python 3.12`（uv 托管 CPython 3.12.13）+ `uv pip install -e .` 后正常。结论：本仓库在本机不要用 Anaconda 发行版解释器建环境。
- 安装与启动命令（实测成功）：`uv venv .venv --python 3.12` → `uv pip install -e . -p .venv` → `.venv/Scripts/deeptutor.exe start --no-browser --detach`。`deeptutor start` 自动完成 `web` 的 `npm ci` 与 Next.js 16.2.3 生产构建（source-production 模式），Backend http://127.0.0.1:8001，Frontend http://localhost:3782（重定向 /chat 返回 200）。
- 导入与定位验证（自制样本，英文文本以避开 PDF 中文字体问题）：手写 PDF（2 页）与手写 EPUB 3.0（2 章 spine）经 `POST /api/reading/materials` 导入成功（extractor=pymupdf / epub-spine，locator 从 1 起）。`GET /materials/{id}/units/{locator}` 对两种格式各核 3 处：unit1、unit2 文本与来源一致且顺序正确，越界 locator 明确报错。
- 未执行：模型配置与模型交互（`model_catalog.json` 为全空，需要用户提供服务商/模型/密钥与预算，见第 7 节第 2 条）；真实书籍导入；B1 全部核验。
- 下一步：用户提供密钥后在 Settings > Catalog 配置主模型，做一次小范围模型交互；然后按第 7 节第 1 条取真实 PDF/EPUB 复核导入与中文抽取，进入 B1。

### 执行记录 2 2026-10-24（B1 离线审计与修复，用户令先跳过需密钥项）

**离线测试**：`pytest tests/reading deeptutor/learning/tests tests/capabilities/test_mastery_semantic_assessment.py` 共 1136 项。修复 2 个缺陷后 1135 通过、1 跳过、1 失败（见下）。改动文件 ruff check/format 通过。

**已修复缺陷（本会话代码改动，未提交）**
1. 同刻提交的最新作答投影覆盖丢失（复习一致性）：`deeptutor/services/session/sqlite_store.py` `_record_assessment_sync` 的 `is_latest` 平局裁决用 `attempt_id` 字典序，而 attempt_id 是内容哈希，字典序与提交顺序无关；两个作答落在同一时间戳时，较新提交若 id 排序在前会被判"非最新"，Question Notebook 最新卡保留旧答案。已有测试 `test_old_submission_retry_cannot_overwrite_newer_answer` 复现（单独跑即失败）。修复：平局改按到达序（同刻新到者生效）；同 id 重试的幂等保护在早退分支，不受影响。
2. EPUB MIME 受 Windows 注册表污染：`deeptutor/reading/store.py` `_guess_mime` 经 `mimetypes.guess_type` 在 Windows 返回 `application/epub`，违反 faithful viewer 契约的 `application/epub+zip`。修复：加 `.epub` 覆盖表（与既有 `_MEDIA_MIME` 同模式）。
3. 仍失败 1 项：`test_async_reading_action_can_be_retried_after_timeout[True]`，判定为 Windows 测试环境 flake 而非产品缺陷——测试把动作超时压到 0.01s，Windows 上 `run_in_executor` 首次线程池启动延迟可超过它，导致首个请求在 handler 执行前即超时。不改测试语义，真实运行不受影响（默认超时远大于此）。

**第 3 节契约审计结论（源码审计 + 离线测试，均为"未核验真实模型行为"）**

| 核验项 | 判定 | 关键差距 |
|---|---|---|
| 练习答案隔离 | 复用（设计良好） | 视觉题卡片在作答前下发 `answer_cues/key_status`（`learning/visual_practice.py:216-228`），严格口径属作答前线索；无"题目卡 payload 不含答案键"的集中防线测试 |
| 作答证据 | 部分实现 | 缺题目版本、评估版本字段；"看答案"无独立事件类型；跨库（session store / learning store）写入非原子，靠 `linked_applied`+reconcile 补偿 |
| 复习一致性 | 复用（含本会话修复） | 覆核 void 只改 learning 库，session store 不可变 attempt 不标 void（单向）；void 不清理 qualitative evidence；`attempt_count` 由调用方传入可被滥用绕过幂等 |
| 掌握展示 | 部分实现 | qualitative 通过一律显示满分不看 hints（`policy.py:161-166`），与 `learning_stage` 可能矛盾；qualitative 无 independent 概念；无 verdict 失败默认记 partial（`service.py:2927`）偏宽容 |
| 来源与版本 | 部分实现 | locator/revision/注释重锚机制完整；**但题目与作答不带 material_revision**，材料重抽取升版后旧作答静默指向新文本（`reading_extensions.py:347-360,453`）；PDF 重抽取不归档旧 units（`store.py:568,580-589`） |
| 抽取质量 | 部分实现 | 全空文档拦截、加密拒绝、预览与单元边界可用；部分扫描页/空文本页无 per-unit 标记可进 quiz（运行时 503）；乱序/缺页/截断无检测或标记 |
| 调度规则 | 复用 | 非固定间隔表：指数遗忘模型（stability×-ln(retention)），失败减半，同会话 0.25 天去重；全 UTC epoch；`desired_retention` 调整不计作答（#1541）。与第 3 节旧候选方案（0-4 分/固定 1-3-7-14）冲突处以现有实现为准 |

**B2 优先修复建议（待用户确认后动手）**：① 给题目/作答/quiz pending 挂 `material_revision` 并在 refresh 路径补旧版归档或失效标记；② 空文本单元的 per-unit 质量标记与出题拦截；③ qualitative 展示与 hints 一致性。

**未做**：真实模型调用、真实书籍流程（B1 行为验证）、usage/预算运行时行为核验（源码层面未细查，标记为未知）。

每批在本节追加简短记录：日期、基线/实际提交、改动、样本与版本、命令和检查结果、真实调用与费用、语义审核、用户试用、失败与下一步。任务状态在第 5 节同步更新；检查未执行须明确标记。

### 执行记录 3 2026-10-24（B0 真实书籍导入与定位验证）

- 用户在 `docs/` 放入 3 本真实书：`agentic-ai-guide-zh-v1.1.0-b6d31949bac5.pdf`、`AI-Agents-in-Depth-zh-CN-d689642521fa.epub`、《提问的艺术》EPUB（z-library 长文件名）。书籍文件不进 Git（docs 下需注意提交时排除，见下方提醒）。
- **PDF（agentic-ai-guide-zh，599 页文字型）**：经 `POST /api/reading/materials` 导入成功（material `cd182bf9e84a911a`，pymupdf，85.7 万字，outline 1041 条，revision 1；同文件重复上传被 reuse 去重，未产生重复 material）。中文抽取正常；核 3 处定位（unit 3 / 60 / 62），单元文本与 PyMuPDF 原页文本逐字一致、顺序正确。物理页与印刷页存在偏移（目录标注"前言 27"），后续引用需按物理 locator。
- **EPUB（《提问的艺术》，39 个 spine 单元）**：导入成功（material `d9508cc08c037ea5`，epub-spine，9 万字，outline 41）。核 3 处定位：unit 5（引言）与 unit 39（译者后记）与 EPUB spine 原文匹配、顺序正确；unit 1 为空文本（封面页）。**全 39 单元扫描：空文本单元仅 unit 1，API 响应无任何 per-unit 质量标记（字段仅 locator/text/unit）——在真实书上确认了执行记录 2 的 B2 缺口 ②（空单元无标记、可否进 quiz 未拦截）**。
- **模型配置现状**：`model_catalog.json` 仍为全空（connections/profiles 均无）。核对源码：catalog 支持自定义 `base_url`（OpenAI 兼容端点可配），但密钥仍必需。用户明确 token 未恢复无法提供密钥；子代理后端（claude-code/codex/kimi 等本地 CLI）是独立于主模型 LLM 的另一层，不构成主模型的替代。**结论：真实模型交互保持阻塞，不用 mock 冒充；已向用户说明。**
- 下一步：B1 中不依赖模型的核验项（阅读持久化、书签/注释、作答证据存储、重启恢复）可先做；真实模型交互、学习路径全流程待用户密钥恢复后补验。

### 执行记录 4 2026-10-24（B2 三项优先修复完成，离线通过）

用户确认动手后，本轮完成执行记录 2 列出的 B2 优先修复（代码改动，未提交）：

1. **material_revision 链**：`AssessmentRecord` 新增 `material_revision`（默认 0 = 未捕获，随 attempt JSON 持久化）；阅读 quiz 生成时把当前 material revision 盖进每个 pending 题目（`_persist_reading_quiz_pending`），提交作答时写入评估记录（`reading_extensions.py`）。`ReadingStore.refresh_document`（PDF 重抽取）现在把旧版 units/manifest/outline/unit_refs 归档进 `revisions/{旧版号}/`，与重导入路径同契约——旧作答证据可用 `revision_unit_text` 回到原文本，不再静默指向新文本。注：notebook_entries 投影表未加列，修订号存于不可变 attempt JSON。
2. **空单元质量标记与出题拦截**：`GET /units/{locator}` 与修订版端点新增 `empty`、`char_count` 字段；quiz 扩展在空文本单元上直接 422（此前是运行时 503）。真实 EPUB 封面空单元（执行记录 3）即此场景。
3. **qualitative 展示一致性**：`record_qualitative_in_memory` 新增 `hints_used` 并落到 LearningEvidence（`record_qualitative` / `record_qualitative_for_path` 穿透）；带提示的定性通过不再把 mastery_levels 抬到满分，`display_mastery` 对有提示证据的定性通过回退到 mastery_levels，与 `learning_stage` 的"practiced_with_help"一致；无 verdict 的定性失败由"partial"改为如实记"incorrect"（quality 仍 0.2，调度器行为不变，#1781 修复分支不受影响）。

**回归测试**（新增 4 个）：quiz pending/attempt 携带 revision、refresh_document 归档旧 units、空单元出题 422 与端点 empty 标记、带提示定性通过展示降级。2 个旧断言（无 verdict 失败=partial）更新为新契约。**套件结果：tests/reading + tests/api/test_reading_quiz_answers.py + deeptutor/learning/tests + mastery 语义测试共 1156 项，1155 通过、1 跳过、1 失败**——失败仍为执行记录 2 已判定的 Windows flake（`test_async_reading_action_can_be_retried_after_timeout[True]`，0.01s 超时压测，与本次改动无关）。改动文件 uvx ruff check/format 全过。

**边界与未做**：mastery 路径自产的题目卡（learning service 侧）未挂 material_revision（不在阅读 quiz 链上，B1 真实验证后再定）；notebook_entries 投影无 revision 列（attempt JSON 可溯源即可）；后端进程仍在跑旧代码，真实调用验证前需重启 `deeptutor start`。真实模型交互、B1 行为验证、浏览器流程：待用户 token 恢复。

### 执行记录 5 2026-10-24（等待额度期间的复核与开发计划）

- 用户要求先判断是否继续优化，随后确认先形成开发计划，由新会话实施。本轮只更新本文，不修改功能代码、不调用付费模型。
- 现场：`main` / `cfb3e8d1`，开始时工作区干净；已有修复提交为 `217ffe3d` 与 `6986d9ca`。本地 catalog 的 connections/profiles 均为 0。此前真实书籍导入记录不等于模型学习闭环已通过。
- 已实际补跑：`tests/api/test_reading_quiz_answers.py`、`tests/reading/test_reading_captions.py::test_refresh_document_archives_outgoing_units`、`deeptutor/learning/tests/test_guided_mastery_updates.py::test_hinted_qualitative_pass_does_not_display_full_mastery`，结果 **19 passed in 8.34s**。只覆盖这些定向项，未重跑完整套件，未覆盖此前记录的 0.01s 超时失败。
- 测试入口先因 `_overlapped` / `WinError 10106` 在收集前失败；只读检查发现当前执行进程缺 `SystemRoot`、`WINDIR`、`ComSpec`。仅在测试进程补齐后 `asyncio` 导入与上述 19 项测试通过；没有重装 Python、改系统配置或禁用插件。该环境问题与此前 0.01s 超时用例不是同一问题。
- 本轮复核确认：现有阅读导出入口用于原书与批注，不能据此声称完整学习记录已可备份恢复；已有 usage 统计不能据此声称有全局预算拦截。视觉卡片的 `answer_cues/key_status` 是状态元数据，字段存在本身不能证明泄露正确答案，O1 应检查实际响应中的答案内容与辅助条件。
- 下一步：执行第 9 节 O0→O1→O2→O3；每批先核验、复用通过项，仅修复可复现的缺口。完成后停止扩大范围，等待模型就绪再回到 B0/B1。历史大套件计数不作为本次新结果引用。

### 执行记录 6 2026-10-24（O0，离线完成）

- 原现场 `main / cfb3e8d1`，仅本文未提交，基线包含 `217ffe3d`、`6986d9ca`。隔离 worktree：`C:\Users\O1830\.codex\worktrees\learning-offline\DeepTutor`，分支 `codex/learning-offline`；显式带入最新未提交计划，主工作区原稿与数据未覆盖。未提交/推送。
- 原数据仍在 `D:\Code\project\study\DeepTutor\data`（已忽略），只统计到 1 个 `.db` 和 4 个 `.sqlite3`，未打开业务记录或迁移数据。发现 Python/Node 服务进程，未停服或重启；CIM 查询失败，改用进程枚举确认。worktree 初始无 data，测试运行时使用临时 DEEPTUTOR_HOME。
- 单独 `uv venv .venv --python 3.12`，实际 CPython 3.12.13。首次安装因 10106 失败；只补当前命令的 SystemRoot/WINDIR/ComSpec 后，`uv pip install --offline -e .` 与 pytest/pytest-asyncio/httpx 安装成功，未装 Manim 等可选组。未调用模型。
- 新增 `scripts/run_learning_offline.ps1`：固定本 worktree 的 `.venv`，验证 3.12 / asyncio / _overlapped，隔离运行数据，退出恢复进程变量。默认重跑执行记录 5 的 19 项。
- 基线含超时测试：**20 passed、1 failed**（`data-o0-baseline.log`）；0.01 秒从线程池启动前计时，导致 sync wrapper 的第一次处理尚未进入便超时。根因是测试把线程启动时间混入“运行中的协程可取消并重试”的断言。改用实际 asyncio Timeout，在 handler 进入后重排至当前时刻，Event 确认已进入和已取消；保留 503→200、恰好两次处理断言，不扩大超时、不 skip、不改应用逻辑。复跑相同入口：**21 passed in 10.84s**（`data-o0-fixed.log`）。日志为本地忽略文件。
- 下一批 O1：reading API 实际 JSON 的 `correct_choice_index` 泄露已由契约断言复现（`data-o1-repro.log`），将修复公开投影并核验恢复与一致性；真实模型、语义、浏览器与延迟复测仍待验。

### 执行记录 7 2026-10-24（O1，有界离线交付）

**存储关系**：reading quiz 的题目与答案键先存 session SQLite 的 pending，API 提交后经 `record_assessment` 将原始回答、locator、已捕获 revision、辅助条件及 verdict 写入同库不可变 `assessment_attempts`，同时更新 Notebook 最新投影；有效显式 objective 链接再写 learning SQLite 的 evidence/repetition/queue，失败留 pending linked 事件供 `reconcile_linked_assessments` 重放。Mastery Path 的 pending/interaction、原始回答、学习证据、覆核事件由 learning SQLite 事务保存，Notebook 是额外的 best-effort 投影，不是另一份掌握真源。Question Notebook 另有 practice review state/events，其自评复习不是 Mastery 的语义评估。

| O1 场景 | 本批结果与边界 |
|---|---|
| 保存/重开/跨进程 | 新增真实 Python 子进程断点→新进程补偿→再重开测试；自制中文原始回答、题目标识、revision=3、locator=2、辅助条件与结果保留，证据与 due 不重复推进。旧 record 缺 revision 仍为 0；不追填当前版本。原材料历史归档沿用已有修复。 |
| 重复/并发/新作答 | 12 个同事件并发只有一个写入；8 个同刻不同事件全部保留，最新 Notebook 与落盘到达序一致；旧请求不覆盖新答案。真实独立存储实例暴露 practice 初始化 DROP/CREATE 触发器竞争，已用 SQLite BEGIN IMMEDIATE 将替换原子化。 |
| 跨库中断/补偿 | reading/book 显式链接链复用不可变事件和 reconcile；故障注入后原始回答保留，重复补偿、旧请求重试不重复推进，不调用模型。Mastery→Notebook 仍为 best effort，支持重试时同步；未证明启动时自动补齐所有历史缺失投影，保留差距。 |
| 覆核/作废 | 复用既有按题移除/重算、保留其他题证据、修正答案键测试；新增真实 Notebook 重开、重复作废仍两条 attempt、理由审计及辅助条件测试。修复覆核同步丢 hints_used；service 的历史事件保留原 verdict 和理由。跨库故障下所有覆核的自动恢复尚未闭合。 |
| 作答前响应 | actual reading API JSON 泄露 correct_choice_index 已先复现后修复；先保存完整 pending，再以公开字段白名单输出，不下发 key/解释/rubric/内部隔离标记。前端无需答案键即可提交，使用服务端 verdict。Mastery 实际工具 content+metadata+status 响应的文字参考答案/评分说明 sentinel 检查通过，复用公开投影。visual 的 answer_cues/key_status 为状态，reference_quote/reference_answer 不在公开字段中。 |
| 辅助条件 | 新 reading pending 服务端标记已隔离；历史 pending 曾带 key，保守作辅助练习；同题反馈后新的作答标记辅助，同事件重试不增加次数。修复 Mastery 覆核及定性评估同步 Notebook 时丢 hints_used。不能追溯用户在外部看答案或全部旧定性作答的辅助情况，仍留缺口。 |

**验证**：最初相关 62 项通过；新增跨进程/并发专项修复后 3 项通过。受影响整合入口 `tests/reading tests/api/test_reading_quiz_answers.py deeptutor/learning/tests tests/capabilities/test_mastery_semantic_assessment.py tests/services/session/test_sqlite_store.py` 首次 **1208 passed、1 skipped、1 failed**；失败是旧迁移测试未关闭 SQLite 句柄，Windows 无法移动文件。仅修测试关闭句柄并断言旧表数据，定向 **1 passed**。补齐辅助条件后的定向范围 `test_mastery_state_integrity.py + test_mastery_semantic_assessment.py + test_offline_recovery.py + tests/api/test_practice.py` **64 passed in 25.08s**。最终整合计数见执行记录 10，不把分次结果相加为全绿套件。

前端答题 **3 passed**；typecheck、i18n parity/audit、改动文件 eslint 与 webpack production build 通过。契约首次检查因 checkout CRLF 与生成器 LF 不同报 stale；执行既有 contracts:generate 后 check 通过，Git 内容无契约变更。仅改变动态 quiz payload 投影，不新增 API schema。npm 离线安装缺缓存后正常 npm ci 成功，保留锁文件，未自动 audit fix。Python 按仓库 Ruff 0.16.0 检查；测试和构建日志留本地忽略文件。未提交/推送。

**放行边界**：本批修复与上述离线契约已验证；O1 仍有自动投影恢复与不可追溯辅助条件缺口，不勾整批/整体 MVP 完成。独立推进 O2 调用核验和 O3 隔离恢复，不调提示词、评分标准或调度公式；B0/B1 真实模型闭环、题目反馈语义与个人延迟保持未验。

### 执行记录 8 2026-10-24（O2，有限调用保护）

- 路径核对：reading quiz→complete→factory→provider；语义评估→complete_with_config→同一 factory/provider；Mastery 回合另经 agentic loop。reading quiz 单次最多 2500 output tokens、结构化空答再试一次，显式 max_retries=0；semantic assessment 最多 2200 output tokens、6 个来源页且图片 URL 总量 16 MiB，沿用 factory 的 retry 设置（默认 8 次重试即 9 次 provider 尝试，不是 3 次）。不能将 provider 尝试数冒充 SDK HTTP 请求数。
- OpenAI-compatible/Anthropic SDK 显式 max_retries=0。OpenAI-compatible 内部还存在有界 key rotation（429 时 max(2, key 数量)）、Responses input-status 兼容重试、Responses→chat 兼容退路、response_format/forced_tool_choice 兼容重试；配置不同会叠加，不能声称“所有模型最多两次”。未配置真实模型，未给出未验证的全入口总 HTTP 上界。普通配置并发门默认 20、600 RPM、获取槽位限时 30 秒；OpenAI stream 有 90 秒 idle guard，reading action 外层 120 秒；SDK 非流式超时沿用实际所选 provider/SDK，尚无统一本应用总 deadline。
- **先复现再修复**：通用图片降级曾把鉴权、模型配置、余额错误也去图再调一次，新增 4 个 fake-provider 用例全部失败（日志 `data-o2-image-repro.log`）。修复为要求图像输入错误分类命中，并拦截鉴权、已识别模型/余额错误才允许已有显式降级；不修改主模型或阅读语义评估的 allow_image_fallback=False。OAuth 既有一次凭据刷新是独立明确恢复机制，保留已有测试。
- **计量有限修复**：`UsageTracker.summary` 不再把未知模型套 GPT-4o-mini 价格或把未配置价格显示为 0；返回 total_cost_usd=null / cost_status=unknown，已知静态表仅标 estimated，字符估算另计 estimated_calls。CLI 明示 cost=unknown。旧 `LLMStats` 日志消费者仍保留兼容默认价格，未宣称其账单准确；transport ledger 的 estimated/interrupted/failed 状态已由真实临时 SQLite 测试覆盖。超时且无 usage 的实际服务商扣费仍未知，不能按估算当结算。
- **硬预算缺口明确保留**：未发现持久化调用前费用门禁或在途金额预留，未据猜测金额设置预算；本批未实现全局硬预算。provider 内部兼容重调可能仅记成一次 provider measurement，全部 HTTP 计费归因也未闭合。达到金额上限拒绝新调用、并发预算争用这两项因缺该机制不能标通过，B4 保持未完成。
- 验证：原 retry/auth/structured/ledger/stream-usage/pricing/statistics 范围 **64 passed in 34.70s**；图片降级修复、CLI 和 ledger/pricing 追加范围 **52 passed in 18.37s**，后追加 0/2/8 次重试耗尽计数测试，最终准确整合计数见执行记录 10。保留原错误结果，不因数据库保存失败重新请求模型；本轮没有真实模型请求。

### 执行记录 9 2026-10-24（O3，选定存储备份恢复）

- 新增维护脚本 `scripts/learning_backup.py`，仅接收显式 user-root，范围为 `chat_history.db`、`usage.sqlite3`、`workspace/learning`（含 mastery/V1 archive）、`workspace/reading`（含 catalog、manifest、units、原书和历史 revisions）、`workspace/notebook`。不复制 settings 中的模型配置/密钥文件、logs、外部 knowledge_bases、其他 workspace 或多用户目录；不会筛改原始回答或原书文本。恢复这些外部引用和完整迁移/全部删除仍留 B4。
- 必须先停所有写入者，并显式传 `--quiesced`。SQLite 用只读连接与 backup API 收集已提交 WAL，目标转换为独立 DELETE-journal 快照，不把运行中的 db 主文件复制当备份。保持源连接并用 data_version 和目录变化检查拒绝可观察的中途写入；SHM 读标记变化不是业务写入。**跨库一致性仍以前置停写为条件，脚本不是在线跨库事务快照。**
- snapshot.json 记录格式/应用版本、每库 schema hash/user_version、逐文件 SHA256/大小和范围。先写 `.partial-UUID`，校验后才发布成功目录；失败保留 partial 便于排查。恢复先验证再复制，复制后再验证，只接受不存在的新目录，拒绝已有目标、路径越界、链接、遗漏/额外文件或校验损坏。校验和检测意外损坏，不是签名认证。
- 合成 PDF/历史修订→自制中文回答/linked evidence/Notebook→备份→另一目录恢复→重新打开 stores，核对原始回答、locator/revision、历史来源文本、记录数、证据/掌握相关状态及 due；补偿和重复提交均不新增证据或改变日程。另验证 WAL-only 提交、损坏/不完整/schema mismatch、拒绝覆盖/嵌套目标及中途写入，初轮修复后 **9 passed in 13.96s**；新增中断复制不能出现成功目录，最终计数见执行记录 10。
- 初轮 **8 failed、1 passed** 原始输出保留在 `data-o3-validation.log`：TXT fixture 未保留可重抽取原书，改用自制 PDF；SQLite 读连接产生 SHM 读标记被误判为业务修改，且目标 WAL 模式会产生校验清单外 sidecar。修复为保持源连接/data_version 检测真实提交、忽略 SHM 读标记、目标快照转 DELETE journal；故障注入“备份期间有写入必须失败”仍保留，未通过删除保护让测试变绿。
- 只在临时实例实验，未备份或恢复用户真实数据，未停现有服务。使用示例（父目录需提前存在，实际维护前先停写）：

```powershell
.venv/Scripts/python.exe scripts/learning_backup.py backup --user-root "D:/Code/project/study/DeepTutor/data/user" --output "D:/Backups/DeepTutor-learning-snapshot" --quiesced
.venv/Scripts/python.exe scripts/learning_backup.py restore --backup "D:/Backups/DeepTutor-learning-snapshot" --destination "D:/Restore/DeepTutor/data/user"
```

恢复结果是 user 目录；启动恢复实例时 DEEPTUTOR_HOME 应指向其 `data` 的父目录（例中 `D:/Restore/DeepTutor`），另行配置模型。需要新版本兼容、外部 KB 引用、多工作区或全部用户数据恢复时，本格式不构成完整方案。

### 执行记录 10 2026-10-24（离线收尾）

最终受影响链路整合：**1332 passed、1 skipped、0 failed in 379.78s**，日志 `data-offline-final-integration.log`；没有沿用早期计数。实际入口：

```powershell
& ./scripts/run_learning_offline.ps1 -TestPaths @(
  'tests/reading',
  'tests/api/test_reading_quiz_answers.py',
  'deeptutor/learning/tests',
  'tests/capabilities/test_mastery_semantic_assessment.py',
  'tests/services/session/test_sqlite_store.py',
  'tests/api/test_practice.py',
  'tests/services/test_learning_backup.py',
  'tests/services/llm/test_provider_auth_retry.py',
  'tests/services/llm/test_provider_retry_classification.py',
  'tests/services/llm/test_provider_core_image_fallback.py',
  'tests/services/llm/test_structured_retry.py',
  'tests/services/llm/test_usage_ledger.py',
  'tests/core/test_record_streamed_usage.py',
  'tests/logging/test_llm_stats.py',
  'tests/services/session/test_usage_statistics.py',
  'tests/cli/test_turn_renderer.py'
)
```

整合运行之后新增的真实 SQLite 旧记录缺 revision→重开→携当前版本重试测试，单独 **1 passed in 1.48s**（`test_offline_recovery.py::test_legacy_unknown_revision_is_not_replaced_on_reopen`，日志 `data-o1-legacy-revision.log`）；原不可变 JSON 继续缺该字段、模型视图仍为未知 0，不写成当前 99。此结果单列，不与整合计数相加。

改动 Python 文件 Ruff **0.16.0** check/format 与 `scripts/check_repo_hygiene.py`、`git diff --check` 通过；前端 `npm run architecture:check`（914 modules，无依赖违规）、`contracts:check`、定向 `test:unit`（reading quiz persistence **3 passed**）、改动文件 eslint、typecheck、i18n:check 和 webpack production build 通过。未运行整个仓库的 pre-commit --all-files 或全部前端/e2e 套件，避免为本批扫改无关文件；本轮没有提交。

原始失败及后续验证日志均已核实在 Git 忽略范围，虚拟环境、node_modules、测试数据/备份均不进入提交。最新代码与本计划保留在 `codex/learning-offline` worktree，原工作区仅追加续接指针；没有覆盖用户数据、切换运行服务、提交或推送。

**仍未关闭**：Mastery→Notebook 所有历史缺失投影/覆核的自动补偿；全部旧辅助条件追溯；持久化费用硬预算与在途预留；provider 内部全部 HTTP 计费归因及旧日志计费；范围外 KB/多工作区数据恢复、完整导出删除和升级兼容。预算相关项保持 B4 未完成，不因有限调用保护放行付费任务。

**待真实验收**：B0/B1 配置与完整 PDF/EPUB 各一个单元的模型闭环、全部题目/反馈/引用语义审核、浏览器个人流程、B5 至少 7 天延迟复测。本轮真实模型请求为 0，语义与学习效果没有新证据。停止扩展教学功能；后续优先按未关闭项确定小批范围，额度恢复后按 9.5 的有限真实试用协议继续。

### 执行记录 11 2026-10-25（提交与新会话交接）

- 用户要求先更新相关文档，再提交并 push，剩余开发留给新会话。本轮补齐 9.6 的 R1–R4 顺序、入口与放行条件，重写第 10 节续接指令；README 增加本计划及维护恢复工具入口。O1/O2 保持有限交付，不以提交/推送代替验收。
- 提交范围仅本轮代码、脚本、合成测试、README 和本文，共 27 个文件；原工作区数据、原稿、日志、备份、虚拟环境、node_modules 不进入提交。目标为个人 fork 的 `codex/learning-offline`，不用 force、不推 main/上游，不新建 PR。
- 本轮重新执行仓库卫生、分支策略、改动 Python 文件 Ruff 0.16.0 check/format、staged diff 检查和 detect-secrets 1.5.0 扫描。扫描唯一命中是备份测试的字面值 `SYNTHETIC_SECRET`，仅该行加 allowlist 注释，未修改 baseline 或放宽全局规则。
- 当前环境没有 pre_commit 模块，未执行 pre-commit --all-files；没有将检查缺席写成通过。除上述测试注释外，本轮不改功能代码；沿用执行记录 10 在本会话已实际跑出的整合/前端结果，未为文档提交重跑全套功能测试，未调用真实模型。提交和远端 SHA 以实际 Git 核对及本会话交付消息为准。

### 执行记录 12 2026-10-25（R1，事务同步快照与自动补偿）

- **现场与范围**：复用 `codex/learning-offline / 036b6bf7` 的现有 worktree；开工时干净，原工作区数据与未提交计划保留。不重启或切换原运行服务，不调用真实模型；本批只做 R1，不改教学提示词、评分标准或调度公式，未提交/push。
- **根因与防线（RCG）**：学习 SQLite 先提交→工具 best-effort 写 Notebook→写入失败只记录日志→没有同事务交付凭据→进程退出后无法知道缺了哪次原作答/覆核。这是跨库事务边界的系统性缺口。保留两库，以 `mastery_notebook_outbox` 同事务存同步快照，引用原 `mastery_events.id`；快照写失败则原事务回滚，不能留下“作答成功但没有恢复凭据”的新状态。
- **实现**：`learning/notebook_recovery.py` 从源事务捕获单题、分组子题、定性评估以及更正/作废快照，保留原始回答、来源证据快照、辅助条件、原 verdict 与更正理由；不为组父题额外记掌握。Notebook 成功提交后才标 applied；进程中断或确认写失败可安全重送，重复覆核保留审计事件但不增加相同 Notebook 作答。修正仍更新原作答所属的 session/turn 卡片，不因覆核发生在新 turn 而另起一张旧卡片副本。
- **顺序保护**：`AssessmentRecord` 增加内部源流/事件序号及覆核来源字段；Notebook 最新投影依据同一源流的提交序号，避免并发补偿、同刻时间戳或时钟回拨造成旧事件覆盖新回答。不重算学习状态，不重新请求模型；原不可变 attempt 继续保留。
- **自动入口**：Web lifespan 启动补偿；现有应用恢复周期在既有 user/workspace scope 内补偿；`mastery_status` 读取及原 grade/repair/qualitative 同步入口也投递快照，CLI/SDK 下次读取可恢复。失败保留 pending，不把成功保存的回答再次交给模型评分。恢复范围跟随现有存储 scope，不扩 O3 到多工作区备份。
- **复现与验证**：新增真实临时双 SQLite、独立 Python 进程断点测试；无快照对照路径能保留 learning 作答但恢复后仍无 Notebook 卡片，明确证明旧边界。新路径覆盖作答/更正/作废写入中断→退出→重开→补偿、确认落盘失败后的重复/并发重送、旧事件乱序到达、其他题证据保留、事务回滚、状态读取、组题/定性作答及待同步快照备份恢复。子进程阻断 LLM client 并断言调用次数为 0。定向范围 `test_notebook_recovery.py + test_mastery_state_integrity.py + test_mastery_semantic_assessment.py + test_mastery_question_groups.py + test_learning_backup.py` 在新增最后一项乱序新回答用例前 **86 passed in 47.71s**（`data-r1-targeted-v3.log`）；最后完整计数待整合结束更新，不与分次结果相加。
- **失败记录保留**：初轮 **3 failed / 2 passed** 发现新增字段误加在 outcome 而非 record 导致恢复丢序号/覆核元数据，已修正；追加范围 **2 failed / 71 passed** 发现重复作废多记一次 attempt，已加源事务内相同快照去重；后续 **1 failed / 74 passed** 是分组 fixture 的相同目标/相同题干违反既有契约，改为不同题干并保留生产约束。原日志 `data-r1-initial.log`、`data-r1-targeted.log`、`data-r1-targeted-v2.log` 均在 Git 忽略范围，没有删除测试放行。
- **历史边界**：不回填本次变更前缺少交付快照的旧作答/覆核；旧 `grade_and_record` 等没有完整 interaction 的路径、无 session 的 SDK 记录不能据缺失字段造题或绑定对话。旧辅助条件仍按 R4 待审计，不能借刷新推定独立作答。已有旧工具重试兼容入口保留。新保障已实现不代表“所有历史 Notebook 投影已补齐”，O1 继续有限交付。
- **检查与下一步**：Ruff 0.16.0 check/format、仓库卫生与 diff 检查定向执行；当前虚拟环境缺 `pre_commit`，未声称全仓 pre-commit 通过。本批无前端或公开 API schema 改动，不重复全站构建。整合检查进行中，完成后再更新准确计数；下一可开发单元是 R2 持久预算与在途预留，R3 底层计量、R4 历史证据及真实模型/语义/延迟验收继续保留。

### 执行记录 13 2026-10-25（R1 整合补完；R2/R3/R4 离线实施）

- **现场与范围**：复用同一 worktree 与 `codex/learning-offline / 036b6bf7`，R1 未提交改动全部保留。不重启原运行服务、不调用真实模型；本批完成 R2/R3/R4，不改教学提示词、评分标准与调度公式，未提交/push。
- **R1 整合补完**：执行记录 12 遗留的整合检查已完成。此前 5 failed（tests/app 两文件）逐一定位为默认 pytest 临时目录路径超 Windows MAX_PATH（`pytest-of-unknown\...` 深层嵌套 >260 字符，workspace 写探针 `touch` FileNotFoundError）——环境限制而非 R1 回归：用短 `--basetemp` 复跑该 5 项单独通过，随后同范围全量 **1344 passed / 4 skipped / 0 failed in 288.72s**（`data-r1-integration-v2.log`）。未改产品代码与测试语义；本轮及后续跑 tests/app 时用短 basetemp 即可。
- **R2 持久预算门禁（默认关闭）**：新增 `deeptutor/services/llm/budget.py` 与 `llm_budget.json` 设置（`enabled/window_days/max_requests/max_total_tokens/max_cost_usd/reservation_ttl_minutes`，0=不设限）。状态表（`budget_window/budget_reservations/budget_settled`）与 usage ledger 同库 `usage.sqlite3`（O3 备份自动覆盖，无提示词/密钥/正文，仅数值与标识）。预留用 SQLite `BEGIN IMMEDIATE` 原子完成"读当前用量→查上限→插入"；窗口到期滚动 epoch 并清扫旧在途；TTL 过期在途清扫为 `crashed`（仍计数）。保守结算：completed+usage→实际；completed 无 usage→chars/3.5 估算；failed/interrupted/crashed→预留上界（估算 prompt + 请求 max_tokens）；费用查静态价格表（`get_pricing(fallback=False)`），配置费用上限时未知价格拒绝（`unknown_price`）、窗口内有未知费用历史拒绝（`unknown_history_cost`）。挂钩点：services 层 `factory.complete/complete_with_config/stream`（逻辑调用级）与 agentic 层 `metrics.instrument_client`（SDK create 级，流式经 MeasuredStream 收尾结算）；预算拒绝抛 `LLMBudgetExceededError`（不重试），预算启用但存储不可用时 fail-closed。验收 `tests/services/llm/test_budget_gate.py` 13 项全绿：并发 8 争用只有预算内 3 个到达 provider、三类上限先拒后达、超时/未知 usage/真实子进程崩溃预留不免费、TTL 清扫仍计数、落盘失败保留 answer 且不重调模型（provider 次数=1、预留留 in-flight）、窗口滚动重置、agentic 非流/流两路径、默认关闭零触碰。
- **R3 底层 HTTP 计量**：`metrics` 新增任务级尝试计数（`note_llm_http_attempt`），在两个漏斗点计数——`openai_compat_provider._create_with_key_rotation`（覆盖普通调用、key 轮换、Responses input-status 重试、Responses→chat 退路、response_format 丢弃重试、forced tool 重试的每次底层请求）与 agentic `_KeyRotatingCompletions.create`。`CallMeasurement` 记录新增 `attempts`（未 bump 记 1），随 ledger 行持久化（`_CALL_FIELDS`），`TurnUsage.summary` 新增 `total_attempts`。`tests/services/llm/test_http_attempt_metering.py` 5 项断言选定入口真实尝试数：普通 1、3-key 429 轮换 3、Responses→chat 退路 2、response_format 重试 2、agentic 轮换 2，且均为一次上层 measurement 对应多次底层请求并已落账。价格口径沿用 O2：budget/UsageTracker 未知为 null/unknown；旧 `LLMStats` 兼容默认价格保留为已记录边界，未扩充价格表。
- **R4 旧辅助条件未知语义**：`LearningEvidence.hints_used` 与 `QuizAttempt.independent` 改 tri-state（默认 `None`=未捕获，0/`True` 才是"已捕获且无辅助"）；`AssessmentRecord.hints_used` 同步 None 化（解析失败→None，不伪造 0）。判定收紧：`learning_stage`（独立需 `is True`/`== 0`；"有辅助"需 `is False`/真值，未知落 `practiced_not_demonstrated`）、`visual_achievements`、`display_mastery`（未知降级到 mastery_levels）、`calculate_mastery`（未知不进独立分）、repair 的 hints 聚合（未知不伪造提示）、`scheduler._resolved_quality` 容忍 None、notebook recovery 快照回退问题自身辅助标记。notebook API 边界保持整数契约（`to_notebook_item` None→0；`NotebookEntryItem/UpsertEntryRequest` 与前端契约不变，无 web 改动）。验收 `deeptutor/learning/tests/test_legacy_assist_conditions.py` 8 项全绿：旧 JSON 无字段→存储往返/二次保存仍 None；旧定性通过不升 independent 且显示降级，显式 0 才独立；旧 quiz 尝试未知独立不升不降；视觉成就需显式 0 提示；junk 解析为 None；调度器不崩。
- **受影响回归与整合**：learning+mastery 范围 **728 passed / 0 failed**；budget/metering 与既有 ledger/retry/auth/structured/usage 统计/CLI 定向 **98 passed**；最终受影响链路整合（执行记录 10 范围 + 新增三测试文件 + agentic client 消费方 + key rotation/responses fallback/metrics）**1566 passed / 2 skipped / 0 failed in 444.15s**（`data-r2r3r4-integration.log`）。改动 Python 文件 Ruff 0.16.0 check/format 全过（`deeptutor/` 全包 check 通过）。中途一次全量 `tests/services/llm/` 目录跑被中止（25 分钟无输出，疑个别文件网络等待；历史上各批均未整目录跑过），以定向受影响范围为准，未把该中止记为失败或通过。
- **边界与未闭合**：预算门禁仅覆盖 factory 与 agentic create 两入口——`fetch_models` 等元数据调用、其他 SDK 直连未覆盖；费用为静态表估算非账单；预算无设置界面/CLI（直接编辑 JSON）；启用前零行为变化，**不据此放行付费任务，B4 预算项按"可配置防线已实现、全局硬预算未声称"记账**。R4 后旧记录在 notebook 卡片上仍显示 0 提示（整数契约边界，阶段/掌握判定已如实未知）。O3 范围外项（外部 KB、多 workspace、完整导出删除、升级兼容）维持 B4 未完成。真实模型闭环、语义审核、浏览器流程与 B5 延迟复测仍待额度恢复后按 9.5 执行。
- **交付**：应用户指令，R1–R4 的代码、测试、README 与本文一并提交并推送至个人 fork 的 `codex/learning-offline`（不推上游或 main、不用 force）。提交前重跑了改动文件 Ruff 0.16.0 check/format、`scripts/check_repo_hygiene.py`、`git diff --check` 与 detect-secrets 1.5.0 扫描；当前虚拟环境缺 `pre_commit` 模块，未执行 pre-commit --all-files，未把检查缺席记为通过。本轮沿用本会话已实际跑出的整合/定向结果，未为提交重跑全套功能测试，未调用真实模型。提交与远端 SHA 以实际 Git 核对及本会话交付消息为准；不以提交代替验收，各批放行状态以本节记录为准。

## 9. 等待额度期间：离线可靠性优化实施计划

### 9.1 目标、边界与执行顺序

目标：在不消耗真实模型额度的前提下，确认学习证据不会丢失、重复推进或被错误覆核，并具备有限调用保护和可验证的数据恢复办法，为第一次真实学习试用准备可靠基础。

本轮是 B1–B4 中可独立实施部分的细化，不另起新一套产品路线。按下表顺序逐批交付，每批同步第 5、8、9 节；已有能力满足验收时记录证据直接复用，不为“优化”重写。三个批次完成后可报告“本轮离线范围完成”，不得据此标记 B0–B5 或整个 MVP 完成。

| 顺序 | 对应原批次 | 交付物 | 当前状态 |
|---|---|---|---|
| O0 接手与可重复运行 | 所有批次的前置 | 现场快照、隔离工作区、可运行的定向测试入口 | 离线完成；见执行记录 6 |
| O1 记录与复习一致性 | B1/B2/B3 的离线部分 | 真实存储/接口复现、必要的最小修复与回归防线 | 有界离线交付；R1 新记录自动补偿已实施（执行记录 12），R4 收紧旧辅助条件为显式未知（执行记录 13）；旧无快照投影不回填的边界保留 |
| O2 调用保护 | B4 的调用部分 | 有界调用策略、用量未知状态、预算覆盖范围与缺口记录 | 鉴权降级重调/未知价格已修（执行记录 8）；R2 实现可配置持久预算门禁+在途预留+保守结算（默认关闭，覆盖 factory/agentic 两入口，执行记录 13）；未覆盖入口与"非全局硬预算"边界见执行记录 13 |
| O3 备份与恢复 | B4 的数据部分 | 最小本地备份恢复流程或脚本、隔离恢复验证 | 选定存储离线实现与隔离恢复通过，范围外项保留；见执行记录 9 |

本轮不调教学提示词、语义评分标准和调度公式，不批量建题库、不生成整书、不接入新付费服务、不换主模型，也不扩到新的媒介或多用户功能。测试可使用自制题目和假 provider，但必须标记为离线契约验证，不能当作真实题目质量证据。

**O0 起步要求**：

1. 读根 AGENTS.md、CONTRIBUTING.md、本文；检查分支、HEAD、未提交改动、worktree、实际数据位置与服务进程。保护本计划的未提交修改。功能开发使用隔离 worktree 和 `codex/` 分支，保证基线含 `217ffe3d`、`6986d9ca`，不要切到不含这些修复的旧基线。
2. 使用本项目 uv 托管的 CPython 3.12 环境；新 worktree 单独核对依赖，不复制或删除用户数据，不默认 `python` 指向正确解释器。只有观察到环境缺失时才安装最低必要依赖。
3. 若再次遇到 10106，先验证 `asyncio` / `_overlapped` 导入和上述 Windows 环境变量。执行记录 5 的办法只作用于当前命令进程：通过 `[System.Environment]::GetFolderPath('Windows')` 获取并检查 Windows 目录，设置 `SystemRoot`、`WINDIR`、`ComSpec` 及 `PYTHONUTF8=1` 后重试；不做系统级网络重置，不因这个异常修改应用逻辑。
4. 定向重跑执行记录 5 的 19 项作为起点。另行复核历史 `test_async_reading_action_can_be_retried_after_timeout[True]`；若确为测试调度竞争，优先用事件同步保留超时与可重试的语义，不靠删除用例、任意放大超时或标 skip 让结果变绿。失败仍保留原始输出。

### 9.2 O1：记录与复习一致性

先画清 reading quiz、Mastery Path、Question Notebook 的题目→作答事件→评估→学习证据→复习投影关系，明确各自存储边界。入口为 `deeptutor/learning/assessment.py`、`service.py`、`policy.py`、`storage.py`、`deeptutor/services/session/sqlite_store.py` 与 reading quiz API。执行记录 2 的风险是核验线索，不能跳过复现直接认定现状有漏洞。

| 场景 | 必须观察到的结果 |
|---|---|
| 保存后关闭并重新打开存储/进程 | 原始回答、题目标识、来源 locator 与已捕获 revision、辅助条件、评估结果能恢复；旧数据未知 revision 仍明确为未知，不能补成当前版本 |
| 同一提交重试、并发重复与新一次作答 | 同一事件最多推进一次；真正新作答被保留；同刻提交有确定的最新投影；旧请求重试不会覆盖新回答 |
| 跨 session/learning 库中途写入失败 | 已保存的原始作答不丢失；重开后补偿可收敛；reconcile 重复执行不重复推进，不为补数据库重新调用模型 |
| 作答覆核、更正或作废 | 原评估与更正理由可追踪；掌握展示、学习证据、复习时间和 Notebook 展示一致；只移除受影响证据，不清掉其他题的有效记录；重复覆核仍幂等 |
| 作答前接口响应 | reading quiz 与 Mastery Path 均不下发参考答案、评分要点或正确选项标记；检查实际 JSON/事件，不只看界面隐藏；状态元数据与真正答案内容分别判断 |
| 已看答案或带提示的作答 | 不能记为独立掌握；前台展示与持久证据一致；无法追溯的辅助条件明确保留为缺口 |

优先复用并扩展 `tests/api/test_reading_quiz_answers.py`、`deeptutor/learning/tests/test_assessment.py`、`test_mastery_state_integrity.py`、`test_guided_mastery_updates.py`、`test_storage.py` 及 session store 相关测试。必须有真实临时 SQLite/文件存储和关闭重开验证；跨进程恢复至少覆盖一条自制作答链，单纯 mock 或复用同一内存对象不算重启证据。

修复优先沿用不可变事件、现有投影与补偿流程；若确认缺题目/评估版本或覆核关联，先检查现有 ID/事件能否满足，再补最小字段和向后兼容。不要直接重构整个存储层或另建学习引擎。批次交付需列出每个场景的“复用／已修复离线通过／仍未知”，未过项不勾完成。

### 9.3 O2：调用保护

核对 reading quiz、Mastery Path 到共享 LLM 入口的真实调用路径，复用现有配置、UsageTracker 与 usage ledger。候选入口为 `deeptutor/services/llm/`、`deeptutor/runtime/agentic/`、`deeptutor/services/config/runtime_settings.py` 和相关能力设置；先确认生效层，不新增旁路调用。

1. **有界请求**：记录实际上下文、输出、并发、超时及各层重试上限，核对 SDK、transport、structured retry 叠加后的总尝试次数。鉴权/配置错误不盲重试；失败后保留原结果与请求标识，数据库落盘失败不自动重调模型。
2. **诚实计量**：区分服务商返回、估算、未知、失败和超时后可能计费的状态；未知不能显示为 0 或免费。检查未知模型是否套默认价格、估算是否有标记，再决定最小修复；不在此时维护整张模型价格表。
3. **预算边界**：验证是否已有可持久化的调用前预算检查与在途预留。若缺失且能在共享入口小范围补齐，可补配置、并发预留和失败后的保守结算防线；覆盖不了的入口明确列出，不宣称全局保护。没有用户实际预算/价格时不猜金额，不启用真实付费批量任务，不因此阻塞 O3。
4. **离线验收**：假 provider 记录真实调用次数，覆盖鉴权失败、超时、重试耗尽、并发争用、达到已配置上限拒绝新请求、usage 缺失，以及已有成功结果保存失败。断言次数、状态和持久记录，不能只断言错误文案。

参考已有 `tests/services/llm/test_provider_auth_retry.py`、`test_provider_retry_classification.py`、`test_structured_retry.py`、`test_usage_ledger.py`、`tests/core/test_record_streamed_usage.py` 与 usage statistics 测试；新增测试仅针对确认的风险和实际改动。

应用侧请求/Token/费用限制与服务商账号周额度分开：本应用无法保证控制同一账号其他客户端的消耗。若硬预算尚未实现或覆盖不全，O2 可记录有限交付，但 B4 对应验收项继续保持未完成；不得以 usage 统计替代预算防线。

### 9.4 O3：备份与恢复

优先提供最小本地维护流程或脚本，不新增云同步、定时任务或管理界面。先盘点实际 storage/schema、所有者目录与引用关系，再决定打包范围。

- **恢复范围**：原始作答与不可变评估事件、题目/来源标识及已捕获版本、学习证据与复习状态、Notebook 投影，以及核对这些引用所需的材料 manifest、单元与历史 revision。明确哪些内容未纳入；原书与批注导出不能替代该备份。
- **一致性**：优先在已停止写入的隔离实例备份；在线 SQLite 使用一致性备份机制，不能仅复制正在写入的主 `.db` 而遗漏 WAL，也不能把跨库不同时间的快照冒充整体一致。
- **最小操作保护**：备份记录 schema/应用版本与文件校验信息；中断的备份不能呈现为成功。恢复默认到新目录，覆盖已有目录必须拒绝；不在用户真实目录执行删除或回滚试验。备份默认不含模型密钥，恢复环境的模型配置另行本地处理。
- **验收链**：在临时实例写入自制作答与修订记录→关闭/一致性备份→恢复到另一新目录→重新打开接口/存储→核对记录数量、原始回答、来源文本、revision、掌握与到期时间→重复提交/补偿仍不重复推进。另覆盖损坏或不完整备份被明确拒绝。

删除和迁移先核对实际范围，测试只用临时数据；本轮不增加真实数据批量删除功能。完整导出格式、全部删除语义、全部升级兼容如未覆盖，仍留在 B4，不因一次恢复成功整体关闭。真实书籍、个人回答、备份和日志均留在核实已忽略的本地目录，不进 Git。

### 9.5 每批验收、交付与停止条件

- 每批先给真实复现与最小修复，再运行改动相关回归和 Python lint/format。涉及 API 字段、前端或用户文案时补对应契约生成、i18n、前端测试与构建；不改前端则不为凑检查重跑全站。修复必须有能拦住复发的适当测试或代码约束，不只补说明。
- O1–O3 收尾执行受影响完整链路的整合检查，记录命令、准确 passed/skipped/failed、未执行项及原因；不得沿用历史总数当成本次通过数。离线检查通过、真实调用通过、语义审核通过、个人试用通过分开报告。
- 每批更新同一文档：场景结论、涉及文件、实际提交（若有）、兼容影响、验证结果、未闭合项与下一步。先完成一个可验收单元，再继续下一批；不因测试通过自动进入新的教学功能开发。
- 出现必须依赖真实生成结果才能判断的差距，保留样本与问题，继续其他独立离线项。O1–O3 可执行范围结束后等待额度恢复，保留 B0/B1 真实闭环、B3 语义质量、B4 未覆盖项、B5 至少 7 天延迟复测。
- 恢复额度后先核实服务商/模型/单次预算、当前运行代码，再做一次小范围连接与交互；随后用真实 PDF、EPUB 各一个小单元验证完整学习链，审核全部题目/反馈和引用，记录消耗，再决定教学优化。不得用短调用成功代替完整单元验收。

### 9.6 新会话剩余开发顺序（2026-10-25）

前会话已更新文档、提交并 push；随后两个会话按用户指令续接：R1（事务快照/自动补偿）与 R2/R3/R4（预算门禁、底层计量、旧辅助条件未知语义）均已实施并离线验证，见执行记录 12、13。**本节是第 9 节的续接，不新增平行任务清单；O1/O2 的有界交付边界保留。** R1–R4 的离线契约已实现并有防线测试；下一阶段不是继续扩离线范围，而是等待额度恢复后按 9.5 做真实试用验收，或按下方”剩余小批”按需推进。

| 顺序 | 剩余工作与入口 | 放行证据 | 当前状态 |
| --- | --- | --- | --- |
| R1：O1 自动补偿 | `learning/storage.py` 在源事务内保存 outbox 快照，`learning/notebook_recovery.py` 负责无模型投递；Web 启动/恢复周期、Mastery 状态读取及工具同步入口自动补偿。未捕获快照的历史作答/覆核不回填，详见执行记录 12。 | 已覆盖真实临时双库及作答、更正、作废各自跨进程恢复；原始回答、原评估、更正理由可追踪；重复/并发/确认失败补偿不重复推进，其他题证据保留，旧事件不覆盖新回答，provider 调用次数为 0。 | **已实施**：定向 86 passed；整合补跑 1344 passed / 4 skipped / 0 failed（此前 5 failed 为 tests/app 在默认 pytest 临时目录超 Windows MAX_PATH 的环境限制，短 basetemp 复跑通过，见执行记录 13）。不宣称所有历史投影已恢复。 |
| R2：再补 O2 预算门禁 | 先画清 factory/provider/SDK 内部兼容重试的生效入口，沿用 runtime JSON 设置、usage ledger。补配置驱动的持久化调用前检查、原子在途预留和保守结算；默认不猜真实金额或价格、不启用付费任务。 | fake provider + 真实 SQLite：并发争用只有预算内请求到达 provider；达到已配置请求/Token/费用上限时拒绝新调用；超时/未知 usage 和崩溃后的 reservation 不被当成免费；重启后仍有效；结果已保存但后续落盘失败不重调模型。费用限制若仅覆盖部分入口须逐项标明，不能声称全局硬预算。 | **已实施（默认关闭）**：`services/llm/budget.py` + `llm_budget.json` 设置 + factory/stream 与 agentic `instrument_client` 两入口挂钩；13 项离线验收全绿（含真实子进程崩溃预留、并发争用 8 取 3、TTL 清扫、落盘失败不重调、窗口滚动、未知价格拒绝），见执行记录 13。未覆盖入口与边界逐项列明；启用与金额由用户配置后才生效，不据此放行付费任务。 |
| R3：闭合 O2 计量边界 | 记录 provider 内 key rotation、Responses/chat、参数兼容与凭据恢复实际 HTTP 尝试，关联请求标识与上层作答；核对旧 `LLMStats` 默认价格与所有未知费用展示。可与 R2 分成两个小批，不能用上层一次 measurement 代替底层多次请求。 | 对选定入口断言底层真实尝试数、provider 返回/估算/未知/失败状态和持久记录；未知不记 0 或默认便宜模型价格。模型价格表不在此时扩充；真实账单准确性仍待选定服务商后核验。 | **已实施**：任务级 HTTP 尝试计数经两个漏斗点（`_create_with_key_rotation`、agentic `_KeyRotatingCompletions.create`）覆盖普通/key 轮换/Responses input-status 重试/Responses→chat 退路/response_format 丢弃重试；ledger 行新增 `attempts`、summary 新增 `total_attempts`；5 项断言测试全绿。价格沿用 O2 口径（fallback=False，未知为 null/unknown）；旧 `LLMStats` 兼容默认价格保留为已记录边界。 |
| R4：整理无法追溯项与 O3 边界 | 旧辅助条件缺少证据时保留”未知”，不得追填独立作答或编造历史提示；核对新记录是否充分捕获。O3 的外部 KB、多 workspace、完整导出删除和升级兼容继续列在 B4，按实际试用需要另定小批。 | 新增记录的辅助条件真实落盘并进入展示；旧记录的未知状态不被刷新/重试改成独立通过。已有 O3 测试保持通过；没有扩大恢复范围的实现和隔离验证时不勾 B4 完成。 | **已实施**：`hints_used`/`independent` 改 tri-state（None=未捕获），learning_stage/visual_achievements/display_mastery/calculate_mastery/repair 聚合/scheduler 收紧判定；notebook API 边界保持整数契约不变；8 项验收测试全绿（含存储往返不回填、旧定性通过不升级）。O3 测试在整合范围保持通过；O3 范围外项继续留在 B4。 |

**剩余小批（按需，非阻塞）**：① 预算门禁目前无设置界面/CLI，配置方式为直接编辑 `data/user/settings/llm_budget.json`（字段见执行记录 13）；真实试用前若需要界面再单独小批。② 预算未覆盖入口（`fetch_models` 等元数据调用、其他 SDK 直连）按需评估。③ O3 范围外项（外部 KB、多 workspace、完整导出删除、升级兼容）维持 B4 未完成，按实际试用需要另定。

R1–R4 的开发与离线契约完成后，才可报告相应离线缺口关闭；真实 PDF/EPUB 学习闭环、语义审核与至少 7 天复测仍独立保留。本文件每批更新；不为让状态变绿删除用例、补造历史或自动放行付费调用。

## 10. 新会话可直接使用的指令

**交付位置（2026-10-25）**：origin 为上游 `HKUDS/DeepTutor`，个人 fork remote 为 `fork`（`git@github.com:JueJuez/DeepTutor.git`）。R1–R4 改动（代码、测试、README 与本文）已按用户指令提交并推送至 `fork/codex/learning-offline`；接手先用 `git status --short`、`git log -1 --oneline` 和 tracking ref 核对实际基线与未提交改动，保留现场成果。最新代码与本文在 `C:\Users\O1830\.codex\worktrees\learning-offline\DeepTutor`，本地分支 `codex/learning-offline`。原工作区仍为 `main / cfb3e8d1`，只维护续接指针，原稿及数据保留；不要重置主工作区或重复实施已有修复。后续提交/push 按该会话用户指令处理，不推上游或 main。

> 请在现有隔离 worktree C:\Users\O1830\.codex\worktrees\learning-offline\DeepTutor 的 codex/learning-offline 分支续接 PDF/EPUB 个人学习助手。先读 AGENTS.md、CONTRIBUTING.md、本文执行记录 13 与 9.6，必要时回看 6–12，用 git status --short、git log -1 --oneline 和 fork tracking ref 核对基线；R1–R4（事务快照补偿、预算门禁、HTTP 尝试计量、旧辅助条件 tri-state）已提交推送，不重做已通过修复。离线可开发范围（R1–R4）已完成并有防线测试；剩余小批见 9.6 末尾（预算设置界面、未覆盖入口、O3 范围外项），仅在用户要求时推进。用户模型额度恢复后，按 9.5 核实服务商/模型/预算与运行代码，先做一次小范围连接与交互，再用真实 PDF、EPUB 各一个单元验证完整学习链，审核全部题目/反馈和引用，记录消耗；预算门禁启用方式为编辑 data/user/settings/llm_budget.json（enabled 与各上限，见执行记录 13），默认关闭。保护原工作区数据及未提交计划；不调用真实付费模型、不绕过额度或更换服务商，不扩教学提示词/评分/调度算法。B4 范围外项与 B5 至少 7 天延迟复测继续保留。当前授权是续接剩余工作；提交/push 按该会话用户指令处理。
