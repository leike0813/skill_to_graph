# 源约束与职责映射

本图由执行 Agent 读取更新后的 `skill-to-graph` 指令，inspect/copy 第一轮完整源包，再按以下职责生成。源依据相对 `source/literature-analysis/SKILL.md`；本应用不读取第一轮图代码或运行 DB。

| 源依据 | 执行者、必要输入 | 实现 | 验证 |
| --- | --- | --- | --- |
| 输入输出硬契约、SQLite SSOT | 初始化与调用方；四业务字段及任务目录 | initialize 固化，context 只读 DB 设置；result 原样返回 | 同输入哈希、镜像一致、绝对路径、score-only 分支 |
| 核心指令 3–6、各阶段 CLI | 图和主执行者；runtime next_action | StateGraph 路由及限定当前阶段 run_stage | 固定顺序、正式阶段回执和错误停止 |
| 参数词表 language | 摘要、引文、各 batch；DB 实际值 | context→stage user message；delegate→batch user message | 改变输入语言时接收值同步，复核正文 |
| LLM/脚本职责边界 | 语义代理；规范化原文及当前 JIT | prompts.DUTIES、read_context、run_stage | 真实模型、源脚本实际提交渲染 |
| analysis plan、digest、scoring | 对应局部节点；大纲/scopes/原文/rubric | 局部任务、按需 read_text、锁定评分填表 | 源结构校验，原文数值及覆盖人工复核 |
| Subagent Delegation Contract | batch 代理；原路径单批次与适用语言 | delegate_batches 核对当前 runtime 路径，只开放 read_batch | 五类返回主键、实际工具和语言记录 |
| reference core 与 metadata rules | 各批次代理；local evidence、canonical fields | 批次 prompt 和源校验 | 不联网、不改 locked fields、拒绝无证据 metadata |
| citation 语义与全局闭包分工 | batch 代理做局部；主代理做 summary/timeline；runtime 做桶与渲染 | DUTIES/BATCH、run_stage | 正文按源 snippets、summary 不由规则生成 |
| 各阶段失败分支、finalization/recovery | 当前主代理及恢复入口；结构化失败、原 DB | run_stage 允许同命令正式修正；finalize 不接业务 payload | 初次成功后仍能修订并重渲染，不手改产物 |
| 正式 stdout 与固定产物 | runtime 与调用方；最终 DB | outcome、调用方序列化 result | schema、镜像、文件及内容一致性 |

每阶段的控制流程不由模型重新解释完整 SKILL.md；`prompts.py` 是转换后局部指令，源参考仅在对应职责需要时读取。纯原始记录和渲染文件保留在独立任务目录；外部依赖由环境提供。
