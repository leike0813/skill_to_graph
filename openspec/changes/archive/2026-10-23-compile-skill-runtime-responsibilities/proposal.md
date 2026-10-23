# Proposal

## Why

首版已交付转换 Skill、辅助脚本及真实验收资产，但 literature-analysis 图在每个阶段重新注入完整源指令，遗漏跨阶段语言参数，并限制了后续修正。需要在转换时完成职责拆分，使运行图落实源流程，并完成从 `create-skill-to-graph` 迁入的保真和整体验收。

## What Changes

- 在转换流程中明确源约束的执行者、所需数据、工具权限和验证方法；固定控制进入图，语义判断保留在局部节点。
- 按职责提供运行指令与必要上下文，将语言等适用约束传递到阶段和委派代理；完整源包继续用于资源调用与追溯。
- 保留源允许的修订和恢复路径，不为阶段控制额外禁止必要修正，也不增加源未授权的重试。
- 接收第一轮原任务 5.2、5.4，保持其验收标准和未完成状态；用新目录重新转换并验收，保留首轮失败证据。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `skill-graph-generation`：明确局部运行职责、适用约束和参数传递，以及源允许的修正路径。
- `conversion-acceptance`：增加跨节点、委派边界和语义正文的验收要求，承接完整保真与整体验收。

## Impact

- 主要修改发布包 `skill-to-graph/SKILL.md` 及包内映射参考，按需同步根目录开发映射；不建设通用编译器或统一中间语言。
- 复用现有测试驱动、受控样本及真实 `wait-what`、`literature-analysis` 样本，在独立新目录生成优化后的图，保留原包、首次图和既有结果。
- 模型、外部工具与依赖仍由环境提供；不增加依赖安装或服务启动的默认行为，不以文本快照、关键词或字符占比代替语义验收。
- 迁入来源及失败依据见首轮任务范围调整说明、`tests/acceptance/RESULTS.md` 和 `tests/acceptance/literature-analysis-attention/REPORT.md`。
