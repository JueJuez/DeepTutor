# PDF / EPUB 个人学习助手：验证与开发计划

更新：2026-10-30。状态：O0–O3 有界交付；R1–R4 实施并离线验证；B0/B1 真实调用通过（执行记录 14）；B2 推理隔离、解释审核与阅读来源持久绑定已实施并有真实正例（记录 15–19）；浏览器阅读链验证完成（记录 20–21）；**新 CommandCode key 已接入（记录 22）：引用回跳点击级验证通过，EPUB 原分类目标重测为正确拒绝（故障模式消除），批次节奏改为"每 2 项→更新文档→提交 push"**。B5 未开始，不代表整体 MVP 完成。开发分支为 `codex/learning-offline`，本地隔离 worktree 为 `C:\Users\O1830\.codex\worktrees\learning-offline\DeepTutor`；已推送提交以实际 Git 核对及 `fork/codex/learning-offline` tracking ref 为准，接手先核对、不重置或覆盖。原工作区数据和未提交计划保留。

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
| B0 本机运行基线 | 检查 Python/Node/包管理器、端口、已有配置与数据；按本仓库安装启动；配置一个主模型；导入一个 PDF 和一个 EPUB | 原书可读，一次小范围模型交互可用；记录运行命令、依赖障碍、usage/未知项和原有缺陷 | **真实调用通过（执行记录 14）**：主模型 CommandCode deepseek-v4-flash 配置并连通；真实 PDF/EPUB 导入定位复核；小范围交互与 usage 记录可用（cost=unknown 为已知口径） |
| B1 现成闭环与差距核验 | 各选一个单元，走阅读→学习路径→独立回答→应用反馈→到期复习；逐项填第 3 节证据；读 scheduler、存储与相关测试 | 每项明确“复用／需修复／未知”；有实际复现和最小修复范围，不能仅引用 README | **真实调用通过（执行记录 14）**：两种格式各一单元走通 阅读→quiz→作答→判分→持久化→幂等 与 掌握路径→独立作答→语义反馈→复习队列生成；浏览器流程与跨天复习推进仍未验 |
| B2 来源与作答可信链 | 仅修复已确认的定位、版本、异常材料、答案隔离和原始作答保存问题 | 一个单元引用可靠；提交前网络响应无答案；刷新/重启恢复；错误与缺证据不能升级掌握 | 既有三项修复保留；O1 追加修复 reading 答案键隔离，恢复与并发专项离线通过；真实流程已验（执行记录 14：题卡公开 payload 无答案键、revision/hints 落盘）；**整回合推理隔离已真实复验；阅读引用现已绑定至题目、定性评估和 Notebook，旧版重开/权限失效检查通过；PDF 与 EPUB 原文范围内正例已有真实调用证据（执行记录 18），浏览器回跳与完整样本验收仍未做；本批交付范围与提交核对见执行记录 19**。**浏览器侧：定位/目录跳转/位置保存与刷新恢复已通过（刷新恢复两缺陷修复后复验，执行记录 20）；EPUB 桌面浏览器复核通过且 linear="no" 封面翻页死端已修复（执行记录 21）；引用回跳点击级验证已通过、EPUB 原分类目标重测为正确拒绝（执行记录 22）** |
| B3 反馈、掌握与复习 | 补齐实际缺失的语义评估边界、辅助条件、覆核、事件幂等和日程一致性 | 正确/错误/部分正确/等价表达/不知道均经审核；并发与重复提交、覆核重算、时区测试通过 | O1 修复并发初始化、辅助条件投影并验证重复覆核；R1 覆核自动补偿已实施；R4 将旧记录辅助条件收紧为显式"未知"。执行记录 14 报告的等价表达接受、错误判分与部分正确行为保留；**执行记录 16 从原事件发现负梯度反馈解释错误，语义质量重新打开；执行记录 17 新增解释审核门禁并通过已知反例真实回归，仍不能称两单元全部反馈审核通过**；覆核/时区真实调用场景未重演 |
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

当前交付以第 5 节及执行记录 18–19 为准：本地安装、有限真实 PDF/EPUB 调用、解释审核与阅读来源可信链已有证据；原 EPUB 分类比较目标仍未通过。浏览器完整流程、扩大语义样本、用户独立试用与延迟复测仍未完成。以下执行记录保留各阶段当时的状态；历史“未提交”“旧代码运行”“等待额度”等字样不能替代接手时的 Git 与运行状态核对。

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

### 执行记录 14 2026-10-25（9.5 真实模型验收：PDF/EPUB 各一单元完整学习链，人工语义审核通过）

