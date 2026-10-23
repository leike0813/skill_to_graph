# 图续跑结果

2026-10-23

**图已从原 DB 成功续跑完成。** 本次耗时 708.8 秒（11 分 49 秒），模型仍为本地 Responses 的 `gpt-6.1-sol`、medium。39 个请求均 HTTP 200，模型和 reasoning.effort 已逐请求核对；未再出现 502，未切换模型或开启 SDK 自动重试。

## 恢复范围

初次运行的 [502 记录](../graph-result.json)、[初次比较](../comparison.json) 和 [原报告](../REPORT.md) 保留。本目录保存续跑前 DB 快照（本机忽略目录）、状态/回执、失败最终回复、事件和请求记录，续跑结果为 [graph-result.json](graph-result.json)。

图入口调用源 runtime 的 `status`，得到 `persist_digest` 后开始摘要；初始化、归一化与计划没有重跑。原 `persist_outline_and_scopes` 回执内容和时间均未变化。恢复为阶段级：中断的模型调用重新执行，不恢复先前 SSE 的 token 流。

执行顺序为摘要→评分→参考审核→引文审核→源 runtime 渲染。未手改 DB、公开产物或结果镜像，也未使用 omp 的正文或评分填充图结果。业务结果中的 generated_at 仍是最初 DB 初始化时间，符合源 provenance，不伪造本次重新初始化。

## 检查与产物

[comparison.json](comparison.json) 记录两组当前状态，图的 16 项结构检查均通过，最终 JSON、镜像、DB provenance、六份绝对路径文件及 schema 一致。DB 为 `stage_8_completed`，两组仍有相同的输入 hash；原计划回执保持不变的断言通过。

- [图中文摘要](../graph-run/artifacts/digest.md)
- [图引文报告](../graph-run/artifacts/citation_analysis.md)
- [图参考文献](../graph-run/artifacts/references.json)
- [图评分](../graph-run/artifacts/literature_score.json)
- [图引文 JSON](../graph-run/artifacts/citation_analysis.json)
- [图匹配元数据](../graph-run/artifacts/literature_matching_metadata.json)

参考文献 40 条，引文 21 条，范围为引言与背景第 25–44 行。评分为 80.0，把握 0.95，把握调整后 76.0；与 omp 的 84.0/0.92/77.3 不同，不以两组分数相同为验收条件。最终 warning 为 `reference_pattern_ambiguous: 40 entries`。

[batch-audit.json](batch-audit.json) 核对每个实际批次 draft 的主键集合与 runtime 分配相同且无重复，日志中的模型均为 `gpt-6.1-sol`、语言均为 `zh-CN`。批次代理由现有图的 `read_batch` 闭包限制读取范围；它不拥有主节点的 DB 写入、文件写入或网络工具。这是图的工具能力边界，不是操作系统沙箱证明。

## 正文复核与结论

摘要与引文解释、全局总结及时间线均为中文，作者、题名和引句按源保留原语言。代表性内容复核确认：

- 区分 WSJ-only 91.3 与半监督 92.7，未将跨训练范式对比夸大为全面领先。
- 保留英德 28.4，以及英法摘要/表 2 的 41.8 与正文 6.1 的 41.0 差异。
- 区分 base dropout 0.1、big 常规 0.3、英法 big 0.1，区分开发集消融与最终测试设置。
- 保留位置编码外推、注意力可视化等结论的推测性质，未将训练并行解释为并行生成。
- 引文按所选片段解释使用作用，未复现将 Neural GPU [17] 混同为卷积并行化例子或“研究已进入饱和”的旧问题。

因此，本次续跑在所列完成、结构及代表性语义检查范围内通过。初次 502 仍是已发生的传输失败，成功续跑不将其抹除，也不证明端点长期稳定。omp 此前完成产物但额外调用 `report_issue` 的越界事实不因图续跑成功而改变；本次没有再次运行 omp。

未验证 CLI、搬移、其他论文/输入格式、score-only、全部评分的唯一正确性、生产恢复或外部动作 exactly-once。没有对所有自然语言判断作逐条独立认证。

执行命令：

```sh
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/literature-sol-medium/resume.py
```

该脚本仅适用于本次摘要阶段的单次恢复，并拒绝覆盖 `resume-1/`。以后若再次中断，应按新的 DB 状态和新记录目录处理，不直接覆盖本次记录。
