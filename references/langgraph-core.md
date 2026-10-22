# LangGraph Python 1.x 核心编程 API 参考

本文基于 **LangGraph Python 1.2.16**（2026-10-22 查询 PyPI 最新发行版撰写）。版本号来源：<https://pypi.org/pypi/langgraph/json>（`info.version = "1.2.16"`；`requires_dist` 含 `langgraph-checkpoint>=4.3.0,<5.0.0`、`langgraph-prebuilt>=1.1.0,<1.2.0`、`langchain-core>=1.4.7,<2`、`pydantic>=2.7.4`）。

API 签名逐字抄自 `reference.langchain.com`（源码 commit `41c9c22`）与 `langchain-ai/langgraph` 仓库 `main` 分支源码。文中 `docs.langchain.com/oss/python/langgraph/...` 链接均为 1.x 现行文档。

**关键导入路径（1.x）**

```python
from langgraph.graph import StateGraph, START, END, MessagesState, add_messages
from langgraph.types import Command, Send, interrupt, RetryPolicy, CachePolicy, TimeoutPolicy, Overwrite
from langgraph.checkpoint.memory import InMemorySaver, MemorySaver   # MemorySaver 是 InMemorySaver 的向后兼容别名
from langgraph.errors import GraphRecursionError, NodeTimeoutError, InvalidUpdateError
from langgraph.runtime import Runtime
from langgraph.config import get_stream_writer, get_store, get_config
from langgraph.func import entrypoint, task
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent  # create_react_agent 已废弃
from langgraph.store.memory import InMemoryStore
```

> `from langgraph.constants import Send, Interrupt` 已废弃（`LangGraphDeprecatedSinceV10`），改用 `langgraph.types`。`START == "__start__"`，`END == "__end__"`（`langgraph/constants.py`）。

---

## 1. StateGraph 构造与 State schema

### 最小可运行代码

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]   # 带 reducer 的通道
    counter: int                               # 无 reducer：默认覆盖

def bump(state: State):
    return {"counter": state["counter"] + 1}

builder = StateGraph(State)
builder.add_node("bump", bump)
builder.add_edge(START, "bump")
builder.add_edge("bump", END)

graph = builder.compile()
graph.invoke({"counter": 0})   # {'counter': 1}
```

### 构造签名

```python
StateGraph(
    self,
    state_schema: type[StateT],
    context_schema: type[ContextT] | None = None,
    *,
    input_schema: type[InputT] | None = None,
    output_schema: type[OutputT] | None = None,
    kwargs: Unpack[DeprecatedKwargs] = {},
) -> None
```

- `state_schema` 必填。可为 `TypedDict`、`dataclass` 或 Pydantic `BaseModel`。**官方推荐 `TypedDict`**："Pydantic's recursive validation can be slow. For performance-sensitive applications, you may want to consider using a `dataclass` instead."
- `input_schema` / `output_schema` 默认为 `None`（等价于用 `state_schema`）。指定后，图内部仍使用一份"合并 schema"通信：`input_schema` 约束入口、`output_schema` 过滤 `invoke` 的返回值。
- `context_schema` 定义 **run 级只读上下文**（如 `user_id`、db 连接），通过 `graph.invoke(inputs, context={...})` 传入，节点用 `runtime.context` 读取。`config_schema` 参数 v0.6.0 起废弃、v2.0.0 移除；`input=` / `output=` 旧参数也已废弃（`LangGraphDeprecatedSinceV05`），改用 `input_schema` / `output_schema`。

### Reducer 机制

每个 state key 有**独立的**二元 reducer，签名 `(Value, Value) -> Value`：

- 左参 = 累积的当前 state 值；右参 = 节点本次返回的更新值。
- **默认 reducer 丢弃左参、保留右参**（即覆盖）。不写 reducer 时，节点的 `{"foo": 2}` 会整体覆盖 `foo`。
- 自定义 reducer 用 `Annotated[T, reducer_fn]` 声明（TypedDict / dataclass / Pydantic 通用）：

```python
from operator import add
class State(TypedDict):
    foo: int
    bar: Annotated[list[str], add]     # 累积
```

- **合并型 reducer 无法用空值清空字段**。返回 `{"errors": []}` 不会清空已有的 `["bad sql"]`，因为空列表被"合并"进去了。要清空必须用 `Overwrite`：

```python
from langgraph.types import Overwrite
def clear_errors(state: State):
    return {"errors": Overwrite([])}
```

`Overwrite(value, type='__overwrite__')` 只对 `BinaryOperatorAggregate` 通道有效；同一 super-step 内多个节点对同一 key 使用 `Overwrite` 会抛 `InvalidUpdateError`。等价 JSON 写法：`{"errors": {"__overwrite__": [...]}}`。

### `add_messages`

```python
add_messages(left: Messages, right: Messages, *, format: Literal['langchain-openai'] | None = None) -> Messages
```

作用（`langgraph/graph/message.py`）：

1. **按 ID 覆盖更新**。新消息（无 ID 或 ID 不存在）追加到尾部；ID 相同的消息**替换**旧消息而非追加。这正是它比 `operator.add` 强的地方——HITL 场景下用 `operator.add` 会把"修改后的消息"追加成第二条，而不是就地改写。
2. **反序列化**为 LangChain `Message` 对象。支持 `{"role": "user", "content": "..."}` 这种 dict 简写输入。
3. 因为会被反序列化成 Message 对象，访问要用**点号**：`state["messages"][-1].content`。

`MessagesState` 是预置的 `TypedDict`，只有一个键：

```python
messages: Annotated[list[AnyMessage], add_messages]
```

扩展方式：`class State(MessagesState): documents: list[str]`。

### input / output schema 与私有通道

```python
class InputState(TypedDict):
    user_input: str
class OutputState(TypedDict):
    graph_output: str
class OverallState(TypedDict):
    foo: str
    user_input: str
    graph_output: str
class PrivateState(TypedDict):
    bar: str

builder = StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)
```

关键事实：

- 节点可以写入**图 state 的任意通道**，包括不在其 `input_schema` 里的通道。
- 节点若声明返回类型为 `PrivateState`（如 `def node_2(state: OverallState) -> PrivateState`），`bar` 会作为**新的私有通道**被加入图——只要 `PrivateState` 这个 schema 在代码中已定义。
- **私有通道不会在 `invoke` 返回值中被隐藏，但会在 `stream_mode="values"` 中暴露**。要限制流式输出，用 `graph.stream(..., output_keys=["graph_output"])`，或改用 `stream_mode="updates"`。

### 节点如何声明 state 通道

LangGraph **没有** `Annotated[..., ShouldContinue]` 这类"控制流注解"。`Annotated` 只用于声明 reducer，不参与路由。控制流只有三种表达方式：

1. `add_conditional_edges(source, path)` —— 路由函数读 state 返回目标节点名；
2. 节点返回 `Command(goto=...)` —— 节点自己决定路由；
3. `add_edge` —— 静态边。

"应该继续吗"的判断函数只是普通命名约定，官方示例写作 `should_continue(state) -> Literal["tools", END]`：

```python
def should_continue(state: State) -> Literal["tools", END]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END
```

### Pydantic 作为 state schema

```python
from pydantic import BaseModel

class OverallState(BaseModel):
    a: str

builder = StateGraph(OverallState)
```

已知限制（官方原文）：

- 图的输出**不会**是 Pydantic 模型实例（返回 dict）；
- 运行时校验只发生在**第一个节点的输入**，后续节点和输出都不校验；
- Pydantic 的校验错误栈不指出是哪个节点出错；
- Pydantic 会做类型强制转换（`"42"` → `42`，`"true"` → `True`）；
- `langchain.agents.create_agent` **不支持** Pydantic state schema；
- 消息字段建议用 `AnyMessage` 而不是 `BaseMessage`，以保证序列化/反序列化正常。

---

## 2. 图的边：`add_node` / `add_edge` / `add_conditional_edges`

### 最小可运行代码

```python
from typing import Literal
from langgraph.graph import StateGraph, START, END

def route(state: State) -> Literal["a", "b"]:
    return "a" if state["x"] > 0 else "b"