- **现场与数据归属（接手先核对）**：worktree `codex/learning-offline / ba1715b9` 干净、已推 fork。主工作区 `main / cfb3e8d1` 的 8001（uvicorn）与 3782（Next standalone）服务**仍跑旧代码、用主工作区数据**，本轮全程未动。worktree 数据目录独立（DEEPTUTOR_HOME=worktree 根），本轮新建：从主工作区复制 `model_catalog.json`（conn-cmdcode / deepseek/deepseek-v4-flash，OpenAI 兼容 `https://api.commandcode.ai/provider/v1`，密钥在本地 settings 不进 Git）到 worktree `data/user/settings/`（已核对 git-ignore），`llm_budget.json` 保持 `enabled=false`（按用户指令未开预算门禁）。以 worktree venv 在 **127.0.0.1:8002** 起隔离后端跑当前代码，验收后已停。
- **连接与计量**：CLI chat 小交互成功（20.6k tokens）；usage ledger 按调用记录模型名/状态/`attempts`（R3 计量生效），未知成本如实显示 cost=unknown（O2 口径）。
- **PDF（material `cd182bf9e84a911a`，单元 62「1.5.1 梯度下降：基础」）**：quiz 生成 3 道选择题，逐题对照单元全文人工审核——全部可答、引用成立；公开 payload 仅含 id/prompt/choices/material_revision，无正确项/解释（O1 隔离修复在真实响应生效）。作答 2 对 1 错：判分与星级正确；`assessment_attempts` 落 revision=1、hints_used=0、原始选项文本与 section_id=62；同 submission_id 重试幂等（不新增 attempt、attempt_count=1、奖励不重复）；Notebook 投影 3 条。
- **掌握路径（PDF，会话 `unified_1792941600093_680d460f`）**：tutor 经 SDK 驱动（`mastery_path` capability，题卡以下一轮 `mastery_answer` 回答）建 5 知识点路径并逐题考核，共 10 次交互、8 个回合。① 换说法的等价表达（一阶泰勒+柯西–施瓦茨论证负梯度方向）被语义评估**满分接受**；② 故意机制性错误（"学习率大更稳定"）被判错、kp3 归 0、error_record 建立，反馈定位为"机制理解颠倒"并用数值表格重讲，变式重考后恢复 1.0；③ 5 个 KP 全部过门槛，复习队列按指数遗忘生成（kp3 约 9.5h 后到期，失败 KP 间隔更短）；④ R1 outbox 13 条、Notebook 投影 13 条。
- **EPUB（material `d9508cc08c037ea5`《提问的艺术》）**：真实空单元 unit 1 → quiz 生成 **422 拦截**、unit 端点返回 `empty: true / char_count: 0`（B2 修复在真书生效）。单元 5（引言）quiz 3 题逐题审核可答、引用成立（Q2"损者"为原书自带译法，题目忠实原文）；作答 2 对 1 错，判分、reward、attempt 记录（rev=1、section=spine locator）全部正确。
- **掌握路径（EPUB，会话 `unified_1792942688827_0b8fe6b4`）**：把单元节选贴给 tutor 后建 2-KP 小路径。kp0 开放题换说法作答过门；kp1 应用题**部分正确被判 partial**——反馈区分"揪对假设"与"问题仍可从报表取数、未掀开前提"两个层次，给标尺与示范后出同型变式；会话收尾如实报告"kp1 还开着，没算过"，不冒充掌握。
- **消耗**：全程 **58 次 LLM 调用，1,070,698 tokens**（prompt 991,101 / completion 79,597；大量 cache 读），ledger HTTP attempts=58=调用数（无隐藏重试）。分项：小连接 ~2.1 万；PDF quiz 链 ~2.4 万；PDF 掌握路径 ~48 万；EPUB quiz 链 ~1.5 万；EPUB 掌握路径 ~53 万。掌握路径 agentic 回合是成本大头（单回合 2.6 万–10.6 万 tokens）。
- **发现（未修复，待用户裁决优先级）**：
  1. **thinking 事件流可含答案标记**：tutor 组题时的模型推理流（`thinking` 事件，客户端可见且随 turn 持久化）出现 `expected_answer: A` 等字样（events.jsonl 中 10 处命中）。题卡与判分键都在服务端，但若前端在作答前渲染 thinking 即构成作答前线索，属 B2"作答前响应不泄露"口径的新缺口（本轮验收事件日志在 worktree `data/mastery-pdf-u62/events.jsonl`，git-ignored）。
  2. **reading_references 未挂载正文**：`TurnRequest.reading_references(material, revision, locators)` 传入后 tutor 自述读不到材料（工作区/知识库均无），路径目标从模型通识生成（`source_grounded: false`）；把原文贴进消息后教学正常，但 `source_grounded` 仍为 false——该标志与实际依据脱节。掌握路径的"来源与版本"契约（目标锚定原文、引用可回原文）在真实流程尚未闭合。
  3. 题目质量小疵：个别选择题选项自带解释近乎自曝正确项（PDF 单元 62 第 2 题选项 A）；不影响可答性，属教学优化范畴。
- **状态判定**：B0/B1 两种格式的"真实调用通过"；B3 语义审核（本会话人工审核两单元全部题目/反馈/引用）通过；本轮未做浏览器端完整流程、未到 7 天延迟复测日期、B4 未覆盖项维持原状——**不标整体 MVP 完成**。下一批次二选一：先修发现 1/2（答案隔离与材料挂载），或先进入教学优化（题目质量/提示词）；听用户裁决。验收产物：worktree `data/mastery-pdf-u62/`、`data/mastery-epub-u5/`（事件 JSONL、驱动脚本 `data/mastery_driver.py`），均在 git-ignore 范围。
- **交付**：应用户指令，本文（执行记录 14 + 第 5/10 节状态）作为唯一改动提交并推送至 fork `codex/learning-offline`（不推上游/main、不用 force）。本轮只改文档，未改功能代码，未重跑功能测试；真实调用消耗以本记录与 usage ledger 为准。第 10 节续接指令已重写为新会话接手口径。


### 执行记录 15 2026-10-26（修复执行记录 14 的两个发现：thinking 答案隔离与掌握路径材料挂载）

- **决策与范围**：新会话核对基线 `4511545c`（干净、与 fork tracking ref 一致）后，用户在"先修两个缺口 / 直接进教学优化"中拍板先修缺口。本轮属 B2 口径内小批修复：thinking 流作答前答案隔离、掌握路径挂载单元正文；不动调度公式、评分标准、题目质量与提示词（教学优化批次保留）。未调用真实模型。
- **缺口 1 根因**：mastery tutor 走 chat agentic 循环，组题轮的模型推理经 `agent_loop._call_llm` 逐 chunk 实时写入 `thinking` 事件（客户端可见且随 turn 持久化），执行记录 14 的 events.jsonl 中 10 处命中（9 处 thinking 含 `expected_answer: A` 类推理 + 1 处 tool_result 校验文案，后者不含答案值）。tool_call 展示参数此前已被敏感参数剥离覆盖（`tool_dispatch._sensitive_arg_names`），thinking 是剩下未隔离的通道。
- **缺口 1 修复（按轮持有）**：`agents/loop/pipeline.py` 新增聚合钩子 `_capability_thinking_hold_tools`（沿 `owned_tools`/`rebinding_tools` 既有模式，默认空集，chat 行为不变）；`capabilities/mastery/loop.py` 声明 `thinking_hold_tools = ("mastery_quiz",)`；`agent_loop._call_llm` 在 hold 集非空时按轮缓冲全部 thinking 发射点（4 处：inline think、provider reasoning 兜底、Responses reasoning items、delta reasoning），轮末定型 tool_calls 后判定——轮内调用了 hold 名单工具则整轮丢弃，否则按原 metadata 补发；传输异常轮随失败丢弃不补发。组题轮的推理在模型写出答案键之后才可能被补发/丢弃，不改变 provider 侧推理回放（`thinking_blocks` 走 LLM 消息通道，与事件流无关）。代价：mastery 回合的推理轨迹改为轮末到达（原本逐 chunk 实时）。
- **缺口 2 根因**：会话 turn executor 的 SourceInventory 只在 chat 能力路径构建；非 chat 能力（mastery_path 等）的 else 分支只拼 notebook/history/book，`reading_references` 被静默丢弃。mastery 只依赖建向导绑定的 topic 材料（`_topic_material_manifest`），真实验收传入的 reading_references 未产生任何上下文 → tutor 自述读不到材料、目标从通识生成、`source_grounded` 恒 false。
- **缺口 2 修复**：`_turn_runtime_shared.py` 新增 `_reading_reference_manifest`（复用 `resolve_reading_sources` 的用户隔离与 fail-closed 语义：文本只来自当前用户 ReadingStore、已删材料/未知 revision 不产生行、不因材料失败打断 turn）与 `_merge_mastery_source_mounts`（新轮引用遮蔽 topic 材料同 sid，沿 chat 路径"本回合材料优先"先例）；executor 的 mastery 分支在 topic manifest 后解析本回合 reading_references 并合并进 `mastery_topic_source_index` + `source_manifest`，tutor 的 `read_source` 无需改动即可读取单元全文（index 键 `rd-<material>-r<rev>-<locator>` 与 chat 一致）。
- **边界与保留**：`source_grounded` 的置位链路未改——仍只在 `mastery_prepare_lesson` 的 lesson evidence 验证通过时置真；本修复让真实材料可被 tutor 与备课证据读取，`source_grounded` 能否在真实流程翻转属真实调用验证，不在此勾选。thinking 持有为 mastery 能力声明，其他能力（如 immersive_reading 的题目生成走独立 pipeline）不在本批范围。选项自曝等题目质量项留教学优化批次。
- **防线测试**：`tests/agents/chat/test_agent_loop.py` 新增 3 项（hold 轮推理不外泄且后续轮正常补发；无 hold 时推理照常实时流——防过度抑制回归；mastery 声明 `mastery_quiz` 且普通 chat 为空集）；`tests/services/session/test_mastery_reading_reference_mount.py` 新增 4 项（真实 ReadingStore 解析进 manifest/index、未知材料 fail-closed、合并先例、空解析不覆盖 topic 状态）。
- **验证**：定向回归全部通过——`test_agent_loop.py` 117 passed；mastery 能力/教学交付/-reviewed-revision + reading 引用 + source inventory + mastery group runtime 191 passed；`tests/services/session` + `tests/api/test_reading_quiz_answers.py` 487 passed / 1 skipped。改动文件 uvx ruff check/format 全部干净。真实前端是否在作答前渲染 thinking、修复后 mastery 真实回合的推理轨迹表现与 `source_grounded` 翻转：按 9.5 待额度恢复后真实复验。
- **交付**：本轮未提交未推送（按当前会话授权，等用户指令）；改动共 7 个文件（5 源码 + 2 测试）+ 本文。第 10 节续接指令已更新。

