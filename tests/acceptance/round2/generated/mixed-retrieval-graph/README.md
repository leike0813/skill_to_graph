# mixed-retrieval 图

源名和 graph ID 为 mixed-retrieval，Python 包为 skill_graph。应用按目录分发并保留完整
source/mixed-retrieval/ 快照。固定阶段是 collect、validate、retrieve、confirm、write；
retrieve 是唯一的自主区段，由模型选键并按语义判断证据是否充分。

业务输入为 question、catalog，output_dir 在写前确定。validate 检查 question 非空，catalog
是 UTF-8 JSON 对象且值全为字符串；失败返回 error，且不调用 lookup。retrieve 只向模型提供
局部检索职责、问题、可用键和 lookup 工具，不注入完整源指令，也不预先提供证据正文。模型的
结构化输出为 sufficient/insufficient、report、used_keys。lookup 故障停止为 failed，不重试；
证据不足返回 insufficient 且不写文件。confirm 收到 JSON true 后，write 以排他模式创建
report.md；其他回复为 cancelled，不创建目录。

    from skill_graph.graph import make_graph
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command

    graph = make_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "mixed-1"}}
    pending = graph.invoke({"question": "Explain control and stored progress",
                            "catalog": "/path/catalog.json",
                            "output_dir": "/path/out"}, config)
    result = graph.invoke(Command(resume=True), config)

运行环境显式提供 MODEL_PROVIDER、MODEL_ID、MODEL_BASE_URL、MODEL_API_KEY_ENV（值为密钥
环境变量名）和可选的 MODEL_OPTIONS，并安装对应 provider 的 LangChain 集成。图不绑定默认
供应商，模型调用设置 max_retries=0。凭据只从环境读取。

CLI 在应用根用 langgraph.json 的 cli_graph(config) 加载，向已有 Agent Server 的
/threads/{thread_id}/runs/wait 提交 assistant_id、input，恢复用 command.resume。两个入口
共享 make_graph。服务存储由运行环境提供；InMemorySaver 仅用于同进程演示。

确认前不创建输出目录。排他写入保护已有文件；进程崩溃后仍可能留下部分文件，图不自动重试、
换路径或补偿。模型输出的语义充分性与证据引用须依据源契约人工复核。

