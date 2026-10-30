# PDF / EPUB 个人学习助手：MVP 收尾与教学增强计划

更新：2026-10-30。状态：**MVP 收尾待执行；教学增强为候选方案，尚未开工；整体 MVP 未验收。**

本文是后续任务、状态和交接的唯一维护入口。[原计划](personal-learning-mvp.md)保留需求基线、验收标准与执行记录 1–23，不再维护第二份后续清单。本次获授权的是调研与计划整理，写入候选功能不代表用户已经决定实施、部署模型或扩大产品范围。

## 1. 当前结论与工作现场

**建议收口旧计划的执行阶段，将未完成项迁入本文；先完成现有 MVP 的交付验证，再按证据选择教学增强。** 不需要为了维护旧计划而继续堆积长日志，也不能把迁移写成整个 MVP 已完成。

- 实际开发位置：`C:\Users\O1830\.codex\worktrees\learning-offline\DeepTutor`，分支 `codex/learning-offline`。调研起点 HEAD 与本地 `fork/codex/learning-offline` tracking ref 均为 `005eb1f08aaf77120dfd5a7c710e4c071991e7b2`；这是现场读取结果，不是本轮远端网络同步证明。
- 原工作区 `D:\Code\project\study\DeepTutor` 位于 `main / cfb3e8d1`，有用户已有的计划修改及本地数据，不能覆盖。那里只保留续接指针，不作为当前实现基线。
- 已交付基础：O0–O3 有界离线可靠性工作、R1–R4，以及记录 14–23 的有限真实调用、来源绑定、推理隔离、解释审核、浏览器阅读恢复与引用回跳。最新功能提交为 `ca082138`，`005eb1f0` 同步其文档。
- 最近缺口：PDF p150 正样本未出题卡；综合样本不足；出题卡/学习模式的窄屏与平板流程未验；B3 部分真实场景、B4 范围外项、用户独立试用与至少 7 天复测未闭合。
- 本轮只审阅文档和源码，没有重跑历史功能测试、浏览器或真实模型，也没有新增学习效果证据。历史通过数仅见原计划各执行记录。

需求和完成标准继续采用原计划第 1–4、6–7 节：本机个人使用、中文优先、文字型 PDF 与无 DRM EPUB、原书学习、独立作答与延迟证据；不批量重写整书、不重写 scheduler、不引入多用户或新媒介。扫描/混合页、复杂图表等未可靠抽取时继续明确限制受影响单元。

## 2. Omni-Edu 调研：能借鉴什么

### 2.1 核验范围与证据边界

