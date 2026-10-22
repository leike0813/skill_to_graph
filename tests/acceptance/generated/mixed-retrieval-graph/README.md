# mixed-retrieval 图

源名、graph ID 是 `mixed-retrieval`，Python 包为 `skill_graph`。`validate → retrieve(agent) → confirm → write` 保持固定阶段，检索阶段用 create_agent 自主选键和按语义判断充分性。外层不以检索次数或关键词判断充分性。

业务输入 question、catalog、output_dir 直接映射到图输入。catalog 是本地 JSON 文件，校验节点仅检查格式并提供键名；实际证据只由 lookup(key) 工具按需读取。检索模型返回 sufficient/insufficient、report、used_keys。模型输出对应源契约，工具故障停止为 failed，输入非法为 error，证据不足为 insufficient；确认 false 为 cancelled；写文件成功为 ok，path 指向真实 report.md。中间 keys、approved 是框架状态。output_dir 未提供时先暂停询问，然后单独确认写入。

运行配置为 MODEL_PROVIDER、MODEL_ID、MODEL_BASE_URL、MODEL_API_KEY_ENV（实际密钥环境变量的名字），另提供所选 provider 的 LangChain 集成。环境负责凭据、文件权限和持久化。无默认供应商，不添加图级重试。以应用目录分发，source/mixed-retrieval 必须随目录保留，不宣称单独 wheel 包含源资源。

```python
from skill_graph.graph import make_graph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

graph = make_graph(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "task-1"}}
pending = graph.invoke({"question": "How does a Graph control a task?", "catalog": "/path/catalog.json", "output_dir": "/path/out"}, config)
result = graph.invoke(Command(resume=True), config)
```

Python 将应用根加入 sys.path。CLI 的单参数入口 `cli_graph(config)` 由 langgraph.json 指定，转调同一 `make_graph`，不在工厂内配置服务存储；服务运行环境注入设施。向已有 Agent Server `/threads` 建 thread，同 thread `/threads/{id}/runs/wait` 提交 assistant_id、input，恢复为 command.resume。启动服务需要环境相应授权。

确认前不创建输出目录或文件，写节点使用排他创建保护已有文件。模型节点与确认节点分离，确认恢复不会重新检索；故障恢复仍可能重跑某节点，检查点不能保证外部副作用 exactly-once。写入失败可能留下部分文件，按源要求停止，不补偿、不重试。真实模型结果和证据引用需按源人工复核。