### 执行记录 16 2026-10-26（MVP 现场与实测复核）

- 用户确认本轮“MCP”指 MVP 项目进度和实测。现场为主目录 `main / cfb3e8d1` 与隔离目录 `codex/learning-offline / 4511545c`；执行记录 15 的 5 个源码、2 个测试及本文改动仍未提交（其中材料挂载测试为 untracked）。保留全部现有改动，不重复实施，不提交或推送。
- 只读重查真实 `data/user/usage.sqlite3`：58 条调用，全部 completed；prompt=991,101、completion=79,597、total=1,070,698、HTTP attempts=58，与记录 14 一致。未知费用仍未知，本轮没有新增真实模型调用。
- **语义反例，重新打开 B3**：`data/mastery-pdf-u62/events.jsonl` 第 2671 行，turn `turn_1792941924382_573bf547af`、question `d67ad66171d54ab5a02f021d37f4ddab`，正确选项判为 A，但公开 `feedback` 和 `explanation` 都写“梯度为负意味着增大 θ 会使损失上升，那么要降低损失就该增大 θ”。首句方向颠倒且与后句矛盾：一维可微函数在导数为负的点，足够小的正向增量使损失局部下降。选项与更新方向正确不能证明解释正确；本条推翻“全部题目/反馈语义审核通过”的笼统结论，原始回答、判分与历史记录不改写。
- **根因与优化边界（RCG）**：本例判分接受了正确选项，但模型生成的解释含机制错误；既有验收未独立逐句核对解释，判分正确与解释正确被合并为通过。后续语义回归须将同题题干、选项、答案、解释、来源一起审核；本例用导数符号或简单函数 `L(θ)=(θ−3)²` 验算。原事件作为失败样本保留；本轮尚未新增运行时解释校验，不能声称产品防线已补齐，也不靠改掉历史一句话声称生成质量修复。
- **答案隔离复核边界**：旧 PDF 日志有 9 条 thinking 事件含 expected_answer，均随后调用 mastery_quiz；旧 EPUB 日志也有 9 条，其中 1 条在 mastery_mode/mastery_build 前讨论出题和答案键字段。后者尚未证实泄露具体答案，但说明应在真实复验时覆盖组题之前的轮次，不能只查最终 quiz 轮。执行记录 15 的按轮隔离不等于整个 mastery turn 的推理均已隔离。
- **本轮定向验证**：补跑 `tests/agents/chat/test_agent_loop.py` 与 `tests/services/session/test_mastery_reading_reference_mount.py`，**121 passed in 347.24s，0 failed**；这是离线代码回归，不替代修复后的真实调用和浏览器验证。`git diff --check` 通过。
- **下一步**：先保留并核对错误解释及其原题，完成两项 B2 修复的小范围真实复验，再验证反馈解释改进与选项自曝问题；不重复整套百万 Token 流程。B4 未覆盖项、B5 用户独立作答与至少 7 天复测仍未关闭；2026-10-25 的代理驱动样本不代表用户本人已开始延迟学习实验。

### 执行记录 17 2026-10-26（解释审核门禁与整回合推理隔离）

