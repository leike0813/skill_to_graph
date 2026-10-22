# LangChain 1.x Agent 运行时层参考（Python）

> **版本声明**：本文档描述 **LangChain 1.x（Python）** 的 Agent 运行时层。编写时 PyPI 最新版为 **`langchain==1.4.7`**（2026-10 发布），依赖 `langchain-core>=1.6.13`、`langgraph>=1.2.12`、`pydantic>=2.7.4`、Python `>=3.10`。
> 版本与依赖来源：https://pypi.org/pypi/langchain/json
> API 签名一手来源：https://reference.langchain.com/python/langchain/agents/factory/create_agent
> 行为描述一手来源：https://docs.langchain.com/oss/python/langchain/agents

---

## 0. 分层职责边界：LangChain 层 vs LangGraph 层

本项目（Skill → LangGraph 图转换）的设计前提，必须先钉死这条边界。

**LangChain 1.x 层（`langchain.*`）负责「Agent harness」**：

- `create_agent`：把「模型 + 工具 + 中间件」装配成一个 ReAct 循环。
- 中间件系统（middleware）：在 agent 生命周期的 6 个钩子上改状态 / 改请求 / 改响应 / 短路。
- 工具定义（`@tool` / `BaseTool`）、工具 schema 生成、工具错误处理中间件。
- 消息模型与标准 content blocks、`init_chat_model`、agent 级结构化输出策略。
- 运行时上下文（`context`）接入点、长期记忆接入点（`store`）。

**LangGraph 层（`langgraph.*`）负责「图运行时」**：

- `StateGraph` / `CompiledStateGraph`：节点、边、条件边、reducer、`Send` 并行扇出。
- `Checkpointer`（短期记忆的持久化后端）、`BaseStore`（长期记忆后端接口）。
- `Runtime`（`context` / `store` / `stream_writer` / `execution_info` 的容器）。
- `ToolNode`（工具执行节点本体）、`tools_condition`（路由函数）、`Command`（状态更新 + 跳转）。
- Pregel 执行引擎与全部流式模式（`values` / `updates` / `messages` / `custom` / `checkpoints` / `tasks` / `debug`）。
- `interrupt()` / `Command(resume=...)` 中断恢复协议。

**关键事实（决定了本项目该怎么生成产物）**：

1. `create_agent` **返回的就是一个 `CompiledStateGraph`**，不是自定义运行时。官方原文："LangChain [agents](https://docs.langchain.com/oss/python/langchain/agents) are built on top of LangGraph in order to provide durable execution, streaming, human-in-the-loop, persistence, and more."（https://pypi.org/pypi/langchain/json ）
2. 中间件**不是独立运行时**："Middleware is not a separate runtime: hooks run inside the compiled [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) that [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent) returns. You can drop the whole agent (middleware and all) into a larger [StateGraph](https://docs.langchain.com/oss/python/langgraph/graph-api) as a node or subgraph, and every middleware hook continues to run."（https://docs.langchain.com/oss/python/langchain/middleware/overview ；原文中该 StateGraph 链接指向 `.../langgraph/graph/state/StateGraph`，2026-10 已 404，此处替换为等价的 `graph-api` 页面）
3. 编译后的节点名固定为：`"model"`、`"tools"`，以及每个中间件的 `f"{m.name}.before_agent"` / `f"{m.name}.before_model"` / `f"{m.name}.after_model"` / `f"{m.name}.after_agent"`（源码 `libs/langchain_v1/langchain/agents/factory.py`）。
4. `create_agent` 编译时设置 `recursion_limit: 9_999`，并写入 `metadata["ls_integration"] = "langchain_create_agent"`。

**给本项目的判据**：

| 源 Skill 的特征 | 该用哪一层 |
|---|---|
| 「读文件 → 调用某 CLI → 写文件」这种线性/分支流程，需要精确控制每一步 | `langgraph.graph.StateGraph` 自建节点 |
| 「让模型自己决定调用哪些工具、循环到任务完成」 | `langchain.agents.create_agent` |
| 需要在 agent 循环前后插入确定性的前后处理 | 中间件（`before_agent` / `after_agent`）或外层 StateGraph 节点 |
| 需要可恢复 / 可中断 / 人工审批 | LangGraph `Checkpointer` + `interrupt()`（HITL 用 `HumanInTheLoopMiddleware`，它内部要求 checkpointer） |
| 需要跨会话长期记忆 | `langgraph.store` 的 `BaseStore` 实现 |
| 需要把模型输出解析成固定 schema | `response_format=` + `ToolStrategy` / `ProviderStrategy`（不要自己解析文本） |

---

## 1. `create_agent`：完整签名与行为

```python
create_agent(
    model: str | BaseChatModel,
    tools: Sequence[BaseTool | Callable[..., Any] | dict[str, Any]] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware[StateT_co, ContextT]] = (),
    response_format: ResponseFormat[ResponseT] | type[ResponseT] | dict[str, Any] | None = None,
    state_schema: type[AgentState[ResponseT]] | None = None,
    context_schema: type[ContextT] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    interrupt_before: list[str] | None = None,
    interrupt_after: list[str] | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache[Any] | None = None,
    transformers: Sequence[TransformerFactory] | None = None,
) -> CompiledStateGraph[AgentState[ResponseT], ContextT, InputAgentState, OutputAgentState[ResponseT]]
```
（逐字抄自 https://reference.langchain.com/python/langchain/agents/factory/create_agent ）

### 行为（官方原文）

> The agent node calls the language model with the messages list (after applying the system prompt). If the resulting [`AIMessage`][langchain.messages.AIMessage] contains `tool_calls`, the graph will then call the tools. The tools node executes the tools and adds the responses to the messages list as [`ToolMessage`][langchain.messages.ToolMessage] objects. The agent node then calls the language model again. The process repeats until no more `tool_calls` are present in the response. The agent then returns the full list of messages.

**最小用法**：

```python
from langchain.agents import create_agent

def check_weather(location: str) -> str:
    '''Return the weather forecast for the specified location.'''
    return f"It's always sunny in {location}"

graph = create_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    tools=[check_weather],
    system_prompt="You are a helpful assistant",
)
inputs = {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
for chunk in graph.stream(inputs, stream_mode="updates"):
    print(chunk)
```

### 约束与坑

- **`tools` 为空**时，agent 退化为「只有 model 节点，无工具循环」。
- **不接受预绑定模型**（`model.bind_tools(...)` 的结果）：官方迁移指南明确 "To better support structured output, `create_agent` no longer accepts pre-bound models with tools or configuration"。工具必须通过 `tools=` 传入。
- **`state_schema` 只支持 `TypedDict`**：Pydantic model / dataclass 已不支持（https://docs.langchain.com/oss/python/migrate/langchain-v1 ）。
- **`response_format` 传裸 JSON Schema dict 不会被自动识别**，必须显式包成 `ProviderStrategy(...)` / `ToolStrategy(...)`（https://docs.langchain.com/oss/python/langchain/structured-output ）。
- **`tools` 不接受 `ToolNode` 实例**（v0 的 `create_react_agent` 接受）。
- `system_prompt` 传 `str` 会被转成 `SystemMessage`；`ModelRequest.system_message` 永远是 `SystemMessage` 对象。
- `transformers` 顺序：最终图上的顺序是 `ToolCallTransformer` → 中间件声明的 transformer（按中间件顺序）→ 调用方传入的 `transformers`（源码 `factory.py` 的 `_dedupe_transformers`）。
- 流式事件里的节点名从 v0 的 `"agent"` 改名为 `"model"`（迁移指南「Streaming node name」条）。