builder = StateGraph(State)
builder.add_node("a", a_fn)
builder.add_node("b", b_fn)
builder.add_edge(START, "a")
builder.add_conditional_edges("a", route)     # 返回节点名
builder.add_edge("a", "b")                     # ⚠ 与条件边并存会同时执行
builder.add_edge("b", END)
```

### `add_node`

```python
add_node(
    self,
    node: str | StateNode[NodeInputT, ContextT],
    action: StateNode[NodeInputT, ContextT] | None = None,
    *,
    defer: bool = False,
    metadata: dict[str, Any] | None = None,
    input_schema: type[NodeInputT] | None = None,
    retry_policy: RetryPolicy | Sequence[RetryPolicy] | None = None,
    cache_policy: CachePolicy | None = None,
    error_handler: StateNode[Any, ContextT] | None = None,
    destinations: dict[str, str] | tuple[str, ...] | None = None,
    timeout: float | timedelta | TimeoutPolicy | None = None,
    trace_policy: TracePolicy | None = None,
    kwargs: Unpack[DeprecatedKwargs] = {},
) -> Self
```

- `add_node(fn)` 时节点名默认取函数名；`add_node("name", fn)` 显式命名。节点名是后续 `add_edge` / `add_conditional_edges` / `interrupt_before` 的引用键。
- `input_schema` 可给单个节点一个更窄的输入 schema（默认继承图 state schema）。
- `destinations` 只影响**图渲染**（让 `Command(goto=...)` 的目标节点出现在图上），**不影响执行**。
- `defer=True` 把节点推迟到整轮即将结束时执行。
- `trace_policy=TracePolicy(process_inputs=..., process_outputs=...)` 只影响该节点自身 run 的 trace 记录内容，不改变传入节点的值，也不影响执行。

### `add_edge`

```python
add_edge(self, start_key: str | list[str], end_key: str) -> Self
```

- 单个 `start_key`：该节点完成后执行 `end_key`。
- **多个** `start_key`（list）：等待**全部**起点完成后才执行 `end_key`（barrier 语义）。
- `START` / `END` 是虚拟节点：`add_edge(START, "a")` 指定入口，`add_edge("a", END)` 指定出口。

### `add_conditional_edges`

```python
add_conditional_edges(
    self,
    source: str,
    path: Callable[..., Hashable | Sequence[Hashable]] | Callable[..., Awaitable[Hashable | Sequence[Hashable]]] | Runnable[Any, Hashable | Sequence[Hashable]],
    path_map: dict[Hashable, str] | list[str] | None = None,
) -> Self
```

约定与坑：

- `path` **返回目标节点名**（字符串或字符串列表）。返回多个名字时，这些节点在**同一个 super-step 并行执行**。
- `path` 返回 `'END'` 即终止执行。
- 不给 `path_map` 时，返回值**直接当节点名**；给了 `path_map` 则先查表映射，如 `{True: "node_b", False: "node_c"}`。
- **没有返回类型注解或 `path_map` 时，图可视化会假设该边可能跳到图中任意节点**。官方 warning 原文："Without type hints on the `path` function's return value (e.g., `-> Literal["foo", "__end__"]:`) or a path_map, the graph visualization assumes the edge could transition to any node in the graph."
- 路由函数只**决定去哪**，不更新 state。要同时更新 state 并路由，用 `Command`。

### 入口/出口的等价写法

| 方法 | 等价于 |
|---|---|
| `set_entry_point(key)` | `add_edge(START, key)` |
| `set_finish_point(key)` | `add_edge(key, END)` |
| `set_conditional_entry_point(path, path_map=None)` | `add_conditional_edges(START, path, path_map)` |
| `add_sequence([n1, n2, n3])` | 依次串起 n1→n2→n3 |

官方注：`add_edge(START, ...)` / `add_edge(..., END)` 是"推荐的现代语法"，`set_entry_point` / `set_finish_point` 仍然有效。

`add_sequence` 签名：

```python
add_sequence(
    self,
    nodes: Sequence[StateNode[NodeInputT, ContextT] | tuple[str, StateNode[NodeInputT, ContextT]]],
) -> Self
```

### 关键约束

> **同一个节点只能选一种路由机制**：静态边（`add_edge`）和动态路由（`add_conditional_edges` / `Command`）不要混用。两者都存在时**两条路径都会执行**（`Command` 只增加动态边，不会取消静态边）。

一个节点有多个出边时，**所有目标节点都会并行执行**（同一 super-step）。

---

## 3. `Command` API

### 最小可运行代码

```python
from typing import Literal
from langgraph.types import Command

def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        update={"foo": "bar"},       # state 更新
        goto="my_other_node",        # 控制流
    )
```

### 签名

```python
Command(
    self,
    *,
    graph: str | None = None,
    update: Any | None = None,
    resume: dict[str, Any] | Any | None = None,
    goto: Send | Sequence[Send | N] | N = (),
)
```

| 参数 | 用途 |
|---|---|
| `update` | 应用到 state 的更新（同节点返回值），**会经过 reducer** |
| `goto` | 跳转到指定节点；可以是节点名、节点名序列、`Send` 或 `Send` 序列 |
| `graph` | 目标图。`None` = 当前图；`Command.PARENT` = 最近的上级图 |
| `resume` | 恢复 `interrupt()` 的值。也可传 `{interrupt_id: value}` 映射 |

### 三种使用场景

1. **节点返回** —— 用 `update` + `goto`（+ `graph`）把"改状态"和"路由"合并成一步。
2. **作为 `invoke` / `stream` 的输入** —— 用 `resume` 恢复被 interrupt 暂停的图。
3. **工具返回** —— 工具可以返回 `Command`，同时更新 state 并路由。

### 关键约束

- **必须写返回类型注解** `Command[Literal["target"]]`。官方原文："When returning `Command` in your node functions, you must add return type annotations with the list of node names the node is routing to, e.g. `Command[Literal["my_other_node"]]`. This is necessary for the graph rendering and tells LangGraph that `my_node` can navigate to `my_other_node`."
- **`Command` 只增加动态边**，静态边照常执行。同一个节点不要同时用 `Command` 和 `add_edge`。
- **`Command(resume=...)` 是唯一允许作为 `invoke`/`stream` 输入的 Command 形态**（可再加 `update=`）。不要用 `Command(update=...)` 作为输入来续接多轮对话——传任何 `Command` 都会从"最近一次 checkpoint"恢复而不是从 `__start__` 开始，会表现为"卡住"。续接对话请直接传普通 dict：

```python
graph.invoke({"messages": [{"role": "user", "content": "follow up"}]}, config)   # ✅
graph.invoke(Command(update={"messages": [...]}), config)                        # ❌
```

- **子图内导航到父图**：

```python
def my_node(state: State) -> Command[Literal["other_subgraph"]]:
    return Command(update={"foo": "bar"}, goto="other_subgraph", graph=Command.PARENT)
```

  从子图节点向父图节点更新**父子共有 key** 时，父图该 key **必须定义 reducer**，否则并行写会冲突。

### 与 `add_conditional_edges` 的取舍

| | `Command(goto=...)` | `add_conditional_edges` |
|---|---|---|
| 能否同时更新 state | ✅ `update=` | ❌ 只能路由 |
| 代码位置 | 节点内部 | 图构建期单独一个函数 |
| 可视化 | 需要 `Command[Literal[...]]` 注解 | 直接可见 |
| 适用 | 「算完才知道去哪」 | 「纯路由判断」 |

官方建议原文："Use `Command` instead of conditional edges if you want to combine state updates and routing in a single function." / "If you only need to route without updating state, use conditional edges instead."

---

## 4. `Send` API（map-reduce / 动态并行分支）

### 最小可运行代码

```python
from typing import Annotated
from operator import add
from langgraph.types import Send
from langgraph.graph import StateGraph, START, END

class OverallState(TypedDict):
    subjects: list[str]
    jokes: Annotated[list[str], add]

def continue_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]

builder = StateGraph(OverallState)
builder.add_node("generate_joke", lambda state: {"jokes": [f"Joke about {state['subject']}"]})
builder.add_conditional_edges(START, continue_to_jokes)
builder.add_edge("generate_joke", END)

