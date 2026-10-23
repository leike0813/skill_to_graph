# DeepSeek high 真实模型验收

2026-10-23

**本轮语义验收未通过。** 新转换图与 omp 源执行各三次，六次均完成真实调用并得到回复，但都将“已保存的 Checkpoint”展开为原话没有给出的保存步骤；多份回复还增加了执行时序或恢复保证。双方均出现问题，不能将 omp 输出当作正确答案，也不能据此将问题单独归因于转换。

本轮仅重复上次 `wait-what` 对照场景，使用相同原始会话和术语表。当前发布 Skill 被执行 Agent 用于重新转换源包，新应用在 [generated/wait-what-graph](generated/wait-what-graph/README.md)。旧 round2 应用及记录未修改。义务映射、预先确定的语义判据与未覆盖范围见 [CONTRACTS.md](CONTRACTS.md)。

## 实际配置与调用证据

| 组别 | 指定配置 | 实际观察 |
| --- | --- | --- |
| 新转换图 | `combo/deepseek-v4.1-flash`，high | 八个 POST 均发往 `https://192.168.13.111:10100/v1/responses`；请求体的 model 与 reasoning.effort 符合指定值，均 HTTP 200，三次图执行完成 |
| omp 源 Skill | `commandcode/deepseek/deepseek-v4.1-flash`，`--thinking high` | 三次进程退出 0；最终消息均为 provider=`commandcode`、model=`deepseek/deepseek-v4.1-flash`、api=`openai-responses` |

图响应中的模型标识为 `deepseek/deepseek-v4.1-flash`，与本地路由前缀 `combo/` 的请求标识分别保留于原始记录。图使用现有 `OPENCODEX_API_AUTH_TOKEN`，TLS 使用 `NODE_EXTRA_CA_CERTS` 指向的现有证书包，未关闭证书验证。omp 使用现有 provider 配置；没有将其改到图的本地端点。凭据未写入记录。

omp 的 high 由实际命令行参数确定；本轮没有拦截 omp 的 HTTP 请求体，因此不把参数配置当作其线上 reasoning.effort 的直接证据。模型角色均指定相同 commandcode 模型，关闭 prewalk 和模型 fallback。图设置 SDK `max_retries=0`。三次是预定的独立重复，不是失败后自动重试。

## 逐份语义复核

原话说：Graph 在确认点暂停；已保存的 Checkpoint 将回复与暂停执行关联；恢复后下游 Node 生成报告；崩溃后的外部文件写入没有 exactly-once 保证。保存记录是一种已存在的状态描述，不足以推出“批准后创建 Checkpoint”或额外的执行步骤。

| 记录 | 正确保留的内容 | 已观察的问题 | 判定 |
| --- | --- | --- | --- |
| [graph-1.json](graph-1.json) | 读取术语表，等待批准，下游报告，外部写入可能重复 | 明确写出 “When you approve, the Graph saves a Checkpoint.”，改变保存时序 | 未通过 |
| [graph-2.json](graph-2.json) | 读取术语表，报告在恢复后产生，不承诺 exactly-once | 在 “What happens at your approval” 下写出保存 Checkpoint 的新步骤，另增加任务目录说明 | 未通过 |
| [graph-3.json](graph-3.json) | 读取术语表，使用领域术语，保留外部写入限制 | “What happens after you approve” 下列出停止、保存、重启；增加“不保持活进程”、记录回复的实现解释及具体崩溃窗口 | 未通过 |
| [omp-1.json](omp-1.json) | 读取源文件与术语表，等待回复、批准后继续、下游报告、外部写入限制 | 增加 “Graph completes a Node”、在停止时保存的新步骤，以及“不从头开始”的恢复保证；原话没有明确这些细节 | 未通过 |
| [omp-2.json](omp-2.json) | 读取源文件与术语表，报告与外部写入限制 | 明确写出 “You approve. Then the system makes a Checkpoint.”，又增加“从同一 Node 继续” | 未通过 |
| [omp-3.json](omp-3.json) | 读取源文件与术语表，批准释放暂停流程，外部动作可能重复 | “What happens after you approve” 下新增保存步骤；增加“写入期间失败”的具体解释和额外目录说明 | 未通过 |

六份回复总体使用短句与领域名词，且都保留外部写入没有仅一次保证；ASD-STE100 只进行语言与可读性审阅，不作词典级认证。标题、列表和正常措辞差异不是失败判据。

这里将“新增保存步骤”判为扩写，不意味着保存操作在真实系统中一定不发生；本样本验收的是重述给定原话，不能用一般实现知识补成原话的承诺。omp-1 没有 graph-1/omp-2 那样明确的“批准后保存”倒置，但仍有新增步骤和恢复保证，所以分别记录问题，不把六份结果描述为完全相同的错误。

## 结构、输入与验证边界

- 完整快照三份文件与源包逐字节一致；生成应用的 Python 语法、入口与 JSON 静态检查通过，见 [checks.json](checks.json)。
- 图请求首轮消息含完整源指令，原始三条会话及其顺序保留。新图是一个自主 agent，运行时用通用规则绑定待重述原话，没有添加本案例专属的正确答案。
- 图每次使用只放术语表的独立任务目录；omp 每次另放完整源 Skill 副本。均未提供旧结果。六次实际调用了术语表读取工具；部分读取先探测不存在的 MAP 或 references，随后仍取得正确术语表。
- 图传入原生会话角色；omp 接收带角色 JSON。两组的系统提示、工具及端点不同，不构成严格单变量对照。本轮未测纯源指令与新图在相同工具和原生历史下的第三组对照，无法据此判断转换是否增加了错误概率。
- 本轮不是与旧版本提示词的效果比较，也不能证明当前 Skill 优化提升或降低了模型质量。旧 gpt-6.1-sol/medium 的成功结论仅属于原配置。
- 未运行 LangGraph CLI 服务、搬移和多术语表分支，也未重新验收固定、混合、论文样本或生产恢复。静态入口合法与 Python 真实调用不能替代 CLI 运行证据；本次不是整个项目所有场景的重新通过。

## 复现

使用已有工作区外环境，未安装或升级依赖：langgraph 1.2.16、langchain 1.4.7、langchain-core 1.6.13、langchain-openai 1.7.2、openai 3.37.0、httpx2 2.16.0；omp 18.12.2。

```sh
/tmp/skill-to-graph-acceptance-20261022/bin/python -B skill-to-graph/scripts/check_graph.py tests/acceptance/skill-smith-deepseek-high/generated/wait-what-graph
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/skill-smith-deepseek-high/run.py graph --repetitions 3
/tmp/skill-to-graph-acceptance-20261022/bin/python -B tests/acceptance/skill-smith-deepseek-high/run.py omp --repetitions 3
```

六份记录均以新文件方式创建，重复上述命令会拒绝覆盖；另一次验收需使用新的独立记录目录。本轮没有根据失败回复修改提示或继续抽样。发布包与原有证据保持本轮开始时状态，未启动服务、提交或归档。