### 与 `langgraph.prebuilt.create_react_agent` 的关系

**`create_react_agent` 仍然存在，但已废弃**。源码（`libs/prebuilt/langgraph/prebuilt/chat_agent_executor.py`）：

```python
@deprecated(
    "create_react_agent has been moved to `langchain.agents`. Please update your import to `from langchain.agents import create_agent`.",
    category=LangGraphDeprecatedSinceV10,
)
def create_react_agent(...)
```

同文件里 `langgraph.prebuilt.AgentState` / `AgentStatePydantic` / `AgentStateWithStructuredResponse` 也都带 `@deprecated(..., category=LangGraphDeprecatedSinceV10)`，提示改用 `langchain.agents.AgentState`。

**结论**：

- **推荐入口 = `langchain.agents.create_agent`**。官方迁移指南原文："Prior to v1.0, we recommended using `langgraph.prebuilt.create_react_agent` to build agents. Now, we recommend you use `langchain.agents.create_agent` to build agents."
- `langgraph.prebuilt.create_react_agent` = **已废弃的旧入口**，导入即触发 `LangGraphDeprecatedSinceV10` 警告。仍然可用但不应用于新代码。
- `langgraph.prebuilt` 中**仍然有用**的东西（未废弃）：`ToolNode`、`tools_condition`、`InjectedState`、`InjectedStore`、`ToolRuntime`、`ToolCallTransformer`、`ValidationNode`。
- 注意：`langchain.tools` 里的 `InjectedState` / `InjectedStore` / `ToolRuntime` 只是 `langgraph.prebuilt` 的再导出（源码 `libs/langchain_v1/langchain/tools/tool_node.py`：`from langgraph.prebuilt import InjectedState, InjectedStore, ToolRuntime`）。

### 关键迁移差异（v0 → v1）

| v0（`create_react_agent`） | v1（`create_agent`） |
|---|---|
| `prompt=` | `system_prompt=` |
| `pre_model_hook=` | 中间件 `before_model` |
| `post_model_hook=` | 中间件 `after_model` |
| `state_modifier=` | 中间件 `@dynamic_prompt` / `wrap_model_call` |
| `response_format=(prompt, Schema)` | 已移除，改用 `ToolStrategy` / `ProviderStrategy` |
| `tools=ToolNode([...])` | `tools=[...]` |
| `ToolNode(handle_tool_errors=...)` | 中间件 `wrap_tool_call` / `ToolErrorMiddleware` |
| 节点名 `"agent"` | 节点名 `"model"` |
| `config["configurable"]` 注入 | `context=` 参数 + `context_schema=` |
| 动态模型 callable | 中间件 `wrap_model_call` + `request.override(model=...)` |

（来源：https://docs.langchain.com/oss/python/migrate/langchain-v1 ）

---

## 2. 中间件系统（middleware）

### 2.1 两类钩子

| 钩子 | 类型 | 运行时机 |
|---|---|---|
| `before_agent` | node-style | agent 开始前（每次 invoke 一次） |
| `before_model` | node-style | 每次模型调用前 |
| `after_model` | node-style | 每次模型响应后 |
| `after_agent` | node-style | agent 完成后（每次 invoke 一次） |
| `wrap_model_call` | wrap-style | 包裹每次模型调用 |
| `wrap_tool_call` | wrap-style | 包裹每次工具调用 |

来源：https://docs.langchain.com/oss/python/langchain/middleware/custom

### 2.2 装饰器签名（逐字）

```python
before_model(
    func: _CallableWithStateAndRuntime[StateT, ContextT] | None = None,
    *,
    state_schema: type[StateT] | None = None,
    tools: list[BaseTool] | None = None,
    can_jump_to: list[JumpTo] | None = None,
    name: str | None = None,
) -> Callable[[_CallableWithStateAndRuntime[StateT, ContextT]], AgentMiddleware[StateT, ContextT]] | AgentMiddleware[StateT, ContextT]
```

`after_model` / `before_agent` / `after_agent` **签名完全相同**（仅语义不同）；`after_agent` 的异步版本叫 `aafter_agent`。

```python
wrap_model_call(
    func: _CallableReturningModelResponse[ContextT, ResponseT] | None = None,
    *,
    state_schema: type[StateT] | None = None,
    tools: list[BaseTool] | None = None,
    name: str | None = None,
) -> Callable[[_CallableReturningModelResponse[ContextT, ResponseT]], AgentMiddleware[StateT, ContextT]] | AgentMiddleware[StateT, ContextT]
```

```python
wrap_tool_call(
    func: _CallableReturningToolResponse | None = None,
    *,
    state_schema: type[StateT] | None = None,
    tools: list[BaseTool] | None = None,
    name: str | None = None,
) -> Callable[[_CallableReturningToolResponse], AgentMiddleware[StateT, ContextT]] | AgentMiddleware[StateT, ContextT]
```

```python
dynamic_prompt(
    func: _CallableReturningSystemMessage[ContextT] | None = None,
) -> Callable[[_CallableReturningSystemMessage[ContextT]], AgentMiddleware[StateT, ContextT]] | AgentMiddleware[StateT, ContextT]
```

来源（逐字）：https://reference.langchain.com/python/langchain/agents/middleware/types/before_model 、 .../after_model 、 .../before_agent 、 .../after_agent 、 .../wrap_model_call 、 .../wrap_tool_call 、 .../dynamic_prompt

### 2.3 类式中间件：`AgentMiddleware`

`AgentMiddleware` 可覆写的方法（每个都有对应的 `a*` 异步版）：

```
before_agent / abefore_agent
before_model / abefore_model
after_model  / aafter_model
wrap_model_call / awrap_model_call
after_agent / aafter_agent
wrap_tool_call / awrap_tool_call
```

类属性（编译期被 agent factory 读取）：

- `state_schema` —— 扩展 agent state。
- `tools` —— 随中间件一起注册的工具（如 `TodoListMiddleware` 的 `write_todos`）。
- `transformers` —— scope-aware 流式 transformer 工厂元组（需 `langchain>=1.3.2`）。
- `trace_policy` —— 追踪输入输出的裁剪策略（需 `langchain>=1.3.15`）。

来源：https://reference.langchain.com/python/langchain/agents/middleware/types/AgentMiddleware ；https://docs.langchain.com/oss/python/langchain/middleware/custom