graph = builder.compile()
graph.invoke({"subjects": ["cats", "dogs"]})
# {'subjects': ['cats', 'dogs'], 'jokes': ['Joke about cats', 'Joke about dogs']}
```

### 签名

```python
Send(
    self,
    /,
    node: str,
    arg: Any,
    *,
    timeout: float | timedelta | TimeoutPolicy | None = None,
)
```

### 用法与限制

- `Send` **只能从条件边函数返回**，返回值是 `list[Send]`。也可以作为 `Command(goto=...)` 的元素。
- `arg` 是**传给目标节点的私有 state**，可以与图的主 state **不同**。目标节点只能看到 `arg` 里的键——所以 worker 节点的输出必须写进**与主图共享的、带 reducer 的通道**才能被聚合。
- 目标节点被**并行执行多次**（每个 `Send` 一次），因此并行写同一通道必须用 reducer（通常 `Annotated[list, operator.add]`）。
- 与 reducer 的关系：`Send` 负责"扇出"，reducer 负责"扇出结果的合并"。二者缺一不可——没有 reducer 时并行写同一 key 会报 `InvalidUpdateError`。
- `Send` 可携带 `timeout=`，覆盖目标节点在该次 push 上的静态超时。
- 官方经典场景：orchestrator-worker（每个 worker 有私有 state，输出写到共享 `completed_sections: Annotated[list, operator.add]`）：

```python
def assign_workers(state: State):
    return [Send("llm_call", {"section": s}) for s in state["sections"]]
```

---

## 5. 编译与运行

### `compile()`

```python
compile(
    self,
    checkpointer: Checkpointer = None,
    *,
    cache: BaseCache | None = None,
    store: BaseStore | None = None,
    interrupt_before: All | list[str] | None = None,
    interrupt_after: All | list[str] | None = None,
    debug: bool = False,
    name: str | None = None,
    transformers: Sequence[Callable[[tuple[str, ...]], Any]] | None = None,
) -> CompiledStateGraph[StateT, ContextT, InputT, OutputT]
```

- `checkpointer`：
  - `None` —— 不使用 checkpointer；作为子图时**继承父图的 checkpointer**；
  - `False` —— 显式不使用、也不继承；
  - `True` —— 子图使用自己的 checkpointer（拥有独立的 checkpoint 历史）；
  - `BaseCheckpointSaver` 实例 —— 指定的持久化后端。
- **启用 checkpointer 后必须在 config 里传 `thread_id`**。
- `cache`：`BaseCache` 实例，配合节点的 `cache_policy=CachePolicy(ttl=...)` 使用。
- `store`：`BaseStore` 实例，用于跨线程长期记忆（与 checkpointer 是两套东西）。
- `interrupt_before` / `interrupt_after`：节点名列表，静态断点，**需要 checkpointer**。`All` 表示所有节点。
- **注意**：`compile()` **没有** `retry_policy` 参数。`RetryPolicy` 在节点级（`add_node(..., retry_policy=...)`）或 `set_node_defaults(...)` 配置；`Pregel` 底层构造器有 `retry_policy` / `cache_policy`，但 `StateGraph.compile()` 不暴露。

节点级缓存示例：

```python
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy

builder.add_node("expensive_node", expensive_node, cache_policy=CachePolicy(ttl=3))
graph = builder.compile(cache=InMemoryCache())
```

命中缓存时 `stream_mode="updates"` 的输出会带 `{'__metadata__': {'cached': True}}`。

### 运行方法

```python
invoke(
    self,
    input: InputT | Command | None,
    config: RunnableConfig | None = None,
    *,
    context: ContextT | None = None,
    stream_mode: StreamMode = 'values',
    print_mode: StreamMode | Sequence[StreamMode] = (),
    output_keys: str | Sequence[str] | None = None,
    interrupt_before: All | Sequence[str] | None = None,
    interrupt_after: All | Sequence[str] | None = None,
    durability: Durability | None = None,
    control: RunControl | None = None,
    version: Literal['v1', 'v2'] = 'v1',
    kwargs: Any = {},
) -> dict[str, Any] | Any
```

```python
stream(
    self,
    input: InputT | Command | None,
    config: RunnableConfig | None = None,
    *,
    context: ContextT | None = None,
    stream_mode: StreamMode | Sequence[StreamMode] | None = None,
    print_mode: StreamMode | Sequence[StreamMode] = (),
    output_keys: str | Sequence[str] | None = None,
    interrupt_before: All | Sequence[str] | None = None,
    interrupt_after: All | Sequence[str] | None = None,
    durability: Durability | None = None,
    control: RunControl | None = None,
    subgraphs: bool = False,
    debug: bool | None = None,
    version: Literal['v1', 'v2'] = 'v1',
    kwargs: Unpack[DeprecatedKwargs] = {},
) -> Iterator[dict[str, Any] | Any]
```

- `ainvoke` / `astream` 是对应的异步版本，签名一致。
- `input` 是位置参数且**必须传**（恢复时传 `None`）。
- `durability`：`"sync"`（下一步开始前同步落盘）/ `"async"`（下一步执行期间异步落盘，**默认**）/ `"exit"`（仅在退出时落盘）。
- `subgraphs=True`：子图事件以 `(namespace, data)`（多模式时 `(namespace, mode, data)`）元组形式发出。
- `print_mode`：只打印到控制台，不影响返回值。

### `stream_mode` 取值

| Mode | 类型 | 含义 |
|---|---|---|
| `values` | `ValuesStreamPart` | 每步之后的**完整 state**。Functional API 下只在结束时发一次 |
| `updates` | `UpdatesStreamPart` | 每步之后的**增量更新**（`{node_name: update}`）。同一步多个节点的更新**分别发出** |
| `messages` | `MessagesStreamPart` | LLM token 级 `(message_chunk, metadata)` 二元组 |
| `custom` | `CustomStreamPart` | 节点内 `get_stream_writer()` 写入的任意数据 |
| `checkpoints` | `CheckpointStreamPart` | checkpoint 创建事件（格式同 `get_state()`），**需要 checkpointer** |
| `tasks` | `TasksStreamPart` | task 开始/结束事件（含结果与错误），**需要 checkpointer** |
| `debug` | `DebugStreamPart` | 全部信息 = `checkpoints` + `tasks` + 额外元数据 |

`version="v2"`（**需要 LangGraph 1.1+**）统一输出格式，每个 chunk 是 `{"type": ..., "ns": (), "data": ...}`：

```python
for part in graph.stream(inputs, stream_mode=["values", "updates"], version="v2"):
    if part["type"] == "values":
        print(part["data"])
    elif part["type"] == "updates":
        for node_name, state in part["data"].items():
            print(node_name, state)
```

`version="v1"`（默认）：单模式返回裸数据，多模式返回 `(mode, data)` 元组，`subgraphs=True` 返回 `(namespace, data)`。

> **Python < 3.11 的异步坑**：`ainvoke`/`astream` 必须显式传 `RunnableConfig` 才能正确流式输出。

### `config` 传参

```python
config = {
    "configurable": {
        "thread_id": "my-thread",     # checkpointer 的主键
        "checkpoint_id": "...",        # 可选：定位到某个具体 checkpoint
        "checkpoint_ns": "",          # 可选：子图命名空间
    },
    "recursion_limit": 100,           # ← 顶层 key，不在 configurable 里
    "max_concurrency": 8,
    "tags": [...],
    "metadata": {...},
}
```

- `thread_id` **必须在 `configurable` 里**。
- `recursion_limit` 是**独立的顶层 config key**，不能放进 `configurable`。
- `recursion_limit` = 允许的最大 **super-step** 数。**自 v1.0.6 起默认值为 1000**（此前为 25）。超限抛 `GraphRecursionError`。
- 当前步数可在节点内通过 `config["metadata"]["langgraph_step"]` 读取；其它 metadata 键：`langgraph_node`、`langgraph_triggers`、`langgraph_path`、`langgraph_checkpoint_ns`。
- 主动降级方案：用 managed value `RemainingSteps`（`from langgraph.managed import RemainingSteps`）在 state 中声明，节点内读 `state["remaining_steps"]`。

---

## 6. 持久化与检查点

### 最小可运行代码

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "1"}}

graph.invoke({"foo": "a"}, config)
snapshot = graph.get_state(config)
snapshot.values    # {'foo': 'a'}
snapshot.next      # ()  表示图已结束
```

