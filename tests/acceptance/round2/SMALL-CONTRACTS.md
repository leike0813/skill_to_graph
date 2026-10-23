# 第二轮三个小样本的源契约映射

本文件按更新后的发布 Skill 重新转换的 fixed-file、mixed-retrieval、wait-what 图，逐条记录源义务的
执行者、输入、实现位置和验证方法。新应用位于 round2/generated/，由
skill-to-graph/scripts/skill_package.py inspect + copy 从源包快照生成；完整快照已逐文件与源包
比对（见 small-scenarios.json 的 snapshot 字段）。首轮应用与首轮结果未改动。

## 转换输入与快照

| 源包 | inspect | copy | 快照文件 |
| --- | --- | --- | --- |
| tests/fixtures/skills/fixed-file | small-inspect-fixed-file.json，ok，7 项 | small-copy-fixed-file.json | SKILL.md、data/example.csv、scripts/render.py、templates/summary.txt |
| tests/fixtures/skills/mixed-retrieval | small-inspect-mixed-retrieval.json，ok，3 项 | small-copy-mixed-retrieval.json | SKILL.md、examples/catalog.json |
| tests/fixtures/skills/wait-what | small-inspect-wait-what.json，ok，4 项 | small-copy-wait-what.json | SKILL.md、agents/openai.yaml、.mattpack-owner.json |

## fixed-file（固定流程）

源位置指 tests/fixtures/skills/fixed-file/SKILL.md 行号。

| 源义务 | 源位置 | 执行者 | 输入 | 实现位置 | 验证 |
| --- | --- | --- | --- | --- | --- |
| 首次调用必须提供 source_csv、output_dir，缺失时先问 | 15-20 | 图 collect 节点 + interrupt | 调用方第一次输入 | skill_graph/graph.py collect | small-scenarios.json 的 missing-output-dir-asks；确认前无目录 |
| CSV 校验：UTF-8、必需列、非负整数、空白行忽略、失败即停不重试 | 24-33 | 源脚本 render.py（确定性） | source_csv 路径 | subprocess 调用 SC 快照内 scripts/render.py | negative、missing-column、script-io-failure 均 error |
| 计算 rows/total/content，只读、不写、不换算法 | 35-50, 86-90 | 源脚本 render.py | CSV + 包内模板 | plan 节点解析脚本 JSON | approve 得 rows=2、total=5、Total: 5 |
| 确认时说明 rows、total、路径；只接受明确 true | 52-56 | 图 confirm 节点 + interrupt | 计划值 | interrupt 负载；approved = reply is True | reject/refusal 返回 cancelled，path 键不出现 |
| 未批准不创建输出目录、不写文件 | 54-60 | 图控制流 | approved | 条件边直接 END | refusal-has-no-path，目录不存在 |
| true 后创建目录、写 <output_dir>/summary.txt、已有文件失败不覆盖 | 58-65 | 图 write 节点 | output_dir、脚本 content | Path.mkdir + open("x") | approve、existing 场景；existing 内容保持 |
| 写失败停止、不重试、不换路径；结构化错误含 code/path/detail | 67, 84 | 图 write 节点 | OSError | error() | 写错误路径由 existing 与脚本失败的 error 结构覆盖 |
| 成功输出 status/rows/total/path；取消输出 rows/total 无 path | 69-84 | 图状态 | 计划与写入结果 | 节点返回值 | fixed runtime 断言 |

API 映射：Python 用 make_graph(checkpointer=...)，CLI 用 langgraph.json 的 cli_graph(config)，
两者共享 StateGraph。状态通道 source_csv/output_dir/rows/total/content/approved/status/
path/error 只承载跨节点数据；业务输出是 status、rows、total、path 或 error。无模型、无网络。

## mixed-retrieval（混合流程）

源位置指 tests/fixtures/skills/mixed-retrieval/SKILL.md 行号。