### 2.4 执行顺序（官方明文）

> **Before hooks run in order:** 1. `middleware1.before_agent()` 2. `middleware2.before_agent()` 3. `middleware3.before_agent()`
> **Agent loop starts** 4. `middleware1.before_model()` 5. `middleware2.before_model()` 6. `middleware3.before_model()`
> **Wrap hooks nest like function calls:** 7. `middleware1.wrap_model_call()` → `middleware2.wrap_model_call()` → `middleware3.wrap_model_call()` → model
> **After hooks run in reverse order:** 8. `middleware3.after_model()` 9. `middleware2.after_model()` 10. `middleware1.after_model()`
> **Agent loop ends** 11. `middleware3.after_agent()` 12. `middleware2.after_agent()` 13. `middleware1.after_agent()`
>
> **Key rules:** `before_*` hooks: First to last；`after_*` hooks: Last to first (reverse)；`wrap_*` hooks: Nested (first middleware wraps all others)

源码印证（`factory.py`）：`before_agent` 链是 `middleware[0].before_agent → middleware[1].before_agent → ...`；`after_model` 链是 `middleware[-1].after_model → ... → middleware[0].after_model`；`after_agent` 链是 `middleware[-1].after_agent → ... → middleware[0].after_agent → END`。

### 2.5 自定义钩子能做什么

**node-style 钩子（`before_agent`/`before_model`/`after_model`/`after_agent`）**：

- 返回 `dict[str, Any]` → 合并进 agent state（走 reducer）。
- 返回 `Command` → 控制流（跳转）。
- 返回 `None` → 无更新。
- 返回 `{"jump_to": ...}` 可提前退出。合法目标只有三个：`'end'`、`'tools'`、`'model'`。
  - `'end'`：结束 agent 循环（源码映射到 `exit_node`：若有 `after_agent` 中间件则进入其链，否则直接 `END`）。
  - `'tools'`：跳到 tools 节点。
  - `'model'`：跳到 model 节点（源码映射到 `loop_entry_node`：第一个 `before_model` 节点，若无则 `"model"`）。
- 跳转能力必须声明：`@before_model(can_jump_to=["end"])`，或类式 `@hook_config(can_jump_to=["end"])`。

**wrap-style 钩子（`wrap_model_call` / `wrap_tool_call`）**：

- 你决定 `handler` 被调用 0 次（短路）、1 次（正常）、或多次（重试）。
- `wrap_model_call` 可返回 `ModelResponse`、`AIMessage`（源码会归一为 `ModelResponse(result=[...], structured_response=None)`）或 `ExtendedModelResponse`；要同时注入 state 更新则返回 `ExtendedModelResponse(model_response=..., command=Command(update={...}))`。
- `wrap_tool_call` 返回 `ToolMessage` 或 `Command`。
- `Command.goto` / `Command.resume` / `Command.graph` 在 `wrap_model_call` 中**会抛 `NotImplementedError`**（源码 `factory.py::_build_commands`）。要跳转请用 node-style 钩子的 `jump_to`。
- 多层 wrap 的 `Command` 合成规则：消息走 reducer 是**累加**；非 reducer 字段**外层覆盖内层**；外层若重试了 `handler`，内层先前调用产生的 command 会被丢弃。

**`ModelRequest` 可改的字段**（`request.override(...)` 的合法键）：

```python
ModelRequest(
    self,
    *,
    model: BaseChatModel,
    messages: list[AnyMessage],
    system_message: SystemMessage | None = None,
    system_prompt: str | None = None,          # deprecated，转换为 SystemMessage
    tool_choice: Any | None = None,
    tools: list[BaseTool | dict[str, Any]] | None = None,
    response_format: ResponseFormat[Any] | None = None,
    state: AgentState[Any] | None = None,
    runtime: Runtime[ContextT] | None = None,
    model_settings: dict[str, Any] | None = None,
)
```
（https://reference.langchain.com/python/langchain/agents/middleware/types/ModelRequest ）

### 2.6 内置中间件清单（按 `langchain.agents.middleware.__all__` 实测）

来源（源码 `libs/langchain_v1/langchain/agents/middleware/__init__.py`）：

| 类 | 用途 |
|---|---|
| `ToolErrorMiddleware` | 把工具异常转成 `ToolMessage(status="error")`。需 `langchain>=1.3.14` |
| `ToolRetryMiddleware` | 工具调用指数退避重试 |
| `ModelRetryMiddleware` | 模型调用指数退避重试 |
| `ModelFallbackMiddleware` | 主模型失败时降级到备用模型 |
| `SummarizationMiddleware` | 接近 token 上限时压缩历史 |
| `HumanInTheLoopMiddleware` | 工具调用前人工审批（**必须配 checkpointer**） |
| `ModelCallLimitMiddleware` | 限制模型调用次数（thread/run） |
| `ToolCallLimitMiddleware` | 限制工具调用次数（全局或按工具名） |
| `PIIMiddleware` | PII 检测与 redact/mask/hash/block |
| `TodoListMiddleware` | 注入 `write_todos` 工具 + 计划提示词 |
| `LLMToolSelectorMiddleware` | 用小模型先筛工具 |
| `ProviderToolSearchMiddleware` | 把工具藏到 provider 的 server-side tool search 后面 |
| `ShellToolMiddleware` | 持久 shell 会话；配 `HostExecutionPolicy` / `DockerExecutionPolicy` / `CodexSandboxExecutionPolicy` |
| `FilesystemFileSearchMiddleware` | 提供 `glob_search` / `grep_search` |
| `ContextEditingMiddleware` + `ClearToolUsesEdit` | 到达 token 阈值时清掉旧的 tool 输出 |
| `LLMToolEmulator` | 用 LLM 模拟工具执行（测试用） |

**不在 `langchain` 包里**（官方 built-in 文档里列了，但 import 路径在 `deepagents`）：

- `FilesystemMiddleware` → `from deepagents.middleware.filesystem import FilesystemMiddleware`
- `SubAgentMiddleware` → `from deepagents.middleware.subagents import SubAgentMiddleware`
- `RubricMiddleware` → `from deepagents import RubricMiddleware`（beta，需 `deepagents>=0.6.5`）

**关于「patch toolcalls」**：**未能从一手来源证实** `langchain 1.x` 存在名为 "patch toolcalls" 的内置中间件。最接近的两项能力是：(a) `wrap_tool_call` 中用 `request.override(tool_call={**request.tool_call, "args": {...}})` 改写工具入参；(b) `ContextEditingMiddleware` / `ClearToolUsesEdit` 清理旧工具输出。

---

## 3. 工具定义

### 3.1 `@tool` 装饰器