### `checkpointer` 接口

所有实现继承 `BaseCheckpointSaver`，核心方法：

- `.put(config, checkpoint, metadata, new_versions)` —— 存一个 checkpoint，返回带 `checkpoint_id` 的 config
- `.put_writes(config, writes, task_id, task_path="")` —— 存 super-step 内某个节点的中间写入（pending writes）
- `.get_tuple(config)` —— 取 checkpoint 元组，用于填充 `get_state()` 的 `StateSnapshot`
- `.list(config, *, filter=None, before=None, limit=None)` —— 列出 checkpoint，用于 `get_state_history()`
- `.delete_thread(thread_id)`

异步执行时使用异步版本：`.aput`、`.aput_writes`、`.aget_tuple`、`.alist`、`.adelete_thread`。

### 现有实现

| 类 | 包 | 说明 |
|---|---|---|
| `InMemorySaver` | `langgraph-checkpoint`（随 langgraph 安装） | 内存，**仅用于调试/测试**。源码 docstring 明确写 "Only use `InMemorySaver` for debugging or testing purposes. For production use cases we recommend installing langgraph-checkpoint-postgres and using `PostgresSaver` / `AsyncPostgresSaver`." |
| `MemorySaver` | 同上 | **`MemorySaver = InMemorySaver  # Kept for backwards compatibility`**（`libs/checkpoint/langgraph/checkpoint/memory/__init__.py` 末尾） |
| `SqliteSaver` | `langgraph-checkpoint-sqlite`（需单独安装） | 同步、本地文件。源码注明 "meant for lightweight, synchronous use cases (demos and small projects) and does not scale to multiple threads" |
| `AsyncSqliteSaver` | 同上 | 需要 `aiosqlite` |
| `PostgresSaver` | `langgraph-checkpoint-postgres`（需单独安装） | 生产推荐。`PostgresSaver.from_conn_string(conn_string, *, pipeline=False)`，`setup()` **必须由用户首次手动调用**建表迁移 |
| `AsyncPostgresSaver` | 同上 | 生产推荐 |
| `MongoDBSaver` | `langgraph-checkpoint-mongodb` | 生产 |
| `CosmosDBSaver` | `langchain-azure-cosmosdb` | Azure |

其它事实：

- 使用 `PostgresSaver` 时 `thread_id` 字段长度有限，**建议控制在 255 字符以内**。
- `MemorySaver` / `InMemorySaver` **进程重启后全部丢失**。
- `PostgresSaver.from_conn_string(...)` 是 context manager；`setup()` 需在首次使用前调用。
- Agent Server 托管模式下**无需自己配置 checkpointer**。
- checkpointer 保存图状态和可恢复的 task/write 记录，不提供外部操作的 exactly-once 保证。节点恢复可能从头重跑，外部调用仍可能重复；需要幂等、隔离或有边界的恢复方案。

### `thread_id` 语义

- `thread_id` 是 checkpointer 存取 checkpoint 的**主键**，必须写在 `configurable` 里。
- 同一个 `thread_id` = 同一条会话线，状态**跨多次 invoke 累积**（对话记忆）。
- 新的 `thread_id` = 全新的空状态线程。
- **恢复 interrupt 时必须用与中断时相同的 `thread_id`**。
- `thread_id` 就是"持久化游标"。

### `get_state` / `update_state` / state history

```python
get_state(self, config: RunnableConfig, *, subgraphs: bool = False) -> StateSnapshot
```

`StateSnapshot` 字段：

| 字段 | 说明 |
|---|---|
| `values` | 该 checkpoint 的 state 通道值 |
| `next` | 接下来要执行的节点名元组；`()` 表示图已完成 |
| `config` | 含 `thread_id` / `checkpoint_ns` / `checkpoint_id` |
| `metadata` | `source`（`"input"` / `"loop"` / `"update"`）、`writes`（节点输出）、`step`（super-step 计数） |
| `created_at` | ISO 8601 时间戳 |
| `parent_config` | 上一个 checkpoint 的 config，首个为 `None` |
| `tasks` | 本步待执行的 `PregelTask` 元组，每项含 `id`、`name`、`error`、`interrupts`，`subgraphs=True` 时还含 `state` |

```python
update_state(
    self,
    config: RunnableConfig,
    values: dict[str, Any] | Any | None,
    as_node: str | None = None,
    task_id: str | None = None,
) -> RunnableConfig
```

- 更新会**创建一个新 checkpoint**，不修改原 checkpoint。
- 更新值**同样经过 reducer**，所以带 reducer 的通道是**累加**而不是覆盖。
- `as_node` 指定"这次更新当作哪个节点的输出"，决定下一个执行哪个节点（不指定则用最后更新 state 的节点，若有歧义会报错）。
- `update_state` 返回新的 config，可直接 `graph.invoke(None, new_config)` 继续跑。

```python
get_state_history(
    self,
    config: RunnableConfig,
    *,
    filter: dict[str, Any] | None = None,
    before: RunnableConfig | None = None,
    limit: int | None = None,
) -> Iterator[StateSnapshot]
```

返回的快照**按时间倒序**（最新在前）。常用筛选：

```python
history = list(graph.get_state_history(config))
before_node_b = next(s for s in history if s.next == ("node_b",))
step_2 = next(s for s in history if s.metadata["step"] == 2)
forks = [s for s in history if s.metadata["source"] == "update"]
interrupted = next(s for s in history if s.tasks and any(t.interrupts for t in s.tasks))
```

**时间旅行（fork）**：把某个历史 checkpoint 的 config 传给 `update_state`，再 `invoke(None, fork_config)`，即可从该点重新执行后续节点（该点之后的节点会重跑，包括 LLM 调用和 interrupt）。

```python
bulk_update_state(
    self,
    config: RunnableConfig,
    supersteps: Sequence[Sequence[StateUpdate]],
) -> RunnableConfig
```

批量回放多个 super-step 的更新。**需要 checkpointer**。每个 update 是 `(values, as_node, task_id)` 元组，`task_id` 可选。

### Checkpoint 命名空间（与子图相关）

- `""`（空串）：父（根）图的 checkpoint。
- `"node_name:uuid"`：作为该节点被调用的子图的 checkpoint。
- 嵌套子图用 `|` 连接，如 `"outer_node:uuid|inner_node:uuid"`。
- 节点内可通过 `config["configurable"]["checkpoint_ns"]` 读取。

---

## 7. 人机交互（interrupt）

### 最小可运行代码

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt

class State(TypedDict):
    messages: list[dict]

def human_review(state: State):
    answer = interrupt("Do you approve?")   # 第一次调用抛 GraphInterrupt
    return {"messages": [{"role": "user", "content": answer}]}

graph = (
    StateGraph(State)
    .add_node("human_review", human_review)
    .add_edge(START, "human_review")
    .add_edge("human_review", END)
    .compile(checkpointer=InMemorySaver())
)

config = {"configurable": {"thread_id": "graph-api-resume"}}

result = graph.invoke({"messages": []}, config)
result["__interrupt__"]   # (Interrupt(value='Do you approve?', id='...', response_schema=None),)

