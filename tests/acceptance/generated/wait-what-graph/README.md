# wait-what 图

源名和 graph ID 为 `wait-what`，Python 模块为 `skill_graph`。它是直接导出的自主 agent 图，无额外固定外层阶段。源平台 `disable-model-invocation: true` 表示显式调用的触发约束，部署方也应仅在用户调用该任务时运行；没有自动路由。

业务输入为前一条消息及会话上下文，按原顺序映射至 `messages`；任务工作目录通过 config.configurable.workdir 提供。重述目标绑定到输入中的最后一条 assistant 消息。输出从最后一条 assistant 消息的 content 中提取 text 块（content 为字符串时直接使用），不将思考块及框架工具消息视为业务输出。工具负责读取该工作目录中的术语表，存在 GLOSSARY-MAP.md 时由模型按源要求选择术语表。源原文从携带的快照加载，参考未预加载。

运行环境显式配置 MODEL_PROVIDER、MODEL_ID、MODEL_BASE_URL、MODEL_API_KEY_ENV（值为实际密钥变量名）。凭据保留在后者指向的环境变量中。依赖还包括所选 provider 的 LangChain 集成；没有默认供应商。本应用按目录分发，保留完整 source/wait-what；不承诺单独 wheel 安装包含这些资源。

```python
from skill_graph.graph import make_graph
config = {"configurable": {"workdir": "/path/to/task"}}
graph = make_graph(config)
result = graph.invoke({"messages": conversation}, config)
reply = result["messages"][-1].content
```

Python 将应用根加入 sys.path。CLI 用 `langgraph.json` 中工厂，在已有服务 `/runs/wait` 提交 `{"assistant_id":"wait-what","input":{"messages":[...]},"config":{"configurable":{"workdir":"/path/to/task"}}}`。启动服务需要环境相应授权；两入口共用同一 agent。

文件读权限由环境提供，路径语义与任务上下文一致。没有源要求的文件写入或人工确认；未增加这些步骤。模型/工具错误按框架错误传播，不添加图级重试、降级或补偿。语义、术语与 ASD-STE100 要求需按源复核，生成代码不等于已通过该审查。