```python
tool(
    name_or_callable: str | Callable[..., Any] | None = None,
    runnable: Runnable[Any, Any] | None = None,
    args: Any = (),
    *,
    description: str | None = None,
    return_direct: bool = False,
    args_schema: ArgsSchema | None = None,
    infer_schema: bool = True,
    response_format: Literal['content', 'content_and_artifact'] = 'content',
    parse_docstring: bool = False,
    error_on_invalid_docstring: bool = True,
    extras: dict[str, Any] | None = None,
) -> BaseTool | Callable[[Callable[..., Any] | Runnable[Any, Any]], BaseTool]
```
（https://reference.langchain.com/python/langchain-core/tools/convert/tool ）

```python
from langchain.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"
```

约束：

- **类型标注是必需的**，它定义工具的输入 schema。
- docstring 默认成为工具 description；`@tool("name")` 可改名字；`@tool("name", description="...")` 可改描述。
- 描述优先级：`description=` 参数 > 函数 docstring > `args_schema` 的 description。
- `args_schema` 可传 Pydantic model 或 JSON Schema dict。
- **保留参数名**：不能把工具参数命名为 `config` 或 `runtime`（前者会被注入的 `RunnableConfig` 遮蔽，调用时报 `TypeError: ... missing 1 required positional argument: 'config'`；后者被 `ToolRuntime` 占用）。langchain-core 层面还建议避开 `run_manager` / `callbacks`（这两个会被静默从 schema 中剔除）。
- 工具名**建议用 `snake_case`**：含空格或特殊字符的名称某些 provider 会报错。
- `extras={"defer_loading": True}` 标记工具可被 provider server-side tool search 延迟加载。

### 3.2 `BaseTool` 子类

```python
from langchain_core.tools import BaseTool
from pydantic import Field

class Multiply(BaseTool):
    """Multiply two numbers."""

    name: str = "multiply"
    description: str = "Multiply two integers."
    a: int = Field(description="first operand")
    b: int = Field(description="second operand")

    def _run(self, a: int, b: int) -> int:
        return a * b
```

`BaseTool` 的关键字段（源码 `libs/core/langchain_core/tools/base.py`）：

- `name: str`、`description: str` —— 必填。
- `args_schema: Annotated[ArgsSchema | None, SkipValidation()] = None` —— 必须是 `pydantic.BaseModel` 子类或 JSON Schema dict，否则 `TypeError`。写成 `args_schema: Type[BaseModel] = SchemaClass` 是错的，会抛 `SchemaAnnotationError`。
- `return_direct: bool = False`
- `handle_tool_error: bool | str | Callable[[ToolException], ToolExceptionHandlerOutput] | None = False`
- `handle_validation_error: bool | str | Callable[[ValidationError], str] | None = False`
- `response_format: Literal["content", "content_and_artifact"] = "content"`
- `extras: dict[str, Any] | None = None`

### 3.3 注入机制：`ToolRuntime`（推荐）/ `InjectedState` / `InjectedStore` / `InjectedToolCallId`

```python
@dataclass
class ToolRuntime(_DirectlyInjectedToolArg, Generic[ContextT, StateT]):
    state: StateT
    context: ContextT
    config: RunnableConfig
    stream_writer: StreamWriter
    tool_call_id: str | None
    store: BaseStore | None
    tools: list[BaseTool] = field(default_factory=list)
    execution_info: ExecutionInfo | None = None
    server_info: ServerInfo | None = None

    def emit_output_delta(self, delta: Any) -> None: ...
```
（源码 `libs/prebuilt/langgraph/prebuilt/tool_node.py`）

用法（**参数名必须是 `runtime`，不需要 `Annotated`**）：

```python
from langchain.tools import tool, ToolRuntime
from langchain.messages import HumanMessage

@tool
def get_last_user_message(runtime: ToolRuntime) -> str:
    """Get the most recent message from the user."""
    for message in reversed(runtime.state["messages"]):
        if isinstance(message, HumanMessage):
            return message.content
    return "No user messages found"
```

泛型参数顺序是 **`<ContextT, StateT]`**：

```python
from langchain.agents import AgentState
from langchain.tools import ToolRuntime

class CustomState(AgentState):
    user_name: str

@tool
def greet(runtime: ToolRuntime[None, CustomState]) -> str:
    """Use this to greet the user by name."""
    return f"Hello {runtime.state.get('user_name', 'Unknown')}!"
```
（只写 `ToolRuntime[UserContext]` 时 StateT 取默认 `dict`。）

**旧注入方式（仍可用，但官方建议迁移到 `ToolRuntime`）**：

- `InjectedState`（`langgraph.prebuilt`，`langchain.tools` 再导出）：`Annotated[dict, InjectedState]` 注入整个 state；`Annotated[str, InjectedState("foo")]` 只注入 `state["foo"]`。
- `InjectedStore`：注入 store 实例。
- `InjectedToolCallId`（`langchain_core.tools`）：`Annotated[str, InjectedToolCallId]` 注入当前 tool call id。

官方迁移说明原文："Older examples used `InjectedState`, `InjectedStore`, `get_runtime()`, or `InjectedToolCallId`. Use `ToolRuntime` instead for one explicit interface to state, context, store, and execution metadata."

**坑**：

- 注入参数**不出现在给模型看的 schema 里**；注入值由系统写入，LLM 伪造的同名字段会被剥离（源码 `_inject_tool_args`：`stripped_args` + `injected_args` 覆盖）。
- `runtime.state` 在 tools 节点执行时从 channel 读取（`CONFIG_KEY_READ`），不是把 state 内联进 `Send` 负载（源码注释：避免 O(N²) TASKS 写入）。
- **源码不一致提醒**：`langgraph/runtime.py` 里 `Runtime` 的 docstring 声称 "`ToolRuntime` ... is a subclass"，但源码里 `ToolRuntime` 是独立的 dataclass（继承 `_DirectlyInjectedToolArg`），**不是** `Runtime` 子类。两者共享 `context` / `store` / `stream_writer` 三个字段，但 `ToolRuntime` 另有 `config` / `state` / `tool_call_id` / `tools` / `execution_info` / `server_info`。
- `runtime.execution_info` / `runtime.server_info` 需 `langgraph>=1.1.5`。

### 3.4 工具返回值 → 消息的转换规则

`ToolNode._normalize_tool_response` + `msg_content_output`（源码）：

| 工具返回 | 转换结果 |
|---|---|
| `str` | `ToolMessage.content = str` |
| `list[dict]`，且每个 dict 的 `type` ∈ `TOOL_MESSAGE_BLOCK_TYPES` | `ToolMessage.content = list[dict]`（多模态） |
| 其它任意对象 | `json.dumps(output, ensure_ascii=False)`；JSON 序列化失败则退化为 `str(output)` |
| `ToolMessage` | 直接使用（content 仍会过一遍 `msg_content_output`） |
| `Command` | 走 state 更新路径，见下 |
| `list[Command | ToolMessage]` | 允许，但**必须恰好有一条**与本 tool call id 绑定的终止 `ToolMessage`，否则 `ValueError` |

`TOOL_MESSAGE_BLOCK_TYPES = ("text", "image_url", "image", "json", "search_result", "custom_tool_call_output", "document", "file")`（源码 `langchain_core/tools/base.py`）。

