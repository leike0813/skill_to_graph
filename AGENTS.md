# skill-to-graph （Agent skill 向 LangGraph 图的转换工具）

## 项目背景

- 本项目是一个 **Agent Skill** 开发项目，并非常规软件工程项目
- 本项目旨在开发一个用于将 Agent skill 转化为可被 `langgraph` CLI 或其他可以执行 LangGraph 图的运行时执行的 LangGraph 图

## 目标

- **将任意 Agent Skill 转化为 LangGraph 图**：本 Skill 的输入为一个 Agent Skill 包路径。产物为一个可被 `langgraph` CLI 或其他可以执行 LangGraph 图的运行时执行的 LangGraph 图
- **保持功能不变**：转化后的 LangGraph 图必须与源 Skill 具有完全相同的功能
- **提高流程控制能力**：转化后的 LangGraph 图的执行流程应可以更加准确、可控

## 非目标

- **改变源 Agent Skill 的意图**：不得擅自增加/修改/删除源 Skill 的行为模式和规则
- **改变源 Agent Skill 的输入输出契约**：转化后的 LangGraph 图必须具有与源 Skill 完全一致的输入输出契约

## 你该做什么

- 本文档仅是一份宏观指导，距离可供 Agent 实施的详细指令（SKILL.md）还有不小距离
- 你的任务是，基于目前的宏观指令，生成符合 Open Agent Skills 规范的 Skill 包。本项目 Skill 包的发布目录为 `skill-to-graph` （与 Skill 名称一致）
- 本项目是 Agent Skill 开发项目，其核心是用自然语言（面向LLM的语言风格）编写 Skill 包的核心指令文件 `SKILL.md`，明确 Skill 的输入/输出格式、任务目标/非目标、关键约束、执行流程
- 为实现 Skill 的既定目的，可以适当地编写 Python 脚本，用于在 Skill 执行过程中将一部分确定性的、重复性大的业务逻辑从 Agent LLM 的职责中 offload。不过需要注意，所有编写的脚本都需要在 `SKILL.md` 中显式说明其用途、调用方法和调用时机。
- 生成图须保留源 Skill 所需能力的调用逻辑并声明外部运行依赖；这些依赖由调用环境提供，图不承诺任意运行环境都能满足依赖。
- 转换时完成职责拆分；多阶段图的运行 Agent 使用局部指令和明确传入的适用约束，图承载固定控制，并保留源允许的修正路径。
- 首版验收在仓库内准备最小验收环境，按选定被测图声明配齐运行依赖。该环境仅为仓库资产，置于发布目录外，不随 Skill 包或转换图分发。

## 你不该做什么

- **避免生成不符合 Open Agent Skills 规范的文件**：Open Agent Skills 规范规定，一个 Skill 包中必须有一个位于包根目录的 `SKILL.md` 作为 Agent 直接读取的核心指令文件。核心指令文件不宜过长。按需执行的补充指令、参考文档等可放在 Skill 包中的 `references` 目录中（需要在 `SKILL.md` 中声明其用途及用法）；Python 脚本放在 Skill 包中的 `scripts` 目录中；其它资产文件可放在 Skill 包中的 `assets` 目录中。
- **避免在 `SKILL.md` 中添加对 Skill 执行没有帮助的信息**: `SKILL.md` 中应仅包含对 Skill 执行具有约束作用或帮助作用的指令。一切面向用户的提示、说明，以及错误的、自相矛盾的、模棱两可的指令均不应该出现在 `SKILL.md`中

## 参考资料

开发决策见[已完成的决策地图](.scratch/skill-to-graph/map.md)。执行转换时以发布包 `skill-to-graph/SKILL.md` 为完整入口；仓库测试、样本和验收环境位于 `tests/`，不随发布包分发。脚本测试命令与真实验收约定见 [tests/acceptance/README.md](tests/acceptance/README.md)。

`references/` 存放本项目开发所需的外部知识。全部基于 2026-10-22 的一手来源（官方文档站、官方仓库源码、官方 API 参考、PyPI 元数据）撰写，每份文档末尾列出对应来源 URL。版本基线：`langchain 1.4.7`、`langgraph 1.2.16`、`langchain-core 1.6.13`、`langgraph-cli 0.4.37`。

| 文件 | 内容 | 何时读 |
| --- | --- | --- |
| `references/skill-to-langgraph-mapping.md` | 固定、自主和混合流程的映射、输入输出契约、节点边界、状态与 reducer、工具/权限、产物及保真检查 | 编写 SKILL.md 的转换流程与检查清单时先读 |
| `references/langgraph-core.md` | LangGraph 1.x 核心 API：`StateGraph`、reducer、条件边、`Command`、`Send`、编译与运行、checkpointer、`interrupt()`、子图、错误处理、Function API、`langgraph.prebuilt` | 需要写图代码或查 API 准确签名时 |
| `references/langchain-agent-runtime.md` | LangChain 1.x agent 层：`create_agent`、中间件钩子、工具与注入、消息模型、`init_chat_model`、context/store、流式、结构化输出 | 产物用 agent 而非自建节点时 |
| `references/langchain-cli-and-deployment.md` | `langgraph` CLI、`langgraph.json` 全字段、Agent Server 运行期契约（thread/durability/recursion_limit/并发）、流式端点、托管平台边界 | 设计产物目录结构、部署形态或服务契约时 |
| `references/agent-skills-package-format.md` | Agent Skills 规范：frontmatter 字段与约束、目录结构、渐进式披露、`scripts/`/`assets/` 约定、各 harness 差异、校验规则 | 解析源 Skill 包或校验 frontmatter 合规性时 |

两条与本项目命名直接相关的事实：

- 现行 CLI 是 `langgraph`（发行包 `langgraph-cli`），不是 `langchain`。`langchain new/build/dev/prompt` 均不存在，`langchain-cli` 已被官方从主仓库删除。产物要按 `langgraph.json` + `langgraph dev` 设计。
- `langgraph.prebuilt.create_react_agent` 已废弃，导入即触发 `LangGraphDeprecatedSinceV10`；新代码用 `langchain.agents.create_agent`。

文档定位：当前这几份是**开发期**知识，留在仓库根的 `references/`。其中要随 Skill 包分发的（至少 `skill-to-langgraph-mapping.md`），需另存到 Skill 包根目录的 `references/`，并在 `SKILL.md` 中声明各自用途与读取时机。
