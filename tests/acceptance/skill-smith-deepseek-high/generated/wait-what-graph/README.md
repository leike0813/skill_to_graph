# wait-what graph

源 Skill 为 `wait-what`；graph ID 保留源名，Python 包名为 `skill_graph`。
源是纯自主的重述任务，直接使用 `create_agent`，没有新增固定业务阶段、确认或文件写入。
`disable-model-invocation: true` 表示显式调用，本应用不提供自动触发路由。

业务输入是对话历史，图封装为 `{"messages": conversation}`；待重述对象是最后一条用户消息之前的 assistant 消息。
业务输出取最后一条 assistant 消息的 `content`，与工具消息分开。
相对文件路径按 `config.configurable.workdir` 解析，绝对路径保留。运行环境提供相应读权限；两个文件工具只读。
模型按源要求读取 `GLOSSARY.md`，多个术语表时按 `GLOSSARY-MAP.md` 选择。
源完整指令仍由一个自主区段执行，源快照用于溯源，模型取得指令正文及原始会话。

Python 调用：

```python
from skill_graph.graph import make_graph

config = {"configurable": {"workdir": "/path/to/task"}}
result = make_graph(config).invoke({"messages": conversation}, config)
reply = result["messages"][-1].content
```

环境显式提供 `MODEL_PROVIDER`、`MODEL_ID`、`MODEL_BASE_URL`、`MODEL_API_KEY_ENV`（凭据变量名），
可选 `MODEL_OPTIONS` 是模型参数 JSON。模型供应商未由源限定；按实际 provider 提供相应集成包，
此依赖声明提供 OpenAI 协议集成。代码不内置供应商或凭据，SDK 重试关闭，不设业务重试或补偿。

CLI 在应用目录执行 `langgraph dev` 启动服务（遵守环境启动与安装授权），使用相同 `make_graph(config)` 工厂。
服务已配置时，向 `POST /runs/wait` 提交：

```json
{"assistant_id":"wait-what","input":{"messages":[]},"config":{"configurable":{"workdir":"/path/to/task"}}}
```

将示例空数组替换为实际对话。本任务没有人工暂停；若调用方需要会话存储，由相应运行环境提供。
术语表是任务工作文件，不是随源包携带的资源。源包相对模块定位，本应用按完整目录搬移分发；不声明 wheel 携带 source。
运行依赖、工具及凭据由环境提供；语义与 ASD-STE100 简化英语仍需按实际回复复核。
实际验收证据另存于仓库验收目录，不随本应用分发；静态检查本身不证明模型输出保真。