**`Command` 返回的硬约束**（源码 `_validate_tool_command`）：

- `Command.update` 必须是 dict（当 ToolNode 以 dict 输入调用时）或 list（以 list 输入调用时），否则 `ValueError`。
- 若 `Command.graph` 为 `None`（指向当前图），`Command.update["messages"]` 里**必须包含** `tool_call_id` 与本次调用匹配的 `ToolMessage`，否则 `ValueError`："Every tool call (LLM requesting to call a tool) in the message history MUST have a corresponding ToolMessage"。
- 想写父图用 `Command.PARENT`，此时该要求解除。
- `Command.update` 中的 `ToolMessage` 会被自动填上 `name=call["name"]`。

```python
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command

@tool
def set_language(language: str, runtime: ToolRuntime) -> Command:
    """Set the preferred response language."""
    return Command(update={
        "preferred_language": language,
        "messages": [ToolMessage(content=f"Language set to {language}.",
                                 tool_call_id=runtime.tool_call_id)],
    })
```

**`return_direct=True`**：

- 工具输出**不**再回灌模型，直接作为最终结果返回。
- **并行调用时，只有当这一批里所有被调用的工具都是 `return_direct=True` 时才短路退出**；混有普通工具时不会退出。
- 返回 `Command` 时**不会**自动转成 `ToolMessage`，仍需自己放 `ToolMessage`。

### 3.5 工具错误处理

**LangChain 层**：错误处理是**中间件**的事，不是 `ToolNode` 参数的事。

```python
from collections.abc import Callable
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest

@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )
```

`ToolErrorMiddleware(on_error=..., aon_error=..., tools=[...])`：`on_error(exc, request) -> str | list[ContentBlock] | None`，返回 `None` 则异常继续向上抛。要与重试组合，需把 `ToolRetryMiddleware` 放在**内层**（列表更靠后）且 `on_failure="error"`。

**LangGraph 层（`ToolNode`）**：`handle_tool_errors` 默认值 `_default_handle_tool_errors` —— 只捕获 **工具调用参数校验错误**（`ToolInvocationError`），其余执行异常**重新抛出**。校验错误信息里会过滤掉注入参数（state/store/runtime），只保留 LLM 可控字段的报错。

`ToolCallRequest` 结构：

```python
@dataclass
class ToolCallRequest:
    tool_call: ToolCall      # {"name", "args", "id", "type"}
    tool: BaseTool | None     # 未注册的工具为 None
    state: Any
    runtime: ToolRuntime

    def override(self, **overrides) -> ToolCallRequest: ...
```
（直接给 `request.tool_call` 赋值已 deprecated，会发 `DeprecationWarning`；必须用 `override()`。）

---

## 4. 消息模型

### 4.1 四种消息

`langchain.messages` 全部从 `langchain_core.messages` 再导出。

| 类 | 关键字段 |
|---|---|
| `SystemMessage` | `content` |
| `HumanMessage` | `content`、`name`（不同 provider 语义不同）、`id` |
| `AIMessage` | `text`、`content`、`content_blocks`、`tool_calls`、`id`、`usage_metadata`、`response_metadata`；流式时为 `AIMessageChunk` |
| `ToolMessage` | `content`（必填）、`tool_call_id`（必填，必须与 `AIMessage.tool_calls[i].id` 匹配）、`name`（必填）、`artifact`（不进模型上下文，仅程序侧可读） |

`AIMessage.tool_calls` 结构：`[{"name": str, "args": dict, "id": str, "type": "tool_call"}]`。

### 4.2 content blocks

`message.content_blocks` 是**惰性解析**属性：把 `content` 解析成跨 provider 统一的有类型 dict 列表。

- 核心块：`TextContentBlock`（`{"type": "text", "text": ...}`）、`ReasoningContentBlock`（`{"type": "reasoning", "reasoning": ...}`）。
- 多模态块：`image`、`file`、`audio`、`video`（用 `url` / `base64` + `mime_type` / `file_id`）。
- 工具块：`tool_call`、`tool_call_chunk`。
- provider 私有数据塞在块的 `extras` 里。

Anthropic 的 `thinking` 块 → 归一为 `{"type": "reasoning", "reasoning": "...", "extras": {"signature": "..."}}`；OpenAI 的 `reasoning` summary → 归一为 `{"type": "reasoning", "id": ..., "reasoning": "summary 1"}`。

**想让 content 本身就以标准块存储**：设 `LC_OUTPUT_VERSION=v1` 环境变量，或 `init_chat_model("gpt-5-nano", output_version="v1")`。默认 `message.content` 仍是 provider 原生形态，`content_blocks` 才是标准形态。

构造消息时可直接用 `content_blocks=[...]`，它会同时填充 `content`。

### 4.3 `add_messages` reducer 语义

`langgraph.graph.message.add_messages`（源码 `libs/langgraph/langgraph/graph/message.py`）：

> Merges two lists of messages, updating existing messages by ID. By default, this ensures the state is "append-only", unless the new message has the same ID as an existing message.

- 缺 `id` 的消息自动赋 `uuid.uuid4()`。
- **`right` 中与 `left` 同 id 的消息会替换 `left` 中的那一条**（原地覆盖，不追加）。
- `RemoveMessage(id=...)` 删除对应 id 的消息；删除不存在的 id 抛 `ValueError`。
- 哨兵 `REMOVE_ALL_MESSAGES = "__remove_all__"`：`RemoveMessage(id=REMOVE_ALL_MESSAGES)` 会清空之前的全部消息（源码：返回 `right[remove_all_idx + 1:]`）。
- 可选 `format="langchain-openai"`：把消息转成 OpenAI 格式。
- `MessageGraph` 已在 langgraph 1.0.0 废弃（"to be removed in 2.0.0. Please use StateGraph with a `messages` key instead."）。

**因此**：中间件里返回 `{"messages": [SomeMessage(id="x")]}`，如果 state 中已有同 id 消息，就是**原地替换**；要追加就必须给新 id。

### 4.4 Agent 的 state schema

```python
class AgentState(TypedDict, Generic[ResponseT]):
    messages: Required[Annotated[list[AnyMessage], add_messages]]
    jump_to: NotRequired[Annotated[JumpTo | None, EphemeralValue, PrivateStateAttr]]
    structured_response: NotRequired[Annotated[ResponseT, OmitFromInput]]
```

- `InputAgentState`：只有 `messages: Required[Annotated[list[AnyMessage | dict[str, Any]], add_messages]]`。
- `OutputAgentState`：`messages` + `structured_response: NotRequired[ResponseT]`。

（https://reference.langchain.com/python/langchain/agents/middleware/types/AgentState ）

`jump_to` 带 `EphemeralValue`（不 checkpoint 持久化）+ `PrivateStateAttr`（不出现在对外 state 输出中）。

---

## 5. 模型接入

### 5.1 `init_chat_model`

