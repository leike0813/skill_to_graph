# Skill 包 → LangGraph 图：映射规则参考

**本文件的用途**：执行「把一个 Agent Skill 包转换成可运行的 LangGraph 图」时，用来决定图的结构、状态通道、工具集和运行形态。

**本文件依赖的事实来源**（同目录，均为一手来源整理）：

| 文件 | 覆盖内容 |
| --- | --- |
| `langgraph-core.md` | `StateGraph`、reducer、条件边、`Command`、`Send`、checkpointer、`interrupt()`、子图、错误处理 |
| `langchain-agent-runtime.md` | `create_agent`、中间件、工具、消息模型、`init_chat_model`、context / store / 流式 |
| `langchain-cli-and-deployment.md` | `langgraph` CLI、`langgraph.json` 全字段、Agent Server 运行期契约、部署边界 |
| `agent-skills-package-format.md` | Agent Skills 规范：`SKILL.md` frontmatter 字段、目录结构、渐进式披露、脚本约定 |

---

## 0. 总则

1. **保真优先于优化**：源 Skill 的行为模式与输入输出契约不得被转换过程改写。转换做的是「把 harness 隐式行为显式化为图结构」，不是「重新设计 Skill」。
2. **能确定性解析的不交给模型**：frontmatter 字段、目录树、`references/` 引用路径、脚本清单属于确定性工作，应由 `scripts/` 下的解析脚本完成；只有「这段文字是第几步」「这一步需要哪些工具」这类语义判断才交给模型。
3. **两条基础产线与混合组合**：

| 源 Skill 的形态 | 产线 | 依据 |
| --- | --- | --- |
| 步骤固定、条件明确（「先 A，若 B 则 C」），控制流需要精确复现 | 自建 `StateGraph` 节点 | `langgraph-core.md` §1–§4 |
| 流程由模型依据 SKILL.md 自行决定，工具由模型挑选 | `langchain.agents.create_agent` | `langchain-agent-runtime.md` §1 |
| 固定阶段与自主决策并存 | 外层 `StateGraph` 落实固定阶段，自主区段组合 `create_agent` | `langgraph-core.md` §1–§4、§12；`langchain-agent-runtime.md` §1 |

   判据：逐个控制区段判断**把流程写成代码还是保留给模型**。固定顺序、明确条件或循环限制需要显式落实时用 `StateGraph`；源 Skill 只规定目标并允许模型自主选工具时，优先用 `create_agent`；两者并存时按局部语义组合，不为纯自主流程增加没有职责的外层图。
4. **同一套构图逻辑支持两种调用方式**：`graph.invoke(...)`（纯 Python）与 `langgraph dev`（CLI 服务）。按实际配置选择 compiled graph 或工厂函数中的一个入口，不要求同时导出两者；二者的差异表见 `langchain-cli-and-deployment.md` §9。

---

## 1. 输入输出契约映射

源 Skill 通常没有显式的 I/O schema，它声明的是「agent 收到一个任务 → 产出若干文件或一段回复」。转换时必须把这个隐式契约**显式化**，且不得收窄或改义。

### 1.1 契约由源 Skill 决定

源 Skill 的输入输出契约是唯一依据。下面的 `messages` / `artifacts` 仅是消息型调用和文件产物可以使用的示例，不是所有转换产物的默认契约。

```python
# 示例输入：源 Skill 本来就接受消息输入
{"messages": [{"role": "user", "content": "..."}]}

# 示例输出：源 Skill 确实要求文件产物清单
{"messages": [...], "artifacts": [{"path": "...", "kind": "file|inline"}]}
```

- 先按源 Skill 规定确定调用方输入、业务结果、文件和副作用。框架字段可以承载内部过程；若源契约不使用消息或产物清单，不要把它们暴露成新的业务字段。
- 用 `create_agent` 时，工厂自身的输入输出使用消息型 `InputAgentState` / `OutputAgentState`，见 `langchain-agent-runtime.md` §8.3。需要贴合不同源契约时，在入口或结果节点做明确映射；`state_schema=` 只用于源流程确有扩展通道需求的情况，不固定添加 `artifacts` 或 `structured_response`。
- 自建图确有内外部 schema 差异时，可用 `StateGraph(State, input_schema=InputState, output_schema=OutputState)` 区分内部状态与对外契约（见 `langgraph-core.md` §1）。源契约不需要拆分时，不额外制造一层 schema。

### 1.2 契约保真规则

