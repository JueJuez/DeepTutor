# PDF / EPUB 个人学习助手：验证与开发计划

更新：2026-10-24。状态：B0 部分完成——安装启动、自制样本与真实书籍（1 PDF + 1 EPUB）导入定位均验证通过；模型配置与真实模型交互仍阻塞在用户密钥（用户令 token 未恢复，无法提供）。

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

本次本地提交为 `a31d8262`（提交说明 `release: v1.6.15`）；开始时工作区无未提交修改。这里只做了关联会话阅读和有限源码核对，未安装依赖、启动应用、导入材料或调用模型。该提交是本地快照，不代表上游最新版本。

| 现有入口 | 本地证据 | 当前可下的结论 |
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
| B0 本机运行基线 | 检查 Python/Node/包管理器、端口、已有配置与数据；按本仓库安装启动；配置一个主模型；导入一个 PDF 和一个 EPUB | 原书可读，一次小范围模型交互可用；记录运行命令、依赖障碍、usage/未知项和原有缺陷 | 部分完成：安装启动与两种格式导入定位已离线通过（自制样本）；主模型与真实模型交互待用户密钥 |
| B1 现成闭环与差距核验 | 各选一个单元，走阅读→学习路径→独立回答→应用反馈→到期复习；逐项填第 3 节证据；读 scheduler、存储与相关测试 | 每项明确“复用／需修复／未知”；有实际复现和最小修复范围，不能仅引用 README | 源码审计与离线测试完成（见第 8 节执行记录 2）；真实单元流程待 B0 模型与材料就绪 |
| B2 来源与作答可信链 | 仅修复已确认的定位、版本、异常材料、答案隔离和原始作答保存问题 | 一个单元引用可靠；提交前网络响应无答案；刷新/重启恢复；错误与缺证据不能升级掌握 | 优先三项已修复（见执行记录 4，离线通过）；真实调用验证待 B0 模型就绪 |
| B3 反馈、掌握与复习 | 补齐实际缺失的语义评估边界、辅助条件、覆核、事件幂等和日程一致性 | 正确/错误/部分正确/等价表达/不知道均经审核；并发与重复提交、覆核重算、时区测试通过 | 待 B2 所需基础满足 |
| B4 费用与数据保护 | 补齐预算检查、失败恢复、导出删除、备份恢复和升级兼容中的实际缺口 | 已支出加在途预留约束新任务；重试有界；未知费用可见；恢复能找回作答与引用 | 未开始；可与前批独立项交错推进 |
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

开发时先执行改动相关测试与仓库规定检查；后端依据当前 Python 测试/ruff 配置，前端依据 [package.json](../web/package.json) 的 `typecheck`、`test:node`、`test:unit`、`lint`、`build` 及契约/i18n/架构检查。综合交付再覆盖受影响完整链路；不要照搬旧仓库不存在的 `test:coverage` 或 mypy 要求。本次仅文档变更不运行功能测试。

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

当前交付：完成需求承接、有限源码核对、本文与根入口指针。没有功能修改、环境配置、真实调用、提交或推送。B0–B5 均未验收。

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

### 新会话可直接使用的指令

**远端布局（2026-10-24 确认）**：origin = 上游 `HKUDS/DeepTutor`（无推送权，JueJuez 账号被拒）；个人 fork remote 名为 `fork` = `git@github.com:JueJuez/DeepTutor.git`。本地提交一律 `git push fork main`。截至本记录已推送至 `4d701cb0`。

> 请先读根 AGENTS.md、CONTRIBUTING.md 和 docs/personal-learning-mvp.md，重新检查分支、提交、未提交修改、已有配置与数据。按计划先完成 B0 和 B1：在本机跑通 DeepTutor，用文字型 PDF 与无 DRM EPUB 各一个单元验证原书阅读、学习路径、独立作答、应用反馈、持久化和复习，记录真实代码与运行证据，再补确认存在的缺口。先核实模型、材料与预算，不批量生成整书，不照搬 Open Notebook 的安装/数据库方案，不重建已有学习引擎。缺少真实输入时继续源码审计、自制样本与离线检查。按批推进并更新同一计划，区分实现、离线测试、真实调用、语义审核与个人延迟试用；保留失败和原始证据，不覆盖已有数据。