- **范围与基线**：用户要求继续处理，沿现有 `codex/learning-offline / 4511545c` 未提交成果推进；不切换模型、不启用预算、不改调度公式或历史真实作答，未提交/push。本批只闭合新生成解释的审核门禁和已复现的推理泄露；原书持久证据链仍保留未完成。
- **解释错误根因与修复（RCG）**：选择题正确标签可直接判分，随后原样展示注册时的 explanation；旧 bind_questions 在无来源证据时跳过，在有来源时也只明确要求题目和答案键受支持。现在有解释的题目必须经过同一有界审核入口，独立返回严格布尔 explanation_valid=true；缺字段、false、字符串 true 或调用失败均不发布题卡、不保存作答或推进掌握。来源已有审核时复用该调用；原先无来源的解释题增加一次审核，每组 1–4 题仍只调用一次，不增加单独的第二轮审核或自动改写重试。工具描述补充符号、因果方向和每句解释自检。
- **持久防线与兼容**：PendingQuestion.content_review 私有保存当前题干/选项/答案/解释的 fingerprint 和审核回执，重开后可校验篡改；公开题卡继续走白名单投影。该回执与 source_evidence 分开，不能冒充原书依据或自动置 source_grounded。旧题缺回执仍是历史未审核状态，不编造通过、不回填、不改历史解释；直接引擎注册等既有低层入口不据此宣称全覆盖。审核本身是模型判断，有误差，必须保留语义抽检。
- **先失败再修复**：新增无来源反例、缺失/错误类型 verdict、回执重开与篡改、空解释无调用、来源支持不能替代解释审核、组题中一题失败不发布整组等回归。修复前 4 failed / 1 passed；首次整合 6 failed / 53 passed，发现旧源审核 fixture 缺新字段、两条旧覆核 fixture 缺审核 mock，逐项补全而非放宽生产门禁（日志 data-feedback-review-offline.log）。随后相关 9 文件 126 passed（data-feedback-integration.log）。
- **有限真实解释回归**：在独立临时 LearningStore 中取原错误题的副本（原题/选项/答案不改），使用既有 CommandCode deepseek-v4-flash 真实审核：原错误解释 supported=true / explanation_valid=false，被门禁拒绝；修正为“负导数下足够小的正向增量使损失局部下降”后，两项均 true，被接受。只证明此已知反例的有限回归有效，不能推广成普遍语义质量通过。记录在忽略的 data/feedback-review-live/。
- **推理隔离的真实失败与修复**：首个 SDK 掌握路径小回合成功读取 PDF unit 62、建 1-KP 路径、发出经审核题卡，但早于 mastery_quiz 的推理里仍出现 expected_answer 标签讨论（700 条 thinking、3 处字段命中）。根因是工具调用名称只能说明本轮执行动作，不能限制更早轮次计划答案。改为 MasteryLoopCapability.private_thinking，AgentLoop 四类推理输入统一不向客户端发事件；普通 chat 继续流式推理，模型侧推理回放和教学正文不变。定向 3 passed / 114 deselected。第二个真实 SDK 回合读取原文并切回本批新建路径、重现已有题卡，客户端 thinking=0，仍有正常 content、tool_result、done；它是保留题卡流程，不冒充又生成了新题。
- **来源链真实结论**：读取原文成功仅确认挂载与 read_source 生效；当前 ReadingStore 引用不进入基于 KB/PDF 的 selected_scope 备课证据链，测试路径没有建立 lesson_evidence，source_grounded 仍 false。本轮不为显示绿色直接改标志。下一小批需明确阅读单元的持久材料版本、定位与证据审核/重开/失效契约后补齐；源码入口为 lesson_evidence.selected_scope / prepare_lesson / validate_evidence 与 semantic_assessment.bind_questions，不能把正文可读当作来源闭环已验收。
- **真实消耗与产物**：本轮本地 usage 库由 58 增至 70 条，增量 12 次调用 / 12 次 HTTP 尝试，155,790 prompt + 8,735 completion = 164,525 tokens；费用仍未知。包括两次反例对照与两个有限 SDK 回合及其内部记忆调用；没有重跑百万 Token 流程。原始失败保留在 data/mastery-fix-probe/，复验在 data/mastery-fix-probe-v2/。首个驱动在已写完结果后调用了不支持的 close 参数，留下 TypeError；第二次驱动改用真实 close() 正常结束，不把首轮驱动退出错误算作应用回合失败。
- **最终离线与检查**：首次整合 900 passed / 21 failed（data-feedback-final-integration.log），失败为旧 fixture 缺新审核 mock；补齐后相关 26 passed（data-feedback-all-fixture-fixes.log）。随后复跑在续接时工具进程已结束，日志仅到 85%，没有最终计数，不记通过；后续整合见记录 18。改动 Python Ruff 0.16.0 check/format、git diff --check、仓库卫生检查通过；未修改前端，未执行浏览器完整流程或全站构建。测试和驱动日志均在已核对的 Git 忽略范围。
- **下一步与边界**：先闭合阅读材料的持久来源证据链，再以 PDF/EPUB 小单元验证题目、解释和引用；选项质量、浏览器完整流程、B4 范围外项和 B5 用户独立学习/至少 7 天复测仍未关闭。本批通过项不能代替整个 MVP 验收。

### 执行记录 18 2026-10-26（阅读来源持久绑定、覆盖门禁与有限真实对照）

- **授权与范围**：用户再次要求继续，保留此前全部未提交改动，在同一 worktree 续接来源链。新增 learning/reading_evidence.py，复用现有 ReadingStore 引用解析、题目审核、学习事务、outbox 和 Notebook；不建整书向量库、不更换模型、不启用预算开关，不改调度公式或原始失败记录。
- **题目与来源**：mastery_quiz / mastery_prepare_lesson 的引用由运行时覆盖注入，模型不能注入原文。服务端按当前用户权限重新读取固定 material_id/revision/locator，保存原文文本、SHA256、精确引文及审核回执；发卡前与评分前都重新核对。引用缺失、未知修订、空单元、权限撤销、内容或目标变化均停止发题/评分，不写负面学习证据。旧修订可从归档读取；不把 revision 1 静默换成当前版。成功审核的阅读范围随路径持久化，后续回合可重新挂载，新的显式选择优先；纠正旧题仍重验旧题原修订。已有 KB/PDF 选择范围不能被阅读引用绕过。
- **备课与掌握边界**：阅读备课单独审核覆盖范围，保存完整目标/局部 focus/缺失内容和精确引文，支持经过重新授权及文本核对的缓存。只验证了具体题目或局部讲解，不能作为整个目标的定性过门证据。完整目标覆盖包才允许 mastery_assess 定性评分；模型判断仍有误差。source_grounded=true 表示存在已审核的来源包或具体题目，不等于整个路径已教完、用户已掌握或所有来源始终可访问。
- **持久记录**：题目和定性评估的 source_evidence 经原事务 outbox 保存并投递至不可变 attempt JSON；单一被引用单元同步实际 material_id/material_revision/section_id，逻辑路径与知识点另存 mastery_path_id/knowledge_point_id。多单元不伪造单一版本字段，完整依据留在 evidence 中。重复提交/补偿不重复推进，回执/引文不进入作答前题卡；文本证据不冒充原始页面像素检查。
- **有界调用与真实失败修复**：每次最多 6 个单元、合计 24,000 字符，过大明确拒绝，不静默截断。真实 EPUB 流程中，三次题目审核都耗尽旧 2,200 output tokens，且 reasoning_tokens=completion_tokens=2200，没有 JSON；不能把它们记作语义拒绝。来源/解释审核现用单次最多 4,096 output tokens，为推理和 JSON 留空间；评分保持原上限，不改全局模型设置。空/不可解析的审核响应有独立错误类型，同一回合后续换题不能再次触发审核调用；新回合可重试，未新增无限重试或自动模型回退。既有来源审核调用复用，组题最多 4 题仍合并一次。
- **真实 PDF 正例**：原 material cd182bf9e84a911a / revision 1 / locator 62，在新测试路径 reading-source-pdf-1792985133 上经 SDK 读取原文→阅读备课→带原文审核的选择题→程序性正确作答→Notebook attempt。source_grounded=true，题目 source_evidence.kind=reading；attempt 的 material_id/revision/section 为原 PDF / 1 / 62；客户端 thinking=0。focus 包只证明本次所选范围，不借此放行整目标定性评估。
- **真实 EPUB 失败保留与新正对照**：原测试路径 reading-source-epub-1792985220 的目标要求“解释好问题与索取信息的区别”。原文引言列出好问题的作用、CEO/爱因斯坦/德鲁克例子，却没有直接建立该分类对比；备课仅给部分覆盖。随后三次审核还发生上述输出耗尽，驱动在 180 秒边界取消末轮；没有题卡或学习证据，原目标仍未通过。Agent 对照单元原文后，另建 reading-positive-epub-1792985841 作为正对照，目标限定为“解释引言中好问题的作用，并用其中一个德鲁克提问说明”，不覆盖或改写旧目标。完整目标备课、开放题审核、换说法作答评分和定性评估均通过；两条 Notebook attempt 均记录原 EPUB / revision 1 / locator 5；定性作答 hints_used=1。该正例只证明所选原文范围内的有限链路，不修补原失败目标的验收结论。审核与评分使用同一模型配置，Agent 核对原文不等于用户/专家标注。
- **消耗与产物**：本次来源阶段台账增量 21 次调用 / 21 次 HTTP 尝试，245,841 prompt + 28,684 completion = 274,525 tokens；20 条 provider completed（其中 3 条无 JSON）、1 条 failed 且用量为估算，不能当作实际结算或免费，费用仍未知。结果分别在忽略的 data/reading-source-live/ 与 data/reading-source-positive/，原失败保留；程序作答不代表用户独立学习，B5 延迟试用未开始。
- **验证**：来源链定向 40 passed、扩展关联范围 79 passed、新增覆盖/缓存/定性/故障测试 17 passed；输出预算及同回合阻断追加范围 47 passed，均单列不相加。扩大整合为 **2121 passed / 2 failed / 2 skipped / 5 subtests passed，939.24s**。两项失败分别为结算恢复测试的 mock 未接收新增 reading_references 参数、摘要投影测试依赖隔离目录外的 agents.yaml；已分别补显式参数断言与最小配置 stub，未放宽生产门禁。覆盖两处修复、来源/解释/语义审核、读取挂载和模型历史的最终定向范围 **72 passed in 36.03s**（data-source-final-followup.log）。整合启动后追加了审核输出保护，不能把分次结果拼成一次最终代码的全量全绿；原失败日志与完成标记保留。执行脚本 data/source-final-checks.ps1、日志 data-source-final-integration.log、完成标记 data/source-final-exit.json 均已忽略。Python Ruff 0.16.0 check/format、后端架构边界、前端 contracts:check、仓库卫生与 diff 检查通过；pre-commit 未安装，未执行。未改前端，未运行全站构建或浏览器完整流程。
- **剩余**：B3 仍需扩大新样本、人工核验全部题目/解释/来源与争议；B4 未覆盖入口、完整导出删除/迁移等边界保留；原书界面的真实引用回跳/刷新恢复和用户独立试用、至少 7 天复测仍待完成。不会把原目标失败、模型回执、程序正确作答或测试数量改记为整体质量通过。

