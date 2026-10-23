# fixed-file 图

源名和 graph ID 为 fixed-file，Python 包为 skill_graph。应用按目录分发，运行时保留
source/fixed-file/ 完整快照；源脚本和模板从该快照读取。无模型依赖，需要 Python 3.11+、
文件读写权限和 langgraph。

业务输入是 source_csv 与 output_dir。缺失时图暂停询问，不猜路径。图先调用源包
scripts/render.py（该校验并计算，不写文件），再暂停显示 rows、total 和目标路径。只有恢复值
为 JSON true 才创建目录并以排他模式写入 summary.txt；其他值返回 cancelled。
成功返回 status=ok、rows、total、path；失败返回 status=error 和结构化 error。
已有文件不覆盖，脚本或写入失败不重试。

    from skill_graph.graph import make_graph
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command

    graph = make_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "fixed-file-1"}}
    pending = graph.invoke({"source_csv": "/path/input.csv", "output_dir": "/path/out"}, config)
    result = graph.invoke(Command(resume=True), config)

Python 进程须将应用根加入 sys.path。CLI 由 langgraph.json 的 cli_graph(config) 入口加载；
在应用根运行 langgraph dev，向 /threads/{thread_id}/runs/wait 提交
{"assistant_id":"fixed-file","input":{...}}，恢复提交 {"command":{"resume":true}}。
两个入口共享 make_graph。服务存储由运行环境提供；InMemorySaver 只用于同进程演示。

写入使用排他创建保护已有文件。进程在创建文件后崩溃时可能留下部分内容，图不自动重试或补偿。