```python
init_chat_model(
    model: str | None = None,
    *,
    model_provider: str | None = None,
    configurable_fields: Literal['any'] | list[str] | tuple[str, ...] | None = None,
    config_prefix: str | None = None,
    kwargs: Any = {},
) -> BaseChatModel | _ConfigurableModel
```
（https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model ）

```python
from langchain.chat_models import init_chat_model

gpt_5 = init_chat_model("openai:gpt-5.5", temperature=0)
```

- 推荐带 provider 前缀（`"openai:gpt-5.5"`）。裸名靠前缀猜测（`gpt-*`→openai，`claude*`→anthropic，`gemini*`→`google_vertexai`，`mistral*`→`mistralai`，`deepseek*`→`deepseek`，`grok*`→`xai`，`sonar*`→`perplexity`，`solar*`→`upstage`，`command*`→`cohere`，`accounts/fireworks*`→`fireworks`；`amazon.*`/`anthropic.*`/`meta.*`→`bedrock`）。猜测是 best-effort。
- 也可 `model_provider=` 显式传（等价于前缀形式），provider 包必须单独安装（如 `langchain-openai`）。
- `configurable_fields="any"` **有安全隐患**：`api_key`、`base_url` 等可在运行时被改，可能把请求导向别的服务。接收不可信配置时必须显式枚举字段。
- `config_prefix` 用于多模型共存时给 config key 加前缀。

### 5.2 工具调用循环由谁驱动

**由 `create_agent` 编译出的 LangGraph 图驱动，模型只负责「决定调用哪个工具」。**

源码 `factory.py::_make_model_to_tools_edge` 的判定顺序：

1. state 里有 `jump_to` → 优先按 `jump_to` 跳。
2. 没有 `AIMessage`（消息被清空）→ 退出循环。
3. 最后一条 `AIMessage` 没有 `tool_calls` → 退出循环（经典退出条件）。
4. 有未完成的 tool call → `[Send("tools", [tool_call]) for ...]`（并行扇出）。
5. 本轮新生成了 `structured_response` → 退出循环。
6. 有 tool call 但都已完成（说明是注入了合成 tool message）→ 回 model 节点。

`_make_tools_to_model_edge`：

1. 没有 `AIMessage` → 回 model。
2. 本批已执行工具**全部** `return_direct=True` → 退出。
3. 执行了结构化输出工具且 `status != "error"` → 退出。
4. 否则回 model 继续循环。

单独用模型时（不建 agent），工具循环要自己写：绑定工具 → 模型返回 `tool_calls` → 执行 → 把 `ToolMessage` 追加进 messages → 再调用模型（https://docs.langchain.com/oss/python/langchain/models#tool-calling ）。

### 5.3 模型级结构化输出 `with_structured_output`

```python
model_with_structure = model.with_structured_output(Movie)          # Pydantic
model_with_structure = model.with_structured_output(MovieDict)      # TypedDict
model_with_structure = model.with_structured_output(json_schema, method="json_schema")
```

- `method` 可为 `'json_schema'` / `'function_calling'` / `'json_mode'`（provider 决定支持情况）。
- `include_raw=True` → 返回 `{"raw": AIMessage, "parsed": ..., "parsing_error": ...}`。
- 这是**模型级**能力；**agent 级**用 `response_format=`（见 §8）。

### 5.4 模型 profile

`langchain>=1.1` 起 chat model 暴露 `model.profile`（含 `max_input_tokens`、`tool_calling`、`structured_output`、`image_inputs`、`reasoning_output` 等），数据来自 models.dev。`create_agent` 用它自动选择结构化输出策略；`SummarizationMiddleware` 用它算 `("fraction", x)` 阈值。profile 缺失时可用 `init_chat_model("...", profile={...})` 手动指定。

---

## 6. 上下文工程与记忆

### 6.1 运行时上下文 `context`

- `create_agent(context_schema=MyContext)` 声明类型；`agent.invoke(inputs, context=MyContext(...))` 传入。
- 通过 `runtime.context`（中间件）与 `runtime.context`（工具内 `ToolRuntime.context`）读取。
- **不可变**：文档表述 "Context provides immutable configuration data that is passed at invocation time. Use it for user IDs, session details, or application-specific settings that shouldn't change during a conversation."
- `thread_id`（`config={"configurable": {"thread_id": ...}}`）作用域是**会话/线程**；`context` 是**每次运行**携带的静态依赖。生产中通常两者都传。
- `Runtime` 字段：`context`、`store`、`stream_writer`、`heartbeat`、`previous`、`execution_info`、`server_info`、`control`。`Runtime` **不含** `config`——要拿 `RunnableConfig` 请直接加 `config: RunnableConfig` 参数或用 `langgraph.config.get_config()`。
- 迁移提醒：v0 用 `config["configurable"]` 注入，v1 改用 `context=`。

### 6.2 短期记忆（checkpointer）

```python
from langgraph.checkpoint.memory import InMemorySaver
agent = create_agent(model="openai:gpt-5.5", tools=[...], checkpointer=InMemorySaver())
thread_config = {"configurable": {"thread_id": "1"}}
agent.invoke({"messages": [{"role": "user", "content": "Hi! My name is Bob."}]}, thread_config)
agent.invoke({"messages": [{"role": "user", "content": "What's my name?"}]}, thread_config)
```

- 短期记忆 = **agent state 本身**（主要是 `messages`），由 checkpointer 持久化到 thread。
- state 在每次 invoke 或每个 step（工具调用等）完成后更新，step 开始时读取。
- 生产用 DB 后端：`langgraph-checkpoint-postgres`（`PostgresSaver`）、`langgraph-checkpoint-sqlite` 等。
- `HumanInTheLoopMiddleware` **必须**配 checkpointer 才能跨中断保持状态。

### 6.3 长期记忆（store）

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
agent = create_agent(model="openai:gpt-5.5", tools=[...], store=store)

@tool
def get_user_info(user_id: str, runtime: ToolRuntime) -> str:
    """Look up user info."""
    item = runtime.store.get(("users",), user_id)
    return str(item.value) if item else "Unknown user"