### 执行记录 19 2026-10-26（本批文档、提交与推送交付）

- 用户明确要求先更新文档，再提交并 push。交付分支为 codex/learning-offline，目标为个人 fork 的同名分支；不推 main 或上游，不创建 PR，不改主目录旧服务、原书或学习记录。
- 本批覆盖执行记录 15–18 的源码、合成测试和本文：整回合私有推理、解释审核与无 JSON 响应的回合内阻断、阅读单元版本/定位/引文持久绑定、备课覆盖门禁、Notebook 来源同步及相关隔离测试修正。第 5/8/9.6/10 节的当前状态与交接入口同步更新，历史失败保留；实际提交和远端 SHA 以 Git 核对及本次交付消息为准。
- 验证证据沿用记录 18 的准确分层结果：扩大整合 2121 passed / 2 failed / 2 skipped，修正两处测试依赖并覆盖最后追加的审核输出防线后，最终定向 72 passed。不将分次结果相加冒充最终全量全绿。本次文档交付不重新调用模型，也不为提交重跑无关功能套件。
- 提交前执行改动 Python 的 Ruff 0.16.0 check/format、仓库卫生、分支策略、diff 和选定文件的凭据扫描；pre-commit 主程序的离线依赖不齐，未执行完整 pre-commit，不能把单项检查写成完整检查已通过。运行产物、原书、个人回答、凭据、模型配置、测试缓存、日志和虚拟环境均不进入提交。
- 本批交付不关闭 B3 整体语义质量、B4 未覆盖项或 B5 真人学习与至少 7 天复测；下一步仍是浏览器定位/引用回跳/刷新恢复，以及扩大原文范围内的语义对照。提交推送本身不代表整体 MVP 验收完成。

### 执行记录 20 2026-10-29（浏览器阅读链验证；刷新恢复两缺陷修复）

- **现场与范围**：worktree `codex/learning-offline / 1c35e1d2` 开工时干净、与 fork tracking ref 一致；主工作区 `main / cfb3e8d1` 未动，其旧服务此前已停。以 worktree 数据目录（运行 home=worktree 根，模型配置与既有学习数据在其中）`deeptutor start` 起隔离服务（backend 8001 / frontend 3782），首跑自动重建前端生产构建；auth 关闭。本轮改动 3 个前端文件 + 新增 2 个 spec + 修复 1 个过期契约测试 + 本文，未提交/未推送。
- **浏览器测量限制（非产品缺陷）**：ZCode 内置浏览器 webview 的 `requestAnimationFrame` 完全饥饿（setTimeout 正常），所有 rAF 延迟的 UI 状态（页码指示器、可见页测量、位置保存）冻结到强制出帧为止。判定以截图强制刷帧 + 后端 API 落库值为准；不把该环境因素记为缺陷。
- **浏览器验证通过**：材料库 → 新建集合「学习验收」→ 加入两份材料 → 从集合进入阅读器；PDF（599 页）渲染与翻页指示正常；目录（1041 entries）跳转定位到 62「梯度下降：基础」，正文与图 1.8 正确；阅读位置保存落库（locator=100）。
- **缺陷 1（已修复）位置保存竞态导致进度回归**：打开材料时文档视图挂载即上报 locator=1，400ms 防抖保存会在 resume 的 `GET /position` 返回前落库，把已存进度覆盖为 1；此后 resume 永远读到 1、永不跳转（重载一次即丢进度）。修复：`ReaderPane` 新增 `positionResumeReadRef`，位置保存门禁至 resume 读取落定；回归 spec `tests/reading-position-resume.spec.tsx` 2 项（stored position 未读前不保存；读取落定后正常保存）。
- **缺陷 2（已修复）resize anchor 恢复吞掉跳转滚动**：文档加载完成时页面列表替换加载态、滚动条出现触发宽度重测，anchor 在跳转前视口（第 1 页）捕获；React 重渲染 599 页后 layout effect 提交（晚于跳转滚动约 105ms），anchor restore 把 scrollTop 从 83655 写回 0，resume 跳转被静默清零。证据：sessionStorage 时间线 `jump(locator 100, st 83655)@37656 → anchor(locator "1")@37761`，且 React fiber 内省确认 jump prop 仍在、`scrollToLocator` 曾成功执行。修复：`PdfDocumentView` 在跳转处理开始与滚动落地时使过期 anchor 失效（anchor 语义仍保留给用户真实的阅读中缩放）。
- **修复后浏览器复验**：重载后恢复到存储位置（scrollTop=83655，指示器 Page 102/599，内容为 1.15 投机解码区域，与存储的 page 100 对应），随后存储位置按实际可见页更新为 102，不再回归第 1 页。指示器与存储值存在 ±2 页的"最大覆盖页"口径差，不影响恢复语义。
- **测试与检查**：vitest 定向 spec 全绿——`reading-pdf-jump-after-load.spec.tsx` 2 项（新增；断言 jsdom 可观测的渲染窗口契约，不含布局几何）、`reading-position-resume.spec.tsx` 2 项（新增）、`pdf-reading-resize` + `reading-text-navigation` 8 项；node 套件 **1318 passed / 0 failed**——其中修复 O1 批次遗留的过期契约断言（`reading-extensions.test.ts`「reading quizzes reveal grading」仍要求客户端组件含 `correct_choice_index`，与 O1 答案隔离修复冲突；改为断言组件无答案键、判分来自服务端 verdict）。web `tsc` 全量与改动文件 eslint 通过。本轮未跑 Python 套件（未改 Python）。
- **阻塞与保留**：① CommandCode key 再次 401（Invalid Authorization，2026-10-29 实测；catalog 仅此一个连接），阅读伴侣问答、引用回跳的浏览器点击验证与第 10 节的语义对照样本扩展全部待额度恢复；引用跳转与已修复的 jump 机制同链，模型可用后需补点击级验证。② EPUB 阅读器在本 IAB 内容区空白（`/render` 314KB 200 已到位，epub.js rendition iframe 未挂载；翻页无内容），本环境无法区分帧饥饿与产品缺陷，保留待桌面浏览器复核；EPUB 数据链（导入/定位/quiz/空单元 422）维持执行记录 3/14/18 的 API 层证据。③ 浏览器窄屏操作、错误提示与完整 B5 流程未验。服务在轮末停止：`deeptutor stop --home "C:\Users\O1830\.codex\worktrees\learning-offline\DeepTutor"`，重启 `deeptutor start --no-browser --detach`（worktree 根）。
- **交付（2026-10-29，用户指令）**：先更新本文（执行记录 20 + 第 5/10 节），随后提交并 push。提交范围为上述 3 个前端文件、2 个新增 spec、1 个契约测试修复与本文，共 6 个文件；目标为个人 fork 的 `codex/learning-offline`，不用 force、不推 main/上游，不新建 PR。提交前重跑：vitest 定向 spec（`reading-pdf-jump-after-load` 2 项、`reading-position-resume` 2 项、`pdf-reading-resize` + `reading-text-navigation` 8 项）、node 套件 **1318 passed / 0 failed**、web `tsc` 全量与改动文件 eslint、`scripts/check_repo_hygiene.py`、`git diff --check`。本轮未改 Python，未重跑 Python 套件；前端生产构建在验证阶段已实际重建并复验。运行产物、原书、个人回答、凭据、模型配置、测试缓存、日志和虚拟环境均不进入提交。实际提交与远端 SHA 以 Git 核对及本次交付消息为准；提交推送不代表整体 MVP 验收完成。

