# conversion-acceptance Specification

## Purpose

用范围明确的代表性样本和最小仓库环境取得转换验收证据，区分结构检查、实际调用及行为保真结论，使环境受阻、未验证和已知违约均能被准确记录并用于修正转换结果。

## Requirements

### Requirement: Repository-only acceptance environment
项目 MUST 在发布目录外准备最小验收环境，满足选定被测图声明的运行依赖。环境、样本及验收资产 SHALL 不随转换 Skill 或生成图分发；连接和凭据通过运行配置提供。

#### Scenario: Prepare dependencies for a selected graph
- **WHEN** 一个验收图需要指定的解释器、模型或外部工具
- **THEN** 仓库环境提供对应条件或明确记录环境受阻，不要求发布产物包含该环境

### Requirement: Representative contract-derived samples
首版 MUST 用少量受控样本及至少一个真实 Skill 覆盖固定、自主、混合流程，以及分支循环、人工确认、文件副作用和失败处理。预期 MUST 来自源契约，同一样本可覆盖多个风险。

#### Scenario: Reuse a mixed-workflow sample
- **WHEN** 一个样本同时含语义判断、确认和文件写入
- **THEN** 用它核对相应多项行为，不为每个功能点机械增设独立样本

### Requirement: Distinguish controlled doubles from real integrations
替身 MUST 仅提供其实际覆盖范围的证据；真实本地文件与脚本直接执行，代表性整体场景 MUST 使用真实模型及所需工具。替身通过 SHALL 不代表真实外部接入通过。

#### Scenario: Inject a controlled tool failure
- **WHEN** 替身稳定返回工具失败以驱动错误路径
- **THEN** 验收记录该失败处理行为，不据此声称真实服务连接或调用已验证

#### Scenario: Required live dependency is absent
- **WHEN** 必需的真实模型或服务不可用
- **THEN** 对应真实验收记为环境受阻，不以替身结果计作该项通过

### Requirement: Judge observable source obligations
验收 MUST 以源契约检查输入输出、文件、副作用、顺序、交互和失败行为。确定性行为检查可观察结果，模型相关行为按明确要求审查，必要时人工复核。源与图对照仅提供辅助证据。

#### Scenario: Both source and generated graph violate a rule
- **WHEN** 对照运行中双方都在确认前写入文件，而源要求确认后写入
- **THEN** 验收判定已知违约，不因双方相同而通过

#### Scenario: Natural language differs within the contract
- **WHEN** 回复措辞不同但满足源内容、格式和语气要求，且源未要求逐字一致
- **THEN** 不仅因措辞差异判定失败，不使用无源依据的整段文本快照作为判据

### Requirement: Verify both entry modes and relocation
选定验收图 MUST 在 Python 与 CLI 两入口取得加载和基本调用证据。复杂行为主要在一条路径深入验证，另一条检查入口差异；适用时覆盖暂停恢复。验收 MUST 在搬移后的目录实际核对携带资源的使用。

#### Scenario: One entry only imports successfully
- **WHEN** Python 完成业务调用而 CLI 仅验证了入口可加载
- **THEN** CLI 基本调用仍未验证，对应必验项尚未完成

#### Scenario: Validate a moved application
- **WHEN** 产物搬到新目录后完成任务且使用携带的源资源
- **THEN** 记录该范围的搬移证据；首版默认验收不额外要求镜像构建或托管部署

### Requirement: Evidence-bounded completion
验收 MUST 在判断前明确范围和预期，记录源样本、契约要求、运行配置、观察、依据及未覆盖范围。必验项均有支持证据且无已知违约才通过；未运行、证据不足和环境受阻 MUST 分别注明且不计通过。

#### Scenario: A required case remains blocked
- **WHEN** 已选必验场景因环境缺口无法执行
- **THEN** 对应验收不计通过，缺口与转换逻辑错误分开报告，不通过事后缩减范围掩盖问题

#### Scenario: Complete the declared sample matrix
- **WHEN** 已选必验场景均满足源契约并有证据支持
- **THEN** 仅对该验收范围给出通过结论，不外推任意 Skill 和执行路径均已保真

### Requirement: Maintain behavior-focused script tests
脚本测试 MUST 覆盖稳定、可观察的包处理与产物检查行为，不静态断言 Skill 指令文本。正式验收还 MUST 区分结构检查、加载、执行及保真证据。

#### Scenario: Revise instruction wording without changing behavior
- **WHEN** 主文件文字表达调整而工具业务行为与源契约保持一致
- **THEN** 不因对整段指令的文本断言失败而阻断验收

### Requirement: Verify obligations at runtime responsibility boundaries
验收 MUST 核对跨阶段和委派时适用规则及必要参数的可见性，并按源要求复核实际语义产物。结构合法、文件存在或语言元数据正确 SHALL NOT 替代正文语言、内容依据及权限边界的验证。复验 MUST 保留旧证据并区分新旧生成物。

#### Scenario: Language metadata disagrees with report content
- **WHEN** 引文 JSON 标为中文而报告正文大量使用英文
- **THEN** 验收判为违反语言契约，即使结构及渲染一致性检查全部通过

#### Scenario: Source control run also violates its instructions
- **WHEN** 对照执行错误转述最终 JSON 或子代理读取分配批次之外的材料
- **THEN** 记录其违约及比较限制，不以对照输出为正确答案，也不因此免除图的源契约要求

#### Scenario: Revalidate an optimized conversion
- **WHEN** 调整转换职责后重新验收真实样例
- **THEN** 在新的生成和运行目录取得证据，保留首次失败产物，并逐项说明正文、控制流程和恢复行为的复核结果
