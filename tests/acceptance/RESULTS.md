# 项目首版交付与试用报告

2026-10-22

本轮已经完成转换 Skill 的首版实现，并用三个样例生成、运行了 LangGraph 应用。文件处理、用户确认、失败停止等流程已有实际运行证据。自然语言任务的保真验收仍有缺口，因此目前可以开始试用，还不能宣称已经实现了“任意 Skill 都能完全保真转换”。

后续增加了 [literature-analysis 与《Attention Is All You Need》的真实对照测试](literature-analysis-attention/REPORT.md)：同一份 MinerU Markdown 分别由 omp 和转换图执行，均完成六份产物。图的引文报告未遵守中文要求；对照组也有事实错误、最终 JSON 改写和批次越界读取。本轮未关闭完整保真验收的缺口，详细结果见该报告。

交付入口是 [skill-to-graph/SKILL.md](../../skill-to-graph/SKILL.md)。使用时，向执行这个 Skill 的 Agent 提供一个源 Skill 包路径。Agent 会读取包内要求，设计并生成图；两个辅助脚本负责检查源包、完整复制资源，以及检查生成代码和配置。转换中的语义理解仍由 Agent 完成。

生成的应用包含图代码、完整源包副本、依赖声明和运行说明。它应保留源 Skill 的输入输出与行为要求，同时把需要固定的步骤写成明确流程。例如，源要求“确认后才能写文件”，生成图就必须先等待回复，不能提前写完再询问。模型、外部工具和存储由目标运行环境提供，转换器不承诺这些能力在任何机器上都已就绪。

这次用三种任务检验了实现：

| 样例 | 实际做了什么 | 当前结论 |
| --- | --- | --- |
| 固定文件流程 `fixed-file` | 读取 CSV、计算总数、请求确认，再写摘要。还检查了拒绝、文件已存在、数据非法、缺列和源脚本读取失败。 | 所测场景通过。确认前没有创建输出目录；拒绝后不写文件；已有内容没有被覆盖。 |
| 检索后写报告 `mixed-retrieval` | 使用真实 MiniMax 模型选择并读取本地证据，生成带引用的报告，确认后写文件。另测试了拒绝写入和证据不足。 | 这些真实场景通过。继续检索和工具故障后立即停止，另用预设模型回复验证，不能把这部分算作真实模型能力的证明。 |
| 真实 Skill `wait-what` | 提供前文，让图读取术语表，用简单英语重新解释上一条消息。 | 可以运行，也确实读取了术语表；完整保真尚未验收通过。输出对原文有扩写，仍需复核。 |

`wait-what` 的问题需要单独说明。原文说图会在确认点暂停，检查点将回复关联到暂停的任务；一次 CLI 输出写成了“When you approve, the Graph waits at a confirmation point”。这给原文增加了“批准时才等待”的时间关系。Python 输出也补充了批准后保存检查点的步骤。原文不足以支持这些具体时序，因此只能确认它完成了读取和重述，不能把这些扩写当作忠实转换的证据。简化英语目前只做了人工风格审查，没有完成 ASD-STE100 的词典级核对或第三方认证。

运行方式也做了实际检查。三个图都通过 Python 和 `langgraph` CLI 调用过；固定流程和混合流程在暂停后收到了用户回复，并继续执行。固定文件应用还被搬到新目录运行，测试用的临时原包原路径已不可用，图仍能读取随身携带的模板。这里的搬移结论只覆盖该样例和整个应用目录。

辅助脚本及验收记录工具的 14 项自动测试通过，三个生成应用的语法、配置和源包副本检查也通过。OpenSpec 严格校验通过，说明规划文件符合其格式要求。上述检查各有范围，都不能单独证明业务行为完全一致。

首版已经具备交付试用的内容：发布 Skill、辅助脚本、参考资料、样例应用及可追查的测试记录。当前尚待完成的是自然语言样例的保真验收，以及据此作出的整体验收结论。任务清单已将这两项恢复为待完成，当前为 14/16 项；这次报告修订没有修复图的生成逻辑，也没有取得新的运行证据。