- 源 Skill 的「产物」若主要是文件，转换后的图**不能**把文件内容塞进 state 字符串；应保留路径，读取由工具节点完成。
- 源 Skill 若规定了输出格式（如「输出一段 JSON」），用 `response_format` + `ToolStrategy` / `ProviderStrategy` 落地（`langchain-agent-runtime.md` §8.1），不要靠提示词约定。
- 图的 `name` 与 `langgraph.json` 的 graph ID 在目标规则允许时沿用源 Skill frontmatter 的 `name`，便于部署后用 `assistant_id` 选择图（`langchain-cli-and-deployment.md` §3）。它不是 Python 模块名或变量名。

---

## 2. SKILL.md 各部分 → 图的构件

| 源 Skill 构件 | 规范位置 | 转换结果 |
| --- | --- | --- |
| frontmatter `name` | 必填，≤64 字符，须等于父目录名 | 保留为图名；目标允许时用作 graph ID / `langgraph.json` 的 key。Python 模块名和导出变量名必须是合法技术标识，不能机械复用含连字符等字符的源名；需要转换时记录对应关系 |
| frontmatter `description` | 必填，≤1024 字符 | 图的用途描述；`create_agent` 的 `system_prompt` 开头段落；也用于路由到本图 |
| frontmatter `license` / `compatibility` / `metadata` | 选填 | 随图一起保留的元数据；`compatibility`（≤500 字符）→ 运行前置条件说明 |
| frontmatter `allowed-tools` | 选填，实验性 | 保留其预授权语义，不因字段名直接把工具池裁成白名单。工具可用性、调用预授权与禁止规则分别处理；只有源包或目标平台的明确语义支持排除时才限制工具 |
| SKILL.md 正文 | 指令正文 | 转换时提取职责：固定控制进入图，语义判断生成局部运行指令，跨职责规则在适用接收点明确传递；完整自主区段可保留其必要完整指令 |
| `references/` | 渐进式披露，按需加载 | **不得**全文注入 prompt；保留在 `source/<原包目录名>/references/`，改为工具（`read_reference(path)`）或独立节点按需读取（`agent-skills-package-format.md` §5） |
| `scripts/` | 确定性脚本 | 保留在 `source/<原包目录名>/scripts/`；源流程需要时提供真实运行路径并声明运行依赖（见本文件 §8）。转换 Skill 自身的脚本不与源脚本混放 |
| `assets/` | 模板、样例等只读资源 | 保留在 `source/<原包目录名>/assets/`，脚本与节点按源包内相对路径访问 |

`SKILL.md`、`references/`、`scripts/`、`assets/` 是常见构件，不是源包目录的完整清单；源包还可能有任意目录，产物仍须完整保留原结构。

**渐进式披露的保真要点**：源 Skill 里「需要时再读 `references/foo.md`」这句语义，转换后必须仍然成立 —— 图里要有「读取某个 reference」这个动作，而不是把 reference 内容提前塞进 state。

---

## 3. 流程语句 → 节点与边

分析 SKILL.md 正文时，先识别源规定的控制语义，再选择下图中的机制。表是映射选项，不表示每个编号、段落或列表项都要变成节点；节点边界由独立控制阶段、数据边界和恢复边界决定。

| SKILL.md 里的写法 | 图里的构造 | API |
| --- | --- | --- |
| 「1. … 2. … 3. …」顺序步骤 | 仅当源要求这些阶段按序发生时，才按独立阶段建节点与 `add_edge` 链；编号本身不能决定节点数量或边界 | `add_node` / `add_edge` / `START` / `END` |
| 「如果 … 则 …，否则 …」 | `add_conditional_edges`，返回目标节点名 | `langgraph-core.md` §2 |
| 「重复直到 … 满足」 | 回边（自环）并保留源停止条件；`recursion_limit` 只是运行上限，不是业务停止条件 | `recursion_limit` 是 config 顶层 key（v1.0.6 起默认 1000），超限抛 `GraphRecursionError`，此时报告执行受限而非业务完成（`langgraph-core.md` §5、§9） |
| 「对列表中每一项分别处理」 | 默认用显式顺序循环并保留逐项对应关系；仅当源允许并行且顺序、副作用不受影响时，才用 `[Send(node, item)]` 与 reducer 聚合 | `langgraph-core.md` §4 |
| 「本步更新状态并决定下一步」 | 节点返回 `Command(update=..., goto=...)` | `langgraph-core.md` §3 |
| 「等待用户确认/补充信息」 | 节点内 `interrupt()`，编译时挂 checkpointer | `langgraph-core.md` §7 |
| 「让模型自己决定下一步」 | `create_agent` 的 model→tools 循环 | `langchain-agent-runtime.md` §1 |
| 「失败则停止并报告」 | 保留源的停止、报告或降级行为；`RetryPolicy` 只在源要求重试或重试与其失败策略兼容时使用，不能替代停止 | `langgraph-core.md` §9 |

**切分粒度**：一个节点承载一个相对独立的控制阶段或恢复边界，不按句子、编号或“是否能重试”机械切分。连续而且没有独立控制语义的工作可以合并在一个节点；出现不同输入输出、分支、人工等待或需要隔离的副作用时再拆。

