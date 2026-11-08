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
| C2 综合样本与语义证据 | 补足 2 份文字型 PDF（概念/方法）+ 1 份 EPUB，各至少 2 单元；每单元核对 ≥3 处引用及全部练习可答性。逐目标覆盖正确、部分、错误、等价、“不知道”、辅助作答与新情境应用；完成原计划异常样本核验 | 既有 reading/Mastery API、`data/` 样本脚本、原计划第 6 节 | 依赖 C1 的 PDF 正例；可以先整理其他样本。保留所有首跑、失败、争议与审核人类型；按实际调用预算逐小批执行 | **五类作答审核完成（轮 8，S1/S4/S5 三卡 15 项判分 12/15 按预期）**；**异常样本核验完成（轮 8–9）**：损坏 PDF/EPUB 明确拒绝、缺失引用拒绝、空单元 422、超 24K 包拒绝，且轮 9 新增 **sparse 质量标记与出题拦截**（`unit_quality` 单一真源，`SPARSE_TEXT_CHARS=40`：非空但低于阈值的扫描残页/分隔桩标记 `sparse` 并与空单元一样 422 拒绝出题；两个单元端点暴露该字段）；乱序/缺页对 PDF 物理页序与 EPUB 固定 spine 结构性不可能发生，截断经 `char_count` 与 24K 包上限可见。**dont_know 判类不一致**（S4→ungraded、S1/S5→incorrect）与 S4 等价表达被判 partial 属语义分歧，保留待复核。剩余：用户人工核对（等待用户）。**第二份方法类 PDF 已于 2026-11-08 补齐**（轮 7）：用户提供《销售铁军》（贺学友，文字型 PDF，material 30f2747b9933252e，222 页正文 11.2 万字），出卡 2 单元（p140 拜访计划 + p100 签单阻碍，design 层 construct/diagnose），备课覆盖审核通过、bind 引文逐字审查通过（provenance=adapted——本书抽取句中带空格，字节级 original 不可达，如实记），五类作答真模型判分 10/10 按预期，S7/S8 入样本库（report：8 样本 0 机械失败 0 分歧）。过程中发现并修复抽取崩溃 bug：本书内嵌字体 CMap 损坏产生孤立代理字符，ingest 直接 UnicodeEncodeError——extract.py 抽取边界统一清除 surrogates（tests/reading/test_extract_surrogates.py 3 项） |
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

依赖：C2 可用样本；最小交付是本地样本格式、复用现有 provider 的回放入口和一份可追溯报告，不新增在线自动审核链。验收：能从报告回到原始成功/失败；变更不覆盖原输出，复跑能区分版本和失败原因。**最小交付完成（2026-10-31 轮 11）**：`scripts/teaching_samples.py`（build/replay/report，工具与 9 项离线测试进 Git，真实内容留在 git-ignored `data/teaching-samples/`）——样本库 S1–S5（dev=S1/S4/S5，holdout=S2/S3 有防误回放门禁），机械校验 0 失败；回放经 store 重建完整判分契约（含 source_evidence）并逐项容错记录失败原因，时间戳纳秒化防覆盖（该覆盖 bug 由测试抓出后修复）。**回放复现 dont_know 判类不稳定**（S1/S4/S5 三样本 replay 中 ungraded↔incorrect 全部再现），为验收表分歧①提供直接证据。报告如实列出 7 种情形（答对解释不可靠、缺先修、步骤错误、迁移失败、无历史、用户否认诊断、反复解释无效）无样本待扩展。过程事故如实记录：backfill 曾用 exec_module 加载审计脚本，触发一次计划外的完整真模型重审（15 次调用）并覆盖当日 verdicts.json——已改为 AST 提取常量，重审结果（14/15，两处分歧翻转）作为判分方差的佐证保留在记录中。状态：最小交付完成；情形样本扩展随 E2/E3 需求推进。

### E2 将“有依据的诊断”连到“下一步教学动作”

优先核验 `ErrorRecord`、语义反馈、`teaching_focus` 与建议性 `NextAction` 是否已能满足下列流程；只有样本显示缺口时才加最小字段或提示约束。

1. 诊断引用真实作答片段和对应原文/评分要求，保留正确部分；说明哪里缺证据。无法区分概念缺口与表述歧义时先澄清，不强制选一个错因。
2. 选择一个有用动作：短解释、追问、检查前一步、回到已知先修目标、要求新情境应用。动作是建议，服从当前学习/复习模式及用户明确请求；用户要直接解释时不强迫提示链。
3. 历史笔记仍按目标局部、tentative/learner_report、unknown/helped/not_helped 的既有规则维护。策略改变不授予掌握，复习或目标切换仍由服务端规则决定。
4. 用户可纠正/撤销诊断并保留证据关联；不把诊断扩成全局能力标签，不改变现有 `ErrorType` 和旧事件含义。

入口：`semantic_assessment.py`、`models.py`、`teaching.py`、`policy.py`、Mastery tools/中英文提示，以及 `ObjectiveDetail.tsx` 的现有展示。验收：E1 中答对不被虚构错误，缺历史不编记忆，诊断有依据且动作相关；存储/API 有真实回归，语义样本单列。**核验完成（2026-10-31 轮 12）——既有结构满足，未加新字段**：流程 1（诊断引用作答与原文、保留正确部分）经 S5 卡真模型双探针验证——正确作答的反馈逐点确认无虚构、部分作答的反馈精确指名全部缺失部分（`data/e2-diagnosis-probe.json`）；流程 2/3/4（动作选择、tentative/helped/not_helped 历史规则、用户纠正）由 `teaching_guidance()` 指令、`TeachingObservation` 模型与 loop 提示词既有约束覆盖（含"notes 为空不得编造反馈"的显式禁令）。**样本暴露并修复一个真实缺口**：判分调用 `judge_answers` 沿用 2,200 默认输出预算，reasoning 重的模型间歇性耗尽预算令普通作答提交报"assessment unavailable"（错误诚实抛出、不落分）——按记录 23 同族先例提升到 8,192 有界上限，定向回归 42 passed。状态：核验完成；E2 无未闭合项。