### 执行记录 21 2026-10-30（EPUB 桌面浏览器渲染复核；linear="no" 封面翻页死端发现并修复）

- **现场与记录 20 交付补完**：worktree `codex/learning-offline / 1c35e1d2` 开工时与 fork tracking ref 一致；主工作区未动。按记录 20 已记录的用户指令重跑提交前检查全绿（vitest 定向 12 项、node 套件 1318 passed / 0 failed、web `tsc`、改动文件 eslint、repo hygiene、`git diff --check`）后提交 **`9f5ef28d`** 并推送 `fork/codex/learning-offline`（无 force、不推 main/上游）；`web/next-env.d.ts` 的 dev/prod 构建翻转属生成产物，不进提交。以 worktree 数据目录起隔离服务（backend 8001 / frontend 3782），auth 关闭。
- **EPUB 桌面浏览器复核（第 10 节事项②，改用桌面内核）**：本会话浏览器注册表仅有 ZCode IAB（webview rAF 饥饿、无法定责），按记录 14/20 的隔离验收惯例改用 **Playwright 自带 Chromium（chrome-win64 1228，桌面 Blink 内核、rAF 正常、headless）** 驱动 `http://localhost:3782/learning/reading/rw_14a9e87faf094fb092e55c3eca5c621d`（「学习验收」集合，激活材料为 EPUB《提问的艺术》）。**渲染结论：EPUB 渲染链正常**——`/render` 200（314KB）、epub.js rendition iframe 挂载（834×767）、封面图完整呈现、第 2/3 节正文（版权信息 150 字、目录 1056 字）渲染正确、位置恢复与保存（GET/PUT `/position`）正常、全程无 console/page 错误。记录 20 的"内容区空白"在桌面内核不复现，维持"IAB 环境受限"判定；封面页 textLen=0 属正常（封面为纯图片单元）。
- **新发现真缺陷：linear="no" 封面是翻页死端**：打开位置为封面（locator 1）时点击"下一页"（aria-label Next，点击确认落在按钮上）无任何反应，`rendition.next()` 直调后 `currentLocation()` 仍为原 CFI，IAB 的"翻页无内容"在桌面内核同样复现且无任何报错。定因链（React fiber 内省读 rendition 内部 + epub.js 0.3.93 源码 + 原 EPUB OPF 三方印证）：本书 OPF 封面为 `<itemref idref="x_cover.xhtml" linear="no"/>`（出版商标准做法）；`epubjs/lib/spine.js` 对非 linear 项绑定的 `item.next/prev` 恒返回 undefined，`DefaultViewManager.next()` 拿到 undefined 后静默返回——**非 linear 节成为翻页死端**。普通书 spine 项缺省 `linear="yes"`（`packaging.js` 对缺失属性默认补 "yes"），仅显式 `linear="no"` 的书受影响；隔离实验证明从第 2 节起 next/prev 与直显各节均正常。
- **最小修复（不改 epub.js、不换库）**：`web/lib/epub-page-turn.ts` 新增纯函数 `bridgeEpubNonLinearTurn`——当前节 `linear === false` 时解析相邻 linear 节 href（连续非 linear 一步跳过；线性节/未知 href/越界返回 null 走 rendition 原生翻页）；`EpubDocumentView.turnPage` 在调 `rendition.next/prev` 前先查桥接，命中则 `rendition.display(相邻节.href)`；`EpubSection/EpubBook` 类型补 `index/linear/spineItems`。新增 3 项 node 回归（相邻桥接与 prev 边界、连续非 linear 跳过、linear/未知 href 不桥接）。
- **验证**：node 套件 **1321 passed / 0 failed**；`epub-display-preferences.spec.tsx` 5 项通过；web `tsc` 全量与改动文件 eslint 通过。前端生产构建重建（`deeptutor start` 指纹触发，约 280s）后桌面 Chromium 真书复验：封面 → 下一页 → 版权信息（150 字）→ 目录（1056 字），position 落库 `locator=3`、CFI `epubcfi(/6/6!/4/56/2/1:0)`、percentage 2.6%——翻页→relocated→保存链路完整。截图与驱动脚本在 worktree `data/`（git-ignored）。
- **边界与保留**：① 从 linear 节往回翻仍按 epub.js 语义跳过非 linear 项（如从版权信息 Previous 回不到封面，经目录/大纲可回），未额外处理；② ZCode IAB 内 iframe 是否挂载仍无法定责，仅作测量受限环境记录；③ 引用回跳点击验证、语义对照样本扩展仍待 CommandCode 密钥（2026-10-29 实测 401）；④ EPUB 分类比较目标（记录 18 口径）仍失败待真实额度；⑤ 本轮改动（`web/lib/epub-page-turn.ts`、`web/components/reading/EpubDocumentView.tsx`、`web/tests/epub-page-turn.test.ts` 与本文）已按用户 2026-10-30 指令提交并推送 `fork/codex/learning-offline`（实际 SHA 以 Git 核对为准；不推 main/上游、不用 force）；⑥ B5 延迟复测、窄屏/错误提示、B4 范围外项维持保留，MVP 不标完成。

