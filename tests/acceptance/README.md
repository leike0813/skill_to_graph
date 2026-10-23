# 仓库验收

职责拆分优化的第二轮应用、运行命令和当前证据见 [round2/README.md](round2/README.md) 与 [报告](round2/REPORT.md)。第一轮的生成物及结果保留用于比较。

发布内容只有 `skill-to-graph/`。本目录、源样本和生成应用留在仓库验收资产中，不随发布 Skill 或生成应用分发。

日常脚本测试不触发模型、不启动服务：

```sh
uv run --project /home/joshua/.ar --locked --no-sync -- python -m unittest discover -s tests -v
```

`requirements.txt` 声明图运行基线。环境需要可提供这些依赖的 Python 3.11+，以及显式选择的模型集成。依赖安装、模型配置及服务启动按项目授权规则执行。当前工具链不为验收自动创建虚拟环境或安装依赖。

本轮已获授权的独立环境为 `/tmp/skill-to-graph-acceptance-20261022`，不依赖工作区内虚拟环境。用户选定 MiniMax 中国区 M Plan：模型 `MiniMax-M3.1-Flash`、Anthropic 兼容端点 `https://api.minimax.cn/anthropic`，复用 `MINIMAX_CN_API_KEY`，不复制密钥。`live_scenarios.py` 只在显式执行时配置该运行条件并调用模型，使用真实本地 lookup/文件工具。`fixed_scenarios.py` 验证真实固定流程；`mixed_boundaries.py` 使用模型替身驱动边界，不能用来证明真实模型能力。

```sh
/tmp/skill-to-graph-acceptance-20261022/bin/python tests/acceptance/fixed_scenarios.py
/tmp/skill-to-graph-acceptance-20261022/bin/python tests/acceptance/mixed_boundaries.py
/tmp/skill-to-graph-acceptance-20261022/bin/python tests/acceptance/live_scenarios.py
/tmp/skill-to-graph-acceptance-20261022/bin/python tests/acceptance/cli_scenarios.py --server http://127.0.0.1:20287
```

MiniMax 需要保留完整 thinking/tool 消息。运行选项通过 `MODEL_OPTIONS` 传入，当前为 adaptive thinking 和 max_tokens=16384，混合检索使用 low effort，真实重述样本使用 high effort；不添加模型/图级失败重试。工具策略的强制 tool_choice 会被 Anthropic 集成在 thinking 模式下移除，是否成功产出结构化结果以实际观察为准。

端点与协议依据：<https://platform.minimaxi.com/docs/m-plan/other-tools.md>、<https://platform.minimaxi.com/docs/api-reference/text-anthropic-api.md>、<https://platform.minimaxi.com/docs/guides/text-m3-function-call.md>。

源样本的判据见 [CONTRACTS.md](../fixtures/CONTRACTS.md)，真实样本出处和上下文见 [wait-what.md](../fixtures/wait-what.md)。执行 Agent 读取发布 Skill 后转换三个源包，产物放在 `tests/acceptance/generated/`，不使用另一套转换程序。

## 显式探测

下列命令中的 `<PYTHON>` 表示配置好运行依赖的解释器。驱动只在显式选择 `python` 或 `cli` 时执行业务。输入和结果使用不含凭据的合成数据。

```sh
<PYTHON> tests/acceptance/run.py <生成目录> --graph-id fixed-file --mode static --evidence-kind static --record /tmp/static.json
<PYTHON> tests/acceptance/run.py <生成目录> --graph-id fixed-file --mode python --python-factory make_graph --input <input.json> --resume <true.json> --record /tmp/python.json
<PYTHON> tests/acceptance/run.py <生成目录> --graph-id fixed-file --mode cli --server http://127.0.0.1:2024 --input <input.json> --resume <true.json> --record /tmp/cli.json
<PYTHON> tests/acceptance/run.py <生成目录> --graph-id fixed-file --mode python --python-factory make_graph --input <input.json> --resume <true.json> --relocate --record /tmp/moved.json
```

记录必须是新文件。Python 入口从 `langgraph.json` 的文件或模块位置加载，工厂接受 `config`，若工厂声明 `checkpointer` 参数则驱动提供进程内 saver 用于受控暂停恢复。其他存储/工厂形式按应用说明单独验证。CLI 探测连接已配置服务，不启动服务；需要服务认证时由验收环境提供专用驱动，不在记录中保存密钥。

`--config <json文件>` 提供工作目录等非凭据运行配置，例如 `{"configurable":{"workdir":"/absolute/task/path"}}`。两份模型图还声明 `MODEL_PROVIDER`、`MODEL_ID`、`MODEL_BASE_URL`、`MODEL_API_KEY_ENV` 和可选 `MODEL_OPTIONS`；这些是生成图运行环境，不是转换器输入。

固定与混合图的 CLI 入口是单参数 `cli_graph(config)`，转调同一 `make_graph` 装配函数。Python 选择 `--python-factory make_graph` 后才能注入受控 saver；CLI 使用服务存储。服务会检查完整工厂签名，不能直接用带三个参数的 Python 装配函数作为 CLI 入口。

`--relocate` 将应用复制到临时新目录后运行。它只证明换目录可用；要证明独立于转换时的原包，先从一次性源包副本转换，再将该副本重命名为不可访问的原路径，保留用户原包。CLI 搬移验证须将服务配置到搬移后的应用，另行探测。

## 记录与判定

每条记录含样本入口、图 ID、时间、证据类型、各阶段观察、总体执行状态与待复核判断。补充记录源契约条目、配置标识、命令和人工复核结论。禁止将凭据写入输入、观察或记录。

| outcome | 含义 |
| --- | --- |
| static-passed | 确定性检查通过，尚无加载或业务执行证据 |
| executed | 取得调用观察，保真判断仍需核对源契约 |
| blocked | 缺运行依赖、服务或连接条件 |
| failed | 图执行或探测失败，需定位原因 |
| not-run | 尚未尝试 |

`evidence_kind=double` 只记录替身覆盖；`live-model` 必须有真实调用依据，不能用设置标签代替实际证据。模型语义按源要求人工复核，`wait-what` 的简化英语要求需要保留人工审查，不声称自动认证 ASD-STE100。框架返回的业务 failed、CLI 错误或模型错误必须人工或场景断言判定，HTTP 200 本身不算保真通过。

必验矩阵：固定文件成功、输入非法、拒绝、输出冲突、脚本错误；混合检索语义充分/不足、继续检索、工具故障、确认及文件；真实样本上下文重述/术语/语言；Python 和 CLI 基本调用及暂停恢复；搬移后读取模板。未运行、证据不足、受阻不计通过。