resumed = graph.invoke(Command(resume="yes"), config)   # interrupt() 返回 "yes"
```

### `interrupt()` 签名

```python
interrupt(
    value: Any,
    *,
    response_schema: dict[str, Any] | type | None = None,
) -> Any
```

### 关键约束（官方原文要点）

- **必须有 checkpointer**，且 config 里必须有 `thread_id`。
- **恢复时节点从头重跑**："The graph resumes from the start of the node, **re-executing** all logic." —— `interrupt()` 之前的代码会再次执行，所以 `interrupt()` 之前的副作用必须**幂等**。
- 一个节点内有多个 `interrupt()` 时，LangGraph 按**节点内的调用顺序**匹配 resume 值；该列表按 task 隔离，不跨 task 共享。
- `value` 必须是 **JSON 可序列化**的（生产环境）。
- `resume` 的值成为 `interrupt()` 的返回值。
- **`Command(resume=...)` 是唯一允许作为 `invoke`/`stream` 输入的 Command 形态。**
- `response_schema`（**需要 langgraph>=1.2.12**）：可传 JSON Schema dict（**不做校验**）或 Pydantic model / `TypedDict` / dataclass（转成 JSON Schema 给客户端渲染表单，并**校验** resume 值，返回校验后的对象）。校验失败抛 `pydantic.ValidationError`，可用同一 `thread_id` 重新 `Command(resume=...)`。
- 多 interrupt 并行挂起时，用 `{interrupt_id: value}` 映射一次恢复全部：

```python
resume_map = {i.id: f"answer for {i.value}" for i in stream.interrupts}
resumed = graph.stream_events(Command(resume=resume_map), config, version="v3")
```

- 事件流（`graph.stream_events(..., version="v3")`，LangGraph v1.2 引入的 typed-projection API）通过 `stream.interrupted` / `stream.interrupts` 暴露挂起信息，`stream.output` 暴露最终 state。默认 `invoke()` API 则通过 `result["__interrupt__"]` 暴露。

### 静态断点 `interrupt_before` / `interrupt_after`

```python
# 编译期（需要 checkpointer）
graph = builder.compile(interrupt_before=["node_a"], interrupt_after=["node_b", "node_c"], checkpointer=checkpointer)
graph.invoke(inputs, config=config)      # 跑到第一个断点
graph.invoke(None, config=config)        # 跑到下一个断点

# 运行期（每次 invoke 可改）
graph.invoke(inputs, interrupt_before=["node_a"], interrupt_after=["node_b"], config=config)
```

- 语义：`interrupt_before` 在**节点执行前**暂停；`interrupt_after` 在**节点执行后**暂停。
- 恢复一律用 `graph.invoke(None, config=config)`。
- 静态断点**必须**有 checkpointer（编译期设置时）。
- `interrupt()`（动态）与静态断点可以共存。

### 与 LangChain middleware HITL 的关系（仅 LangGraph 侧事实）

- LangGraph 侧的人工介入能力就是上面这套 `interrupt()` + `Command(resume=...)` + checkpointer 机制。
- `langchain.agents.create_agent` 的 `interrupt_before` / `interrupt_after` 参数直接透传到编译期断点。
- `langchain` 侧的 HITL（middleware / `HumanInTheLoopMiddleware`）构建在 LangGraph 运行时之上；其暂停点最终仍落到 LangGraph 的 checkpoint 与 interrupt 机制上。
- **转换器注意**：如果目标 Skill 的人工介入语义是"暂停节点、等待外部输入、恢复后继续"，用 `interrupt()`；如果是"在某个节点前/后设固定断点"，用 `interrupt_before` / `interrupt_after`。两者都需要 `compile(checkpointer=...)`。

---

## 8. 子图

### 两种模式（官方对照表）

| 模式 | 何时用 | state schema |
|---|---|---|
| **在节点内调用子图** | 父子 schema **不同**（无共享 key），或需要做状态转换 | 手写 wrapper：父 state → 子入参 → 子出参 → 父 state |
| **把子图当节点添加** | 父子**共享 state key** | 把 compiled 子图直接传给 `add_node`，无需 wrapper |

### 模式 A：作为节点嵌入（共享 schema）

```python
from langgraph.graph import StateGraph, START

class SubgraphState(TypedDict):
    foo: str   # 与父图共享
    bar: str   # 子图私有

def subgraph_node_1(state: SubgraphState):
    return {"bar": "bar"}

def subgraph_node_2(state: SubgraphState):
    return {"foo": state["foo"] + state["bar"]}

subgraph = (
    StateGraph(SubgraphState)
    .add_node("subgraph_node_1", subgraph_node_1)
    .add_node("subgraph_node_2", subgraph_node_2)
    .add_edge(START, "subgraph_node_1")
    .add_edge("subgraph_node_1", "subgraph_node_2")
    .compile()
)

builder = StateGraph(ParentState)
builder.add_node("subgraph_node", subgraph)     # 直接传 compiled graph
```

- 子图**自动**读写父图同名通道，无需手写映射。
- 子图节点能看到**父图 + 子图 state 的并集**（官方示例中子图节点既读 `foo` 这个父图共享键，也读 `bar` 这个子图私有键）。
- 反之：**父图节点读不到子图私有 key**。

### 模式 B：节点内调用（独立 schema）

```python
class SubgraphState(TypedDict):
    bar: str        # 与父图无共享

def call_subgraph(state: ParentState):
    subgraph_output = subgraph.invoke({"bar": state["foo"]})   # 父 → 子
    return {"foo": subgraph_output["bar"]}                     # 子 → 父

builder.add_node("node_1", call_subgraph)
```

- 三层嵌套时，每层只能看到自己的 schema（官方示例注释："child or parent keys will not be accessible here"）。
- 该模式下子图是**独立调用**（`subgraph.invoke`），没有父子 checkpoint 的自动关联。

### 状态命名空间与 checkpoint

- 子图作为节点时，其 checkpoint 落在父图下的独立命名空间：`checkpoint_ns = "node_name:uuid"`；嵌套用 `|` 连接。
- 子图默认**继承父图的 checkpointer**（`compile(checkpointer=None)`）；`compile(checkpointer=True)` 让子图拥有**自己的 checkpoint 历史**，可用 `graph.get_state(config, subgraphs=True)` 拿到子图自己的 config，再对它做 time travel（`parent_state.tasks[0].state.config`）。
- **坑**：子图更新 state 后，父图**不一定立即看到**变化——因为每个子图管理自己的 checkpoint 命名空间。需要跨图边界共享数据，用 `Store`。

### 何时用子图而不是一个大节点

官方给出的适用场景（`use-subgraphs`）：

- 构建 **multi-agent 系统**；
- **复用**一组节点到多个图；
- **分工开发**：不同团队各自实现一部分，只要遵守子图的输入/输出 schema，父图可以不了解子图内部。

不适用：单个节点内部就是一段线性/简单分支逻辑——直接写成节点更省事。

---

## 9. 错误处理与韧性

### `RetryPolicy`（节点级重试）

```python
from langgraph.types import RetryPolicy

builder.add_node("call_api", call_api, retry_policy=RetryPolicy(max_attempts=3))
```

`RetryPolicy` 是 `NamedTuple`，字段与默认值：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `initial_interval` | `float` | `0.5` | 首次重试前等待秒数 |
| `backoff_factor` | `float` | `2.0` | 每次重试间隔的乘数 |
| `max_interval` | `float` | `128.0` | 两次重试之间的最大秒数 |
| `max_attempts` | `int` | `3` | 最大尝试次数（**含首次**） |
| `jitter` | `bool` | `True` | 是否加随机抖动 |
| `retry_on` | `type[Exception] \| Sequence[type[Exception]] \| Callable[[Exception], bool]` | `default_retry_on` | 触发重试的异常类型或判定函数 |

- **默认 `retry_on` 排除**以下异常（及其子类）：`ValueError`、`TypeError`、`ArithmeticError`、`ImportError`、`LookupError`、`NameError`、`SyntaxError`、`RuntimeError`、`ReferenceError`、`StopIteration`、`StopAsyncIteration`、`OSError`。
- 对 `requests` / `httpx` 等 HTTP 库，**只对 5xx 重试**。
- `NodeTimeoutError` **默认可重试**。
- 自定义：

```python
from langgraph.types import default_retry_on

def custom_retry_on(exc: BaseException) -> bool:
    if isinstance(exc, MyCustomError):
        return False
    return default_retry_on(exc)