### 执行记录 22 2026-10-30（新 KEY 接入；引用回跳点击级验证通过；EPUB 原目标重测为正确拒绝；批次节奏确立）

- **KEY 与授权**：用户提供新 CommandCode key（聊天交付；本文不落密钥）。`/models` 与最小 chat 均 200，写入 worktree `data/user/settings/model_catalog.json` 的 `connections[0].api_key` 与 `services.llm.profiles[0].api_key`（**后者是 LLM 链实际生效位**；git-ignored 已 `git check-ignore` 核对）。旧 key（尾 TeeM63）维持作废。
- **Omni-Edu 调研（github haolpku/Omni-Edu）**：开源教育基础模型项目（Qwen3.5 底座 4B/9B/27B，K-12 SFT 约 7 万样本）+ 12 个教育评测基准 SDK。对本期**无直接代码复用**——本地 GPU 门槛且不触"不换主模型"红线；可借鉴的是其评测维度（诊断推理/教学脚手架/证据引用）作为 B3/B5 语义审核 rubric 参考，4B FP8 本地路线仅记录不在本期。按第 4.8 节纪律只按需借鉴结构，不安装其管线。
- **引用回跳点击级验证通过（第 10 节事项①，桌面 Chromium + 真模型）**：伴侣问答真实可用——回答引原文（精确引文 + `[p.5]` 定位引用），链接化为 9 个 `#dt-material-<id>-revision-1-locator-5` 锚点；点击后经 ReaderPane `navigateCitation` 跳至 locator 5（CFI `epubcfi(/6/10!/4/2[dt-reader-heading-1-1]/1:0)`），position 落库，阅读器头部指示 0%→5%。**首轮探测误报"无锚点"系探针选择器只匹配 `#dt-locator-` 前缀——带 materialId 时 href 走 `MATERIAL_LOCATOR_HREF_PREFIX`（`web/lib/reading-citations.ts` buildLocatorHref），产品无缺陷**；记录 20 遗留疑虑解除。工具链证据：`material_outline` / `read_material`（tool_metadata locators=[5]）/ `reader_goto`×3（locator 5 + 逐句精确引文）经 `verifiedReadingLocators` 校验；伴侣跳转部分由 `reader_goto` 服务端导航承担，点击锚点回跳独立成立。观察项：伴侣转写重载后默认开新会话（历史在会话列表），属现行为非缺陷。
- **EPUB 原分类比较目标重测（记录 18 口径）**：以原目标逐字（"解释好问题与索取信息的区别，并用引言中的一个例子说明"）+ 原单元（EPUB revision 1 locator 5）新建路径 `reading-source-epub-retest-1793297683` 重跑。链路全通（read_source → mastery_prepare_lesson → learning_update → mastery_quiz，question_source_kind=reading，无错误无超时），**记录 18 的故障模式（审核输出 2,200 tokens 耗尽无 JSON）未复现**——4,096 上限修复生效，一次 Cloudflare 5xx 由既有有界重试吸收。**目标仍不通过且为正确拒绝**：coverage complete=false（scope=focus），missing 明确"原文只列出好问题的特征并给出例子，没有说明什么是索取信息的问题，也没有对比两者"——来源文本不支撑分类比较目标，覆盖门禁如实降级为聚焦题（题卡 source_evidence.kind=reading）。原失败结论保留，不修补验收；"重测并定性"这一验证项本身完成。
- **消耗（`data/user/usage.sqlite3` 实测）**：25 次调用 / 25 次 HTTP 尝试，prompt 190,764 + completion 14,212 ≈ 204,976 tokens；24 completed、1 failed（该条用量为估算，不当作实际结算或免费）；费用仍未知（O2 口径）。覆盖 KEY 最小测试、EPUB 重测与两次伴侣问答。
- **测试与检查**：本轮**零功能代码改动**（驱动脚本在 git-ignored `data/`：`reading_source_epub_retest.py`、`reading-source-retest/`、`companion_citation_check.mjs`、`citation_click_check.mjs` 等）；按第 6 节"仅文档变更不运行功能测试"，未重跑套件。
- **批次节奏（用户 2026-10-30 确立）**：每批约 2 项 → 更新本文 → 提交并 push `fork/codex/learning-offline`（已授权；不推 main/上游、不用 force）→ 下一批。下一批候选：语义对照样本扩展（记录 18 口径：读 coverage、具体引文与失败样本）、B3 人工语义审核扩充；B5 完整浏览器流程与至少 7 天延迟复测保留。



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

R1–R4 已实施并离线验证（记录 12–13）；额度恢复后已经完成有限真实调用、缺口修复和阅读来源链对照（记录 14–18）。本节保留 O1/O2 的有界交付与 B4 未覆盖范围；下一阶段按第 10 节推进浏览器完整流程、扩大语义样本和用户独立试用，不重复开发已实现部分，也不把有限正例当作整体验收。

