# Proposal

## Why

`skill-to-graph` 的转换功能与验收框架已经齐备。本次依据 skill-smith 优化执行指令的组织与可发现性：主文件中的职责和边界较分散，部分运行易错点主要依赖参考资料，命令帮助尚未完整说明结果与副作用，增加了执行 Agent 漏读和试错的机会。

## What Changes

- 保留现有脚本辅助工作流，以主文件清晰呈现目标、非目标、输入输出、职责分工、硬约束和六步转换流程；合并重复表达，不以缩短篇幅删减义务。
- 将参考资料中执行必需的要求提炼回主文件，参考资料保留 API 示例、语义说明和正反例，并明确读取时机。
- 补全两个辅助命令及包处理子命令的帮助信息，说明输入、输出、写入边界、示例及检查能力范围，保持参数、JSON 结果和退出码不变。
- 使用已有契约和测试复核行为保持情况；不添加指令文本快照、关键词门禁、状态数据库或新转换功能。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。本次落实既有 `skill-graph-generation` 中的 `Publish a self-contained execution contract`，并改善 `skill-package-processing` 中已有帮助信息的表达，不改变要求及可观察业务行为。`.openspec.yaml` 设置 `skip_specs: true`，不编造 delta specs。

## Impact

- 修改发布包 `skill-to-graph/SKILL.md`、`references/runtime-api.md`、`references/skill-to-langgraph-mapping.md`，以及 `scripts/skill_package.py`、`scripts/check_graph.py` 中的命令帮助。
- 保持源包路径及可选输出路径、完整快照、Python/CLI 共享构图、能力接入、权限、失败与修正路径、证据范围等契约。
- 复用 `tests/` 的脚本测试、源样本和验收说明；不改已有生成图、历史证据、模型配置或仓库开发期参考资料。
- 无新增依赖、命令参数、公共结果字段或部署要求。优化效果先通过语义复核确认，正式重新转换及真实模型验收另须具备运行条件和相应授权。
