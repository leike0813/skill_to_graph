# literature-analysis 图应用

源名与 graph ID 为 `literature-analysis`，Python 包为 `skill_graph`。完整源包在 `source/literature-analysis/`，职责映射见 [CONTRACTS.md](CONTRACTS.md)。本应用按整个目录运行和搬移，不宣称单独 wheel 包含源资源。

输入沿用 `source_path`、`language`、`score_only`（默认 false）、`identifier`（可选）；`config.configurable.working_dir` 提供独立任务目录。返回状态的 `result` 为源 runtime 生成的最终业务 JSON，六份文件由原脚本渲染，结果镜像与最终 JSON 一致。调用方直接序列化 `result`，不要让模型转述。

```python
from skill_graph.graph import make_graph
state = make_graph().invoke(
    {"source_path": "/absolute/paper.md", "language": "zh-CN", "score_only": False},
    {"configurable": {"working_dir": "/absolute/run", "model_label": "configured-model"},
     "recursion_limit": 300},
)
result = state["result"]
```

在应用根使用 `langgraph dev` 读取 `langgraph.json`；服务 `/runs/wait` 接收 `assistant_id=literature-analysis`、相同 input 与 config。CLI 和 Python 共用构图逻辑。服务启动须满足调用环境授权。

外部运行条件：Python 3.11+、LangGraph/LangChain、模型供应商集成（中国区 MiniMax 的 Anthropic 协议需要 `langchain-anthropic`），源 runtime 的 `jinja2`、`jsonschema`，文件读写能力和源允许的可选 bibliography 网络。环境提供 `MODEL_PROVIDER`、`MODEL_ID`、`MODEL_BASE_URL`、`MODEL_API_KEY_ENV`（凭据变量名）、可选 `MODEL_OPTIONS`（JSON）及 `RUNTIME_PYTHON`（源脚本解释器命令）。图读取环境中的凭据，不保存密钥或绑定供应商。

运行顺序由图控制：初始化→计划→摘要→评分→参考审核→引文审核；score-only 由原 runtime 路由直接评分。语义节点只取得本职指令、DB 中实际设置和按需证据；批次代理只有本批次读取工具。只有主代理的当前阶段工具写 DB。初次提交后的同阶段修正保留，最终文件不能手改。初始化发现既有 DB 时从源 status 恢复，已完成时由 finalize 重渲染；这不保证崩溃时外部 API 恰好调用一次。

结构化业务错误映射为源失败 JSON，模型或工具异常由调用方处理为同一失败契约。没有额外的图级重试、补偿或审批。源低质量文献分支的公开命令支持仍需核对，不能绕过公开 CLI 假造完成。未取得的入口及业务证据在仓库报告中分别说明；测试环境和论文输入不属于本应用分发内容。