一手来源：官方仓库 README、SDK 与数据处理/评测源码，以及[论文 v1](https://arxiv.org/html/2609.23088v1)。通过临时目录只读克隆核对仓库提交 `94ede68ad50aa109380b3df558c87063038847e8`（提交日期 2026-10-29）；下文源码链接固定到该版本。没有安装 SDK、下载模型权重/完整数据集、训练模型、运行其评测或验证作者成绩。

Omni-Edu 提供 K–12 教育模型、推理 SDK、数据构建与评测工具；已审阅部分没有提供可替代本项目原书阅读、作答事件、复习持久化与备份恢复的完整应用。其公开成绩是作者报告，不能直接外推到中文成人读书、自选 PDF/EPUB 或个人延迟保持。[项目说明](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/README.md)

### 2.2 与本项目的对应关系

| 可借鉴点 | Omni-Edu 的具体来源 | DeepTutor 已有基础 | 建议与边界 |
|---|---|---|---|
| 区分知识正确性、目标/先修对齐、诊断、教学行动 | [论文的能力划分](https://arxiv.org/html/2609.23088v1#S3.SS1) | `KnowledgePoint.prerequisite_ids`、目标来源、语义评分、教学反馈 | 用于组织验收维度；不另建知识图谱或照搬 K–12 课程标准 |
| 将教学动作明确区分为诊断、提示、追问、直接解释等 | [任务指令注册表](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/sdk/src/omniedu/tasks.json) | Mastery 模式、`teaching_guidance`、`teaching_focus`、用户教学偏好 | 借鉴动作与当前作答状态的对应关系；不新增 19 个 capability，也不强制每轮苏格拉底提问 |
| 诊断应指向学习者的具体错误，并保留正确部分 | [错因审核量表](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/data_preparation/stage4_preliminary_diversity_selection_and_fine_grained_quality_filtering/prompts/sr_5_error_diagnosis.md) | `ErrorType` / `ErrorRecord`、原始作答、反馈、目标局部 observation | 先核验现有诊断是否有证据、能否指导下一步；不能从一次答错推断稳定能力或全局标签 |
| 给出最小有用提示，检查是否过早泄露答案 | [提示审核量表](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/data_preparation/stage4_preliminary_diversity_selection_and_fine_grained_quality_filtering/prompts/sr_8_minimal_scaffold.md) | 答案隔离、`assistance_used` / `hints_used`、独立与辅助证据 | 候选是有状态的逐步帮助和帮助后的新题独立作答，不把提示后答对计成独立掌握 |
| 跨会话历史只在有证据时使用，检查策略是否针对困难 | [长期教学审核量表](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/data_preparation/stage4_preliminary_diversity_selection_and_fine_grained_quality_filtering/prompts/sr_6_longitudinal_tutoring.md) | 不可变评估事件、`TeachingObservation`、策略 outcome 与当前消息引文验证 | 复用已有状态；无证据保持 unknown/tentative，用户纠正优先，不另建黑箱画像 |
| 将原始输出、审核、修订候选和复核分开留存 | [语义审核与修订流程](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/data_preparation/stage3_llm_assisted_semantic_auditing_and_rewriting/README.md) | 题卡/解释审核、失败样本与旧 revision 保留 | 用于提高本地样本可追溯性；不自动改原书、不覆盖原始作答、不凭模型分数直接发布修订 |
| 评测与报告按任务拆开，保留评判协议 | [评测注册表](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/sdk/src/omniedu/eval/benchmarks.json)、[报告入口](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/sdk/README.md) | 机械回归、真实调用日志、Agent 语义核对 | 优先建设自己的书籍样本回放与审核报告；外部基准仅作补充，模型审核不能替代用户试用 |

本地复用入口：[models.py](../deeptutor/learning/models.py)、[objective_relations.py](../deeptutor/learning/objective_relations.py)、[semantic_assessment.py](../deeptutor/learning/semantic_assessment.py)、[teaching.py](../deeptutor/learning/teaching.py)、[policy.py](../deeptutor/learning/policy.py)、[Mastery tools](../deeptutor/capabilities/mastery/tools.py)、[中文教学循环](../deeptutor/capabilities/mastery/prompts/zh/mastery_loop.yaml)。这些源码已在本轮读取；“已有结构”不等于现有教学质量全部通过。

### 2.3 不宜直接接入的部分

1. **SDK 不直接进入产品调用链。** [OpenAI backend](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/sdk/src/omniedu/backends/openai_backend.py)自行创建 `AsyncOpenAI`、管理重试；所审阅的返回结构未传递 provider usage。若原样从业务层调用，会引入本项目现有 budget/usage 链之外的路径。候选模型应通过 DeepTutor 现有 provider 接入，独立研究脚本也必须明确其计量与预算边界。
2. **训练语料与修订流水线暂不移植。** 先有本地可审阅样本和明确失败，再考虑候选修订；无需为了个人读书训练教育大模型。代码许可不代表第三方数据、权重和基准许可相同，使用前核对具体资源条款。[许可边界](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/README.md#code)
3. **外部评测规则不能直接变成产品学习规则。** [LongTutor 任务模板](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/sdk/src/omniedu/tasks.json)含固定的遗忘分类时间启发式；它不应替换当前 scheduler。其 [judge](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/sdk/src/omniedu/eval/judge/judge_longtutor.py)使用面向 K–6 的难度描述，且源码说明所沿用 ROUGE-L 分词对中文有明显局限。可借鉴审核维度，不能拿该分数作中文读书学习的质量结论。
4. **模型仅列为可选实验。** 是否部署 4B/9B/27B 取决于本地硬件、可用服务、总显存、成本与本地任务结果；本轮未检查这些条件。README 与 SDK preset 的模型命名空间存在差异（`lhpku20010120` / `OpenDCAI`），真正接入前须再次核对模型卡和 revision；不从别名推断某个服务已存在。[presets.py](https://github.com/haolpku/Omni-Edu/blob/94ede68ad50aa109380b3df558c87063038847e8/sdk/src/omniedu/presets.py)

上述优先级是本轮结合项目目标作出的建议，不是 Omni-Edu 作者对本项目适用性的验证。

## 3. 旧计划如何收口与迁移

原计划路径保持不动，保留需求、历史证据和日志，避免破坏已有引用。旧第 5、9 节变为迁移时快照，第 10 节改为本文指针；后续任务状态只更新本文。

| 原项 | 本次处置 | 本文承接项 | 关闭边界 |
|---|---|---|---|
| O0–O3、R1–R4 | 有界开发及离线验证阶段收口，保留历史证据 | C5 承接未覆盖范围 | 不重做已交付保护，不将历史未知记录补成已验证 |
| B0 运行基线 | 保留已有真实调用证据 | 每批现场检查 | 配置/模型/代码变更后按影响重新核对，不要求重复安装 |
| B1 现成闭环 | 已有有限真实闭环，跨天复习仍待验 | C3、C4、C6 | 复习队列生成不等于真实到期复习或延迟保持 |
| B2 来源与作答可信链 | 已有修复及正反例；保留原 EPUB 分类目标正确拒绝 | C1、C2、C3 | 拒绝越界目标是保护生效，不能改记为该目标学习通过 |
| B3 反馈、掌握与复习 | 五类作答仅有有限核对，尚未全量语义与场景验收 | C2、C4 | 不以单张题卡的五类结果关闭所有反馈质量 |
| B4 费用与数据保护 | 持久预算等已实现但默认关闭；仍有覆盖与数据生命周期缺口 | C5.1–C5.3 | 全部导出删除/升级兼容、外部 KB/多 workspace 不静默划掉 |
| B5 综合验收与个人试用 | 进行中，未完成 | C2、C3、C6 | 不改样本下限，不伪造个人试用或至少 7 天时间 |
| 记录 23 新发现 | 保留失败与疑点，按复现和影响处理 | C1、C3、C7 | 单次 WebSocket 日志先诊断，不能直接定为产品故障 |

旧执行计划可以报告“已完成本阶段开发并迁移剩余工作”。MVP 只能按原验收标准分别报告技术闭环、语义审核、个人试用的状态；三者未全部具备证据前，整体维持未验收。

## 4. 第一阶段：承接既定 MVP 的未完成项

所有任务初始状态均为待执行或待真实条件；引用历史证据不等于本轮已验。原计划第 3 节的每条行为契约都必须在 C2–C5 的最终验收表中标明证据或缺口，不能因下表没有逐字重抄而遗漏。

| ID / 顺序 | 工作与交付物 | 实施入口 | 依赖 / 放行条件 | 当前状态 |
|---|---|---|---|---|
| C1 有效备课包与 PDF 正例 | 复现记录 23 的“有效缓存存在→模型主动 refresh→逐字引文拒绝→放弃出卡”。区分真实材料失效与本次重备失败，给出最小修复或明确未修结论；保留失败请求与原包 | `reading_evidence.py`、Mastery `mastery_prepare`、语义审核/教学循环 | 新修订、权限失效或目标改变时必须拒绝旧缓存；重备失败不破坏仍有效包，不自动无限重调，不放宽引文门禁 | **修复已实施并验证（2026-10-31 轮 1）**：`prepare_reading_lesson` 的 refresh 失败路径现在回退仍有效的缓存包——仅当严格缓存标识命中（同引用/同模型/同 focus）且复验通过时返回并带 `refresh_fallback` 标记；缓存包 id 内嵌目标指纹，目标或修订变化在标识层即拒绝回退；引文门禁未放宽，无自动重调，存储不写入失败标记。离线回归 3 例（伪造引文/非法判定→回退；目标变更→拒绝）。真模型复跑 PDF p150 首次出卡（source_grounded、引文逐字一致）；该轮模型未自触发二次 refresh（非确定行为），回退路径以离线测试为证据 |
| C2 综合样本与语义证据 | 补足 2 份文字型 PDF（概念/方法）+ 1 份 EPUB，各至少 2 单元；每单元核对 ≥3 处引用及全部练习可答性。逐目标覆盖正确、部分、错误、等价、“不知道”、辅助作答与新情境应用；完成原计划异常样本核验 | 既有 reading/Mastery API、`data/` 样本脚本、原计划第 6 节 | 依赖 C1 的 PDF 正例；可以先整理其他样本。保留所有首跑、失败、争议与审核人类型；按实际调用预算逐小批执行 | **五类作答审核完成（轮 8，S1/S4/S5 三卡 15 项判分 12/15 按预期）**；**异常样本核验完成（轮 8–9）**：损坏 PDF/EPUB 明确拒绝、缺失引用拒绝、空单元 422、超 24K 包拒绝，且轮 9 新增 **sparse 质量标记与出题拦截**（`unit_quality` 单一真源，`SPARSE_TEXT_CHARS=40`：非空但低于阈值的扫描残页/分隔桩标记 `sparse` 并与空单元一样 422 拒绝出题；两个单元端点暴露该字段）；乱序/缺页对 PDF 物理页序与 EPUB 固定 spine 结构性不可能发生，截断经 `char_count` 与 24K 包上限可见。**dont_know 判类不一致**（S4→ungraded、S1/S5→incorrect）与 S4 等价表达被判 partial 属语义分歧，保留待复核。剩余：第二份方法类 PDF（需用户供书，见待用户决策）、用户人工核对（等待用户） |
| C3 完整浏览器交付 | PDF/EPUB 阅读→目标→出题卡→独立作答→反馈→复习入口；覆盖桌面、390px、768px、刷新恢复、引用跳转、错误提示与答案隔离。补过期引用提示 i18n，复核目录跳转后的抽屉行为 | `web/components/reading/`、`web/components/space/learning/`、`web/lib/reading-citations.ts`、i18n | 两格式均检查实际网络/事件与持久状态。窄屏阅读已验结果保留；出题卡/学习模式不能只凭无横向溢出放行 | **学习模式两档宽度已验（轮 5）+ 轮 6 观察修正**：390px/768px 学习模式正常开启、无横向溢出、header 按钮均在视口内；伴侣面板与题目文本回放两档无溢出。**轮 5 观察修正（轮 6 查实）**：当时两次「Quiz me on this page」点击实际创建了会话并完成了一个 deep_question 出题回合（52s 跑完、题已生成），"未建 turn"记录有误；另有一个 chat 回合停在 waiting_input（ask_user 等待），其 Skip/Submit 交互件在桌面量测中可见且无溢出。**未闭合**：作答交互卡的 390/768 量测——3 次盲探针未命中正确的会话路由（companion sheet 开合 + 活动会话切换使无状态探针不稳定），下轮经会话列表入口定向进入 waiting 回合再量。其余同前：i18n/抽屉已闭合 |
| C4 反馈覆核与真实复习场景 | 补语义误判更正/作废、原评估保留、Notebook/掌握/日程一致、重复提交、辅助条件、重启恢复；补冻结时间与时区边界，并单列真实到期复习 | `assessment.py`、`service.py`、`storage.py`、`scheduler.py`、`notebook_recovery.py`、现有测试 | 先复用已有离线证据，只修复新复现差距。模拟推进只证明时钟契约；真实跨天与至少 7 天复测分别取证 | **离线矩阵在当前 HEAD 复跑通过（2026-10-31 轮 2）**：`deeptutor/learning/tests` + `tests/api/test_reading_quiz_answers.py` 692 passed；`tests/services/session` + `tests/services/storage` + `tests/services/test_learning_backup.py` 511 passed / 1 skipped，合计 1203 项 0 fail。场景映射：重复提交/同刻投影幂等→`test_assessment.py`；覆核/作废/Notebook/掌握/日程一致→`test_mastery_state_integrity.py`、`test_notebook_recovery.py`、`test_guided_mastery_updates.py`、`test_mastery_revise_batch.py`；辅助条件 tri-state→`test_legacy_assist_conditions.py`；重启/备份恢复→`test_storage.py`、`test_offline_recovery.py`、`test_learning_backup.py`；冻结时钟与时区→`test_scheduler.py`。本轮零代码改动，无新缺口复现。**未闭合**：真实跨天到期复习与语义误判的真模型覆核（前者需真实时间，后者留 ACCEPT_MVP 真实调用段） |
| C5.1 预算与计量范围 | 列出计划使用入口→budget→ledger→HTTP 尝试对应关系；核对选定 provider 的已知/未知费用、限额配置、失败结算与未覆盖直连。设置界面仅在实际需要时补 | `services/llm/budget.py`、factory、agentic、runtime JSON settings | 默认关闭状态真实可见；用户选定预算后才启用。不把静态估价称真实账单，不宣称覆盖同密钥其他客户端或所有入口 | **映射已盘点（2026-10-31 轮 3）**：入口① `factory.complete_with_config`（学习语义审核/备课等全部 factory 调用）→ `_open_budget_guard`→`budget_call`，reserve 失败在 provider 流量前阻断；入口② agentic 流式（chat/research/question）→ `build_openai_client`→`instrument_client`→`budget_call`。台账 usage.sqlite3 `llm_calls` 记 status/attempts/estimated/含 reasoning 的 token 分解。默认关闭现场确认（`llm_budget.json` enabled:false）；`budget_status()` 无 API/UI 暴露，可见性止于设置文件。**未覆盖（如实列）**：embedding 直连（独立 AsyncOpenAI）、imagegen/videogen 媒体 provider、本地 CLI 子代理（独立账号层）、同密钥其他客户端与延迟账单（结构性外部）。设置界面维持"实际需要时再补" |
| C5.2 本地数据生命周期 | 盘点完整导出、删除、升级兼容的实际覆盖，再补确认缺口；验证原始作答、评估/覆核、版本、引用与复习状态能导出及在升级后恢复 | 实际 session/learning/reading 存储、现有 API、`scripts/learning_backup.py` | 先合成临时数据与新目录恢复；既有删除 API 存在不能证明关联数据范围正确。真实删除另依具体请求执行 | **CLI 级恢复链当前 HEAD 实证通过（2026-10-31 轮 3）**：合成 user-root（作答 rev 4 + 归档旧版 + 复习队列 + notebook）→ `learning_backup.py backup --quiesced` → restore 到新目录 → 重开核对全部通过（23 个 manifest 文件、settings/ 密钥排除、旧版文本可回读、原始作答/版本/locator/队列/证据完整）；损坏备份拒绝与中断不发布由 `test_learning_backup.py` 覆盖（轮 2 通过）。**缺口如实保留**：学习记录无用户可见导出 API（Books/co_writer 导出不承担此责，记录 5 判断不变，仅 CLI 备份）；删除端点清单在册（workspace/material/session/material 全局）但关联数据范围未逐项核验；真实删除依具体请求执行。升级兼容：`test_v2_migration.py` 在轮 2 通过 |
| C5.3 恢复范围外依赖 | 明确实际试用是否引用外部 KB 或多个 workspace；若需要，补关联 manifest、权限与恢复验证；若暂不覆盖，列出对使用和验收的限制 | 现有备份 manifest、workspace/KB 引用与真实存储 | 当前 O3 仅选定单用户存储。任何将原验收承诺改成非目标的调整需明确范围决定，不能因“个人使用”自行删项 | **核查完成（2026-10-31 轮 4）**：当前试用数据为单一 reading workspace（catalog 实测 count=1，2 份材料），mastery 存储全库 0 处 `kb_ref` 引用——实际试用未引用外部 KB，O3 备份格式（明确排除 KB/其他 workspace/settings/凭据）与当前使用一致，恢复链（轮 3 实证）覆盖试用全部数据。**对使用与验收的限制（如实列，不改验收承诺）**：未来若把学习路径挂到外部 KB 或使用多 workspace，现有备份不覆盖关联 KB 与其他 workspace，届时需补 manifest/权限/恢复验证或做范围决定——该范围决定属用户，本计划不自行宣布 KB 为非目标 |
| C6 个人试用与延迟证据 | 由用户独立完成前测、同目标不同题的无提示后测、至少 7 天后的无提示复测；记录实际日期、辅助条件、应用题、失败目标与纠正 | 现有学习与复习入口，原计划第 6 节 | 首次学习日期目前未记录，最早复测日不能预填。时间未到不关闭；可以与 C1–C5 并行等待，样本改版时标明适用版本 | 等用户真实使用与时间条件；未开始 |
| C7 未定位观察项 | 定点复现记录 23 的一次 `WebSocket failed to connect after retries`，关联 turn/服务日志与用户影响，再决定是否修复 | durable turn、WebSocket adapter、客户端重连 | 回答当时仍完成；若不复现则报告有限观察，保留日志。后台位置写失败的现有行为另按需求判断，不自动改成打断阅读 | **诊断完成，不修复（2026-10-31 轮 4）**：机制定位——该 error 只在**非 awaitAck 控制命令**（`subscribe_turn`/watchdog resubscribe）的 submit 重试上限（60×200ms=12s）处触发；用户提问走 `sendAwaitingAck` 持久队列，永不经过此分支，硬断 WS 下的确定性表现是另一条"Connection lost while generating"提示+Retry（离线 `routeWebSocket` 探针实测命中，`data/ws-retry-25/`）。记录 23 的"error 与完成回答并存"由此解释：error 来自控制通道，问题走 ack 通道经 durable 回放完成。真模型按记录 23 条件重跑（窄屏伴侣问答）：0 console error、回答完成含引用锚点，正常条件不复现。**不修复理由**：该日志是对 >12s 真实断链的如实告警，控制通道自身随 watchdog 下个 tick 恢复；完成回合无用户影响，断链中回合有专门重试提示。遗留观察（不改）：subscribe 类命令撞上限时会对用户 toast "Couldn't reach the server"，语义略宽于其触发条件，若验收段出现用户可见错误升级再议 |

建议按约两项一批推进：第一批 C1 + C3 的 i18n/布局补验；第二批 C2 分批补样本 + C4；第三批 C5.1 + C5.2，C5.3 按依赖决定；C6 尽早开始真实使用并等待日期，C7 可穿插诊断。一次样本扩展若构成真实批量生成，仍先按既有约定确认范围与预算，本计划不提供该确认。

**第一阶段退出条件**：C1–C5 的适用契约有明确证据，全部阻塞缺陷已修复或已明确停用受影响内容；C7 有影响判断。C6 单独决定个人试用与延迟保持状态。若 B4 范围仍未决定或有未满足要求，保留缺口，不能宣布整体完成。

## 5. 第二阶段：借鉴 Omni-Edu 的教学增强候选

本阶段是建议开发顺序。先通过 E1 找出当前能力不足，用户选择范围后才实施 E2/E3；已经满足的能力直接复用。无付费调用的样本整理与评测设计可在等待 C6 的真实日期时进行，不提前改生产教学流程。

### E1 先建立可回放的教学质量样本

目的：回答“反馈除了判对错，能否正确定位困难并帮助下一次独立作答”，为改教学提示或换模型提供比较基线。

- 基于 C2 的合法材料与历史失败整理固定样本，按来源 revision / 学习目标分组，划分开发回归集与保留验收集；同一题的改写、同目标近重复样本不跨组冒充独立样本。
- 每个样本保留原文定位、题目/评分契约、原始回答、辅助条件、当前教学状态、原始反馈、候选输出、模型与提示版本、usage、失败状态及审核理由。真实内容和个人回答留在已核实忽略的 `data/`，Git 只纳入自制/许可明确的小 fixture。
- 机械项：来源/revision/权限、字段完整、答案隔离、事件幂等、提示记录、预算上限。语义项：错误是否真实存在、诊断证据是否充分、解释正确、提示是否适量、是否泄露答案、是否尊重当前请求、下一步是否可执行。
- 输出逐例差异与分维度报告，至少包括已有五类作答、答对但解释不可靠、缺先修、步骤错误、迁移失败、无历史、用户否认诊断、反复解释无效等情形；不合并成一个“教学总分”。
- 模型审核只标记候选问题；记录模型/提示/时间和与人工意见的分歧。小样本全量人工核对，规模扩大再明确抽样；不能默认自己生成、自己审核就已独立通过。

依赖：C2 可用样本；最小交付是本地样本格式、复用现有 provider 的回放入口和一份可追溯报告，不新增在线自动审核链。验收：能从报告回到原始成功/失败；变更不覆盖原输出，复跑能区分版本和失败原因。状态：未开发。

### E2 将“有依据的诊断”连到“下一步教学动作”

优先核验 `ErrorRecord`、语义反馈、`teaching_focus` 与建议性 `NextAction` 是否已能满足下列流程；只有样本显示缺口时才加最小字段或提示约束。

1. 诊断引用真实作答片段和对应原文/评分要求，保留正确部分；说明哪里缺证据。无法区分概念缺口与表述歧义时先澄清，不强制选一个错因。
2. 选择一个有用动作：短解释、追问、检查前一步、回到已知先修目标、要求新情境应用。动作是建议，服从当前学习/复习模式及用户明确请求；用户要直接解释时不强迫提示链。
3. 历史笔记仍按目标局部、tentative/learner_report、unknown/helped/not_helped 的既有规则维护。策略改变不授予掌握，复习或目标切换仍由服务端规则决定。
4. 用户可纠正/撤销诊断并保留证据关联；不把诊断扩成全局能力标签，不改变现有 `ErrorType` 和旧事件含义。

入口：`semantic_assessment.py`、`models.py`、`teaching.py`、`policy.py`、Mastery tools/中英文提示，以及 `ObjectiveDetail.tsx` 的现有展示。验收：E1 中答对不被虚构错误，缺历史不编记忆，诊断有依据且动作相关；存储/API 有真实回归，语义样本单列。状态：候选，待范围选择。

### E3 按需渐进帮助，并回到新的独立任务

- 在已有题目身份与辅助条件上增加必要的帮助记录：请求帮助→一个可执行提示→需要时更强提示/直接解释→同目标新题独立作答；不预先批量生成全套提示。
- 提示/看答案在响应返回前先由服务端持久记录帮助事件；落盘失败不返回帮助内容，传输中断则保留“发送结果未知”，不能推定未见提示。刷新、重试、多入口不会把该次作答恢复成独立；已见答案的原题不能靠“重试答对”升级独立证据。
- 参考答案与评分细则继续留在服务端；“普通解释”和“练习中提示”的授权边界清楚，浏览器与事件检查实际内容。帮助后用不同题核验，保留所有失败和辅助作答。
- 每步复用共享 provider、预算和持久化；失败保留未发送/发送未知等真实状态，不伪造成功送达或授予掌握分，不自动继续付费循环。新增字段需向后兼容，旧辅助条件未知继续为未知。

依赖：C1–C5 的相关契约及 E1；与 E2 的动作选择协调，避免两套策略。机械验收覆盖提示返回/落盘失败、并发、重复、重启和客户端内容；语义审核检查提示是否过早泄底、能否推进学习。状态：候选，待范围选择。

### E4 可选模型实验，最后决定是否接入

只有 E1/E2/E3 发现现用模型存在稳定不足，且用户选择尝试教育模型后执行。模型本身不应成为新一轮开发的前置条件。

先核对权重卡/revision/许可、实际硬件与可用 endpoint，再选择一个候选规格；经 DeepTutor 现有 provider，用同一原文、题目契约、辅助状态与有界生成参数，与当前配置做小范围对照。记录中文表达、来源服从、结构化输出、诊断/提示、拒绝越界目标、延迟、错误率与真实/未知费用；保留失败并随机化审核展示顺序。

允许结论为“继续使用现有模型”。论文成绩不代替本地结果，模型下载文件大小不等于运行显存，FP8 不自动等价于 BF16，不因候选调用失败静默换主模型。SDK 的外部基准可在独立实验中选用，但不运行默认全套或直接连接真实学习记录。状态：可选实验，未部署、未调用。

## 6. 验证、交付与回退

- **功能开发完成必须测试。** 先执行变更相关测试；后端检查 Ruff 与存储/契约，前端改动执行对应测试、typecheck、i18n、契约/架构检查和必要构建。已有通过范围可复用为历史证据，不能写成新一批结果。
- **零代码改动批次豁免功能测试**：记录具体范围、原因和实际文档检查；文档通过不等于功能、模型语义或用户验收通过。
- 沿用约两项一批的节奏：开发/验证→更新本文状态及证据→提交并 push `fork/codex/learning-offline`。既有授权只覆盖该 fork 分支；不推 main/上游、不 force，不新建另一份待办真源。
- 实际调用前核对模型、单次范围和预算；真实批量生成仍需用户确认。审核 token 上限当前为 8,192（记录 23），核验是否被 reasoning 消耗及实际失败原因，不只继续调大，不新增无界重试。
- 新教学策略先可关闭，保留当前流程；数据 schema 向后兼容，候选输出独立保存。升级前在新目录恢复验证；回退不覆盖用户原始作答、评估、备课包或历史 revision。
- 新发现若改变事实，更新任务行与对应记录；历史结果不删改为新结果。语义分歧、未运行项、环境失败和用户尚未试用分别报告。

## 7. 本轮记录与下一会话入口

### 2026-10-30：调研与计划迁移

- 读取原工作区及隔离 worktree 文档、Git 状态；按最新记录 23 核对收尾缺口，保留原工作区已有修改。审阅 Omni-Edu 固定提交的 SDK、任务注册表、诊断/提示/长期教学量表、语义修订流程与部分评测源码，并阅读论文；未运行外部代码。
- 原计划保留需求与历史记录，后续状态迁入本文；更新隔离 worktree 的 README / AGENTS 导航，在 `.gitignore` 增加本计划的单文件例外，原工作区只补续接提示。`docs/plugin-platform-rfc.md` 属于已有插件契约设计，不因本次学习扩展计划迁移而归档。
- 验证：受影响文档区域的 32 个本地链接存在；外部固定版本源码链接逐个对照已克隆提交中的文件；原 23 条执行记录与 HEAD 逐字一致；主工作区添加提示后的原文与修改前备份逐字节一致。仓库卫生、分支策略和差异空白检查通过；迁移 ID 与未验收状态的机械检查通过。这些检查不证明外部链接始终可访问或教学语义正确。
- 验证范围：零功能代码改动，免跑 Python/前端功能测试、浏览器与真实模型。当前项目环境没有 `pre_commit` / `detect_secrets` 模块，未运行相应工具，不记为通过；仅做本批新增内容的凭据模式检查与人工核对。整体 MVP、候选教学增强和 Omni-Edu 本地适配均未宣称通过。

接手时先读本文件第 1、3–4 节及原计划需求/验收和记录 23，核对 `git status --short`、HEAD、fork tracking ref 与运行代码，保护现场成果。从 C1 与 C3 的下一小批开始，不重复 O0–O3/R1–R4。只做调研整理不自动转入 E2–E4；后续功能范围按用户选择执行。

实际运行方式沿用原记录：在隔离 worktree 执行 `.venv/Scripts/deeptutor.exe start --no-browser --detach`；端口与进程需重新核实。浏览器采用桌面 Chromium/Playwright，历史驱动和事件在 git-ignored `data/`。引用探针兼容 `#dt-material-` 与 `#dt-locator-`；位置路由匹配查询串 `**/position*`。预算设置在 `data/user/settings/llm_budget.json`，默认关闭；不读出或提交模型密钥。

## 8. 无人值守自动化状态机（2026-10-31 新增）

用户 2026-10-31 授权建立无人值守自动化流水线：每轮由定时器唤起一个全新会话（状态以本文为唯一真源），执行 ≤2 个任务或一个验收段，按第 6 节节奏测试、更新本文、提交并 push `fork/codex/learning-offline`。轮次锁为 git-ignored `data/automation.lock`。本节只维护 phase、决策清单与轮次记录；执行细节规则在自动化任务定义中。

- **phase：`DEV_ENHANCE`（2026-10-31 轮 10 起；ACCEPT_MVP 已于轮 10 完成除 parked 项）**
- 状态机：`DEV_MVP` →（C1–C5、C7 完成或全部 blocked/parked）→ `ACCEPT_MVP` →（验收完成，除 parked）→ `DEV_ENHANCE`（按 E1→E2→E3 顺序，用户 2026-10-31 已授权；E4 除外）→ `ACCEPT_ENHANCE` → `DONE_AWAITING_REVIEW`。
- 需要用户决策或必须用户本人参与的事项一律写入下方「待用户决策」并跳过，不阻塞其余工作。

### 待用户决策

| 事项 | 背景 | 状态 |
|---|---|---|
| C2 真实批量生成 | 样本扩展若构成真实批量生成，按第 6 节约定需用户确认范围与预算 | 等待用户 |
| C6 个人试用与延迟复测 | 必须用户本人独立作答，含至少 7 天延迟复测 | 等待用户与时间条件 |
| E4 教育模型实验 | 涉及本地硬件、显存、成本与模型选择，计划明确最后决定 | 等待用户 |
| 第二份方法类 PDF | 综合样本要求 2 份文字型 PDF（概念类+方法类），现有书籍仅 1 份 PDF（agentic-ai-guide，概念类）+ 1 份 EPUB（方法类章节）；第二份方法类 PDF 需用户提供本地路径（原计划第 7 节第 1 条） | 等待用户 |

（后续轮次发现的新决策项追加于此；用户裁决后移入轮次记录并更新对应任务行。）


## 9. MVP 验收表（ACCEPT_MVP，2026-10-31 编制）

按原计划第 3 节行为契约逐条验收。判定口径：passed=有本轮或新鲜历史证据；分歧=语义层分歧如实保留；未执行=注明原因。整体结论：**技术闭环在既定边界内完成；语义审核为 Agent 层（两处分歧保留）；个人试用未开始（C6）。整体 MVP 维持未标完成。**

| 行为契约 | 判定 | 证据与边界 |
|---|---|---|
| 来源与版本 | passed | locator/revision/注释重锚机制完整；题目/作答挂 `material_revision`，refresh 归档旧版（记录 4 + 轮 9 回归 485 passed）；S1–S5 卡引文逐字一致（轮 1/6/7）；轮 9 起 sparse 单元带标记。边界：旧无快照投影不回填的边界保留（记录 13） |
| 抽取质量 | passed | 空单元/加密/损坏文件明确拒绝（轮 8 离线实测）；sparse 扫描残页标记+出题拦截（轮 9，`SPARSE_TEXT_CHARS=40`）；乱序/缺页结构性不可能（PDF 物理页序/EPUB 固定 spine）；截断经 `char_count` 与 24K 包上限可见 |
| 教学目标 | passed | 目标可编辑、概念/方法目标均能出卡（S1/S5=概念，S2/S4=方法，含 A-MEM/主动记忆等概念目标）；越界目标被覆盖门禁正确拒绝并降级聚焦题（记录 23、轮 6） |
| 练习答案隔离 | passed | 作答前不下发参考答案/评分要点——既有测试防线 + 记录 14–23 网络响应检查先例；本轮未重跑网络层检查（沿用历史证据，不当作新结果） |
| 作答证据 | passed | 原始回答、题目版本、来源、辅助条件持久化；关闭重开/补偿收敛/幂等（轮 2 离线矩阵 1203 项 0 fail，含真实 SQLite 重开验证） |
| 评分与覆核 | passed（分歧保留） | 五类作答 12/15 按预期（轮 8）；**分歧①** dont_know 判类不一致（ungraded/incorrect 并存）；**分歧②** S4 等价表达被判 partial——两处留 ACCEPT 语义复核，不刷绿；覆核/作废/幂等/时区（轮 2 矩阵 + scheduler 冻结时钟测试） |
| 掌握展示 | passed（离线） | 带提示定性通过不抬满分、展示与证据一致（记录 4 + 既有测试）；学习者本人视角确认未做（C6 parked） |
| 复习一致性 | passed（离线） | 同刻投影幂等、失败/浏览不推进、覆核重算（轮 2 矩阵 + `test_scheduler.py` 冻结时间）；**真实跨天复习未发生**（需真实时间，随 C6） |
| 费用与失败 | passed（有界口径） | budget 门禁双入口、默认关闭可见、ledger 诚实计量（estimated/attempts，轮 3）；鉴权失败不盲重试（记录 8）；不覆盖同密钥其他客户端与外部消耗（如实声明） |
| 数据生命周期 | passed（CLI 级） | 备份→恢复→重开核对端到端（轮 3，含密钥排除/旧版回读/队列证据完整）；升级兼容 `test_v2_migration.py`（轮 2）；**缺口如实保留**：学习记录无用户可见导出 API、删除关联范围未逐项核验 |

浏览器链（第 6 节检查层次）：阅读/目录/引用跳转/错误提示（记录 21–23）、学习模式 390px+768px 无溢出（轮 5）、伴侣面板两档可用（轮 5）、引用回跳与过期修订提示（轮 1）。**未执行**：作答交互卡（ask_user）的窄屏量测——5 次无头探针未能稳定到达 waiting 回合（会话路由+sheet 状态），无产品缺陷证据（所有已测面无溢出、控件在视口内）；该项随用户实际使用（C6）确认。

真实调用（记录 14–23 先例的小范围）：S1–S5 五张卡出卡、越界目标拒绝降级、五类作答判分、定性过门正负档、伴侣问答与引用回跳——累计调用与 tokens 见各轮记录（O2 口径费用未知）。**未执行**：C6 个人试用与至少 7 天延迟复测（等待用户与时间）。

**ACCEPT_MVP 结论（除 parked 项）**：验收段完成。parked 项清单见第 8 节「待用户决策」。下一 phase：`DEV_ENHANCE`（E1 起）。

### 轮次记录（续）

- 2026-10-31（轮 10，ACCEPT_MVP 验收段）：**完成（除 parked）**。第 3 节十项行为契约逐条编制验收表（上文第 9 节）：8 项 passed、1 项 passed-分歧保留（评分与覆核：dont_know 不一致 + S4 等价边界）、1 项 passed-CLI 级（数据生命周期，缺口如实保留）；浏览器链已验面与真实调用证据汇总入表。**未执行项**：作答交互卡窄屏量测（第 5 次无头探针未到达 waiting 会话，无缺陷证据，随 C6 用户实际使用确认）、C6 个人试用与 7 天复测（等待用户）。phase 推进为 `DEV_ENHANCE`，下一轮按 E1（可回放教学质量样本）开工。

### 轮次记录

- 2026-10-31：自动化建立。phase=`DEV_MVP`，从 C1（PDF 正例修复）与 C3 的 i18n/布局补验开始，按第 4 节既定批次推进。
- 2026-10-31（轮 1，DEV_MVP 批 1：C1 + C3 的 i18n/抽屉）：**完成并验证**。改动：① `reading_evidence.py` refresh 失败回退仍有效缓存包（严格标识+复验，目标/修订变化在缓存标识层拒绝），`lesson_context` 增回退说明，新增 3 个离线回归；② `ReaderPane.tsx` 过期引用/材料打不开提示 `t()` 化并补 6 语言键；③ `ReadingWorkspace.tsx` 窄屏目录/标题/注释跳转后收起导航面板（仅 sheet 宽度）。验证：定向 pytest 20 passed、ruff check/format、前端 `i18n:check`、`typecheck`、vitest 3 文件 9 passed、node 套件 0 fail、`git diff --check`；真模型复跑 PDF p150 首次出卡（`pending_question_present=true`、source_grounded、引文逐字一致），6 次调用 65,220+3,658 tokens 全 `completed`（费用未知，O2 口径；驱动与事件在 git-ignored `data/semantic-samples-24/`、`data/browser-narrow-24/`）；浏览器 390×844 实测抽屉自动收起与 zh 提示命中，无 console 错误。服务轮末已停止，`web/next-env.d.ts` 已还原。待用户决策无新增；phase 保持 `DEV_MVP`，下一轮按批次建议进 C2（非批量生成部分）+ C4。
- 2026-10-31（轮 2，DEV_MVP 批 2：C2 台账 + C4 离线矩阵）：**完成，零代码改动**。C2：样本台账建到 `data/semantic-samples-24/sample-registry.json`（S1/S2/S3/Q1 有效样本 + 六项缺口清单），任务行已更新；新增单元出卡留待逐小批真模型执行。C4：当前 HEAD 全量复跑 `deeptutor/learning/tests`+`tests/api/test_reading_quiz_answers.py`（692 passed）与 `tests/services/session`+`tests/services/storage`+`test_learning_backup.py`（511 passed/1 skipped），共 1203 项 0 fail，场景→测试映射写入 C4 行；无新缺口复现。真实跨天复习（需真实时间）与真模型语义覆核（留 ACCEPT_MVP）未闭合。待用户决策无新增；phase 保持 `DEV_MVP`，下一轮候选：C5.1 + C5.2（第三批）或 C2 第二小批样本。
- 2026-10-31（轮 3，DEV_MVP 批 3：C5.1 + C5.2）：**完成，零代码改动**。C5.1：预算双入口映射（factory `_open_budget_guard` / agentic `instrument_client`，reserve 在流量前阻断）、台账字段（status/attempts/estimated）与默认关闭现场确认，未覆盖入口如实列（embedding、媒体生成、CLI 子代理、外部消耗）；budget 状态无 API/UI，维持"需要时再补"。C5.2：CLI 备份→恢复→重开核对在合成数据上端到端通过（含密钥排除、旧版回读、作答/队列/证据完整），导出/删除面盘点写入任务行（学习记录无用户导出 API、删除关联范围未逐项核验为保留缺口）。证据在 git-ignored `data/c52-e2e/`。待用户决策无新增；phase 保持 `DEV_MVP`。**DEV_MVP 余量检查**：C1/C4/C5.1/C5.2 已闭合（各自边界内），C3 余窄屏出题卡/学习模式与 768 宽度，C2 余第二小批样本（逐小批真模型），C5.3 待范围核查，C7 待穿插诊断；下一轮候选：C7 诊断 + C5.3 引用核查，随后 C2 小批与 C3 收尾。
- 2026-10-31（轮 4，DEV_MVP：C7 诊断 + C5.3 核查）：**完成，零代码改动**。C7：机制定位（error 仅属非 awaitAck 控制命令的 12s submit 上限；用户提问走持久 ack 队列）、离线 `routeWebSocket` 确定性复现另一条断线提示、真模型按记录 23 条件重跑 0 error 且回答完成——**不修复**，理由与遗留观察写入任务行（探针产物 `data/ws-retry-25/`）。C5.3：实测单 workspace + 0 处 kb_ref，试用数据全部在备份范围内，KB/多 workspace 限制如实列出、范围决定留用户。本轮真模型 11 次调用 105,912+4,043 tokens 全 `completed`（O2 口径费用未知）。**DEV_MVP 余量**：C1/C4/C5.1/C5.2/C5.3/C7 闭合；余 C3（窄屏出题卡/学习模式与 768）、C2（第二小批样本）。下一轮候选：C3 收尾（出题卡/学习模式窄屏与 768 浏览器验证）或 C2 第二小批（EPUB 第二单元逐小批出卡）。
- 2026-10-31（轮 5，DEV_MVP：C3 学习模式窄屏与 768）：**部分完成，零代码改动、零模型消耗**。新证据：390px 与 768px 学习模式正常开启（`data-learning=true`）且无横向溢出；390px header 按钮全部视口内（最右 380），768px 无越界；伴侣面板两档宽度可用、含出题卡文本的会话回放无溢出。**未闭合**：作答交互卡（ask_user，仅 waiting_input 回合渲染）的 390/768 布局——需真实等待输入的 mastery 回合；本轮两次「Quiz me on this page」点击未创建 turn（turns 表无新记录、无 POST 发出），探针观察待查（先桌面宽度复测）。探针产物在 `data/learning-layouts-390/`、`data/learning-layouts-768/`、`data/header_rect_probe.mjs` 等。待用户决策无新增；phase 保持 `DEV_MVP`。下一轮候选：桌面宽度触发真实 quiz 回合后补作答卡两档布局 + C2 第二小批样本。
- 2026-10-31（轮 6，DEV_MVP：C3 作答卡探查 + C2 第二小批）：**部分完成**。C3：**修正轮 5 观察错误**——quiz 点击实际创建了会话并完成 deep_question 出题回合（52s、题已生成），"未建 turn"有误；另查实存在一个 chat 回合停在 waiting_input，其 ask_user 交互件（Skip/Submit）在桌面量测可见、无溢出。作答卡 390/768 量测 3 次盲探针未命中会话路由（sheet 开合+活动会话切换），下轮走会话列表定向进入。C2：**EPUB 第二单元达标**——S4=locator 11 出卡；首次尝试目标过宽被覆盖门禁如实拒绝、模型口头收尾被 harness 正确拦下（服务端守卫有效），收紧目标后重试出卡（引文全文逐字一致）。两番共 22 次调用 378,569+52,235 tokens（O2 口径费用未知）。待用户决策无新增；phase 保持 `DEV_MVP`。下一轮候选：作答卡两档量测收口 C3 + C2 第三小批（PDF1 第二单元）。
- 2026-10-31（轮 7，DEV_MVP：C3 作答卡量测 + C2 第三小批）：**C3 未闭合、C2 达成**。C3：经会话标签进入 waiting 回合的第 4 次探针仍未命中（伴侣 sheet 开合状态、"Opening document…"/"Loading models" 加载时序使盲探针不可靠），按不死磕纪律停止；该项保留为未闭合（进入方法：会话列表对话框定向进入 waiting 会话后量 ask_user 卡），无任何产品缺陷证据——所有已测面均无溢出、控件在视口内。C2：**S5=PDF locator 338（17.12 主动记忆架构）首次尝试即出卡**，source_grounded、全文 1273 字符引文逐字一致；**PDF1 与 EPUB 的两单元下限均达标**。第二份方法类 PDF 需用户提供书籍路径（原计划第 7 节），已入「待用户决策」。本轮 19 次调用 301,137+31,470 tokens 全 `completed`（O2 口径费用未知）。下一轮候选：S1/S4/S5 五类作答审核（Agent 可做）+ 异常样本系统核验盘点；C3 作答卡量测待探针方法成熟后再试。
- 2026-10-31（轮 8，DEV_MVP：C2 五类作答审核 + 异常样本盘点）：**完成，零代码改动**。五类作答审核（S1/S4/S5 三卡 15 项真实判分，`data/semantic-audit-27/`）：correct/equivalent/partial/wrong 四类 12/12 按预期；**dont_know 判类不一致**（S4→ungraded、S1/S5→incorrect，与记录 23 单次观察形成分歧），S4 等价表达被判 partial 属边界语义分歧——两项均如实保留待复核，不重跑刷绿。异常样本离线盘点：损坏 PDF/EPUB 明确拒绝、缺失引用拒绝、空单元 422、超 24K 拒绝；**乱序/缺页/截断检测仍未实现**（记录 2 结论成立，列为候选开发项）。本轮 15 次调用 42,245+9,190 tokens 全 `completed`。待用户决策新增第二份方法类 PDF（轮 7）。phase 保持 `DEV_MVP`。下一轮候选：乱序/缺页/截断的 per-unit 质量标记与拦截（最小实现）或 C3 作答卡量测重试；DEV_MVP 可收口面已尽，余项均涉等待用户或语义复核。
- 2026-10-31（轮 9，DEV_MVP 收口 → ACCEPT_MVP）：**sparse 质量标记与出题拦截已实现并验证**。改动：`reading/store.py` 新增 `unit_quality()` 单一真源与 `SPARSE_TEXT_CHARS=40` 命名常量（非空但低于阈值=扫描残页/分隔桩）；`UnitText` 端点（当前/修订版）暴露 `sparse` 字段；quiz 门禁把 sparse 与 empty 同等 422 拒绝（独立文案）。测试：新增 sparse 单元 422 + 正文单元正常出卡 + 端点 sparse 标记三个用例；`tests/reading`+`test_reading_quiz_answers.py` 共 485 passed/1 skipped，Ruff check/format 干净。**DEV_MVP 收口判定**：C1/C4/C5.1/C5.2/C5.3/C7 已闭合，C2 除等待用户项外完成，C3 除作答卡窄屏量测（5 次探针未命中会话路由，无缺陷证据，随 ACCEPT_MVP 浏览器全链验收自然覆盖）外完成，C6 等用户——**全部完成或 parked，phase 推进为 `ACCEPT_MVP`**。下一轮起按状态机第 3 条执行验收段。