用户已决定将当前实现作为首版基线归档。归档中的 5.2、5.4 保持未完成，其保真与整体验收工作移交后续 change `compile-skill-runtime-responsibilities`；归档不代表这些验收已通过。

发布内容在 `skill-to-graph/`。测试样本、生成的样例图和验收记录都留在仓库中，不随转换 Skill 分发；验收环境位于工作区外。临时 CLI 服务已关闭，并确认端口不再响应。

生产环境仍有本轮没有验证的部分：重启后的持久恢复、崩溃时避免重复外部操作、远端委派、并行流程，以及通过 `GLOSSARY-MAP.md` 选择多个术语表。检查点本身不能保证外部操作只发生一次。当前排他写入能保护已有文件，但崩溃时仍可能留下部分内容。也没有进行 Docker、托管部署，或只安装 wheel 后的资源可用性验收。

<details>
<summary>技术附录：运行配置、复现命令和原始记录</summary>

验收判据来自各自源指令、[受控契约](../fixtures/CONTRACTS.md)和[真实样本要求](../fixtures/wait-what.md)。两个受控包为合成样本，`wait-what` 为真实包快照。结论限于下列已执行场景。

## 环境与命令

独立环境在 `/tmp/skill-to-graph-acceptance-20261022`，由用户授权创建并安装依赖，未修改共享环境。Python 3.13.5；PyYAML 6.0.3、langgraph 1.2.16、langchain 1.4.7、langchain-core 1.6.13、langgraph-cli 0.4.37、langgraph-api 0.16.4、langchain-anthropic 1.7.6、anthropic 1.17.0。

真实模型使用用户指定的 `MiniMax-M3.1-Flash`，中国区 M Plan 端点 `https://api.minimax.cn/anthropic`。复用 `MINIMAX_CN_API_KEY`，未保存或输出密钥。adaptive thinking、max_tokens=16384；Python 混合场景使用 low effort，真实重述和 CLI 使用 high effort。无模型或图级自动失败重试。

执行命令：

```sh
uv run --project /home/joshua/.ar --locked --no-sync -- python -m unittest discover -s tests -v
/tmp/skill-to-graph-acceptance-20261022/bin/python tests/acceptance/fixed_scenarios.py
/tmp/skill-to-graph-acceptance-20261022/bin/python tests/acceptance/mixed_boundaries.py
/tmp/skill-to-graph-acceptance-20261022/bin/python tests/acceptance/live_scenarios.py
/tmp/skill-to-graph-acceptance-20261022/bin/python tests/acceptance/cli_scenarios.py --server http://127.0.0.1:20287
openspec validate create-skill-to-graph --strict --json
```

真实 Python 观察分别保存于下列记录，而非将整套模型调用默认为单测。工作区外的临时环境可被系统清理，复现需先按 README 准备依赖。

CLI 使用 `server.json`，在本目录执行 `langgraph dev --config server.json --host 127.0.0.1 --port 20287 --no-reload --no-browser --allow-blocking`，模型配置通过进程环境提供。服务启动经用户明确授权，验收结束后已关闭，并核对端口不再响应。

## 矩阵和证据