```

- 接口：`langgraph.store.base.BaseStore`；实现：`InMemoryStore`（内存字典）、`PostgresStore`（`langgraph-store-postgres`）、MongoDB / Redis 等。
- 数据组织：`namespace`（tuple，类似目录）+ `key`（唯一键）+ value（JSON 文档）。API：`put(namespace, key, value)`、`get(namespace, key)`、`search(namespace, filter=..., query=...)`、`delete`。
- `InMemoryStore` 支持 `IndexConfig(embed=..., dims=...)` 以支持向量检索。
- 作用域：**跨 thread 跨会话**。state 是会话级，store 是跨会话级。
- 工具里 `runtime.store` 可能为 `None`（未传 store 时），务必判空。

---

## 7. 流式

### 7.1 `stream` / `astream` 的 `stream_mode`

Agent 层文档明确列出三种常用模式（https://docs.langchain.com/oss/python/langchain/streaming ）：

| Mode | 内容 |
|---|---|
| `updates` | 每步后的 state 更新。`data` 形如 `{"model": {"messages": [...]}}` / `{"tools": {"messages": [...]}}` |
| `messages` | `(token, metadata)` 二元组；`metadata["langgraph_node"]` 标明来源节点（`"model"` / `"tools"`） |
| `custom` | 节点内 `get_stream_writer()` 写入的任意数据 |

LangGraph 层还有更多：`values`（每步完整 state）、`checkpoints`、`tasks`、`debug`（https://docs.langchain.com/oss/python/langgraph/streaming ）。

**统一输出格式**：传 `version="v2"`（需 LangGraph ≥ 1.1）。每个 chunk 是统一的 `StreamPart` dict：

```python
{
    "type": "values" | "updates" | "messages" | "custom" | "checkpoints" | "tasks" | "debug",
    "ns": (),   # 子图命名空间
    "data": ...,
}
```
v1（默认）格式随模式/子图选项变化，多模式返回 `(mode, data)` 元组。

**坑**：agent 放进父 `StateGraph` 当节点时，它就是子图。父图 `stream_mode="messages"` **不会**透出内层 agent 的 token，除非父图传 `subgraphs=True`。

### 7.2 `stream_events` / `astream_events` / `on_*` 事件

`astream_events` 签名（`langchain_core`）：

```python
astream_events(
    self,
    input: Any,
    config: RunnableConfig | None = None,
    *,
    version: Literal['v1', 'v2', 'v3'] = 'v2',
    include_names: Sequence[str] | None = None,
    include_types: Sequence[str] | None = None,
    include_tags: Sequence[str] | None = None,
    exclude_names: Sequence[str] | None = None,
    exclude_types: Sequence[str] | None = None,
    exclude_tags: Sequence[str] | None = None,
    kwargs: Any = {},
) -> AsyncIterator[StreamEvent] | Awaitable[Any]
```
（https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/astream_events ）

- `version="v2"`（默认）→ 产出 `StreamEvent` dict，事件名形如 `on_{runnable_type}_{start|stream|end}`：`on_chat_model_start/stream/end`、`on_tool_start/end`、`on_chain_start/stream/end`、`on_llm_*`、`on_retriever_*`、`on_prompt_*`。自定义事件 `adispatch_custom_event` **只在 v2/v3 出现**。
- `version="v3"` → 新的「typed projection」协议，**只**在 `BaseChatModel` 和 `langgraph.CompiledGraph` 上实现，普通 `Runnable` 会抛 `NotImplementedError`；**仍是 beta**。
- `version="v1"` 保留兼容，官方标注 "will be deprecated in `0.4.0`"（指 langchain-core 版本，非 LangChain 1.0）。

LangChain 1.x 的推荐写法是 v3 typed projection：

```python
stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    version="v3",
)
for message in stream.messages:
    for delta in message.text:
        print(delta, end="", flush=True)
final_state = stream.output
```
可用投影：`stream.messages`、`stream.values`、`stream.output`、`stream.tool_calls`、`stream.subgraphs`、`stream.subagents`、`stream.extensions`；同步混合消费用 `stream.interleave("messages", "tool_calls", "values")`。

**中间件可注册 transformer**（需 `langchain>=1.3.2`）：`AgentMiddleware.transformers` 是 `Callable[[tuple[str, ...]], StreamTransformer]` 工厂元组，编译期顺序为 `ToolCallTransformer` → 中间件 transformers → 调用方 `transformers=`。`PIIMiddleware(apply_to_output=True)` 用这个机制在**流出前**脱敏文本增量、tool-call args、tool 输出与 state 快照。

### 7.3 与 LangGraph 层的差异

- LangChain 层提供**面向 agent 的语义封装**：`updates` 里的节点名固定为 `"model"` / `"tools"`；v3 投影直接给出 `ChatModelStream` / tool-call 生命周期。
- LangGraph 层提供**图运行时原语**：`Send` 并行扇出、子图 namespace、checkpoints/tasks/debug 模式、`interrupt` 协议。
- LangChain 的 agent 本身就是 LangGraph 图，二者流式栈共用；差别在**投影层**，不在引擎层。

---

## 8. 结构化输出与 state schema 的关系

### 8.1 agent 级 `response_format`

```python
class ProviderStrategy(Generic[SchemaT]):
    schema: type[SchemaT]
    strict: bool | None = None            # strict 需 langchain>=1.2

class ToolStrategy(Generic[SchemaT]):
    schema: type[SchemaT]
    tool_message_content: str | None
    handle_errors: Union[bool, str, type[Exception], tuple[type[Exception], ...], Callable[[Exception], str]]
```

- 传 **schema 类型**（Pydantic / dataclass / TypedDict）时，LangChain 自动选策略：模型 profile 声明支持原生结构化输出 → `ProviderStrategy`；否则 → `ToolStrategy`。
- 传 **JSON Schema dict** 时**必须**显式包策略，否则不生效。
- `ToolStrategy.schema` 还支持 union 类型（模型自己挑）。

### 8.2 输出落在哪

结构化结果落在**最终 state 的 `structured_response` 键**：

```python
class Answer(BaseModel):
    summary: str
    confidence: float

agent = create_agent(model="openai:gpt-5.5", tools=tools, response_format=Answer)
result = agent.invoke({"messages": [{"role": "user", "content": "Summarize AI trends"}]})
result["structured_response"]   # Answer(summary=..., confidence=...)
```

- `structured_response` 在 `AgentState` 里带 `OmitFromInput`（不能作为输入传入）。
- 结构化输出**在主循环内生成**（不再像 v0 那样单独一个节点），减少一次模型往返。
- 每次模型调用若配置了 `response_format` 但本轮没产出结构化结果，源码会把 `structured_response` 显式置 `None`，避免读到上一轮 checkpoint 里的陈旧值。
- 错误类型：`StructuredOutputError`、`StructuredOutputValidationError`、`MultipleStructuredOutputsError`（`langchain.agents.structured_output`）。

### 8.3 最终 state 形状与类型标注

- **输入**：`InputAgentState` —— 只有 `messages`（接受 `AnyMessage` 或 OpenAI 风格 dict）。
- **输出**：`OutputAgentState[ResponseT]` —— `messages: list[AnyMessage]` + `structured_response: ResponseT`。
- **内部/完整 state**：`AgentState[ResponseT]` —— 额外含 `jump_to`（私有 + 临时，不对外输出）。
- `create_agent` 的返回类型标注：`CompiledStateGraph[AgentState[ResponseT], ContextT, InputAgentState, OutputAgentState[ResponseT]]`。**这就是「输入 state / 输出 state」的类型边界**——写转换产物时，输出契约应对齐 `OutputAgentState`，而不是 `AgentState`。

---

## 9. 端到端示例（自定义中间件 + 自定义工具 + 结构化输出 + 可恢复 state）

```python
from typing import Any, Callable

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import (
    ModelRequest,
    ModelResponse,
    before_model,
    wrap_tool_call,
)
from langchain.agents.structured_output import ToolStrategy
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime
from langgraph.types import Command
from pydantic import BaseModel
from typing_extensions import NotRequired


