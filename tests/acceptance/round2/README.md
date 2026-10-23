# 第二轮运行与证据

结论见 [REPORT.md](REPORT.md)。发布 Skill 修改后重新转换的四个应用在 `generated/`；本目录及其模型配置、论文输入引用、测试代码不随发布包分发。保留第一轮的全部已跟踪输入、生成图和结果。

复用已有工作区外环境 `/tmp/skill-to-graph-acceptance-20261022`。源论文 runtime 使用共享 uv 环境；不自动安装依赖或启动服务。模型仍为 `minimax-code-cn/MiniMax-M3.1-Flash`，Anthropic 兼容端点 `https://api.minimax.cn/anthropic`，从环境 `MINIMAX_CN_API_KEY` 读取凭据，无模型 fallback、无 SDK 自动重试。

以下命令从项目根执行。每次选择新的记录名；运行脚本会拒绝覆盖已有记录。

```sh
uv run --project /home/joshua/.ar --locked --no-sync -- python -m unittest discover -s tests -v
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/test_runtime_boundaries.py -v
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/small_scenarios.py --record tests/acceptance/round2/results/small-next.json
```

显式真实调用，须先确认原端点可连接：

```sh
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/small_scenarios.py --live --record tests/acceptance/round2/results/small-next-live.json
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/round2/literature_run.py --record tests/acceptance/round2/results/literature-next.json
```

`literature_run.py` 默认从 `literature-run/` 中现有 DB 恢复，本轮已完成全部阶段，因此再次调用会重渲染已有成功状态；`--run 新目录名` 可启动独立新 run。`--score-only` 仅用于独立新 run。业务输入、阶段语言设置和批次语言记录在各 run 的 `graph-events.jsonl`；恢复状态 `.literature_analysis_tmp/` 留在本机并被 Git 忽略，不能从 Git 新检出直接恢复本次 DB。论文来源仍是首轮保存的 MinerU Markdown，不更换内容。

`server.json` 指向本轮四个应用。CLI 测试须使用本轮配置，服务按适用授权临时启动，地址 localhost:20288；服务现已关闭，端口检查见 `service-shutdown-current.json`。`fixed-cli.json` 记录真实文件操作及暂停恢复，`small-cli-reviewed.json` 记录恢复后的混合调用；`wait-cli-current.json` 仍有时序违约。`literature-cli-invalid.json` 覆盖输入错误，`literature-cli-repaired.json` 覆盖已有成功 DB 的重渲染，不代表从头模型分析。旧 `mixed-cli-timeout.json` 保留原连接失败。

最后本地场景记录为 [small-current-deterministic.json](results/small-current-deterministic.json)，另保留[源脚本重放](results/literature-runtime-replay.json)。本轮实际运行 14 项原测试和 4 项运行边界测试；旧 runtime-boundaries.json 是更早的 3 项测试记录，不能冒充最新输出。真实论文完成结果见 [literature-attempt4.json](results/literature-attempt4.json)，[16 项结构与一致性检查](results/literature-contracts.json)通过。正文语义判定见 REPORT，不以 schema 标签、字符比例或文本快照代替。

真实小样本使用同一模型的 high effort；较早的 low effort 运行保留在旧记录中。论文 max_tokens=32768，small_scenarios 的真实调用 max_tokens=16384，均为 adaptive thinking。修复评分工具后沿用原 DB 恢复，未把首轮语义 payload 当作本轮分析。