### E3 按需渐进帮助，并回到新的独立任务

- 在已有题目身份与辅助条件上增加必要的帮助记录：请求帮助→一个可执行提示→需要时更强提示/直接解释→同目标新题独立作答；不预先批量生成全套提示。
- 提示/看答案在响应返回前先由服务端持久记录帮助事件；落盘失败不返回帮助内容，传输中断则保留“发送结果未知”，不能推定未见提示。刷新、重试、多入口不会把该次作答恢复成独立；已见答案的原题不能靠“重试答对”升级独立证据。
- 参考答案与评分细则继续留在服务端；“普通解释”和“练习中提示”的授权边界清楚，浏览器与事件检查实际内容。帮助后用不同题核验，保留所有失败和辅助作答。
- 每步复用共享 provider、预算和持久化；失败保留未发送/发送未知等真实状态，不伪造成功送达或授予掌握分，不自动继续付费循环。新增字段需向后兼容，旧辅助条件未知继续为未知。

依赖：C1–C5 的相关契约及 E1；与 E2 的动作选择协调，避免两套策略。机械验收覆盖提示返回/落盘失败、并发、重复、重启和客户端内容；语义审核检查提示是否过早泄底、能否推进学习。**完成（2026-10-31 轮 13）**：审计确认既有结构（`assistance_used`/`independent` 判定、视觉分支 teaching_after_question 后备、R4 tri-state、`mastery_note_explained` 投递绑定、重试不削弱独立复习）均有测试背书；**真模型探针实证缺口**——chat 提示后同题答对被记为独立证据（hints_used=0、correct、+0.5 掌握分；同会话复现，提示零泄底），提示词约束不足以约束工具参数。**最小修复**：①服务端后备 `SQLiteSessionStore.has_turns_since`——判分时同会话内题目创建之后存在任何回合即保守视为有辅助，穿过 grade 路径（`_assistance_backstop`）；②双语 playbook 提示约束（判分如实声明 hints_used、提示不给完整答案、不确定按有辅助）。回归 1183 passed/1 skipped；终验真模型同会话流程：hints_used=1、掌握 0.0、零泄底（`data/e3-hint-probe.json`、`data/e3-hint-answer-probe.json`）。残留边界：后备按同会话保守判定，跨会话提示仍依赖判分声明（如实保留）；提示文本的结构化持久化（独立帮助事件）未加——现有后备已满足「辅助作答不得独立」的验收要求。状态：完成。

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

- **phase：`DONE_AWAITING_REVIEW`（2026-11-08 轮 5 起；L 系列 DEV_LOGI→ACCEPT_LOGI 已于 2026-11-08 完成，验收表见第 11.5 节。上一轮 `DONE_AWAITING_REVIEW` 为 2026-10-31 轮 14，其间经用户交互授权插入第 11 节 L 系列；自动化全程 paused）**
- 状态机：`DEV_MVP` →（C1–C5、C7 完成或全部 blocked/parked）→ `ACCEPT_MVP` →（验收完成，除 parked）→ `DEV_ENHANCE`（按 E1→E2→E3 顺序，用户 2026-10-31 已授权；E4 除外）→ `ACCEPT_ENHANCE` → `DONE_AWAITING_REVIEW`；2026-11-07 追加：`DONE_AWAITING_REVIEW` →（用户授权 L 系列）→ `DEV_LOGI`（L1→L5 顺序）→ `ACCEPT_LOGI` → `DONE_AWAITING_REVIEW`。
- 需要用户决策或必须用户本人参与的事项一律写入下方「待用户决策」并跳过，不阻塞其余工作。

### 待用户决策（整体复核入口 · 醒来先看这里）

自动化已完成 DEV_MVP → ACCEPT_MVP → DEV_ENHANCE → ACCEPT_ENHANCE 全部可用工作，phase=`DONE_AWAITING_REVIEW`；2026-11-08 L 系列（LogiNote 借鉴增强）已完成并验收（第 11 节）。**2026-11-08 用户已裁决五项中的三项**（C2 批量=不做、E4=不开展、分歧②=等价成立，见 11.2 节与 11.5 节分歧项 1 的处置），现余两项：

| 事项 | 背景 | 状态 |
|---|---|---|
| C6 个人试用与延迟复测 | 必须用户本人独立作答，含至少 7 天延迟复测。用户 2026-11-08 已知悉协议 | 等待用户真实使用与时间条件 |
| ~~第二份方法类 PDF~~ | **已关闭（2026-11-08）**：用户最终提供《销售铁军》（贺学友，文字型方法类 PDF），2 单元出卡 + 五类审核 10/10 完成，S7/S8 入库（轮 7，C2 任务行已更新） | 已完成 |

