# Spec Delta

## Purpose

使生成图成为可以独立搬移、按声明条件配置并由 Python 或 CLI 调用的应用目录，明确源业务契约与框架调用形式之间的映射，并提供有限而可信的确定性检查结果。

## ADDED Requirements

### Requirement: Lossless invocation mapping
图调用封装 MUST 明确源输入的传入方式及业务结果的取得方式，保持业务含义、格式及文件产物。框架状态 SHALL NOT 被强加为所有源 Skill 的统一业务契约。

#### Scenario: Preserve a file-producing contract
- **WHEN** 源 Skill 要求生成 CSV 文件
- **THEN** 图实际生成该文件，运行说明指出其取得方式，不以状态中的 CSV 字符串替代文件

#### Scenario: Expose a conversational task
- **WHEN** 图使用消息封装传递源任务和回复
- **THEN** 说明区分业务输入输出与框架字段，不要求源任务新增无源依据的业务字段或统一返回 `messages/artifacts`

### Requirement: Minimum independently distributable application
生成产物 MUST 包含完整源包、可导入的图代码、`langgraph.json`、依赖声明和运行说明。源包与生成代码 MUST 分放，项目验收环境及不参与图运行的转换器资产 SHALL 不进入产物。

#### Scenario: Inspect a delivered application
- **WHEN** 用户取得生成目录
- **THEN** 能找到源资源、图入口、声明的依赖及配置和运行方法，且不需要项目验收环境文件作为图的一部分

### Requirement: Relocatable source resources
生成图 MUST 保持携带资源的相对引用语义，区分源包位置与任务工作目录；搬移后 SHALL 不依赖转换时原包的绝对路径。外部运行依赖仍由目标环境提供。

#### Scenario: Run from a relocated directory
- **WHEN** 产物被复制到新目录并在满足声明条件的环境中调用
- **THEN** 图从携带的源包取得运行资源，任务文件仍按源契约和任务上下文处理

### Requirement: Shared graph behavior across entry modes
Python 与 CLI MUST 使用相同构图逻辑及业务语义。入口 MUST 按需要接入会话和存储设施，公共图逻辑 SHALL 不写死后端或依赖仅由服务端注入的身份信息才能执行普通 Python 任务。

#### Scenario: Supply persistence through the caller
- **WHEN** Python 调用需要暂停恢复
- **THEN** 调用方可提供必要会话及存储设施，而 CLI 入口可接入对应服务运行时设施

#### Scenario: Export only the needed entry form
- **WHEN** 一份产物按配置需要选择图对象或图工厂
- **THEN** 运行说明与 CLI 配置指向实际入口，不强制产物同时提供两种导出形式

### Requirement: Preserve source identity with valid technical names
源 Skill 名称 MUST 保留；graph ID 在目标允许时沿用源名，其他技术标识 MUST 符合目标规则。必要名称转换 MUST 明确映射，SHALL NOT 为命名方便改写源包。

#### Scenario: Source name contains a hyphen
- **WHEN** 源名为 `data-analysis`
- **THEN** 源名保留，Python 模块或变量采用合法名称，映射在运行说明中可查

### Requirement: Explicit runtime requirements
运行说明 MUST 覆盖输入输出映射、外部依赖、模型和服务配置、两种调用方式及适用的恢复方法。产物 SHALL 不承诺任意环境均具备依赖，SHALL 不携带真实凭据或暗中选择未由源规定的模型供应商。

#### Scenario: Configure an unspecified model
- **WHEN** 源 Skill 没有指定模型但任务需要模型能力
- **THEN** 调用方按声明能力配置模型和凭据，生成代码不依赖隐藏默认供应商

### Requirement: Bounded deterministic artifact checks
产物检查工具 MUST 检查生成代码语法、配置及可确定的入口和资源路径问题，并提供稳定机器可读结果。检查 SHALL 不执行生成图、调用模型或外部服务，也不将静态通过表述为可运行或语义保真证明。

#### Scenario: Catch a broken entry path
- **WHEN** 配置所指的本地图入口文件不存在
- **THEN** 检查结果报告该路径问题并以失败状态返回

#### Scenario: Static checks pass without runtime dependencies
- **WHEN** 代码和显式配置的确定性检查通过，但当前未提供运行依赖
- **THEN** 结果仅说明检查通过，明确未取得加载、业务执行或保真证据
