# Spec Delta

## ADDED Requirements

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
