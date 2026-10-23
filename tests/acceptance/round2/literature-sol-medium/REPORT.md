# literature-analysis：gpt-6.1-sol / medium

后续状态：用户要求续跑后，图已从摘要阶段完成，16 项结构检查通过，详见 [续跑报告](resume-1/REPORT.md)。下文保留首次运行的结论和证据。

2026-10-23

**本轮不能判定完整验收通过。** 图在摘要阶段因本地 Responses 端点的 502 停止；omp 从头完成全部阶段，六份产物及最终 JSON 的结构检查通过，但额外调用了本次任务范围外的 `report_issue` 工具。两类问题分别记录，不能用 omp 的成功产物补成图的成功。

## 运行范围与结果

本轮复用现有 round2 literature-analysis 图及其完整源快照，没有重新转换或修改图。两组使用同一份《Attention Is All You Need》Markdown，`language=zh-CN`、`score_only=false`、`identifier=arXiv:1706.03762`，从独立空 DB 开始；不读取旧分析 payload、产物或 DB。预先确定的范围见 [CONTRACTS.md](CONTRACTS.md)。

| 组别 | 模型与思考强度 | 用时 | 实际结果 |
| --- | --- | --- | --- |
| 图 Python 入口 | `gpt-6.1-sol` / medium，本地 Responses | 264.4 秒（4 分 24 秒） | 计划已提交，摘要模型调用收到 502；DB 停在 `stage_3_digest`，无最终六份产物 |
| omp 源执行 | `opencodex-hub/gpt-6.1-sol` / medium | 943.9 秒（15 分 44 秒） | `stage_8_completed`，六份产物，最终裸 JSON 与 runtime 镜像一致；16 项结构检查通过 |

两组 DB 的输入 hash 相同：`sha256:84a6c55073f13d094b43394a293aa7994feef2cb594135d051017a2eb3eaed1d`。图的 provenance 模型为 `gpt-6.1-sol`，omp 为 `opencodex-hub/gpt-6.1-sol`；不将路由名不同解释为模型替换。

## 模型与传输证据

图的八个实际请求都为 POST `https://192.168.13.111:10100/v1/responses`，请求 model=`gpt-6.1-sol`、reasoning.effort=`medium`、store=false。前七个 HTTP 200，第八个 HTTP 502：

```text
upstream SSE response failed before a valid terminal response
```

失败类型为 `OpenAIAPIError` / `upstream_server_error`，见 [graph-result.json](graph-result.json)。这是模型传输未完整结束，不能归为源 payload 校验失败，也不能认为摘要已经完成。图按既有失败策略停止，未自动重试、续跑或切换模型；现有 DB 保留。

TLS 使用现有 `NODE_EXTRA_CA_CERTS` 证书包，凭据复用 `OPENCODEX_API_AUTH_TOKEN`，未关闭证书验证或保存令牌。图源 runtime 使用共享 uv 环境，模型运行使用既有工作区外验收环境；本轮未安装依赖。

omp 最终消息元数据为 provider=`opencodex-hub`、model=`gpt-6.1-sol`、api=`openai-responses`。主执行及五个实际批次代理的会话均记录 thinking=`medium`，均使用同一模型，见 [session-audit.json](session-audit.json)。本轮未拦截 omp 的 HTTP 请求体，会话档位不等同于线上 reasoning 字段的抓包证明。

## omp 产物与结构检查

- [中文摘要](control/artifacts/digest.md)
- [中文引文报告](control/artifacts/citation_analysis.md)及 [引文 JSON](control/artifacts/citation_analysis.json)
- [参考文献](control/artifacts/references.json)
- [论文评分](control/artifacts/literature_score.json)
- [匹配元数据](control/artifacts/literature_matching_metadata.json)

[comparison.json](comparison.json) 复用项目原有只读检查函数。omp 的 16 项检查全部通过：输出 schema、成功态、DB provenance 与镜像、最终裸 JSON、六份绝对路径产物、引文 Markdown 与 JSON 一致、语言元数据、参考及引文 render context schema、matching metadata schema。另核对评分包含六个维度。

omp 保留 40 条参考文献、21 条引文条目，范围为引言与背景第 25–44 行。评分为 84.0，把握为 0.92，把握调整后为 77.3；这些是本次模型结果，不要求与旧模型得分相同。warning 为 `reference_pattern_ambiguous: 40 entries`；源 runtime 错误表为空。

