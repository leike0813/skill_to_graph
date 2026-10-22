# literature-analysis 图应用

完整源包在 source/literature-analysis/，新增代码在 skill_graph/。按整个目录分发和搬移；不宣称 wheel 单独包含源资源。源名和 graph ID 为 literature-analysis，Python 包为 skill_graph。

输入沿用源业务字段 source_path、language、score_only（默认false）、identifier（可选）。运行上下文通过 config.configurable.working_dir 指定独立工作目录，不新增业务输入；source_path为唯一论文内容来源。最终业务JSON位于返回状态的 result，由源runtime渲染，六份公开产物名称、路径和错误约定保持源要求。

图的固定阶段为 init_runtime→计划→digest→评分→references→citation，正常citation提交会完成最终渲染；finalize仅用于源规定的恢复。score_only按源分支跳过不适用阶段。SQLite是过程真源，图状态仅携带运行位置和当前结果，恢复时先查询既有DB，不重初始化。

语义阶段采用create_agent处理源的语义判断，只有run_runtime工具可调用当前阶段并写DB。预切batch交给独立同模型agent，只提供读取自己batch的工具，不提供DB/网络/全局闭包能力；主agent合并正式payload后唯一提交。参考/元数据/引文语义不以规则脚本填充。源的确定性脚本完整保留并真实执行。

外部条件：文件读写权限、可调用Python及源脚本依赖jinja2、jsonschema；LangGraph/LangChain；支持工具调用和充分上下文的模型及provider集成；源允许的可选公开bibliography网络。配置：MODEL_PROVIDER、MODEL_ID、MODEL_BASE_URL、MODEL_API_KEY_ENV（密钥变量名）、MODEL_OPTIONS（JSON客户端选项）；RUNTIME_PYTHON为解释器命令，例如 `uv run --project /home/joshua/.ar --locked --no-sync -- python -B`。凭据只从运行环境取得，无默认供应商。

Python导入make_graph，invoke(payload, {"configurable":{"working_dir":"/absolute/run","model_label":"configured-model"},"recursion_limit":300})，业务结果取state["result"]并按源stdout JSON输出。CLI在本应用根以langgraph dev读取langgraph.json，已有服务/runs/wait传assistant_id=literature-analysis、input及相同config；启动服务需要相应授权。

不增加用户确认、自动图级重试、降级或补偿。模型/工具执行异常向调用方传播，不冒充成功；源runtime的payload校验错误可按其原定义修复。迭代受运行资源限制时报告未完成，DB和事件记录保留用于恢复。SQLite事务不保证任意故障下外部API只调用一次。测试环境、论文、omp对照工具和验收记录不随本应用分发。

源约束与实现对应关系如下。源码位置均相对本应用；源依据在携带的 SKILL.md 对应条目中。

| 源约束 | 实现位置 | 当前验证 |
| --- | --- | --- |
| 输入输出硬契约：四项业务输入、绝对产物路径、runtime 渲染结果 | `initialize`、`outcome`；调用方提取 `result` | 完整分析输入实际执行，六份产物及最终 JSON 核对通过；score_only 未运行 |
| 阶段取 DB 真源，prepare/submit 按 next_action 推进 | `initialize`、`stage_node`、`make_graph` | 计划到引文完整执行；两次启动失败后从 DB 恢复 |
| LLM 做语义判断，脚本仅做确定性工作；评分字段锁定 | 阶段 `create_agent`、`runtime`、`fill_scoring_draft` | 真实模型提交；源脚本校验、渲染及错误修复有记录 |
| runtime 预切批次、子代理局部读取、主代理唯一提交 | `delegate_batches`、`run_runtime` | 五个实际批次主键覆盖完整且无重复，metadata 无本地证据字段曾被拒绝 |
| language 控制 digest 与 citation report | 初始化参数及阶段提示 | **未满足**：语言实际值没有明确传入各阶段和批次，引文报告大段英文 |
| 源失败与修复规则 | `run_runtime`、状态恢复 | 已覆盖部分 payload 修复；阶段推进后禁止再次提交妨碍后续修正，保真尚未完成 |
| 资源随应用携带、Python/CLI 共用入口 | `SOURCE`、`langgraph.json`、本说明 | 完整快照及 Python 实际运行通过；本样例 CLI 服务和搬移运行未验证 |

本应用为尚未通过完整保真验收的测试产物。真实论文测试还发现摘要把 base dropout 写成 0.3，而论文明确为 0.1。最终文件存在及 JSON 校验通过不能代表语言与事实正确；需要修正并重新验收后才能宣称保真完成。