已裁决项（2026-11-08，留档）：
- **C2 真实批量生成：不做批量**——个人学习按需出卡即产品形态，无需批量预生成；本项关闭。
- **E4 教育模型实验：暂不开展**——E1–E3 证据未显示现用模型稳定不足；本项关闭（若日后想试再开）。
- **分歧②：等价成立**——S4 替代方案问法按目的判定，source 与 learner 的替代问法都是好问题；judge 提示词已按"目的达到即等价"校准（2026-11-08），judge 重放仍持 partial 异议，按用户语义权威覆盖样本判类为 correct，judge 限如实记为已知边界（细节见 11.5 节分歧项 1 处置）。样本库 disputed_answers 现为 0（含 S2 dont_know 期望类按 L1 裁决后政策更新的顺带修正）。

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


## 10. 教学增强验收表（ACCEPT_ENHANCE，2026-10-31 编制）

按第 3 条口径验收 E1–E3 交付。**结论：三项交付全部通过验收（边界如实保留）；后续轮次发现的新决策项已入第 8 节清单。**

| 交付 | 判定 | 验收证据（轮 14 新鲜取证，非沿用开发轮结果） |
|---|---|---|
| E1 可回放样本库 | passed | `report` 重跑：5 样本机械校验 0 失败、语义分歧 1 项如实携带、7 种情形无样本如实列出；provenance 5/5 可回源（path→store→pending question 与样本契约一致）；离线测试 9 项在 HEAD 通过；回放记录纳秒时间戳无覆盖（覆盖 bug 由测试抓出并修复，轮 11） |
| E2 诊断质量 | passed | 双探针重跑：correct 作答反馈逐点确认、零虚构；partial 作答反馈指名全部缺失部分（精简上下文/三类压缩表示/与反应式记忆区别/全部实证数据）；判分预算修复（8,192）后无 OutputUnavailable 复现。边界：dont_know 判类不稳定（回放复现）保留为语义分歧，待复核 |
| E3 帮助后备 | passed | 全新路径完整周期：提示零泄底（789 字符回复不含答案关键标记）→ 同会话作答 → `hints_used=1`、掌握分 0.0（后备生效，不再授予独立掌握）；对照路径维持模型声明行为。离线回归 620 passed/1 skipped（覆盖 sample bank、reading evidence、semantic assessment、guided mastery、assist tri-state、scheduler、session store） |

**本轮验收消耗**：17 次调用 247,656 + 15,934 tokens 全 `completed`（O2 口径费用未知）。**随验收转入整体复核的边界**：语义分歧两处（dont_know 判类、S4 等价边界）留人工复核；7 种教学情形无样本；跨会话提示与结构化帮助事件为 E3 残留边界；E4 模型实验维持 parked。

### 轮次记录（续）

- 2026-10-31（轮 10，ACCEPT_MVP 验收段）：**完成（除 parked）**。第 3 节十项行为契约逐条编制验收表（上文第 9 节）：8 项 passed、1 项 passed-分歧保留（评分与覆核：dont_know 不一致 + S4 等价边界）、1 项 passed-CLI 级（数据生命周期，缺口如实保留）；浏览器链已验面与真实调用证据汇总入表。**未执行项**：作答交互卡窄屏量测（第 5 次无头探针未到达 waiting 会话，无缺陷证据，随 C6 用户实际使用确认）、C6 个人试用与 7 天复测（等待用户）。phase 推进为 `DEV_ENHANCE`，下一轮按 E1（可回放教学质量样本）开工。
- 2026-10-31（轮 11，DEV_ENHANCE E1）：**最小交付完成**。`scripts/teaching_samples.py`（build/replay/report）+ 9 项离线测试进 Git；样本库 `data/teaching-samples/`（git-ignored）：S1–S5 全样本（dev=S1/S4/S5，holdout=S2/S3 带防误回放门禁）、机械校验 0 失败、判分与分歧（dont_know×3、equivalent×1）忠实入账。回放契约经 store 重建（含 source_evidence），逐项容错记录失败原因；**回放复现 dont_know 判类不稳定**（三样本 ungraded↔incorrect 全部再现），强化验收表分歧①。报告如实列出 7 种无样本情形。**过程事故**：backfill 曾 exec_module 审计脚本触发计划外真模型重审（15 次调用）并覆盖当日 verdicts.json（12/15→14/15，两边界分歧翻转）——已改 AST 提取常量；重审结果作为判分方差佐证保留。本轮窗口合计 92 次调用 227,145+60,359 tokens（含上述事故与契约修正前的作废回放，O2 口径费用未知）。phase 保持 `DEV_ENHANCE`。下一轮候选：E2（有依据的诊断连到下一步教学动作）核验实施。
- 2026-10-31（轮 12，DEV_ENHANCE E2）：**核验完成，未加新字段**。四条流程映射：①诊断质量经 S5 卡真模型双探针验证（正确作答零虚构、部分作答诊断精确指名缺失部分，`data/e2-diagnosis-probe.json`）；②③④动作选择/历史笔记规则/用户纠正由 `teaching_guidance()`、`TeachingObservation` 与 loop 提示词既有约束覆盖。**实质修复**：探针暴露判分调用 2,200 输出预算被 reasoning 间歇性耗尽（学习者普通提交会遇"assessment unavailable"，错误诚实抛出不落分）——按记录 23 先例提升 `judge_answers` 至 8,192 有界上限，定向回归 42 passed。本轮 26 次调用 73,730+20,564 tokens（含两次修复前失败调用，O2 口径费用未知）。phase 保持 `DEV_ENHANCE`。下一轮候选：E3（按需渐进帮助并回到新独立任务）核验实施。
- 2026-10-31（轮 13，DEV_ENHANCE E3）：**完成，含一处实证缺口修复**。审计确认既有帮助链路结构完备（均有测试背书）；真模型同会话探针实证缺口——提示后同题答对被记为独立证据（hints_used=0、+0.5 掌握分；提示本身零泄底）；轮内曾有一次探针方法修正（两次 start_turn 各建会话导致判分看不到提示史——跨会话假象，非产品缺陷）。**修复**：服务端后备 `has_turns_since`（同会话题目创建后有任何回合→判分保守视为有辅助；`_query` 签名 bug 由测试抓出后修复）+ 双语 playbook 提示约束。回归 1183 passed/1 skipped；终验：hints_used=1、掌握 0.0、零泄底。跨会话提示与结构化帮助事件如实记为残留边界。**DEV_ENHANCE 判定**：E1（样本库+回放+报告）、E2（诊断质量核验+判分预算修复）、E3（帮助后备+提示约束）全部完成——**phase 推进为 `ACCEPT_ENHANCE`**。下一轮按状态机第 5 条验收 E1–E3 交付。
- 2026-10-31（轮 14，ACCEPT_ENHANCE 验收段）：**完成（除 parked）**。新鲜取证：离线回归 620 passed/1 skipped（HEAD 直测）；E1 report 重跑 0 机械失败、provenance 5/5 可回源；E2 双探针重跑判类与质量一致（correct 零虚构、partial 指名全部缺失）；E3 全新路径完整周期 hints_used=1、掌握 0.0、零泄底。验收表入第 10 节，「待用户决策」已加整体复核入口提示。本轮 17 次调用 247,656+15,934 tokens 全 `completed`（O2 口径费用未知）。**phase 推进为 `DONE_AWAITING_REVIEW`**——自动化可用工作全部完成；后续唤起读到此 phase 即退出，不再做任何事。

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