builder.add_node("call_api", call_api, retry_policy=RetryPolicy(max_attempts=3, retry_on=custom_retry_on))
```

- 也支持 `retry_policy=Sequence[RetryPolicy]`：给出一组策略，**第一个匹配的生效**。
- 全图默认值：`builder.set_node_defaults(retry_policy=..., cache_policy=..., error_handler=..., timeout=...)`（langgraph>=1.2）。源码注释说明：`retry_policy` / `timeout` 默认值适用于**所有**节点（含 error handler 节点），`cache_policy` / `error_handler` 默认值**只**作用于普通节点；节点级显式值优先于图默认值；图默认值在 `compile()` 时套用，且**不被子图继承**。
- 查看当前尝试次数：`runtime.execution_info.node_attempt`（1-indexed）。`execution_info` 还提供 `node_first_attempt_time`、`thread_id`、`run_id`、`checkpoint_id`、`task_id`；无 retry policy 时 `node_attempt` 恒为 1。
- 转换时按源 Skill 的失败语义决定是否启用重试。`RetryPolicy` 是运行机制；源要求停止或报告时照此实现，不能把自动重试当成失败停止的替代。

### 超时（langgraph>=1.2，仅 async）

```python
from langgraph.types import TimeoutPolicy

builder.add_node("call_model", call_model, timeout=60)
builder.add_node("call_model", call_model, timeout=timedelta(minutes=2))
builder.add_node("call_model", call_model, timeout=TimeoutPolicy(run_timeout=120, idle_timeout=30))
```

`TimeoutPolicy` 字段：`run_timeout`（硬墙钟上限，不刷新）、`idle_timeout`（无进展上限）、`refresh_on`（`"auto"` 默认 / `"heartbeat"`）。

- **超时只支持 async 节点**；同步节点带 `timeout` 会在编译期被拒绝（同步节点无法安全地被取消）。要包同步阻塞 I/O，用 `asyncio.to_thread` 放进 async 节点。
- `refresh_on="auto"` 下，进度信号包括：state 写入、stream 输出、子 task 调度、`runtime` stream writer 调用、以及节点或其后代产生的任何 LangChain callback 事件（LLM token、tool call、chain start/end 等）。
- `refresh_on="heartbeat"` 只认显式 `runtime.heartbeat()`。`runtime.heartbeat()` 在非 idle-timed 场景是 no-op，可以无条件调用。
- 超时触发抛 `NodeTimeoutError`（属性：`node`、`elapsed`、`kind`（`"idle"`/`"run"`）、`idle_timeout`、`run_timeout`），**失败尝试的写入会被清除**，然后由 retry policy 决定是否重试。

### 节点级错误处理（langgraph>=1.2）

```python
builder.add_node("call_api", call_api, error_handler=my_handler)
```

顺序固定：**任何异常（含 `NodeTimeoutError`）→ retry policy 判断 → 重试耗尽后才跑 error handler → 都没有则异常上抛**。handler 收到 `NodeError`，可以返回 state 更新或 `Command(goto=...)` 路由。handler 自身失败不会被自己捕获，run 直接失败。

### Recursion limit 与 `GraphRecursionError`

```python
from langgraph.errors import GraphRecursionError

try:
    graph.invoke(inputs, {"recursion_limit": 100})
except GraphRecursionError:
    ...
```

- `recursion_limit` = 最大 super-step 数，**自 v1.0.6 起默认 1000**。是**顶层 config key**。
- 主动降级：state 中声明 `remaining_steps: RemainingSteps`（`from langgraph.managed import RemainingSteps`），节点内读它并路由到兜底节点，避免真的撞上限。

### 其它错误类型

- `InvalidUpdateError`：同一 super-step 内多个节点写同一无 reducer 的通道（或多个节点对同一 key 用 `Overwrite`）。
- `EmptyInputError` / `NodeError` / `NodeCancelledError` / `GraphInterrupt` / `NodeInterrupt` / `ParentCommand` 等均在 `langgraph.errors`。

---

## 10. 其它实用 API

### 可视化

```python
graph = builder.compile()      # 必须先编译
graph.get_graph().draw_mermaid()          # 返回 mermaid 文本
graph.get_graph().draw_mermaid_png()      # 返回 PNG bytes（需 pillow）
graph.get_graph().draw_ascii()            # 终端 ASCII 图
```

- `get_graph(self, config: RunnableConfig | None = None, *, xray: int | bool = False) -> Graph`，定义在 `Pregel` 上，`CompiledStateGraph` 继承而来。
- **⚠ `StateGraph`（builder）上**没有** `get_graph()`**：1.2.16 的 `StateGraph` 公开方法只有 `set_node_defaults` / `add_node` / `add_edge` / `add_conditional_edges` / `add_sequence` / `set_entry_point` / `set_conditional_entry_point` / `set_finish_point` / `validate` / `compile`。要预览结构，先 `compile()` 再 `get_graph()`。
- 返回的 `Graph` 是 `langchain_core.runnables.graph.Graph`，方法有：`to_json`、`next_id`、`add_node`、`remove_node`、`add_edge`、`extend`、`reid`、`first_node`、`last_node`、`trim_first_node`、`trim_last_node`、`draw_ascii`、`print_ascii`、`draw_png`、`draw_mermaid`、`draw_mermaid_png`。
- `xray=True` 展开子图层级。
- 拓扑渲染只反映已声明结构，不验证源 Skill 的运行时行为、副作用或输入输出保真。

### `CompiledStateGraph` 上的方法

`CompiledStateGraph` 继承 `Pregel`，因此拥有：

| 方法 | 用途 |
|---|---|
| `invoke` / `ainvoke` | 同步/异步执行到结束，返回最终 state |
| `stream` / `astream` | 流式执行 |
| `batch` / `abatch` | 批量执行 |
| `get_state(config, *, subgraphs=False)` | 取当前 `StateSnapshot` |
| `get_state_history(config, *, filter=None, before=None, limit=None)` | 取历史快照 |
| `update_state(config, values, as_node=None, task_id=None)` | 写新 checkpoint，返回新 config |
| `bulk_update_state(config, supersteps)` | 批量写 checkpoint |
| `get_graph(config=None, *, xray=False)` | 可视化 |
| `get_input_jsonschema()` / `get_output_jsonschema()` | 输入/输出的 JSON Schema |

### `StateGraph` 上的其他方法

- `set_entry_point(key)` / `set_finish_point(key)` / `set_conditional_entry_point(path, path_map=None)`
- `add_sequence(nodes)`
- `validate()` —— 校验图结构（孤立节点等）。
- `set_node_defaults(*, retry_policy=None, cache_policy=None, error_handler=None, timeout=None)` —— 为所有节点统一设置默认策略（langgraph>=1.2）。
- 属性：`edges`、`nodes`、`branches`、`channels`、`managed`、`schemas`、`waiting_edges`、`compiled`、`state_schema`、`context_schema`、`input_schema`、`output_schema`。
- 旧版 `MessageGraph` 仍在 `langgraph.graph` 导出中，但新代码应直接用 `StateGraph` + `MessagesState`。

### `Runtime` 与上下文

节点可接受三个参数：`state`、`config`（`RunnableConfig`）、`runtime`（`Runtime`）。`Runtime` 提供 `context`、`store`、`stream_writer`、`execution_info`、`server_info`、`heartbeat()`、`control`。

```python
from langgraph.runtime import Runtime

def node(state: State, runtime: Runtime[ContextSchema]):
    print(runtime.context.my_value)
    print(runtime.execution_info.node_attempt)
```

`context` 通过 `graph.invoke(inputs, context={...})` 传入，与 `config["configurable"]` 分离。

### 自定义流式输出

```python
from langgraph.config import get_stream_writer

def node(state: State):
    writer = get_stream_writer()
    writer({"status": "working"})
    return {...}
```

配合 `stream_mode="custom"` 消费。

### `Store`（跨线程长期记忆）

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
graph = builder.compile(store=store)
```

与 checkpointer 的分工：**checkpointer = 单线程的短期 state 快照**；**store = 跨线程的应用自定义 KV 数据**（用户偏好、事实、共享知识）。节点内用 `get_store()` 或 `runtime.store` 访问。

---

## 11. Function API（`@entrypoint` / `@task`）vs Graph API

### 最小可运行代码

