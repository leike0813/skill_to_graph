# Attention Is All You Need：真实技能对照测试

本轮用同一份论文 Markdown 比较两种执行方式：对照组由 omp 直接执行 literature-analysis，实验组由本项目发布 Skill 转换出的 LangGraph 执行。主模型及文献批次委派均使用用户指定的 `minimax-code-cn/MiniMax-M3.1-Flash`。论文分析语言为中文，执行完整分析而非仅评分。

已完成执行，结论见 [本轮报告](REPORT.md)：两组均生成全部产物；图的引文报告未遵守中文要求，对照组也有内容、最终输出和批次读取违约。本轮不能判定完整保真通过。

源技能：`~/Workspace/Code/Skill/literature_digest/literature-analysis/`。图携带的完整副本在 `graph-app/source/literature-analysis/`；两组运行、DB和公开产物相互分离，不修改源包。

论文由 <https://arxiv.org/pdf/1706.03762> 下载，原PDF保存在 `input/attention-is-all-you-need.pdf`。使用已安装的 mineru-open-api v0.5.9、已配置的令牌和 VLM 精确转换，全15页，识别公式与表格：

```sh
mineru-open-api extract tests/acceptance/literature-analysis-attention/input/attention-is-all-you-need.pdf --model vlm --language en --formula --table -f md -o tests/acceptance/literature-analysis-attention/input/mineru --timeout 900
```

两组唯一论文内容来源都是 `input/mineru/attention-is-all-you-need.md`，配图目录保持原布局。arXiv 标识仅用于原技能允许的公开 bibliography 精确查询，不能替代论文内容。论文评分只依据原文，不依据历史声誉。

预先确定的检查：六份公开产物存在、最终JSON与DB一致、完整阶段/评分锁定字段规则、参考条目与源列表对应、引文分析只覆盖所选背景范围、元数据审核不联网、按runtime批次委派及唯一DB writer。语义核对包括Transformer核心结构、多头注意力、位置编码、训练设置及原文28.4/41.8 BLEU结果，不要求两组措辞或评分完全相同。

两组都输出相同结果不等于满足源契约。记录各自耗时、错误、修复和未完成部分；通过静态检查、成功运行与语义保真分开判断。样本、运行环境及对照工具均不属于发布内容。

本轮使用的命令如下，均从项目根目录执行。凭据复用环境配置，不写入文件。omp 命令记录了本轮的原始运行方式；重做实验应先选择全新的工作目录、会话目录和日志文件，并使 prompt 和图运行脚本指向对应位置，保留现有证据。

```sh
CASE_DIR="$PWD/tests/acceptance/literature-analysis-attention"
omp -p --model minimax-code-cn/MiniMax-M3.1-Flash --thinking high \
  --smol minimax-code-cn/MiniMax-M3.1-Flash \
  --slow minimax-code-cn/MiniMax-M3.1-Flash \
  --plan minimax-code-cn/MiniMax-M3.1-Flash \
  --config "$CASE_DIR/omp-config.yml" --cwd "$CASE_DIR/control" \
  --session-dir "$CASE_DIR/sessions-control" \
  --no-title --no-lsp --no-extensions --no-skills --no-rules \
  --mode json --max-time 60m --approval-mode yolo \
  "@$CASE_DIR/control-prompt.md" \
  > /tmp/literature-analysis-attention-control.jsonl \
  2> /tmp/literature-analysis-attention-control.stderr

/tmp/skill-to-graph-acceptance-20261022/bin/python -B \
  tests/acceptance/literature-analysis-attention/run_graph.py
```

图使用已有独立验收环境，源 runtime 使用共享 uv 环境；本轮没有新安装依赖或启动开发服务器。`run_graph.py` 配置中国区 MiniMax Anthropic 端点，从 `MINIMAX_CN_API_KEY` 取凭据。现有图工作目录已经完成，直接再次执行该命令会读取 DB 并返回已有结果，不会重新调用模型分析论文。

只读复核命令：

```sh
uv run --project /home/joshua/.ar --locked --no-sync -- python -B \
  skill-to-graph/scripts/check_graph.py \
  tests/acceptance/literature-analysis-attention/graph-app
uv run --project /home/joshua/.ar --locked --no-sync -- python -B \
  tests/acceptance/literature-analysis-attention/compare.py
```

第二条当前预期退出 1，原因是对照组最后回复有代码围栏且哈希被截短；它不自动评判语言或内容正确性。`observed-final-response.txt` 分别保留从本轮 omp 事件流提取的最后文本和图第三次运行的 stdout。完整 omp 流式日志约 52 MB，留在 `/tmp`；仓库保留本轮会话记录、结果及精简的 `execution-evidence.json`，后者记录实际模型、子代理读取范围和图的批次覆盖。

Git 保存报告、公开产物、源包快照、输入样本及精简执行证据。两组 `.literature_analysis_tmp/` 和 `sessions-control/` 为本机运行状态，保留在工作区但被 Git 忽略；新检出不能直接恢复本次 DB 或重跑依赖 DB 的 `compare.py`，应先准备独立运行目录重新执行。已保存的 `comparison.json` 为本轮原始检查结果。

最初两次图启动的错误分别见 `graph-run/run-observation-attempt1.json` 和 `run-observation-attempt2.json`。当前图已修正 submit-only 阶段缺 payload 的工具返回与源参考文档相对路径解析。语言传递和阶段推进后的修订限制尚未修复，最终产物保持本次观察结果。
