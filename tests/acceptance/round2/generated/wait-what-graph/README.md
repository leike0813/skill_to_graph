# wait-what 图

源名和 graph ID 为 wait-what，Python 包为 skill_graph。源没有可独立固定的阶段，因此图直接
导出自主 agent，并在运行时保留源 SKILL.md 的完整指令。源平台字段
disable-model-invocation: true 表示只在用户显式调用时运行，不作自动路由。

业务输入是对话历史 messages；待重述内容是最近一条用户消息之前的 assistant 消息。任务工作
目录通过 config.configurable.workdir 提供。read_file 和 list_files 接受相对工作目录的路径或
绝对路径，模型据此读取 GLOSSARY.md，存在多个术语表时先读 GLOSSARY-MAP.md 选择正确的术语表；
文件读权限由运行环境提供。
输出从最后一条 assistant 消息的 content 提取，不含工具消息。源要求的 ASD-STE100 简化英语
和术语须按正文人工复核。

    from skill_graph.graph import make_graph

    workspace = {"configurable": {"workdir": "/path/to/task"}}
    graph = make_graph(workspace)
    result = graph.invoke({"messages": conversation}, workspace)
    reply = result["messages"][-1].content

运行环境显式提供 MODEL_PROVIDER、MODEL_ID、MODEL_BASE_URL、MODEL_API_KEY_ENV（值为密钥
环境变量名）和可选的 MODEL_OPTIONS，并安装对应 provider 的 LangChain 集成。图不绑定默认
供应商，模型调用设置 max_retries=0。思考强度等模型选项由环境通过 MODEL_OPTIONS 显式给出，
图不内置默认值。凭据只从环境读取。

CLI 在应用根用 langgraph.json 的 make_graph 工厂加载，向 /runs/wait 提交
{"assistant_id":"wait-what","input":{"messages":[...]},
"config":{"configurable":{"workdir":"/path/to/task"}}}。服务存储和模型连接由运行环境提供。

本应用按目录分发，完整 source/wait-what/ 快照随目录保留。没有源要求的文件写入或人工确认，
图不增加这些步骤，也不添加重试、降级或补偿。

