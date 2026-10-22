# skill-to-graph 首版转换决策地图

Labels: wayfinder:map
Status: resolved

## Destination

明确首版 `skill-to-graph` Skill 包的范围、转换规则、运行前提与验收方法，使后续会话可以据此编写 OpenSpec 规格并开展实现，无需自行补足关键产品或架构决策。

## Notes

- 用户已确认本轮以决策地图为终点；OpenSpec 规格编写、实施任务拆分与实现属于后续工作。
- 当前规划已完成。进入 OpenSpec 时从本地图按需读取各票答案，交接文件范围和实现反馈处理见最后一票。
- 项目产物是发布在 `skill-to-graph/` 的 Agent Skill 包，核心为自然语言指令及必要的确定性脚本。
- 源 Skill 的意图、行为规则与输入输出契约必须保持一致。外部能力缺失时报告运行或验收条件缺口，不自行替换行为；生成结果与保真验证结论按对应议题分别判断。
- 领域讨论使用 `grilling` 与 `domain-modeling`；需要外部事实时使用 `research`，需要具体样例辅助讨论时使用 `prototype`。
- 项目约束见 [AGENTS.md](../../AGENTS.md)。[转换映射参考](../../references/skill-to-langgraph-mapping.md)包含待审视的设计建议，不能将其默认契约、工具限制或目录示例直接视为用户已批准的规格。
- 领域术语见 [GLOSSARY.md](../../GLOSSARY.md)；具体决策及其适用边界记录在对应议题。
- 本地跟踪约定见 [Local Markdown tracker](../../.agents/skills/setup-matt-pocock-skills/issue-tracker-local.md)。子议题位于 `issues/`；`Status: open` 表示未认领，处理前改为 `claimed`；完成实时讨论后追加 `Answer` 并改为 `resolved`。`Blocked by` 中的议题全部解决后才解除阻塞。按编号选择第一个开放、未认领、未阻塞的议题。
- 地图仅索引已解决的决策；具体答案只记录在对应议题。建图阶段不代替用户解决议题；每次后续会话最多解决一个非研究议题。
- 本轮从本地参考资料出发；尚无需要单独建立的外部研究议题。

## Decisions so far

- [如何定义并判断转换前后的行为保真？](issues/01-fidelity-contract.md)：保留源契约及模型判断空间，验证结论限于证据覆盖范围。
- [转换以哪些材料为依据？](issues/02-conversion-evidence.md)：合法源包是完整转换依据，包内矛盾需澄清，运行配置另行确定。
- [源 harness 的能力与权限如何在目标运行环境中落实？](issues/03-runtime-capabilities.md)：图保留调用与交互逻辑并声明依赖，环境提供外部能力；验收环境仅为仓库资产。
- [固定流程、自主决策和混合流程如何映射为图？](issues/04-graph-semantics.md)：按局部语义组合图与 agent，状态和恢复按需设计，保留源循环、并行及失败策略。
- [生成图的调用契约与独立分发边界是什么？](issues/05-generated-artifact-contract.md)：调用封装保持源业务契约，完整源包与图代码分放，按需导出共享图逻辑的入口。
- [用哪些场景和证据验收转换结果？](issues/06-validation-evidence.md)：以源契约验收代表性样本，区分真实能力与替身证据，验证双入口及搬移，环境受阻不计通过。
- [Skill 核心指令、脚本和资料如何分工并交接给实现？](issues/07-skill-package-responsibilities.md)：核心契约集中于主文件，Agent 生成具体图，脚本处理确定性工作，交接文件范围及完成条件已明确。

## Not yet specified

无已知阻塞规划的问题。原先对样本语义组合及验收差距的担忧已由映射、验收和[实现交接原则](issues/07-skill-package-responsibilities.md)承接；具体执行反馈留待实现阶段处理。

## Out of scope

- 本轮编写 OpenSpec 规格、实施任务或交付 Skill 包实现：均在决策地图完成后开展。
- 调整源 Skill 的目的、行为或输入输出契约：违反项目目标。
- 为缺失能力提供未经确认的替代行为：违反已确认的保真底线。
- 将项目扩展为通用 Agent 平台、harness 产品或托管部署服务：超出本项目 Skill 包的交付目标。
- 将通用 harness transcript 适配作为转换器能力：其原始要求已由用户撤回，见[转换依据议题](issues/02-conversion-evidence.md)的范围澄清。