```python
from langgraph.func import entrypoint, task

@task
def compose(topic: str) -> str:
    return f"essay about {topic}"

@entrypoint(checkpointer=InMemorySaver())
def workflow(topic: str) -> dict:
    essay = compose(topic).result()      # 返回 future，.result() 取值
    review = interrupt({"essay": essay})
    return {"essay": essay, "review": review}
```

### 签名

```python
entrypoint(
    self,
    checkpointer: BaseCheckpointSaver | None = None,
    store: BaseStore | None = None,
    cache: BaseCache | None = None,
    context_schema: type[ContextT] | None = None,
    cache_policy: CachePolicy | None = None,
    retry_policy: RetryPolicy | Sequence[RetryPolicy] | None = None,
    timeout: float | timedelta | TimeoutPolicy | None = None,
    kwargs: Unpack[DeprecatedKwargs] = {},
)
```

```python
task(
    __func_or_none__: Callable[P, Awaitable[T]] | Callable[P, T] | None = None,
    *,
    name: str | None = None,
    retry_policy: RetryPolicy | Sequence[RetryPolicy] | None = None,
    cache_policy: CachePolicy[Callable[P, str | bytes]] | None = None,
    timeout: float | timedelta | TimeoutPolicy | None = None,
    kwargs: Unpack[DeprecatedKwargs] = {},
)
```

- 被装饰的函数**只能接受一个业务参数**；其余参数 `config`、`previous`、`runtime` 由运行时注入。`previous` 需要 checkpointer，用于取同 thread 上一次的返回值。
- `entrypoint.final(value=..., save=...)`：返回给调用者的值与存入 checkpoint 的值可以不同。
- `@task` 的调用产生 **future**，便于并行（`asyncio.gather(*futures)`）。task **只能**在 `@entrypoint` 或 `StateGraph` 节点内调用。
- task 结果在启用 checkpointer 时会被 checkpoint，**恢复时已完成的 task 不重跑**（这与节点级重跑的语义不同）。
- async task 需要 **Python 3.11+**。
- `@task` 也可以用在 `StateGraph` 的节点内部，把节点内的多步操作变成可 checkpoint 的 task（恢复时跳过已完成的 task）。
- task 的 checkpoint 语义不扩展到其调用的外部服务或不可逆副作用；不要据此宣称整个流程 exactly-once。

### 选型对比

| | Graph API | Functional API |
|---|---|---|
| 状态管理 | 显式 `State` schema + reducer | 函数作用域，无共享 state |
| 控制流 | 图结构（边/条件边） | 标准 Python（if/else/循环/函数调用） |
| 可视化 | ✅ `get_graph().draw_mermaid()` | ❌ 图在运行时动态生成，无法做静态拓扑查看 |
| 典型场景 | 复杂分支、多决策点、需要合并的并行路径、团队协作 | 给既有过程式代码加 LangGraph 能力、线性流程、快速原型 |

**两套 API 共享同一运行时，可以混用**（Functional API 的 entrypoint 里可以 `.invoke()` 一个 Graph API 的编译图，反之亦然）。

**转换器建议**：源 Skill 有固定约束（明确顺序、条件、分支、循环或人工等待）时用 **Graph API**，让这些约束落在节点与边上。Functional API 只适合源本身是过程式脚本、且不需要显式结构或静态拓扑检查的场景；它无法做静态拓扑查看，因此不能用来承载需要精确复刻的固定约束。

---

## 12. 预构建组件（`langgraph.prebuilt`）

`langgraph.prebuilt` 现为独立包 `langgraph-prebuilt`（随 `langgraph` 自动安装，版本 `>=1.1.0,<1.2.0`）。导出：`create_react_agent`、`ToolNode`、`ToolCallTransformer`、`tools_condition`、`ValidationNode`、`InjectedState`、`InjectedStore`、`ToolRuntime`。

### `ToolNode`

```python
ToolNode(
    tools: Sequence[BaseTool | Callable],
    *,
    name: str = "tools",
    tags: list[str] | None = None,
    handle_tool_errors: bool | str | Callable[..., str] | type[Exception] | tuple[type[Exception], ...] = _default_handle_tool_errors,
    messages_key: str = "messages",
    wrap_tool_call: ToolCallWrapper | None = None,
    awrap_tool_call: AsyncToolCallWrapper | None = None,
)
```

- 默认节点名 `"tools"`。
- **输入格式**三种：① state 且含 `messages` 键；② 消息列表 `[AIMessage(..., tool_calls=[...])]`；③ 直接的 tool call 列表 `[{"name": ..., "args": {...}, "id": "...", "type": "tool_call"}]`。
- **输出**：普通工具 → `{"messages": [ToolMessage(...)]}`（dict 输入）或 `[ToolMessage(...)]`（list 输入）；`Command` 工具 → `[Command(...)]`。
- `handle_tool_errors` 默认策略：**捕获工具调用错误**（模型给的参数非法）并返回描述性错误消息，**忽略工具执行错误**（会重新抛出）。可传 `True` / `str` / 异常类型 / 异常类型元组 / `Callable[..., str]` / `False`（禁用）。
- `messages_key` 指定 state 中消息列表的键名。
- 工具只能访问传给 `ToolNode` 的 state 值。直接作为 `StateGraph` 节点时是**整个图 state**；手动 `tool_node.invoke(state)` 时取决于传入内容。
- 工具内读取图 state / run 级上下文用注入的 `ToolRuntime`（`runtime.state` / `runtime.context` / `runtime.store`）。

### `tools_condition`

```python
tools_condition(state: list[AnyMessage] | dict[str, Any] | BaseModel, messages_key: str = "messages") -> Literal["tools", "__end__"]
```

- 最后一条 AI 消息含 `tool_calls` → 返回 `"tools"`；否则返回 `"__end__"`。
- 目标节点名必须是 `"tools"`，否则要自己写路由函数。

```python
from langgraph.prebuilt import ToolNode, tools_condition

builder.add_node("agent", agent_fn)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")     # 回到 agent，形成 agent→tools→agent 循环
```

### `create_react_agent` —— **已废弃**

源码 `langgraph/prebuilt/chat_agent_executor.py` 中的 docstring 明确写着：