| 源义务 | 源位置 | 执行者 | 输入 | 实现位置 | 验证 |
| --- | --- | --- | --- | --- | --- |
| question 非空、catalog 可读 UTF-8 JSON 对象且值全为字符串；失败不调用 lookup、不写文件 | 22-29 | 图 validate 节点 | question、catalog | graph.py validate，先于 retrieve 条件边 | input-validation 场景（空问题、缺文件）返回 error |
| 首次调用缺 question/catalog 先问；output_dir 写前确定 | 12-18 | collect/confirm 节点 + interrupt | 调用方输入 | collect 与 confirm 的 interrupt | 代码路径与 approve 场景；未提供目录时 confirm 先问 |
| 选键与次数由模型决定，只能经 lookup 读证据，不外部检索 | 31-34 | retrieve 自治区段（create_agent） | question、catalog 键、lookup 工具 | 局部指令 RETRIEVAL_INSTRUCTIONS + lookup 闭包 | double 场景：alpha→beta→充分；工具调用次序记录 |
| 证据充分性由模型语义判断；不足继续，无证据返回 insufficient | 36-43 | 模型判断 | 每轮 lookup 结果 | 模型结构化 status；图只按 status 路由 | double semantic-loop-routing；small-reviewed-live 的真实充分/不足分支 |
| 不按次数或字数截断 | 42-43 | 图 retrieve 无条件循环上限 | 模型决定 | create_agent 循环；仅 GraphRecursionError 报 execution-limited | 代码检查与真实查键记录，不按调用数推定充分性 |
| lookup 故障停止、failed、不重试、不换路径 | 45 | lookup 工具 + retrieve 异常路径 | catalog 内容 | LookupFailure 经 ToolNode 传播，retrieve 返回 failed | double lookup-failure-stops，tool_calls=1 |
| 提案直接回答并给每条结论标注证据键 | 47-50 | retrieve 模型 | 已取证据 | 局部指令及 Evidence 字段说明要求 [key] 引用 | 真实结果逐句复核见 REPORT；早期扩写保留为失败 |
| 确认前不建目录不写文件；true 才写 report.md；其他回复 cancelled | 52-56 | confirm/write 节点 | approved | 条件边 write/cancel；write 创建目录 | approve/reject 分支；cancel 状态无 path |
| 已有文件失败不覆盖；写错停止不重试 | 58-63 | write 节点 | output_dir | open("x") + error() | double existing-file-protected |
| 检索阶段固定三字段；业务状态 ok/cancelled/insufficient/failed/error | 65-87 | 图与模型 | 结构化响应 | Evidence 模型 + failure() | double 与 input-validation |

API 映射：Python make_graph(checkpointer=...) 注入 saver；CLI cli_graph(config) 共享同一
StateGraph。模型由环境 MODEL_PROVIDER/MODEL_ID/MODEL_BASE_URL/MODEL_API_KEY_ENV（密钥变量名）
和 MODEL_OPTIONS 提供，max_retries=0；lookup 只读本地 catalog，无网络。

## wait-what（纯自主）

源位置指 tests/fixtures/skills/wait-what/SKILL.md 行号。

| 源义务 | 源位置 | 执行者 | 输入 | 实现位置 | 验证 |
| --- | --- | --- | --- | --- | --- |
| 重述上一条 assistant 消息并给少量上下文 | 7 | 自主 agent + dynamic_prompt | messages 历史 | 提取最近 human 前的 ai 消息注入提示，明确区分问题背景与原话的断言 | MiniMax Python/CLI 扩写记录保留；gpt-6.1-sol 三次图与三次 omp 内容复核通过，见 wait-sol/REPORT.md |
| ASD-STE100 Simplified Technical English | 7 | 模型 | 源完整指令 | SKILL.md 正文原样加载 + task binding | 需人工语义复核；无自动判定 |
| 使用 GLOSSARY.md 的 ubiquitous language | 7 | 模型 + read_file 工具 | 工作目录文件 | read_file/list_files 适配器；相对路径按 workdir，绝对路径保留 | 路径适配检查及真实术语表读取；不抵消内容违约 |
| 有多个术语表时跟随 GLOSSARY-MAP.md 选择 | 7 | 模型 | GLOSSARY-MAP.md | 工具可读任意相对/绝对路径；提示要求先读 MAP | wait-glossary-map-live 选择 workflow/GLOSSARY.md，未选 geometry；此记录早于最后提示整理 |
| disable-model-invocation: true（显式调用） | 4 | 部署方 | 平台元数据 | README 说明仅显式运行；图不添加自动路由 | 配置静态检查 |
| 纯自主，无可独立固定阶段 | 7（全文） | create_agent | 会话历史 | 直接导出 agent 图，保留完整源指令 | 结构检查；无固定节点改写 |

API 映射：Python make_graph(config) 与 CLI 同一工厂；工作目录 config.configurable.workdir，
输出取最后一条 assistant 的 content。模型选项由 MODEL_OPTIONS 显式提供（验收环境使用 high
thinking），图不设默认供应商；max_retries=0。

## 复核结果与未覆盖

- MiniMax 重述的时序错误保留；用户指定 gpt-6.1-sol 后三次图与三次 omp 对照通过。
  额外标题/列表限制已删除，按用户要求不再复验，结论及范围见 REPORT 和 wait-sol/REPORT.md。
- 多术语表 MAP 分支已实际调用；仓库根之外映射的绝对路径仅验证适配器，未做真实模型选择。
- CLI 为另一入口的基本调用，Python 承担深度场景；真实模型和受控替身的证据分开。
- 检查点恢复只覆盖进程内 InMemorySaver；崩溃后外部写入的 exactly-once 不在源契约与本轮证据内。