图组的结构比较结果为 `incomplete`，并非“0 项失败所以通过”；未生成最终结果镜像，正式完成检查无可用判据。

## 行为与内容复核

**批次边界。** 本轮 runtime 只要求 5 条 reference core 与 5 条 metadata evidence 进行人工语义审核，各形成一个 batch；不能按旧轮次固定要求四批。引文为 10、10、1 三批。五份 draft 的主键集合与分配批次一致且无重复，见 [batch-audit.json](batch-audit.json)。五个子代理实际只使用 read/write，读取自身批次及其行片段，写对应 draft；未发现其读取别的 batch、DB、原论文，或使用网络/执行 runtime。主执行者合并并正式提交。

**额外工具副作用。** omp 主执行在处理 task 参数问题时调用了 `write`，目标为 `xd://report_issue`，内容是报告 `sourceSession` 和 `model` 参数与 task 接口不一致。日志显示该路径被解释为 `xdev.tool=report_issue`、`mode=execute`，返回 “Noted, thanks!”。这不是本组目录内的普通文件写入，也不是源 Skill 的 bibliography 操作，超出本次授权的任务范围；不据产物成功将完整行为验收判为通过。记录见 [session-audit.json](session-audit.json) 的主会话工具调用及 [omp-collected.json](omp-collected.json)。未采取后续工具调用处理该报告，也未假定可以撤回。

**中文与事实。** 摘要及引文解释、总结、时间线正文为中文，作者、题名与原文引句保留原语言。代表性事实复核确认：英德 big 28.4 BLEU、WSJ-only 91.3 与半监督 92.7、base/big 训练时长和参数规模、英法摘要/表 2 的 41.8 与正文 6.1 的 41.0 差异得到区分。没有把训练并行解释为并行生成，也未声称所有句法分析设置最优。

摘要的正则化段没有展开 base/big 及英法 big 的各项 dropout 数值，因此这份摘要不能作为这些细节均已覆盖的证据；未发现把缺失细节写成相反数值。引文逐项解释有上下文限定，Neural GPU [17] 未再与减少顺序计算的卷积模型族混同，未复现旧报告中的“研究已进入饱和状态”推断。

仍有表达需改善：中期时间线叙述着重强调“RNN 编码器—解码器、序列到序列学习和对齐式注意力确立神经翻译主线”，但其中直接对应的若干 2014/2015 文献实际被 runtime 划到早期。中期叙述与当前桶内文献贴合不足，应进一步按桶内证据复核。此次未正式提交语义修正，保留原始产物；代表性人工审阅不能保证每句自然语言判断均正确。

## 记录器问题与复现

omp 进程实际退出 0，最终回复正确；采集器汇总历史 tool calls 时误将字符串内容块当作对象，抛出 AttributeError。原始 [omp-result.json](omp-result.json) 保留该采集失败；修正本轮采集器的类型处理后，从原始 JSONL 重新提取出 [omp-collected.json](omp-collected.json)，没有再次调用模型、修改最终回复或重跑 runtime。`observed-final-response.txt` 已与原始日志和结果镜像核对一致。

结构检查需要 jsonschema，模型验收环境没有该包；改用已具备依赖的共享 uv 环境执行检查成功，未安装依赖或更改环境。

```sh
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/literature-sol-medium/run.py graph
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/literature-sol-medium/run.py omp
uv run --project /home/joshua/.ar --locked --no-sync -- python -B tests/acceptance/round2/literature-sol-medium/check.py
```

所有运行目录和结果文件均独立创建，重跑须使用新的目录，不能覆盖本轮证据。DB 与运行缓存留在本机并被既有 Git 规则忽略；omp 完整日志及会话保存在 `omp-process.json` 列出的 `/tmp` 路径。仓库保存公开产物和精简审计，不能从新检出恢复本轮 DB。

未运行 CLI 服务、搬移、其他输入格式、score-only 或生产崩溃恢复。现有图与发布 Skill、旧运行记录均未修改；未提交或归档。本轮结论是“图遇端点失败，omp 完成产物但存在任务外副作用”，不是两组完整保真通过。
