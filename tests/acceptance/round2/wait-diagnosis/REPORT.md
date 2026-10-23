# wait-what 对照核实

2026-10-23

**这次没有找到“转换丢失源约束，导致时序错误”的证据。相同模型直接执行源指令时，也稳定出现了相同类型的扩写。** 因而之前仅凭转换图的错误输出就把它当成转换缺陷，归因依据不足。

最有说服力的是同环境对照：使用 MiniMax-M3.1-Flash 中国区端点、相同 high effort / adaptive thinking、相同会话角色、相同文件工具和工作目录。源组只注入原始 SKILL.md 正文；图组执行当前生成图。源组通过替换 agent 的提示装配，保留生成适配器创建的模型与工具闭包，不修改源包或图代码。首次模型请求的实际 system、user、assistant 消息保存在各份记录的 first_request 中。

| 场景 | 源指令 | 转换图 | 可以判断什么 |
| --- | --- | --- | --- |
| 原始会话，各三次 | 3/3 增加保存检查点的时序或其他未给出的步骤 | 3/3 出现批准后等待、随后保存等扩写 | 错误不是转换后才出现 |
| 开头改为一般流程提问，保留原测试目录，各两次 | 仍扩写；但两次都读了 input.json，其中含原始提问 | 仍扩写；未读 input.json | 源组受原测试文件干扰，不能据此单独判断提问的影响 |
| 一般流程提问，工作目录只放术语表，各两次 | 两次仍扩写出完整步骤和操作建议 | 一次较忠实，一次新增保存检查点的时点 | 去掉“批准后”的提问和 input.json，也不能稳定消除扩写 |
| omp 在临时目录直接读源包与术语表，一次 | 仍补出保存步骤、崩溃时点和修复建议 | 不适用 | 另一 harness 的交叉证据；不是严格同请求实验 |

这里“3/3”指本次三份人工复核结果，不是对模型总体错误率的估计，也不表示三份都用了完全相同的错误句子。

原话只说明：图在确认点暂停；一个已保存的检查点把回复关联到暂停执行；恢复后下游节点生成报告；崩溃后外部写入没有 exactly-once 保证。原话没有说明批准时才暂停，也没有给出保存检查点的具体时点和去重操作方案。

具体例子：

- [源指令第 3 次](source-3.json)写了“The system saves a Checkpoint when you approve”，并要求用户检查重复报告。
- [转换图第 1 次](current-1.json)写了“After you approve the task, the Graph waits at a confirmation boundary”。它的 first_request 同时证明原始 Skill 正文、完整原会话和正确的待重述原话都在实际模型输入中。
- [隔离的源组第 1 次](source-neutral-isolated-1.json)补出了九步流程，还建议“Add a Checkpoint after the Node that writes the file. Then a stop after the write is safe”。这些步骤与安全性判断均不在待重述原话中。
- [隔离 omp 结果](omp-isolated-result.json)同样给出保存检查点的步骤和“How you can remove that limit”。工具记录显示它读取了临时副本内的源 Skill、术语表及 agents/openai.yaml，没有读取旧的生成图或验收输出。

对照支持的结论是：**指定模型在这个重述任务中会把上下文扩展成自己理解的工作流程；转换不是该错误出现的必要条件。** 当前样本不足以证明两种执行方式完全等价，也不能排除转换提示影响输出概率。没有证据把所有问题简单归结为 LangGraph、某个中间件或源 Skill 的确定性缺陷。

另有一个可以直接确认的转换问题：当前图提示增加了“Write short paragraphs without headings or lists”。源 Skill 没有限制标题和列表。这属于转换层额外收窄格式，应在修改生成图时去掉；但同环境源组本身也出现时序扩写，不能把格式限制当作已证实的时序错误根因。本次仅核实，未改生成图，也未继续堆叠纠错提示。

第一个 omp 探针在仓库测试目录执行，实际读到了项目说明、既有生成图及旧结果，已在 [omp-contaminated.json](omp-contaminated.json) 标为无效对照。随后在临时目录重跑，使用只读工具及最小 system prompt。omp 的会话以带角色标记的用户数据传入，其基础提示和工具定义也不同，所以它只作为交叉证据；严格比较依赖前面的同环境实验。没有声称已排除 omp 所有全局配置的影响。

以下是本次实际执行的同环境实验命令。探针拒绝覆盖已有记录，不能直接覆盖重跑；再次实验须为记录选择新命名。

```sh
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/wait-diagnosis/probe.py source --repetitions 3
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/wait-diagnosis/probe.py current --repetitions 3
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/wait-diagnosis/probe.py source --repetitions 2 --neutral-context --isolated
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/wait-diagnosis/probe.py current --repetitions 2 --neutral-context --isolated
```

探针只自动检查输入角色、源指令与历史是否完整传入，语义判断来自逐条阅读输出，没有用关键词、字符比例或整段快照代替保真判断。所有 14 次同环境调用和隔离 omp 调用均完成，没有模型 fallback 或业务自动重试。没有安装依赖、启动服务或修改发布包；新证据不使原先不合格的输出自动变成通过。