**路由机制不混用**：同一个节点只用一种路由机制 —— 要么静态边，要么条件边 / `Command`，不要两者并存。

**子图只在接口清晰时拆**：源 Skill 存在「子流程 + 明确的输入输出接口」时才拆子图；父子共享 state key 就把编译后的子图直接作为节点嵌入，schema 不同则在节点函数里 `invoke` 并转换。

---

## 4. 状态与 reducer

- 通道集合保持最小，并按源流程的数据传递与恢复需求设计。不要预设所有图都有 `messages`、`artifacts` 或同一组状态字段；消息型 agent 可以使用 `add_messages`，文件产物仍应落到实际文件，state 只在源契约允许或流程确有需要时保存引用、路径或中间值。
- **不要**把 SKILL.md 正文放进 state：正文要么进 `system_prompt`，要么作为固定字符串常量。
- 节点只返回要更新的键，不返回整个 state。
- 并行分支写同一个列表键时必须配 reducer，否则报 `InvalidUpdateError`（`langgraph-core.md` §1、§9）。
- 私有中间状态放子图：父图与子图 schema 不同时，在节点函数里手动转换（`langgraph-core.md` §8）。

---

## 5. 工具映射

源 Skill 依赖的能力（读文件、写文件、搜索、执行脚本、调用外部服务）必须落成显式工具，否则模型无从调用。

源所需外部工具或服务在当前环境不可用时，仍须生成真实调用路径并声明依赖；缺失环境不阻止产物生成，但不能把未执行的能力写成已验证，也不要用空工具或替身冒充真实调用。

```python
from langchain.tools import tool
from langchain.tools import ToolRuntime   # 实际是 langgraph.prebuilt 的再导出

@tool
def read_reference(path: str, runtime: ToolRuntime) -> str:
    """读取 skill 包内 references/ 下的文档。仅接受包内相对路径。"""
    ...
```

规则：

- 每个工具有稳定 `name` 与**自解释**的 `description`（模型靠它选工具）。工具描述从 SKILL.md 正文抽取，不要另起一套命名。
- 工具参数用类型注解生成 schema；需要读写图状态时用 `ToolRuntime` 注入，不要把状态当普通参数暴露给模型。
- 工具要写状态时返回 `Command(update=...)`，不要用可变副作用。
- 工具失败：默认把异常文本回给模型由模型自行纠正（`langchain-agent-runtime.md` §3.5）；确需硬失败时用 `wrap_tool_call` 中间件显式处理。
- `allowed-tools` 的预授权语义不等于“剩余工具一律禁止”。分别核对工具存在、预授权和禁止规则；只有源包或目标平台的明确语义要求排除工具时才限制工具池。

---

## 6. 中间件映射

harness 侧的隐式 hook 在图里必须变成显式 middleware，否则行为不可复现。

| harness 行为 | middleware 钩子 |
| --- | --- |
| 每轮模型调用前注入/裁剪上下文 | `@before_model` 或 `@wrap_model_call` |
| 每轮模型调用后处理输出 | `@after_model` |
| 工具错误兜底 | `@wrap_tool_call` |
| 达到步数/成本上限就停止 | `@before_model` + `can_jump_to=["end"]` |
| 动态系统提示词 | `@dynamic_prompt` / `@wrap_model_call` |

钩子顺序：before 钩子按声明顺序执行，wrap 钩子嵌套，after 钩子逆序（`langchain-agent-runtime.md` §2.4）。顺序影响行为，声明顺序不可随意调整。

表中的步数与成本上限是**运行限制**。源 Skill 自己规定的停止条件由图按源实现；运行上限触发时报告执行受限，不能当作业务完成条件，也不能反向写成源的停止规则。

---

## 7. 人工介入与持久化

- 源 Skill 里「需要用户确认」的环节 → `interrupt()`，编译时必须挂 checkpointer（`langgraph-core.md` §7）。
- 使用 checkpointer 就必须传 `thread_id`：`{"configurable": {"thread_id": "..."}}`；`recursion_limit` 在 config 顶层，不在 `configurable` 里（`langchain-cli-and-deployment.md` §6）。
- 恢复时用 `Command(resume=value)`，`value` 即 `interrupt()` 的返回值。
- checkpointer 保存图状态和恢复位置，不提供外部副作用的 exactly-once 保证。恢复会从节点开头重跑，外部调用也可能重复；应隔离副作用或使用幂等操作，无法保证时明确记录限制，不能仅凭存在 checkpoint 声称不会重复执行。
- 服务端部署时 thread 是持久化会话容器，同一 thread 同时只跑一个 run（`langchain-cli-and-deployment.md` §6）。

