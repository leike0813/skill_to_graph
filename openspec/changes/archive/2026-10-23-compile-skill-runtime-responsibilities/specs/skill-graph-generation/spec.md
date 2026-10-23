# Spec Delta

## ADDED Requirements

### Requirement: Execute decomposed runtime responsibilities
转换器 MUST 在转换时确定局部职责及其输入输出，将源的固定流程落实为图控制，将语义判断交给对应自主区段。运行节点 MUST 取得其职责所需指令和证据，SHALL NOT 默认通过向每个阶段重复注入完整源 Skill 来重新解释全流程。纯自主源可保留完整自主区段。

#### Scenario: Run one stage of a structured analysis
- **WHEN** 源流程有计划、摘要、评分和引文分析等明确职责
- **THEN** 图控制它们的先后及分支，摘要阶段仅承担摘要判断并取得适用规则、输入与证据

#### Scenario: Preserve a fully autonomous source
- **WHEN** 源没有可独立固定的阶段，完整任务本身是一个自主区段
- **THEN** 图保留该区段及其必要指令，不为缩短上下文人为切分自主行为

### Requirement: Carry applicable obligations across execution boundaries
生成图 MUST 将业务参数、适用的源约束及必要历史上下文传给需要它们的阶段或委派代理。约束仅存于快照、DB 或其他不可见位置 SHALL 不计为已交付执行者；传递约束 SHALL 保持批次证据和权限边界。

#### Scenario: Keep the requested report language in delegated work
- **WHEN** 用户指定中文报告，引文语义工作交给只读单个 batch 的代理
- **THEN** 该代理明确得到中文要求及本批次证据，主代理合并的正文遵守同一要求，且不额外开放其他批次或 DB

### Requirement: Retain source-permitted correction paths
生成图 MUST 保留源允许的业务修正、重渲染和恢复路径。阶段推进 SHALL NOT 单独成为禁止这些操作的理由；修正仍须遵循源的写入、失败及副作用边界，SHALL NOT 演变为源未许可的自动重试或补偿。

#### Scenario: Correct an output after an initial submission
- **WHEN** 首次提交已推进阶段，但内容违反源要求且源允许通过正式提交修正
- **THEN** 图允许按该路径修正并重渲染，不因已提交过一次而强制交付违约结果