| 范围 | 观察与判定 | 依据 |
| --- | --- | --- |
| 辅助脚本与记录驱动 | 14 项 unittest 通过；覆盖元数据、完整复制、目录和执行属性、冲突保护、JSON/退出码、静态不执行代码及记录状态 | `tests/test_*.py`，实际测试输出 |
| 三份应用静态及快照 | 均通过；逐文件核对清单与内容，完整快照一致 | [static-and-snapshots.json](results/2026-10-22/static-and-snapshots.json) |
| 固定文件深度验证 | 批准→ok、拒绝→cancelled、已有文件/非法值/缺列/源脚本 IO 失败→error；确认前没有输出目录，已有内容保持 | [python-fixed.json](results/2026-10-22/python-fixed.json) |
| 搬移运行 | 从临时原包调用 copy，装入图代码，搬移应用，再使临时原包原路径不可用；搬移后同样 6 场景通过，实际读取携带模板 | `fixed_scenarios.py` 与同份 python-fixed.json |
| 真实混合流程 | 真实模型调用 lookup，按证据生成有引用的报告；批准后实际写入；拒绝不写；无相关证据返回 insufficient 且不写 | [python-mixed-live.json](results/2026-10-22/python-mixed-live.json) |
| 继续检索及故障边界 | 模型替身先请求 alpha、再 beta、再返回充分；真实 lookup 与写文件；缺键导致 failed，工具只调用一次；输入非法及输出冲突受到保护 | [mixed-boundaries.jsonl](results/2026-10-22/mixed-boundaries.jsonl)；不作为真实模型判断证据 |
| 真实 Skill | 完整前文进入 messages；实际读取 GLOSSARY.md，缺少 GLOSSARY-MAP.md 不阻断回退；使用术语并保留外部写入可能重复的限制；时序扩写和完整语言要求仍待复核 | [python-wait-what-live.json](results/2026-10-22/python-wait-what-live.json) |
| CLI 基本调用与恢复 | 三图均完成实际调用；固定图 true/false、混合图 true 通过同 thread 恢复；确认前无文件，批准后文件与返回结果一致 | [cli.json](results/2026-10-22/cli.json) |
| 通用 Python 驱动 | 指定 make_graph 工厂，实际加载、暂停、恢复并写入；记录区分执行观察与待语义判断 | [driver-python.json](results/2026-10-22/driver-python.json) |
| 发布包独立性 | 将发布目录单独复制到临时目录，运行 inspect 通过，包内链接存在；发布目录不依赖仓库议题或验收工具 | 实际隔离检查；入口 `skill-to-graph/SKILL.md` |

上表静态快照的精确文件数以 JSON 为准：fixed-file 为 4，mixed-retrieval 为 2，wait-what 为 3，均包含隐藏文件（适用时）。

## 语义复核

混合报告的核心结论分别对应 alpha 的显式节点/边和 beta 的检查点进度，引用可追溯。证据不足的问题没有生成答案或写文件。真实模型自行选择查键，记录显示实际查阅；顺序继续检索和失败停止另由受控边界场景证明，没有据替身宣称真实模型必然采用该顺序。

真实重述使用了术语表，并保留崩溃后外部写入可能重复的限制。但原文没有规定内部检查点写入的精确时序，Python 和 CLI 输出都补充了时序说明；其中 CLI 还将等待确认描述为批准时发生。现有证据不足以判定完整保真通过。语言要求仅做了人工风格审查，未作 ASD-STE100 的第三方或词典级认证。

CLI 承担加载、基本调用及恢复差异验证；模型语义主要以 Python 深度场景复核，不因 HTTP 200 自动判保真通过。记录文件保留 `pending-review` 等原始执行标签，本节补充人工判定，不回写原始观察冒充自动评估。

## 未覆盖和限制

- 没有验证任意 Skill、所有动态资源和所有平台扩展；结论不超出三个样本。
- `GLOSSARY-MAP.md` 选择多个术语表的分支、源允许的并行、远端委派等未覆盖。
- 替身只验证受控路由和错误边界。真实模型输出仍有变化，语义质量需要按源复核。
- 使用进程内/开发服务存储，没有证明生产持久化、任意故障恢复或副作用 exactly-once。排他写入保护已有文件，崩溃时仍可能留下部分内容。
- 按应用目录搬移运行；不承诺单独 wheel 包含源资源。未要求或执行 Docker、托管部署验收。

本轮模型、依赖和服务运行条件已经具备；自然语言样例的保真验收及整体验收结论仍未完成。发布目录仅含 Skill 指令、两份参考和三个 Python 模块；仓库验收环境、样本、生成应用和记录均位于发布目录外。

</details>