| 顺序 | 剩余工作与入口 | 放行证据 | 当前状态 |
| --- | --- | --- | --- |
| R1：O1 自动补偿 | `learning/storage.py` 在源事务内保存 outbox 快照，`learning/notebook_recovery.py` 负责无模型投递；Web 启动/恢复周期、Mastery 状态读取及工具同步入口自动补偿。未捕获快照的历史作答/覆核不回填，详见执行记录 12。 | 已覆盖真实临时双库及作答、更正、作废各自跨进程恢复；原始回答、原评估、更正理由可追踪；重复/并发/确认失败补偿不重复推进，其他题证据保留，旧事件不覆盖新回答，provider 调用次数为 0。 | **已实施**：定向 86 passed；整合补跑 1344 passed / 4 skipped / 0 failed（此前 5 failed 为 tests/app 在默认 pytest 临时目录超 Windows MAX_PATH 的环境限制，短 basetemp 复跑通过，见执行记录 13）。不宣称所有历史投影已恢复。 |
| R2：再补 O2 预算门禁 | 先画清 factory/provider/SDK 内部兼容重试的生效入口，沿用 runtime JSON 设置、usage ledger。补配置驱动的持久化调用前检查、原子在途预留和保守结算；默认不猜真实金额或价格、不启用付费任务。 | fake provider + 真实 SQLite：并发争用只有预算内请求到达 provider；达到已配置请求/Token/费用上限时拒绝新调用；超时/未知 usage 和崩溃后的 reservation 不被当成免费；重启后仍有效；结果已保存但后续落盘失败不重调模型。费用限制若仅覆盖部分入口须逐项标明，不能声称全局硬预算。 | **已实施（默认关闭）**：`services/llm/budget.py` + `llm_budget.json` 设置 + factory/stream 与 agentic `instrument_client` 两入口挂钩；13 项离线验收全绿（含真实子进程崩溃预留、并发争用 8 取 3、TTL 清扫、落盘失败不重调、窗口滚动、未知价格拒绝），见执行记录 13。未覆盖入口与边界逐项列明；启用与金额由用户配置后才生效，不据此放行付费任务。 |
| R3：闭合 O2 计量边界 | 记录 provider 内 key rotation、Responses/chat、参数兼容与凭据恢复实际 HTTP 尝试，关联请求标识与上层作答；核对旧 `LLMStats` 默认价格与所有未知费用展示。可与 R2 分成两个小批，不能用上层一次 measurement 代替底层多次请求。 | 对选定入口断言底层真实尝试数、provider 返回/估算/未知/失败状态和持久记录；未知不记 0 或默认便宜模型价格。模型价格表不在此时扩充；真实账单准确性仍待选定服务商后核验。 | **已实施**：任务级 HTTP 尝试计数经两个漏斗点（`_create_with_key_rotation`、agentic `_KeyRotatingCompletions.create`）覆盖普通/key 轮换/Responses input-status 重试/Responses→chat 退路/response_format 丢弃重试；ledger 行新增 `attempts`、summary 新增 `total_attempts`；5 项断言测试全绿。价格沿用 O2 口径（fallback=False，未知为 null/unknown）；旧 `LLMStats` 兼容默认价格保留为已记录边界。 |
| R4：整理无法追溯项与 O3 边界 | 旧辅助条件缺少证据时保留”未知”，不得追填独立作答或编造历史提示；核对新记录是否充分捕获。O3 的外部 KB、多 workspace、完整导出删除和升级兼容继续列在 B4，按实际试用需要另定小批。 | 新增记录的辅助条件真实落盘并进入展示；旧记录的未知状态不被刷新/重试改成独立通过。已有 O3 测试保持通过；没有扩大恢复范围的实现和隔离验证时不勾 B4 完成。 | **已实施**：`hints_used`/`independent` 改 tri-state（None=未捕获），learning_stage/visual_achievements/display_mastery/calculate_mastery/repair 聚合/scheduler 收紧判定；notebook API 边界保持整数契约不变；8 项验收测试全绿（含存储往返不回填、旧定性通过不升级）。O3 测试在整合范围保持通过；O3 范围外项继续留在 B4。 |

**剩余小批（按需，非阻塞）**：① 预算门禁目前无设置界面/CLI，配置方式为直接编辑 `data/user/settings/llm_budget.json`（字段见执行记录 13）；真实试用前若需要界面再单独小批。② 预算未覆盖入口（`fetch_models` 等元数据调用、其他 SDK 直连）按需评估。③ O3 范围外项（外部 KB、多 workspace、完整导出删除、升级兼容）维持 B4 未完成，按实际试用需要另定。

R1–R4 的开发与离线契约完成后，才可报告相应离线缺口关闭；真实 PDF/EPUB 学习闭环、语义审核与至少 7 天复测仍独立保留。本文件每批更新；不为让状态变绿删除用例、补造历史或自动放行付费调用。

## 10. 新会话可直接使用的指令

**交付位置（2026-10-30，记录 22 后）**：origin 为上游 `HKUDS/DeepTutor`，个人 fork remote 为 `fork`（`git@github.com:JueJuez/DeepTutor.git`）。记录 20（`9f5ef28d`）、记录 21（`391ca9f3`）及记录 22 起的批次文档均已按用户指令/批次节奏提交并推送至 `fork/codex/learning-offline`；提交与远端 SHA 以实际 Git 核对及 tracking ref 为准，接手时 worktree 应干净（仅 git-ignored 运行产物除外）。接手先用 `git status --short`、`git log -1 --oneline` 和 tracking ref 核对实际基线，保留现场成果。最新代码与本文在 `C:\Users\O1830\.codex\worktrees\learning-offline\DeepTutor`，本地分支 `codex/learning-offline`。原工作区仍为 `main / cfb3e8d1`，其 8001/3782 旧服务已停；worktree 服务按执行记录 20 的命令启停。不要重置主工作区或重复实施已有修复。真实验收的隔离运行方式、驱动脚本与事件日志（git-ignored）见执行记录 14 末段与 21/22。新 CommandCode key 已在 worktree catalog 配置（git-ignored，本文不落密钥）；预算门禁仍默认关闭，真实批量生成前先经用户确认。

> 请在现有隔离 worktree C:\Users\O1830\.codex\worktrees\learning-offline\DeepTutor 的 codex/learning-offline 分支续接 PDF/EPUB 个人学习助手。先读 AGENTS.md、CONTRIBUTING.md、本文执行记录 14–22 及第 5 节，用 git status --short、git log -1 --oneline 和 fork tracking ref 核对基线；R1–R4、9.5 真实模型验收、记录 15–19 的推理隔离/解释审核/阅读来源绑定、记录 20–21 的浏览器链与翻页修复、记录 22 的引用回跳点击级验证与 EPUB 原目标重测（正确拒绝）均已实现，不重做。**批次节奏（用户 2026-10-30 确立）：每批约 2 项 → 开发/验证 → 更新本文 → 提交并 push `fork/codex/learning-offline`（已授权；不推 main/上游、不用 force）→ 下一批；开发完成后必须测试，零代码改动批次按第 6 节免跑功能测试并在记录中写明。下一批候选：① 语义对照样本扩展（记录 18 口径：读 coverage、具体引文与失败样本，不把有限正例当整体验收）；② B3 人工语义审核扩充；③ 浏览器完整流程（窄屏/错误提示）。** EPUB 分类比较目标已重测定性为正确拒绝，维持失败保留，不为变绿放行；不调调度公式、不批量建题库。运行方式：worktree 根 `.venv/Scripts/deeptutor.exe start --no-browser --detach`；浏览器验证用桌面内核 Playwright（驱动脚本见 `data/`，锚点选择器须兼容 `#dt-material-` 与 `#dt-locator-` 两种 href）；ZCode 内置浏览器 rAF 饥饿，只作测量受限环境记录。预算门禁默认关闭（`data/user/settings/llm_budget.json`），真实批量生成前先经用户确认。B5 至少 7 天延迟复测与 B4 范围外项继续保留；MVP 未完成。后续提交/push 按批次节奏处理，不推上游或 main。
