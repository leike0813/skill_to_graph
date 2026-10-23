# 第二轮验收报告

2026-10-23

**本轮按已声明的样本和模型配置验收通过，任务完成 7/7。** 论文图已完成真实运行和正式内容修正；gpt-6.1-sol 对照中，wait-what 的图与 omp 各三次均未复现此前的时序错误。用户审阅后要求收尾，并明确不再复验；已删除源未要求的标题和列表限制，这次提示清理未重跑测试或模型调用。旧运行记录保持原样，不作为清理后版本的新执行证据。

通过结论限于本报告的代表性范围：论文使用 MiniMax-M3.1-Flash，wait-what 的最新语义验收使用 gpt-6.1-sol、medium。MiniMax 重述的失败继续保留为该配置的已知表现，不将不同模型的结果合并成“所有配置均通过”。

本轮的职责拆分已经落实：固定顺序由图控制，论文各阶段使用局部指令，语言从 DB 传到阶段和批次。没有再让每个论文阶段读取完整 SKILL.md。`wait-what` 本身是一个自主重述任务，因此保留完整源指令。后者的实际问题表明，完整保留指令和补充提示仍不足以保证模型每次忠实重述。

后续[源指令与转换图的同环境核实](wait-diagnosis/REPORT.md)表明：源指令组三次也都增加了未给出的检查点步骤；隔离 omp 执行源 Skill 同样扩写。实际模型输入未丢失原指令或待重述原话。因此，当前不能把时序错误归因于转换。另确认转换提示额外限制了标题和列表，这是独立的格式收窄问题；核实阶段未修改生成图，也未因双方都出错而将验收改为通过。

随后按用户指定配置完成[gpt-6.1-sol 新一轮对照](wait-sol/REPORT.md)：图实际请求为指定私有端点的 Responses API、medium；omp 为 openai-codex/gpt-6.1-sol、medium。两组三次均保留了等待、恢复、报告生成和外部写入限制的含义。图代码及提示未改，这支持模型或配置影响了此前表现；没有据三次成功外推任意输入均正确。

| 样例 | 本轮实际结果 | 验收判断 |
| --- | --- | --- |
| 固定文件 | Python 六种正常/失败场景、缺输入询问、拒绝不写、CLI 暂停恢复通过；应用搬移并使临时原路径不可用后，六场景仍通过 | 所测范围通过 |
| 混合检索 | 真实模型查阅本地证据；充分、拒绝、不足三分支运行；CLI 确认后写出与提案一致的报告。工具故障和已有文件保护另由受控场景验证 | 最后深度样本的核心结论与证据一致；更早版本存在扩写和引用键不一致，保留失败记录，不承诺任意生成都正确 |
| wait-what | 真实读取术语表，另有 MAP 选择证据；MiniMax 出现时序错误，最新 gpt-6.1-sol 图与 omp 各三次内容复核通过 | 本次指定配置的重述场景通过；额外格式限制已删除，按用户要求不再复验 |
| literature-analysis | 原 MiniMax 模型完成计划、摘要、评分、参考与引文，生成六份公开产物；40 条参考、21 条引文；16 项结构及一致性检查通过 | 中文正文和关键数值已有改善；引文解释的进一步语义修正单独记录，结构通过不等于全部语义通过 |

最值得看的新产物是[中文论文摘要](literature-run/artifacts/digest.md)和[中文引文报告](literature-run/artifacts/citation_analysis.md)。摘要正确区分 WSJ-only 的 **91.3** 与半监督的 **92.7**，base dropout 的 **0.1** 与 big 常规配置的 **0.3**，并说明英法 big 使用 **0.1**。它也保留了论文自身的矛盾：摘要及表 2 是 **41.8**，6.1 节正文是 **41.0**。这些数值依据原始论文及本轮复用的同一份 MinerU Markdown，未把来源差异归咎于转换。

引文的解释、总体总结和时间线现在使用中文，参考题名和原文引句保留原语言。首次完成后的复核仍发现“研究已进入饱和状态”等超出 snippets 的判断，随后通过[真实模型的正式修正](results/literature-semantic-repair.json)移除；Neural GPU [17] 的对照作用也与减少顺序计算的卷积模型族重新区分。初始产物另存于 [literature-before-review/](literature-before-review/)，没有手改最终文件。修正后 17 项结构与返回值一致性检查通过，直接验证了首次完成后仍能正式重交和重渲染。这个结果覆盖已列问题和代表性内容复核，不代表全部自然语言判断已有自动保证。

