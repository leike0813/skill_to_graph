# 本轮转换与验收范围

本轮由执行 Agent 读取当前发布 `skill-to-graph/SKILL.md` 后重新转换 `tests/fixtures/skills/wait-what`。
`skill_package.py inspect` 成功；`copy` 创建新的 `generated/wait-what-graph`，完整快照保持原样。
此前的 round2 图、提示及证据不参与本轮生成，也不被覆盖。本轮不是在旧图上仅更换模型。

| 源义务 | 源位置 | 执行者与输入 | 实现与验证 |
| --- | --- | --- | --- |
| 显式调用 | SKILL.md frontmatter `disable-model-invocation` | 调用环境 | 只经显式 Python/CLI 入口，README 说明触发含义 |
| 重述前一条 assistant 并给少量上下文 | SKILL.md 正文 | 单一自主 agent；完整会话、绑定的目标原话 | dynamic_prompt 提供完整正文及通用目标绑定；核对首轮模型输入与实际回复 |
| 简化英语 | SKILL.md 正文 | 同一 agent；源语言要求 | 逐份语义审阅句子与用词；不声称词典级 ASD-STE100 认证 |
| 使用术语表，多个时按 MAP 选择 | SKILL.md 正文 | 同一 agent；任务目录与只读文件工具 | 审阅实际工具调用和 Graph/Node/Checkpoint 的使用；本轮只测单术语表 |
| 保持模型自主性 | SKILL.md 全文 | create_agent | 无人工拆出的固定业务阶段，保留读资源与重述的自主过程 |

范围与预期在运行前确定：原会话与上一轮相同，两组分别运行三次；图为 Responses 模型
`combo/deepseek-v4.1-flash`、`reasoning.effort=high`，omp 为
`commandcode/deepseek/deepseek-v4.1-flash`、`--thinking high`。
图使用原生消息角色；omp 接受相同会话的带角色 JSON，属于已知调用差异。

每次工作目录只提供术语表（omp 另有完整源包），不提供旧结果。
语义预期来自原话：Graph 在确认点等待；已保存的 Checkpoint 关联回复与暂停执行；
恢复后下游 Node 生成报告；崩溃后的外部写入没有 exactly-once 保证。
不能增加新的操作义务、去重保证或把已存状态改成批准后才发生的步骤。
以原话含义审阅，不以完整文案、关键词比例或图与 omp 相同为通过标准。

本轮取得 Python 加载、基本调用和真实模型证据，静态检查另记。
不启动 CLI 服务；CLI 运行、搬移、MAP 分支、其他 Skill 和生产恢复均不计为已验证。
两组一方违约不免除另一方义务，也不自动证明转换是根因。
