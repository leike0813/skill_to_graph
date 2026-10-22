# fixed-file 图

源名和 graph ID 为 `fixed-file`，Python 包名为 `skill_graph`。应用目录分发：运行时须保留本目录的 `source/fixed-file/`，不承诺单独安装 wheel 后包含源资源。无模型或外部服务依赖；本地 Python、文件读写权限和 langgraph 是运行条件。

业务输入 `source_csv`、`output_dir` 直接作为图输入。先执行携带的只读 render 脚本，返回行数、总数和计划内容，随后暂停。恢复值必须是 JSON true 才写入；其他值取消。最终状态的 status、rows、total、path/error 是业务结果；content、approved 是流程字段。实际文件为 output_dir/summary.txt。文件已有时报错、不覆盖。

```python
from skill_graph.graph import make_graph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

graph = make_graph(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "sample"}}
pending = graph.invoke({"source_csv": "/path/input.csv", "output_dir": "/path/out"}, config)
result = graph.invoke(Command(resume=True), config)
```

Python 进程需把本应用目录加入 sys.path，或安装该代码包并保留资源目录布局。任务路径相对调用工作目录；源资源相对 graph.py 定位。持久化后端由调用方提供，InMemorySaver 只用于同进程演示。

CLI 在应用根目录以 `langgraph dev` 加载 `langgraph.json`（启动服务需相应授权），单参数入口 `cli_graph(config)` 转调同一 `make_graph`。调用已配置服务器的 `/threads` 建立 thread，然后向 `/threads/{id}/runs/wait` 提交 `{"assistant_id":"fixed-file","input":{"source_csv":"...","output_dir":"..."}}`；同 thread 恢复用 `{"assistant_id":"fixed-file","command":{"resume":true}}`。CLI 工厂不配置存储，使用服务注入设施。

确认与写入分为两个节点，避免因确认恢复而重写。文件以 exclusive 模式创建，崩溃后不能保证成功返回或自动恢复；可能留下部分文件，不自动重试或补偿。静态检查、运行覆盖及未验项见仓库验收记录，不属于图运行依赖。