---

## 8. 产物形态

转换产物是一个可独立分发的目录。完整源包原样放在 `source/<原包目录名>/`，新增图代码统一放在合法的 `skill_graph` Python 包中：

```plaintext
<skill-name>-graph/
├── source/
│   └── <原包目录名>/         # 完整源包，原样保留任意目录与文件
│       ├── SKILL.md
│       ├── references/
│       ├── scripts/
│       ├── assets/
│       └── ...
├── skill_graph/             # 新增图代码，使用固定、合法的 Python 包名
│   ├── __init__.py
│   ├── graph.py             # 选定入口；其余模块按实际需要增加
│   └── ...
├── langgraph.json           # 指向 skill_graph 中的实际入口
├── pyproject.toml           # 依赖声明
└── README.md                # 调用映射、配置、依赖与验证边界
```

源包名可以含连字符等不能直接用于 Python 标识符的字符；保留源名和目录，自行记录 Python 名称映射。源包内的脚本留在 `source/<原包目录名>/scripts/`；新图代码及其运行辅助脚本放在 `skill_graph/`。转换 Skill 自身的脚本不复制到生成应用根目录，除非生成图运行确实需要。

`.env` 仅在确有配置需求时创建，不放空模板。

`langgraph.json` 最小形态（字段语义见 `langchain-cli-and-deployment.md` §3）：

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "python_version": "3.11",
  "dependencies": ["."],
  "graphs": {
    "<graph-id>": "./skill_graph/graph.py:<entry>"
  }
}
```

`<graph-id>` 在目标允许时沿用源名；`<entry>` 是实际选择的 compiled graph 或工厂函数之一，不要求双导出。图节点的相对路径读取（`read_reference`）以携带后的 `source/<原包目录名>/` 为基准，删除或拆散源包会破坏渐进式披露和资源引用语义。

---

## 9. 保真检查清单

静态检查、加载成功和有限运行支持不同范围的结论。先按源契约核对可观察行为，再用拓扑辅助理解结构：

1. 源规定的阶段顺序、循环停止条件、失败行为、人工确认和权限约束都有真实落点；agent 内部节点不必与源文本逐句或逐编号一一对应。
2. 每个条件分支在图里有对应边，且条件判定依据与源文本一致。
3. 源 Skill 引用的每个 `references/` 文件在图中都**可达**（有读取它的动作）。
4. 源 Skill 引用的每个 `scripts/` 脚本仍在完整源包中，所需运行依赖已声明。
5. 输入 schema 和结果路径能表达源 Skill 接受的全部输入形态及产物，不额外固定 `messages` / `artifacts`。
6. 中断点（若源 Skill 有）与源 Skill 的「等待用户」位置一致。
7. `graph.get_graph().draw_mermaid()` 只用于检查已声明拓扑，不能证明保真；是否保真仍按源契约和运行证据判断。
8. `graph.invoke(...)` 与 `langgraph dev` 两条调用路径都能加载并调用选定的同一入口，不要求提供两套导出。
9. 外部工具、服务或凭据缺失时，图仍保留真实调用与依赖声明；环境受阻、未运行和证据不足分别记录，均不计作保真通过。

---

## 10. 反模式

| 反模式 | 为什么错 |
| --- | --- |
| 把 SKILL.md 正文整段塞进节点 prompt，并在每一步重复 | 破坏渐进式披露，token 成本随步骤线性膨胀 |
| 把每句话拆成一个节点 | 图结构失去可读性，`recursion_limit` 与调试成本上升 |
| 把 `messages` / `artifacts` 当成所有 Skill 的统一业务契约 | 给源 Skill 增加不需要的输入输出字段，收窄其他输入形态 |
| 把 `allowed-tools` 一律解释成工具白名单 | 混淆预授权与禁止，可能错误删除源流程可用能力 |
| 用 `RetryPolicy` 替代源要求的失败停止 | 自动重试改变失败语义，可能重复副作用 |
| 认为存在 checkpoint 就实现了 exactly-once | 恢复会重跑当前节点，外部副作用仍可能重复 |
| 要求生成拓扑与源步骤机械一致，或以拓扑检查代替行为验证 | agent 内部结构与源文本不需要一一对应，拓扑不能证明输入输出和副作用保真 |
| 用字符串匹配源文本做路由门禁 | 脆弱；条件应从语义判断产出并存进 state |
| 用 `create_react_agent`（已废弃） | 导入即触发 `LangGraphDeprecatedSinceV10`；新代码用 `langchain.agents.create_agent` |
| 把工具当成模型的自由能力，不落成显式 tool | 图无法复现 harness 的工具边界 |
| 产物里删掉 `references/`、`scripts/` 以「保持干净」 | 直接破坏源 Skill 的行为契约 |
