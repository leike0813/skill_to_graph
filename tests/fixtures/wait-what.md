# wait-what 真实样本

2026-10-22 从本仓库安装的 `.agents/skills/wait-what/` 原样复制至 `skills/wait-what/`。来源安装记录随 `.mattpack-owner.json` 保留。快照包含 `SKILL.md`、`agents/openai.yaml` 和隐藏安装元数据；这些内容未按验收答案改写。

任务上下文在 `wait-what-workspace/`。源任务是重述前一条难理解的消息，补少量上下文，使用 ASD-STE100 Simplified Technical English，以及 `GLOSSARY.md` 的领域术语。有 `GLOSSARY-MAP.md` 时应先选择对应术语表。

输入例子见工作目录 `input.json`。`workdir` 在调用前替换为该工作目录的绝对路径；conversation 保持原消息及其顺序。图可以使用消息封装，但必须能无损传入前文并取得重述结果。

验收观察：重述应解释原消息的图与检查点关系，不改变承诺，不丢失前文；按语境使用术语表定义的 Graph、Node、Checkpoint。语言审查关注短句、明确动词和易理解的表达，不按整段期望文本或单一词频阈值判定。不声称自动证明符合全部 ASD-STE100 规范；保留人工复核结论和限制。

另以临时目录中无 GLOSSARY-MAP 的直接术语表检查回退路径；含多个术语表的选择场景单独记录。没有执行的分支仍列为未覆盖。