运行中修复了一个实际工具错误：评分工具对数组的说明含糊，模型传入按键组织的对象后抛 TypeError。现在契约明确，错误输入可返回修正，文件在校验完成前保持不变；锁定评分 form 也不能作为写入目标。4 项运行边界测试通过，覆盖语言传递、只读批次、提交后再修正、缺失状态恢复，以及评分输入错误的修正。原有 14 项测试、四图静态检查、发布包隔离检查和 OpenSpec 严格校验通过。发布包没有混入验收环境。

论文运行的配额拒绝和连接超时解除后，继续使用 `minimax-code-cn/MiniMax-M3.1-Flash`、中国区 Anthropic 兼容端点，没有自动供应商切换或 SDK 重试。最初恢复运行在评分处失败；修复后从原 DB 的评分阶段继续，后续约 11 分钟完成。计划、摘要、后续分析均是本轮真实模型生成，没有用首轮正文填充本轮分析。恢复沿用源 DB 的 provenance，因此时间字段由源 runtime 返回，不另造“重新生成时间”。后续仅 wait-what 按用户指定切换到 gpt-6.1-sol，配置和证据另列。

参考查询服务 Semantic Scholar 返回过 429，源 runtime 按其本地审核路径继续，并在最终 warnings 中保留。它与先前 MiniMax 额度错误是两个不同服务的问题。

临时 CLI 服务已关闭，[端口检查](results/service-shutdown-current.json)确认 localhost:20288 不再响应。本 change 未提交、未归档，首轮资产和失败证据保留。

<details>
<summary>证据与检查范围</summary>

- [本轮真实完整论文结果](results/literature-attempt4.json)、[初始结构检查](results/literature-contracts.json)、[修正后 17 项检查](results/literature-contracts-repaired.json)、[完整阶段与批次记录](literature-run/graph-events.jsonl)。
- [真实混合及重述样本](results/small-reviewed-live.json)、[小样本 CLI](results/small-cli-reviewed.json)、[MiniMax 重述 Python](results/wait-concise-live.json)及[MiniMax 重述 CLI](results/wait-cli-current.json)。后两份均保留时序违约；新的通过依据见 [gpt-6.1-sol 三次图与三次 omp 对照](wait-sol/REPORT.md)。
- [多术语表真实选择](results/wait-glossary-map-live.json)、[固定图搬移](results/fixed-relocated-resumed.json)、[四图及本地场景](results/small-current-deterministic.json)。
- [初次批次审计](results/batch-scope-audit.json)及[含修正的批次审计](results/batch-scope-audit-repaired.json)：初次 11 个、修正新增 3 个批次均覆盖分配的主键集合，语言为 zh-CN；子代理可用工具仅为读取自己批次的闭包。这是工具能力限制，不是 OS 沙箱或完整事实证明。批次响应常带 JSON 围栏及说明，主执行者提取合并后交源 runtime 校验。
- [CLI 论文完成态重渲染](results/literature-cli-completed.json)和[修正后再次调用](results/literature-cli-repaired.json)证明另一入口可加载、调用并重渲染已有成功 DB，**不是另一轮从头模型分析**；[缺失输入路径](results/literature-cli-invalid.json)覆盖源错误结果。
- [发布包隔离](results/release-isolation-current.json)。测试环境在工作区外；gpt-6.1-sol 探针补充的 OpenAI 集成依赖见 [wait-sol/requirements.txt](wait-sol/requirements.txt)，不随产物分发。
- [评分失败](results/literature-attempt3.json)、[最初额度失败](results/literature-attempt1.json)、[连接超时](results/literature-attempt2.json)均保留；`small-resumed-live.json`、`small-grounded-live.json` 及旧 CLI 记录保留逐次发现的扩写。

复核命令和环境见 [README.md](README.md)。源约束去向见 [小样本映射](SMALL-CONTRACTS.md)及[论文映射](generated/literature-analysis-graph/CONTRACTS.md)。首轮生成图、结果、论文输入及源快照未修改。

未验证：ASD-STE100 全词典合规、全部论文输入格式、score-only 的新真实模型运行、生产环境崩溃恢复、外部副作用 exactly-once、全部应用搬移、Docker 或托管部署，以及本次删除格式限制后的再运行。模型语义有不稳定性；通过结论不外推任意 Skill。论文没有重跑新的 omp 对照，wait-what 已取得新模型的 omp 对照；首轮对照的违约记录仍有效，不能作为本轮正确答案。

</details>
