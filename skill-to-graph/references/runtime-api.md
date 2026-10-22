# 运行 API 速查

生成具体代码前读取；版本基线为 langgraph 1.2.16、langchain 1.4.7、langchain-core 1.6.13、langgraph-cli 0.4.37。实际环境使用其他版本时核对对应官方 API。

## 固定图

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    value: str

def process(state: State):
    return {"value": state["value"].strip()}

builder = StateGraph(State)
builder.add_node("process", process)
builder.add_edge(START, "process")
builder.add_edge("process", END)
graph = builder.compile()
result = graph.invoke({"value": " example "})
```

节点返回局部更新。默认更新覆盖通道；仅在业务需要聚合时用 `Annotated[类型, reducer]`。消息通道可用 `add_messages`，不要求其他图也保存消息。
`add_conditional_edges(节点, 路由函数, 路由映射)` 表达条件；`Command(update=..., goto=...)` 可合并更新和跳转，不要再加导致同一跳转重复执行的静态边。`Send(节点名, 子任务输入)` 适用于已获源许可的动态任务分发。

## agent 与混合流程

```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

def make_agent(model_id: str, provider: str, tools, instructions: str):
    model = init_chat_model(model_id, model_provider=provider)
    return create_agent(model=model, tools=tools, system_prompt=instructions)
```

模型标识及 provider 是运行配置；模型供应商集成包需另行声明。模型的技术重试设置与源失败策略一起核对，不额外添加图级重试。agent 输入通常为 `{"messages": [...]}`，结果从返回状态提取；这只是框架封装。固定图可用节点调用 agent 的 `invoke`，传递正确的 config，并只映射所需状态。需要子图恢复时核对检查点传播及调用命名空间。

## 暂停与存储

```python
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

def confirm(state):
    reply = interrupt({"question": "Proceed?"})
    return {"approved": reply is True}

# 假定 builder 已按源契约构建。
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "task-1"}}
paused = graph.invoke(input_state, config)
resumed = graph.invoke(Command(resume=True), config)
```

`interrupt()` 恢复时从节点开头重跑，不能将写操作置于暂停之前并假定只运行一次。`InMemorySaver` 仅适用于同一进程的演示或受控验收。生产持久化由环境提供所选后端。`store` 与 checkpointer 用途不同：前者跨会话数据，后者图执行恢复。

## 应用入口

```json
{
  "dependencies": ["."],
  "graphs": {"source-name": "./skill_graph/graph.py:graph"}
}
```

入口值支持模块或文件的 `:对象名`，对象可为编译图，也可为服务可加载的工厂。使用服务工厂时以实际 CLI 支持的签名接收配置及服务设施，不直接使用服务内部 API。Python 可直接导入同一装配逻辑并注入所需设施。CLI 在应用目录执行 `langgraph dev`，会启动服务；遵守当前环境的启动和安装权限。

基线服务会按完整签名统计工厂参数，额外的可选 keyword-only 参数也计入。需要 Python 注入 checkpointer/store 时，可保留一个装配函数，再用 `def cli_graph(config): return make_graph(config)` 暴露服务入口；不要将带三个参数的装配函数直接配置为服务工厂。两入口仍共享构图逻辑，服务包装不自行绑定存储。

已配置 Agent Server 的基本调用：

```text
POST /runs/wait
{"assistant_id":"source-name","input":{...}}
```

需要跨调用恢复时先 `POST /threads` 取得 thread_id，再调用 `/threads/{thread_id}/runs/wait`；恢复通过 `command.resume` 提交回复。Python 恢复用 `Command`，HTTP 用相应 JSON，业务含义保持一致。

`langgraph.json` 的 `env` 可指定 dotenv 文件或环境变量映射，密钥保持在环境中。配置中的本地文件须随应用携带。资源可相对 `Path(__file__).resolve()` 定位；若 wheel 不包含应用根的 source，就不能宣称安装后仍能读取这些资源。

来源：

- https://reference.langchain.com/python/langgraph/graphs/
- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langchain/agents
- https://docs.langchain.com/langsmith/cli
- https://docs.langchain.com/langsmith/agent-server-api