# --- 1. 自定义 state -------------------------------------------------
class SkillState(AgentState):
    call_count: NotRequired[int]
    facts: NotRequired[dict[str, str]]


# --- 2. 自定义工具：读 runtime.state，写 Command ----------------------
@tool
def remember_fact(key: str, value: str, runtime: ToolRuntime[None, SkillState]) -> Command:
    """Store a fact in the conversation state."""
    facts = dict(runtime.state.get("facts", {}))
    facts[key] = value
    return Command(update={
        "facts": facts,
        "messages": [ToolMessage(content=f"stored {key}", tool_call_id=runtime.tool_call_id)],
    })


# --- 3. 自定义中间件：node-style（改 state / 短路） -------------------
@before_model(state_schema=SkillState, can_jump_to=["end"])
def cap_calls(state: SkillState, runtime: Runtime) -> dict[str, Any] | None:
    if state.get("call_count", 0) >= 3:
        return {"messages": [AIMessage("Call budget exhausted.")], "jump_to": "end"}
    return None


# --- 4. 自定义中间件：wrap-style（改请求 + 重试） ---------------------
@wrap_model_call
def retry_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    for attempt in range(3):
        try:
            return handler(request)
        except Exception:
            if attempt == 2:
                raise
    raise AssertionError("unreachable")


# --- 5. 自定义中间件：wrap-style（工具错误 -> ToolMessage） -----------
@wrap_tool_call
def tool_errors(request, handler):
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(content=f"tool failed: {e}", tool_call_id=request.tool_call["id"])


# --- 6. 结构化输出 ----------------------------------------------------
class Report(BaseModel):
    answer: str
    sources: list[str]


agent = create_agent(
    model="openai:gpt-5.5",
    tools=[remember_fact],
    system_prompt="You are a skill runner.",
    middleware=[cap_calls, retry_model, tool_errors],
    response_format=ToolStrategy(Report),
    checkpointer=InMemorySaver(),          # 可恢复 state
)

config = {"configurable": {"thread_id": "t-1"}}
result = agent.invoke({"messages": [{"role": "user", "content": "go"}]}, config=config)
print(result["structured_response"])      # Report(answer=..., sources=[...])
print(result["messages"][-1].content)
```

**这个示例覆盖的能力归属**：

| 能力 | 来自哪一层 |
|---|---|
| `create_agent` / 工具循环 | LangChain 层（底层是 LangGraph 图） |
| `before_model` / `wrap_model_call` / `wrap_tool_call` | LangChain 层（中间件） |
| `ToolRuntime` / `Command` 写 state | LangGraph 层（`langgraph.types.Command`、`langgraph.prebuilt.ToolRuntime`） |
| `InMemorySaver` / `thread_id` 恢复 | LangGraph 层（checkpointer） |
| `response_format` → `structured_response` | LangChain 层 |

---

## 10. 来源

一手来源（按优先级）：

1. API 参考 —— `create_agent` 签名与参数表：https://reference.langchain.com/python/langchain/agents/factory/create_agent
2. API 参考 —— 中间件类型与装饰器：https://reference.langchain.com/python/langchain/agents/middleware/types
3. API 参考 —— `AgentState` / `InputAgentState` / `OutputAgentState` / `ModelRequest` / `AgentMiddleware`：https://reference.langchain.com/python/langchain/agents/middleware/types/AgentState
4. API 参考 —— `init_chat_model`：https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model
5. API 参考 —— `@tool` / `BaseTool` / `InjectedToolCallId`（langchain-core）：https://reference.langchain.com/python/langchain-core/tools/convert/tool
6. API 参考 —— `astream_events`（langchain-core）：https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/astream_events
7. 官方文档 —— Agents：https://docs.langchain.com/oss/python/langchain/agents
8. 官方文档 —— Middleware 总览 / 内置 / 自定义：https://docs.langchain.com/oss/python/langchain/middleware/overview 、 https://docs.langchain.com/oss/python/langchain/middleware/built-in 、 https://docs.langchain.com/oss/python/langchain/middleware/custom
9. 官方文档 —— Tools：https://docs.langchain.com/oss/python/langchain/tools
10. 官方文档 —— Messages：https://docs.langchain.com/oss/python/langchain/messages
11. 官方文档 —— Models（工具调用 / 结构化输出 / profile）：https://docs.langchain.com/oss/python/langchain/models
12. 官方文档 —— Structured output（agent 级）：https://docs.langchain.com/oss/python/langchain/structured-output
13. 官方文档 —— Streaming / Event streaming：https://docs.langchain.com/oss/python/langchain/streaming 、 https://docs.langchain.com/oss/python/langchain/event-streaming
14. 官方文档 —— 短期 / 长期记忆：https://docs.langchain.com/oss/python/langchain/short-term-memory 、 https://docs.langchain.com/oss/python/langchain/long-term-memory
15. 官方文档 —— LangChain v1 迁移指南（`create_react_agent` → `create_agent`）：https://docs.langchain.com/oss/python/migrate/langchain-v1
16. 官方文档 —— LangGraph 流式（stream_mode 全集、`version="v2"`）：https://docs.langchain.com/oss/python/langgraph/streaming
17. 官方源码 —— `langchain.agents.factory`（图拓扑、节点名、jump_to 解析、transformers 顺序）：https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/factory.py
18. 官方源码 —— `langchain.agents.middleware.__init__`（内置中间件导出清单）：https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/__init__.py
19. 官方源码 —— `langchain.tools`（`ToolRuntime` 等实为 `langgraph.prebuilt` 再导出）：https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/tools/tool_node.py
20. 官方源码 —— `langgraph.prebuilt.tool_node`（`ToolRuntime` 定义、`ToolCallRequest`、工具返回值归一化、注入逻辑）：https://github.com/langchain-ai/langgraph/blob/main/libs/prebuilt/langgraph/prebuilt/tool_node.py
21. 官方源码 —— `langgraph.prebuilt.chat_agent_executor`（`create_react_agent` 的 `@deprecated` 标注）：https://github.com/langchain-ai/langgraph/blob/main/libs/prebuilt/langgraph/prebuilt/chat_agent_executor.py
22. 官方源码 —— `langgraph.graph.message`（`add_messages` reducer 语义、`MessageGraph` 废弃）：https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/graph/message.py
23. 官方源码 —— `langgraph.runtime`（`Runtime` 字段、`ExecutionInfo`、`ServerInfo`）：https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/runtime.py
24. 官方源码 —— `langchain_core.tools.base`（`BaseTool` 字段、`TOOL_MESSAGE_BLOCK_TYPES`）：https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/tools/base.py
25. PyPI —— `langchain` 版本与依赖：https://pypi.org/pypi/langchain/json
