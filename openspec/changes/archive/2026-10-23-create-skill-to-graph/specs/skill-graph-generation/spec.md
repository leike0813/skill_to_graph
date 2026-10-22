# Spec Delta

## Purpose

将源 Skill 的契约、行为约束和自主判断空间转换为可执行图的语义，保留用户可观察的输入输出、副作用、交互及失败行为，使流程显式化而不改写源任务。

## ADDED Requirements

### Requirement: Preserve source business behavior
生成图 MUST 保留源业务契约、明确的顺序和权限要求、文件产物、副作用、确认环节及失败行为。自然语言变化 SHALL 按源要求判断；只有源明确要求的内容才作逐字比较。

#### Scenario: Keep approval before writing
- **WHEN** 源 Skill 要求用户确认后才能写文件
- **THEN** 图在确认前不写文件，即使提前写入会产生相同最终内容

### Requirement: Resolve actual source conflicts
转换器 MUST 列明包内影响行为的矛盾、位置及不同解释的影响，并请求澄清，SHALL NOT 静默选择解释或修改源行为。源明确留给模型的定性判断 SHALL 保留，不作为普遍补充材料要求。

#### Scenario: Instructions conflict with a script
- **WHEN** 指令要求确认后发布，而对应脚本直接发布
- **THEN** 转换器提交该差异供澄清，不擅自复制或修正其中一种行为作为源契约

### Requirement: Preserve local control and autonomy
生成图 MUST 按局部流程保留固定阶段和模型自主决策空间，支持两者组合。转换 SHALL NOT 为可控性新增业务步骤、审批或固定策略，也不得机械地将句子或编号逐一转换为节点。

#### Scenario: Convert a mixed workflow
- **WHEN** 源流程为检查输入、自主检索、用户确认、输出报告
- **THEN** 图保证这些阶段约束，并允许检索阶段按源要求自主选择工具

#### Scenario: Keep a fully autonomous workflow minimal
- **WHEN** 源 Skill 自主安排工作且没有需要外部固定的阶段
- **THEN** 生成图保留其自主行为，不额外增加无源依据的阶段

### Requirement: Preserve condition meaning
明确数据可判定的条件 SHALL 按该数据判断；源规定的语义条件 MUST 保留模型判断及相应分支，SHALL NOT 自行替换为数量、字数或关键词门槛。

#### Scenario: Assess evidence sufficiency
- **WHEN** 源要求资料不足时继续检索
- **THEN** 图依资料充分性的语义判断决定继续或结束，不用检索次数替代该条件

### Requirement: State and resource visibility follow the workflow
生成图 MUST 保存跨阶段传递或恢复所需的信息及源要求的历史上下文，保持参考资料按需读取。转换 SHALL NOT 固化统一的大状态契约或将所有参考资料预先注入模型上下文。

#### Scenario: Read a reference only when needed
- **WHEN** 源流程要求特定条件下才读取一份参考资料
- **THEN** 图保留该条件下的读取能力，而不是在任务开始前无条件加载全文

### Requirement: Preserve loop and parallel semantics
循环 MUST 保留源停止条件及明确次数限制。并行 MUST 有源流程许可且保持顺序要求、副作用和汇总对应关系；逐项处理 SHALL NOT 自动解释为并行。运行步数受限 MUST 报告为执行受限。

#### Scenario: Runtime limit is reached
- **WHEN** 运行时步数限制先于源业务停止条件触发
- **THEN** 图报告执行受限，不把该任务当作正常完成

#### Scenario: Process an ordered collection
- **WHEN** 源要求逐项处理并按原顺序汇总
- **THEN** 图保留对应关系和顺序，并且不会仅凭逐项措辞就启用并行

### Requirement: Preserve failures and disclose recovery limits
生成图 MUST 遵循源失败策略，SHALL NOT 额外增加图级自动重试、降级或补偿。恢复机制 MUST 实际支持所声明的副作用安全性，不能保证安全恢复的操作 MUST 明确限制。

#### Scenario: Source requires stopping on failure
- **WHEN** 源流程要求工具失败后停止并报告
- **THEN** 图遵守该行为，不以自动重试或成功返回替代失败

#### Scenario: Resume near an external side effect
- **WHEN** 外部操作可能因恢复重跑而重复执行
- **THEN** 图采用能实际避免重复的恢复安排，或明确其限制，不仅凭存在检查点就宣称不会重复执行

### Requirement: Declare and call required runtime capabilities
生成图 MUST 保留源需要的工具和委派调用逻辑并声明外部依赖，不能以空函数冒充实现。模型配置、凭据及外部能力由运行环境提供；缺失条件 MUST 与转换逻辑错误分别报告，不仅因此阻止产物生成。

#### Scenario: External service is unavailable during conversion
- **WHEN** 源包足以确定外部服务的调用要求但当前环境没有该服务
- **THEN** 转换器生成实际适配逻辑并声明运行依赖，标明相应接入尚未验证，不要求源包追加运行记录

#### Scenario: Another skill is required
- **WHEN** 源 Skill 调用其他 Skill 或 agent
- **THEN** 图保留调用约定并声明依赖，不默认递归转换所有外部 Skill 或替换委派行为

### Requirement: Keep permission meanings distinct
生成图 MUST 区分工具存在、预授权与禁止规则，保留源明确的权限语义并遵守目标环境授权。工具预授权字段 SHALL NOT 一律解释为仅允许注册这些工具的白名单。

#### Scenario: A preauthorization list is present
- **WHEN** 源包字段在其适用语义中列出预授权工具
- **THEN** 图保留预授权含义，不仅因某工具未列于该字段就推定源禁止该工具

### Requirement: Preserve human interaction boundaries
生成图 MUST 在源规定的位置暂停并保留必要流程状态，在接收回复后继续。调用环境负责问题呈现、回复提交、会话上下文和所需存储设施。

#### Scenario: Continue after a user reply
- **WHEN** 用户在源要求的等待点回复
- **THEN** 图使用该回复恢复对应流程，保持源要求的后续行为和副作用时机

### Requirement: Publish a self-contained execution contract
发布 Skill MUST 在主文件中完整说明流程、输入输出、硬约束、Agent 与脚本职责、脚本调用和完成条件；参考资料提供按需说明并标明读取时机。执行 SHALL 不依赖开发仓库文件或脚本进行语义路由。

#### Scenario: Use the published skill outside this repository
- **WHEN** 执行 Agent 只取得发布 Skill 包与声明的运行条件
- **THEN** 它能够从主文件理解完整转换流程，按需读取包内参考，不需要访问开发期决策票
