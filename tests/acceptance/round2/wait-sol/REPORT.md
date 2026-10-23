# gpt-6.1-sol 重述对照

2026-10-23

**换为用户指定的模型配置后，转换图与 omp 源执行各三次，均没有复现此前的时序扩写。** 六份输出都保留了“先暂停等待确认，恢复后生成报告”和“外部写入不保证仅一次”的含义。图、源 Skill、原始会话和术语表均未修改，MiniMax 旧记录也保留。

| 组别 | 实际配置 | 本轮结论 |
| --- | --- | --- |
| 转换图 | `gpt-6.1-sol`，`medium`，`https://192.168.13.111:10100/v1/responses`；凭据来自 `OPENCODEX_API_AUTH_TOKEN` | 三次均符合本次重述内容要求 |
| omp 执行源 Skill | `openai-codex/gpt-6.1-sol`，`--thinking medium`；使用现有 provider 配置 | 三次均符合本次重述内容要求 |

图的传输记录确认每个实际请求都是 POST `/v1/responses`，请求中的 `model` 为 `gpt-6.1-sol`、`reasoning.effort` 为 `medium`。没有使用 Chat Completions 或偷偷换回 MiniMax。HTTPS 使用机器现有的 `NODE_EXTRA_CA_CERTS` 证书包完成校验，未关闭证书验证，未保存或输出令牌。omp 的最终消息元数据分别确认为 provider `openai-codex`、model `gpt-6.1-sol`、api `openai-codex-responses`。

两组的工作目录只放本任务所需材料，避免读取旧结果。图目录只有术语表；omp 目录还包含完整源包副本。原始会话内容保持不变，其中仍包含“How will this task continue after I approve it?”。图以原生对话角色传入，omp 以带角色标记的数据传入；这一差异与上一轮隔离 omp 对照一致。

人工逐条复核的结果：

- [图第 2 次](graph-2.json)、[第 3 次](graph-3.json)、[第 4 次](graph-4.json)都把 Checkpoint 描述为已有的状态记录，不声称批准时才等待或此时才保存。都实际调用工具读取了 GLOSSARY.md，使用 Graph、Node、Checkpoint，并以简短英语重述。
- [omp 第 1 次](omp-1.json)、[第 2 次](omp-2.json)、[第 3 次](omp-3.json)先说明图已暂停或正在等待批准，再说明批准后继续。没有让用户额外检查、删除重复报告，也没有声称任何去重方案已经落实。对崩溃后写入的描述保留了“can/could”的可能性。
- 六份结果都保留了外部文件写入没有 exactly-once 保证的限制，没有把它变成一个已经解决的问题。用词和展开方式不同，不以逐字一致作为判据。

第 1 份图调用的[原始记录](graph-1.json)也有正确的业务输出，但当时传输记录器拦截了旧 HTTP 库，而新 OpenAI SDK 使用 `httpx2`，导致请求证据断言失败。这是记录器的问题，未作为业务失败或通过计数。修正记录器后以新编号取得三份完整证据，没有覆盖该记录，也没有对模型错误做自动重试。

结果支持“此前指定模型或配置在这个任务上的表现不佳”这一解释，没有支持“转换丢掉了原话或源指令”的证据。它仍不是严格的模型能力单变量实验：端点、协议及思考强度也按用户要求一起更换；omp 与图的基础上下文及工具定义也不同。三次成功不能外推为所有输入或所有模型均会成功，ASD-STE100 仅做人工简化英语复核，未做词典级认证。

上述对照执行时未修改图提示，因此当时仍有额外禁止标题和列表的问题，详见[前一轮核实](../wait-diagnosis/REPORT.md)。用户审阅后要求收尾并明确不再复验；现已删除该限制，未重跑测试或模型调用。本报告的原始请求与输出保持原样，证明的是清理前版本的实际行为，清理后的接受结论及范围见[第二轮总报告](../REPORT.md)。

本轮在此前授权的工作区外环境补充 `langchain-openai 1.7.2`、`openai 3.37.0` 及其依赖 `regex 2026.9.29`、`tiktoken 0.14.0`。`langchain 1.4.7`、`langchain-core 1.6.13`、`langgraph 1.2.16` 保持原版本。声明见 [requirements.txt](requirements.txt)。没有修改共享 Python 环境，也没有启动服务。

本次执行命令如下。记录文件拒绝覆盖；重跑应选择新的起始编号：

```sh
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/wait-sol/run.py graph --repetitions 3 --start-number 2
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/wait-sol/run.py omp --repetitions 3
```

配置与探针是仓库验收资产，不随发布 Skill 或图分发。