> This function is deprecated in favor of [`create_agent`][langchain.agents.create_agent] from the `langchain` package, which provides an equivalent agent factory with a flexible middleware system. For migration guidance, see [Migrating from LangGraph v0](https://docs.langchain.com/oss/python/migrate/langgraph-v1).

- 同文件中 `AgentState`、`AgentStatePydantic`、`AgentStateWithStructuredResponse` 等也带 `@deprecated(..., category=LangGraphDeprecatedSinceV10)`，提示改用 `from langchain.agents import AgentState`。
- 1.x 的推荐写法是 LangChain 侧的 `langchain.agents.create_agent`：

```python
from langchain.agents import create_agent

graph = create_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    tools=[check_weather],
    system_prompt="You are a helpful assistant",
)
```

  `create_agent` 的签名（`langchain.agents.factory`）：

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

- 迁移差异（`create_react_agent` → `create_agent`）：`prompt` → `system_prompt`；`pre_model_hook` / `post_model_hook` → middleware 的 `before_model` / `after_model`；模型节点名从 `"agent"` 变为 `"model"`；运行时依赖从 `config["configurable"]` 改为 `context`；`create_agent` **不接受 `ToolNode` 实例**；结构化输出改用 `ToolStrategy` / `ProviderStrategy`。
- `create_agent` 返回的仍是 `CompiledStateGraph`，与 Graph API 完全兼容。

**转换器建议**：不要在生成的图里用 `create_react_agent`。按源 Skill 的局部语义选构件：固定阶段、明确条件或循环限制需要显式落实时用 `StateGraph`；自主选择工具且不违反源约束时，优先用 `langchain.agents.create_agent`；两者并存时由外层 `StateGraph` 组合固定阶段和自主区段。纯自主流程可直接采用 agent 图，不额外套一层没有职责的图。只有源流程明确要求固定工具循环形态时才用 `ToolNode` + `tools_condition` 手写循环，不能因为存在 tool calling 就默认手写。

---

## 附：转换决策清单在哪

「源 Skill 的步骤如何落成节点与边」「何时挂 checkpointer」「何时拆子图」这类决策不在本文档 —— 本文只记录 API 事实。转换决策规则与检查清单见同目录 `skill-to-langgraph-mapping.md`。

---

## 来源

| # | URL | 支撑内容 |
|---|---|---|
| 1 | <https://pypi.org/pypi/langgraph/json> | 最新版本 1.2.16、依赖版本（`langgraph-checkpoint>=4.3.0`、`langgraph-prebuilt>=1.1.0`、`langchain-core>=1.4.7`）、requires_python |
| 2 | <https://reference.langchain.com/python/langgraph/graph/state/StateGraph> | `StateGraph.__init__` 完整签名、参数表、`config_schema` 废弃说明、`StateGraph` 的公开方法列表（**不含 `get_graph()`**） |
| 3 | <https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_node> | `add_node` 完整签名与参数语义（`defer` / `destinations` / `input_schema` / `timeout` / `trace_policy` 等） |
| 4 | <https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_edge> | `add_edge` 签名、多起点 barrier 语义 |
| 5 | <https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_conditional_edges> | `add_conditional_edges` 签名、`path_map`、无类型注解时的可视化警告 |
| 6 | <https://reference.langchain.com/python/langgraph/graph/state/StateGraph/compile> | `compile` 签名与 `checkpointer` 的 `None`/`False`/实例语义 |
| 7 | <https://reference.langchain.com/python/langgraph/graph/state/StateGraph/set_entry_point>`、`.../set_conditional_entry_point`、`.../add_sequence` | 入口/序列 API 签名 |
| 8 | <https://reference.langchain.com/python/langgraph/graph/state/CompiledStateGraph> | `CompiledStateGraph` 继承 `Pregel`，附加方法 |
| 9 | <https://reference.langchain.com/python/langgraph/pregel/main/Pregel> | `Pregel.__init__`（含底层 `retry_policy`/`cache_policy`）、Pregel 算法说明 |
| 10 | <https://reference.langchain.com/python/langgraph/pregel/main/Pregel/invoke>`、`.../stream`、`.../get_state`、`.../update_state`、`.../get_state_history`、`.../bulk_update_state`、`.../get_graph` | 运行与状态 API 的逐字签名；`stream_mode` 各模式语义；`durability` 取值 |
| 11 | <https://reference.langchain.com/python/langgraph/types/Command> | `Command.__init__` 签名、`goto`/`update`/`resume`/`graph` 参数表 |
| 12 | <https://reference.langchain.com/python/langgraph/types/Send> | `Send.__init__` 签名与 map-reduce 说明 |
| 13 | <https://reference.langchain.com/python/langgraph/types/interrupt> | `interrupt()` 签名、节点重跑语义、多 interrupt 匹配规则、`response_schema` |
| 14 | <https://reference.langchain.com/python/langgraph/types/RetryPolicy>`、`.../CachePolicy`、`.../Overwrite` | 策略类签名 |
| 15 | <https://reference.langchain.com/python/langgraph/graph/message/add_messages>`、`.../MessagesState` | `add_messages` 签名与语义；`MessagesState` 字段 |
| 16 | <https://reference.langchain.com/python/langgraph/errors/GraphRecursionError> | `GraphRecursionError` 定义与 `recursion_limit` 配置方式 |
| 17 | <https://reference.langchain.com/python/langgraph/func/entrypoint>`、`.../task` | Function API 签名、注入参数、`entrypoint.final` |
| 18 | <https://reference.langchain.com/python/langchain-core/runnables/graph/Graph> | `Graph` 的 `draw_mermaid` / `draw_mermaid_png` / `draw_ascii` 等方法 |
| 19 | <https://reference.langchain.com/python/langchain/agents/create_agent> | `create_agent` 完整签名（1.x 推荐的 agent 工厂） |
| 20 | <https://docs.langchain.com/oss/python/langgraph/graph-api> | State/reducer/`add_messages`/节点/边/`Command`/`Send`/`START`/`END`/recursion limit/`RemainingSteps`/私有通道流式暴露/`set_entry_point` 与 `add_edge` 等价性 |
| 21 | <https://docs.langchain.com/oss/python/langgraph/use-graph-api> | input/output schema、Pydantic state 及其已知限制、私有通道、map-reduce + `Send`、`Overwrite`、runtime context |
| 22 | <https://docs.langchain.com/oss/python/langgraph/streaming> | `stream_mode` 取值表、v2 输出格式、Python<3.11 异步注意 |
| 23 | <https://docs.langchain.com/oss/python/langgraph/persistence> | checkpointer vs store 分工、`thread_id` 语义与长度限制、durability 模式 |
| 24 | <https://docs.langchain.com/oss/python/langgraph/checkpointers> | `BaseCheckpointSaver` 接口、checkpoint 库清单、super-step 与 pending writes、`StateSnapshot` 字段表、`checkpoint_ns` 命名空间规则、序列化/加密 |
| 25 | <https://docs.langchain.com/oss/python/langgraph/interrupts> | `interrupt()` 前置条件、恢复流程、多 interrupt 映射、`response_schema`（需 ≥1.2.12）、静态断点、幂等性要求 |
| 26 | <https://docs.langchain.com/oss/python/langgraph/fault-tolerance> | `RetryPolicy` 参数表与默认 `retry_on` 排除列表、`timeout`/`TimeoutPolicy`/`NodeTimeoutError`、错误处理顺序、`execution_info` 字段 |
| 27 | <https://docs.langchain.com/oss/python/langgraph/use-subgraphs> | 子图两种模式对照表、共享/独立 schema 示例、层级可见性规则 |
| 28 | <https://docs.langchain.com/oss/python/langgraph/choosing-apis> | Graph API vs Functional API 选型对比 |
| 29 | <https://docs.langchain.com/oss/python/langgraph/use-time-travel>`、`.../test` | `update_state(as_node=...)` fork 与 partial execution 用法 |
| 30 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/langgraph/langgraph/types.py> | `RetryPolicy` / `TimeoutPolicy` / `CachePolicy` / `TracePolicy` 字段与默认值源码、`default_retry_on` 位置 |
| 31 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/langgraph/langgraph/constants.py> | `START == "__start__"`、`END == "__end__"`、`langgraph.constants` 导入 `Send`/`Interrupt` 已废弃 |
| 32 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/langgraph/langgraph/graph/__init__.py> | `langgraph.graph` 的公开导出（`StateGraph` / `MessagesState` / `MessageGraph` / `add_messages` / `START` / `END`） |
| 33 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/langgraph/langgraph/graph/state.py> | `StateGraph` 源码：`__init__`、`set_node_defaults` 的默认值语义、`add_node`/`add_edge`/`add_conditional_edges`/`add_sequence`/`set_entry_point`/`set_conditional_entry_point`/`compile` 的实现与行号；`StateGraph` 无 `get_graph` 方法（`compile()` 之后即为 `class CompiledStateGraph`） |
| 34 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/checkpoint/langgraph/checkpoint/memory/__init__.py> | `InMemorySaver` 实现；`MemorySaver = InMemorySaver  # Kept for backwards compatibility` |
| 35 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py> | `SqliteSaver` 构造、`from_conn_string`、`setup()` 行为、线程安全说明 |
| 36 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/aio.py> | `AsyncSqliteSaver` 需要 `aiosqlite` |
| 37 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/checkpoint-postgres/langgraph/checkpoint/postgres/__init__.py> | `PostgresSaver.from_conn_string`、`setup()` 必须手动调用、`AsyncPostgresSaver` 同包 |
| 38 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/prebuilt/langgraph/prebuilt/__init__.py> | `langgraph.prebuilt` 的公开导出 |
| 39 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/prebuilt/langgraph/prebuilt/chat_agent_executor.py> | `create_react_agent` 的废弃声明与 docstring、`AgentState` 等的 `@deprecated` 标记 |
| 40 | <https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/prebuilt/langgraph/prebuilt/tool_node.py> | `ToolNode.__init__` 签名、输入/输出格式、`handle_tool_errors` 语义 |