## 11. 第三阶段：LogiNote 借鉴增强（L 系列，2026-11-07 授权）

用户 2026-11-07 交互授权：对 [LogiNote](https://github.com/GlimmerElve/LogiNote-Chinese-version-)（MIT）做功能与设计思想对比 → 定移植清单 → 开发。本节为 L 系列唯一任务真源；执行节奏沿用第 6 节（每批 ≤2 项、测试、更新本文、commit、push fork）。**参照固定版本**：`main@d3ffa2e16b9d175405713f4be327a8e7d8bc8e02`（2026-11-05，v1.1.1 源码快照）；只读解包副本在 `C:\Users\O1830\AppData\Local\Temp\logi-extract\`，仅作设计参照，不执行其代码、不复制其代码（TS→Python 无意义，借鉴设计并注明）。

### 11.1 对比结论（调研事实）

两边哲学高度同构：来源忠实（引文逐字核对 ↔ referenceQuotes 定位回原文）、证据判分、辅助作答不作独立掌握（E3 后备 ↔ hintLevel 0-4 + assisted pass 不累计）、契约冻结（question fingerprint ↔ sourceKey/masteryKey/contractKey）、批量判分逐题回执、指数遗忘族复习调度。

**都有且对齐（不动）**：答案隔离（服务端持钥）、引文逐字门、契约指纹、辅助不作独立、批量判分、调度同族。
**他们有→移植 5 项**（下表 L1–L5）：dont_know 判类统一、判分语义硬化、题目设计层（8 认知操作 + design 元数据 + 操作历史，参照 `src/services/quickCheck/planning.ts`）、机械题干查重 + 位置依赖题拦截（参照 `diversity.ts`/`optionOrder.ts`）、闭合题答案钥注册复核（参照 `evaluation.ts` guardChoice 的独立求钥思想，前移到注册时）。
**都不同→借鉴后不移植**：per-criterion 9 判据量表（我们整题 verdict + 提示词硬化近似达成，全量移植需动判分/存储/UI 三层，ROI 低）；掌握状态机替换（我们分数制+门槛已充分测试）；复习队列实时派生（我们持久化队列，纪律不重写 scheduler）。
**超范围不移植（记候选，不开工）**：个人认知库（cognition/，计划已明确不建知识图谱）、画像证据门（profile/，MVP 无画像需求）、复述论证结构、STORM（已有 deep_research）、个性化教材生成、本地语音、H5P/S2 插件、本地嵌入（若将来要离线 RAG 可参考其 @xenova/transformers + MiniLM-L12 路线）。

### 11.2 用户裁决记录（2026-11-07）

1. **分歧①（dont_know 判类）**：用户要求分情形讨论后裁决。情形拆解：部分作答→partial（既有契约）；判分方证据不足→ungraded（无争议）；**唯一分歧点是明确声明"不知道所考内容"**。agent 推荐「ungraded + 巩固信号」（回执不编错误原因、不进错题、不扣掌握分，但补复习调度信号，修复"声明不知道的尝试完全不落盘、目标可能永不进跨会话复习队列"的实测缺口——`_evaluate_question` 对非 final 回执跳过 `_apply_grade`，service.py:1684）；提问答复未收到，按推荐实施，用户可在验收时否决。
2. **闭合题答案钥交叉复核**：用户拍板「出题注册时复核」——错钥在学习者看到题目前拦截，判分时不加调用。

**2026-11-08 追加裁决**（用户逐项答复待决策五项）：

3. **C2 真实批量生成：不做批量**（用户选项 A）——个人学习按需出卡即产品形态；本项关闭。
4. **E4 教育模型实验：暂不开展**——用户决定挂起；本项关闭，日后可重开。
5. **分歧②：等价成立**——用户裁定 source 与 learner 的替代问法**都是好问题、都能给学习者带来帮助**，替代方案按"目的达到即等价"判定，不二选一。落地：judge 提示词补"替代方案/举例类作答按目的判定，形式不同或未复述原文限定词不降 partial（目的落空才 partial）"；重放 S4（replay S4-1794098755）**judge 仍判 partial**（它把"未来导向/间接"视为方法目的本身）——按用户语义权威将样本该行判类覆盖为 correct（带 owner_ruling 注记与重放证据指针），judge 持续异议如实记为该边界上"judge 比所有者标准更严"的已知限制，不继续调提示词刷绿。顺带修正：S2 dont_know 行的期望类 incorrect 为 L1 裁决前旧标准，更新为 ungraded 并清除过期分歧标记。样本库 report：6 样本 0 机械失败、**disputed_answers 0**。
6. **C6**：用户已知悉协议（真实学习→独立作答→后测→≥7 天无提示复测），等待真实使用与时间条件。
7. **第二份方法类 PDF**：用户先提名 4 本候选（均属方法类，《爆款短视频》为 EPUB 不顶 PDF 槽位），最终提供**《销售铁军》**（贺学友，文字型 PDF）——2026-11-08 轮 7 完成接入与 2 单元出卡审核（详见 C2 任务行与轮 7 记录），本项关闭。

### 11.3 L 系列任务表

| ID / 批次 | 工作与交付物 | 实施入口 | 边界 | 状态 |
|---|---|---|---|---|
| L1 / 批 1 | 判分语义硬化：judge 提示显式三规则（声明不知道→ungraded 永不 incorrect；等价表达保留核心含义与条件→correct 不降 partial；结论对但解释不可靠→partial）；`Verdict` 加可选 `declared_unknown`（默认 None 向后兼容）；声明不知道时记 LearningEvidence（result=ungraded、quality 0.0、assessment_type=declared_unknown）+ 现有 `schedule_review` 喂巩固信号；不建 QuizAttempt、不写 ErrorRecord、不动 mastery | `semantic_assessment.py`（judge 提示 :172-179、Verdict :25-29）、`service.py`（`_evaluate_question` :1684、`_apply_grade` :647 防御） | 不改 scheduler 算法只喂输入；旧回执无新字段=现状行为；E1 dev 集真模型回放验证 S1/S5 incorrect→ungraded、S4 等价→correct | **完成（2026-11-08 批 1）**：judge 三规则 + `declared_unknown` + 巩固信号（单题与组合题两路径，`_record_declared_unknown`，"记录一次、标记随回执续载"的重试幂等）；quality 映射两处防御 `.get`；tools.py tutor 文案按 declared_unknown 分流。测试：新增 `test_declared_unknown.py` 8 项；回归 `deeptutor/learning/tests`+`test_reading_quiz_answers.py` 723 passed。E1 dev 集真模型回放 S1/S4/S5：15 调用 43,880+12,602 tokens 全 completed（O2 口径费用未知）——三卡 dont_know 全部 ungraded+declared_unknown（**分歧①按裁决收敛**），S5 equivalent→correct、S1 diffs 0、S5 diffs 0；**S4 equivalent 仍 partial**（judge 理由为替代方案实质不完整，非措辞差异，不落入"措辞差异不降 partial"规则覆盖面）——**分歧②如实保留**，属等价边界的实质语义分歧，留人工复核裁决（**后已于 2026-11-08 由用户裁决收敛，见 11.2 节追加裁决与 11.5 节分歧项 1 处置**） |
| L2 / 批 1 | 机械防线：题干归一化查重 + 选择题位置依赖题拦截 | `tools.py`（`_normalize_quiz_contract` :227、注册路径）、`models.py`、`pending.py` | 纯机械不加模型调用；拒绝时 tutor 收明确错误可换题 | **完成（2026-11-08 批 1，含一处范围修正）**：①位置依赖题硬拒（题干+选项体保守正则：以上都对/选A/第X个选项/all of the above，经 `position_dependent_quiz_text`，`_build_question` 拦截）；②组合题批内同干硬拒（归一化 `quiz_stem_key`：NFKC+casefold+去标点空白）；③`question_stem_keys` 滚动历史（cap 20）注册时记录。**范围修正（如实记录）**：跨轮同干**不硬拒**——既有 retry 流依赖重出同题（ErrorRecord retry history、scheduler 失败重试、`test_quiz_then_grade_drives_memory_gate` 三轮同题驱动掌握门），且 LogiNote 参照实现本身也只在同批生成内硬拒、历史仅作提示侧软约束；跨轮多样性改由 playbook 与 stem 历史（L3 注入）软驱动。测试：新增 `test_quiz_guards.py` 23 项（含"跨轮同题仍放行"回归） |
| L3 / 批 2 | 题目设计层：`mastery_quiz` 可选 `design{operation,scenario,focus,required_detail}` 参数；`PendingQuestion.design` 可选字段；服务端机械计算目标操作历史并注入推荐下一操作（不硬规划）；zh/en playbook 出题指导（迁移/反事实/新情境一等题类） | `tools.py`（`_build_question`）、`models.py`、`prompts/{zh,en}/mastery_loop.yaml` | design 为元数据不展示（零前端改动）；tutor 自主采纳推荐 | **完成（2026-11-08 批 2，commit 8dee5ab3）**：`QuestionDesign` 模型 + `PendingQuestion.design`（服务端元数据，不出公投影、不入判分契约）；8 种操作冻结枚举（contrast/counterfactual/diagnose/construct/predict/evidence_gap/design_test/revise），operation+scenario 必须成对给出（无情境的操作标签直接拒绝）；`question_operations` 滚动历史（cap 10）注册时记录；工具结果注入 `design_hint`（`next_operation_hint` 按题型偏好序+近 2 次排除，纯机械建议）；组合题 leaf schema 注入 design items（照 visual 模式）；双语 playbook「题型设计层：变换考法，而不是换个说法重问」。测试：`test_quiz_guards.py` 增 7 项（含 leaf schema、hint、拒绝路径）；learning 全套 712 passed |
| L4 / 批 2 | 迁移情形样本：用 L3 真模型小批出 1–2 张 transfer/新情境卡（S6/S7）+ 作答 + 判分，入 E1 样本库，report 更新情形覆盖 | `scripts/teaching_samples.py`、`data/teaching-samples/`（git-ignored） | 逐小批、估 10–20 次调用上限 30；沿轮 6/7 先例；依赖 L3 | **完成（2026-11-08 批 2，S6 一张达"1–2 张"下限，S7 未出）**：真模型链路 propose→`_build_question` 解析 design→bind 引文支持审查（provenance=adapted）→注册（经 service replace 替换 S1 路径旧挂起位）→五类作答（操作员撰答，沿轮 8 先例）→真模型判分 **5/5 按预期**（correct/equivalent→correct、partial、wrong→incorrect、dont_know→ungraded+declared_unknown）；`teaching_samples.py add` 入库，report：6 样本 0 机械失败，**transfer_failure 情形已覆盖**（7 种无样本→6 种）。真模型 14 次调用 25,311+19,230 tokens 全 completed（含 2 次脚本异步 bug 损耗的 propose，如实记）。证据 `data/l4-transfer-probe/`（git-ignored）。**过程中发现并修复 E1 工具完整性缺陷（如实记，超计划范围的最小必要修复）**：S6 注册替换共享路径挂起位后，`replay` 按 `pending_question` 解析题面会让 S1/S4/S5 重放**静默拿错题**——改为按样本自身 question_id 从交互存储解析（`_resolve_question`，挂起优先、交互回退），S1 重放实证（diffs 0，按旧题判分正确）；新增 `add` 子命令（单样本追加、拒绝重复、不动既有样本）；`_attach_verdicts` 支持按 question_id 键的 verdict 文件（l4 探针）且不遮蔽同路径旧样本；build 同步改为按 result 文件记录的题号解析。测试：`test_teaching_samples.py` 9→13 项 |
| L5 / 批 3 | 闭合题答案钥注册复核：bind 阶段对 choice/concept 题批量独立求解（题干+选项+来源→钥），与 expected_answer 冲突即拒绝注册 | `semantic_assessment.py`（`bind_questions` :217） | +1 次调用/张含选择题卡（bind 批量内摊薄）；冲突拒绝不放宽；离线测试用假 provider | **完成（2026-11-08 批 3）**：`verify_choice_keys`——独立求钥只看题干+选项体（stored key/explanation 不出），冲突或不可解即拒绝注册（LogiNote guardChoice 的独立求钥思想前移到注册时）；**视觉题跳过**（其钥锚在页面像素，脱离图像不可解）；**config=None 不跑**（离线/操作员注册保持离线），生产由 `mastery_quiz` execute 对文本选择题显式解析 `get_llm_config()`。**修复流程保留为兜底**：`test_repair_question_tool_voids_wrong_key_from_question_bank`（故意注册错钥测 repair）补 key-review 离线桩——repair 工具仍是"reviewer 自身出错"残余场景的兜底。测试：新增 `test_key_review.py` 11 项（冲突/一致/不可解/无效响应/视觉跳过/非选择跳过/批量逐题/bind 接线/离线路径/工具级拒绝与放行）。**真模型探针**：生产 quiz 路径直接跑——错钥卡（stored A）被独立求钥（derived B）**拒绝注册**、一致钥卡通过审核（挂起位被 S6 占用故注册为 no-op，审核链完整跑过）；11 次调用 13,420+9,753 tokens（complete_with_config 逐 attempt 计费口径，O2 费用未知），证据 `data/l4-transfer-probe/L5-key-review-probe.json` |
| L6 / 批 3 | 验收段 ACCEPT_LOGI：离线回归（learning+reading quiz+session/storage 定向、ruff）、E1 report 重跑、分歧①②复核结论、验收表写入本节 | 全部上述 + 本文 | 按 ACCEPT_MVP 口径如实判定 | **完成（2026-11-08 轮 5）**：验收表见 11.5 节；phase 推进为 `DONE_AWAITING_REVIEW` |

### 11.4 L 系列轮次记录

- 2026-11-07（轮 1，DEV_LOGI 启动）：调研与计划获批（本节 + 第 8 节状态机延长）。现场核对：worktree 干净、HEAD `770e9c7a`、venv 可用、自动化 paused。LogiNote 参照 SHA 已固定（`d3ffa2e1`）。本轮目标：批 1（L1 判分语义硬化 + L2 机械防线）。
- 2026-11-08（轮 2，DEV_LOGI 批 1：L1 + L2）：**完成并验证**。L1：judge 提示三规则、`Verdict.declared_unknown`（receipt 续载）、巩固信号 `_record_declared_unknown`（单题+组合两路径、重试幂等——重试丢标记的 bug 由 `test_resubmitted_unknown_does_not_duplicate_the_signal` 抓出后修复）、quality 映射两处防御、tutor 文案分流。L2：位置依赖硬拒、批内同干硬拒、stem 历史记录；**范围修正**：跨轮同干不硬拒（retry 流依赖 + LN 参照同批硬拒先例），如实写入任务行。验证：新增 31 项测试全过；回归 723 passed（learning+reading quiz）+ 511 passed/1 skipped（session/storage/backup）；ruff check/format 干净。真模型回放：S1/S4/S5 dev 集共 15 调用 43,880+12,602 tokens 全 completed（O2 口径费用未知）——**分歧①收敛**（三卡 dont_know 一致 ungraded+declared_unknown）、S1/S5 diffs 0；**分歧②未收敛如实保留**（S4 equivalent 判 partial 的理由是实质完整性而非措辞，留人工复核）。phase 保持 `DEV_LOGI`。下一批：L3 题目设计层 + L4 迁移样本。
- 2026-11-08（轮 3，DEV_LOGI 批 2：L3 + L4）：**完成并验证**。L3（commit 8dee5ab3）：design 元数据层 + 机械操作提示 + 双语 playbook，7 项新测试。L4：真模型出迁移卡 S6（counterfactual：policy 重置到检查点 C 后两种失败是否仍发生）→ design 注册 → bind 引文审查 → 五类作答判分 5/5 → `add` 入库 → report 覆盖 transfer_failure（7 种无样本情形 → 6 种）。**计划外必要修复（如实记）**：S6 注册暴露 E1 回放按挂起位解析题面的完整性缺陷——`_resolve_question` 按题号解析 + `add` 子命令 + verdicts 按题过滤，`test_teaching_samples.py` 9→13 项。验证：learning 全套 + reading quiz + teaching samples 共 743 passed；ruff 干净；S1 重放实证修复（diffs 0）。真模型 14 次调用 25,311+19,230 tokens 全 completed（含 2 次脚本 bug 损耗，O2 口径费用未知）。phase 保持 `DEV_LOGI`。下一批：L5 答案钥注册复核 + L6 验收段（ACCEPT_LOGI）。
- 2026-11-08（轮 4，DEV_LOGI 批 3：L5）：**完成并验证**。`verify_choice_keys`（独立求钥，冲突拒绝注册；视觉题跳过；config=None 保持离线）+ `mastery_quiz` 生产接线（文本选择题显式解析 config）；`test_repair_question…` 补离线桩（repair 流程保留为 reviewer 出错的兜底）。测试：新增 `test_key_review.py` 11 项；全量回归 1265 passed/1 skipped（learning+reading quiz+teaching samples+session/storage/backup）；ruff 干净——期间抓出并修复该回归测试打真实网络的问题（22.9s→3.99s）。真模型探针：错钥卡被独立求钥拒绝（derived B vs stored A）、一致钥卡审核通过；11 次调用 13,420+9,753 tokens（O2 费用未知）。phase 保持 `DEV_LOGI`。
- 2026-11-08（轮 5，ACCEPT_LOGI 验收段）：**完成，phase 推进为 `DONE_AWAITING_REVIEW`**。新鲜取证（HEAD 直测，非沿用开发轮结果）：全量回归 1265 passed/1 skipped；ruff check/format 干净；E1 report 重跑（6 样本 0 机械失败、1 项语义分歧如实携带、transfer_failure 已覆盖、其余 6 种情形无样本如实列）；S6 重放 diffs 0（5/5 判类一致，含 dont_know→ungraded+declared_unknown）。验收表见 11.5 节。**L 系列真模型消耗合计**：51 次调用 94,952+52,798 tokens，台账全记录（complete_with_config 逐 attempt 口径，O2 费用未知）。

### 11.5 ACCEPT_LOGI 验收表（2026-11-08 编制）

判定口径沿用第 9/10 节：passed=本轮新鲜证据；分歧=如实保留；未执行=注明原因。**结论：L1–L5 交付全部通过验收（边界如实保留）；分歧②（S4 等价边界）留人工复核；phase 推进为 `DONE_AWAITING_REVIEW`。**

| 交付 | 判定 | 验收证据（轮 5 新鲜取证） |
|---|---|---|
| L1 判分语义（dont_know 裁决 + declared_unknown 巩固信号） | passed | 全量回归 1265 passed/1 skipped（含 `test_declared_unknown.py` 8 项）；E1 dev 集三样本回放：S1/S5 diffs 0、三卡 dont_know 一致 ungraded+declared_unknown（**分歧①按 11.2 节裁决收敛**）；S6 迁移卡判分 dont_know→ungraded 一致。巩固信号幂等性有专项测试；旧回执无新字段回归兼容有专项测试 |
| L2 机械防线（位置依赖拦截 + 批内同干拒绝 + stem 历史） | passed | `test_quiz_guards.py` 30 项含跨轮同题放行回归（retry 流不破坏）；位置正则保守集有正反例参数化测试 |
| L3 题目设计层 | passed | design 注册→持久化→操作历史→design_hint 机械推荐全链有测试；leaf schema 注入断言；真模型 propose 经 design 层出反事实迁移卡成功（L4） |
| L4 迁移情形样本 | passed | S6 入库（report：6 样本 0 机械失败，transfer_failure 已覆盖）；五类判分 5/5；S6 重放 diffs 0（轮 5 重跑）。**边界**：S6 一张（"1–2 张"下限），S7 未出；操作员撰答沿轮 8 先例 |
| L5 答案钥注册复核 | passed | `test_key_review.py` 11 项；真模型探针错钥拒绝/一致钥通过；离线纪律修复（回归测试不再打真实网络）；视觉题与 config=None 路径有专项测试。**边界**：reviewer 与出题同时出错的残余场景由 repair 工具兜底（有测试） |
| E1 工具完整性（计划外修复） | passed | `_resolve_question` 按题号解析 + `add` 子命令 + verdicts 按题过滤；`test_teaching_samples.py` 13 项；S1/S6 双重放实证（共享路径、各自按己题判分，均 diffs 0） |

**分歧与边界（处置与留存，不刷绿）**：
1. **分歧②已裁决（2026-11-08 用户）**：等价成立——替代方案按目的判定，两类替代问法都是好问题。处置：judge 提示词补目的判定规则；重放 S4 judge 仍 partial（把"未来导向/间接"视为目的本身），按用户语义权威将样本该行覆盖为 correct（owner_ruling 注记 + 重放证据指针 `replays/S4-1794098755…`）；**judge 持续异议如实保留为已知限制**——该边界上 judge 比所有者标准更严，未继续调提示词刷绿。顺带：S2 dont_know 期望类按 L1 裁决后政策更新（incorrect→ungraded），report disputed_answers 现为 0。
2. L1 的 dont_know 裁决方案（ungraded+巩固信号）按 agent 推荐实施（11.2 节），用户 2026-11-08 复核待决策清单时未否决；若日后否决，回退路径：judge 提示删 declared_unknown 规则 + 停用巩固信号（单点开关 `verify_choice_keys` 同理可回退）。
3. L4 迁移样本 S6 一张；6 种教学情形仍无样本（report 如实列）。
4. L5 探针"一致钥卡"注册为 no-op（挂起位占用），其审核链证据完整但注册路径的真模型一致案由 `test_consistent_key_registers`（假 provider）覆盖。
5. **judge 等价边界的已知限**（分歧②处置的副产物）：目的判定规则下 judge 对"概括未复述限定词"的替代方案仍偏严；真实使用（C6）中若再遇同型分歧，按同一权威流程裁决（用户裁定 → 样本注记覆盖 → judge 限留档），不自动刷绿。

**L 系列真模型消耗（台账口径）**：批 1 回放 15 + 批 2 出卡判分 14 + 批 3 探针 11 + 验收回放 11 = 51 次调用，94,952+52,798 tokens，全部 completed（complete_with_config 逐 attempt 计费，O2 口径费用未知）。
- 2026-11-08（轮 6，DONE_AWAITING_REVIEW 复核段：用户裁决五项待决策）：**三项裁决落地，两项状态更新**。①C2 批量生成=不做（关闭）；②E4=暂不开展（关闭）；③分歧②=等价成立（用户裁定两类替代问法都是好问题）——judge 提示词补"替代方案按目的判定"规则，重放 S4 judge 仍 partial（如实记），按用户语义权威覆盖样本判类为 correct（owner_ruling 注记+证据指针），顺带修正 S2 dont_know 过期期望类（incorrect→ungraded），report disputed_answers 0；④C6=用户已知悉协议，等真实时间；⑤第二份方法类 PDF=用户提名 4 本候选均属方法类（核对结论），等 PDF 路径或明示关闭。改动：`semantic_assessment.py` judge 提示一句 + `data/` 样本注记（git-ignored）+ 本文；离线快速回归 32 passed。phase 保持 `DONE_AWAITING_REVIEW`。真模型消耗：S4 重放 5 次逻辑调用（台账逐 attempt 计），O2 口径费用未知。
- 2026-11-08（轮 7，DONE_AWAITING_REVIEW 复核段：C2 方法类 PDF 收尾）：**完成**。用户提供《销售铁军》（贺学友）——核对为文字型方法类 PDF（222 页正文 11.2 万字，抽样均 505 字/页）。**过程中发现并修复抽取崩溃 bug（如实记，超原话范围的最小必要修复）**：本书内嵌字体 CMap 损坏使抽取文本含孤立代理字符，`ReadingStore.ingest` 写 manifest 时 UnicodeEncodeError 崩溃——`extract.py` 抽取边界统一清除 surrogates（units/title/outline），新增 `tests/reading/test_extract_surrogates.py` 3 项。C2 收尾：接入 material 30f2747b9933252e → 备课覆盖审核（p140/p100 两单元 complete）→ 真模型出题（design 层 construct/diagnose）→ bind 引文逐字审查通过（provenance=adapted：本书抽取句中带空格，字节级 original 不可达，如实记）→ 五类作答真模型判分 **10/10 按预期** → S7/S8 入样本库。report：8 样本 0 机械失败 0 分歧；C2 三种书型各 2 单元的样本要求达成。过程教训（如实记）：覆盖审核的引用门禁对本书有 ~50% 的模型逐字引用失败率（3 次失败 + 1 次手测 4/4 命中诊断确认为抽样方差非门禁/文本缺陷），操作员脚本采用有界重试（≤3 次/卡）通过；产品流程内不自动重试的行为保持不变。回归：tests/reading + learning 全套 + teaching samples 共 1206 passed/1 skipped，ruff 干净。真模型消耗（本轮）：coverage 审核约 7 次（含失败尝试）+ 出题 2 + bind 2 + 五类判分 10 ≈ 21 次逻辑调用（台账逐 attempt 口径），O2 费用未知。phase 保持 `DONE_AWAITING_REVIEW`。待用户余：C6 试用 + 用户人工引用核对。
