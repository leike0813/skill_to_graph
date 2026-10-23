请完整执行 /home/joshua/Workspace/Code/Skill/skill_to_graph/tests/acceptance/round2/generated/literature-analysis-graph/source/literature-analysis/SKILL.md 定义的 literature-analysis 技能。
先读该 SKILL.md，在相应阶段按需读取包内参考和 runtime JIT。不要修改源 Skill 或论文。
任务 payload：{"source_path": "/home/joshua/Workspace/Code/Skill/skill_to_graph/tests/acceptance/literature-analysis-attention/input/mineru/attention-is-all-you-need.md", "language": "zh-CN", "score_only": false, "identifier": "arXiv:1706.03762"}
当前 cwd 是本组独立任务目录 /home/joshua/Workspace/Code/Skill/skill_to_graph/tests/acceptance/round2/literature-sol-medium/control，作为 init_runtime 的 working_dir；产物放 artifacts/，
独立 DB 和结果镜像留在 cwd。model provenance 填 opencodex-hub/gpt-6.1-sol。
Python 使用 uv run --project /home/joshua/.ar --locked --no-sync -- python -B /home/joshua/Workspace/Code/Skill/skill_to_graph/tests/acceptance/round2/generated/literature-analysis-graph/source/literature-analysis/scripts/run_analysis.py ...，保持 cwd，不安装或升级依赖。
从头执行完整流程：计划、digest、评分、参考文献、metadata evidence review、citation semantic review、runtime 渲染。
默认按 runtime 预切 batch 路径委派 task agent。主执行与所有 task 均使用 opencodex-hub/gpt-6.1-sol，
思考强度 medium。主 agent 唯一写 DB；subagent 只读分配批次，只产 draft，不运行 runtime 或渲染。
语义判断由真实模型完成；脚本只做源允许的读取、序列化、合并、校验和渲染，不以规则生成摘要或评分。
源校验错误按其正式修正路径处理，不修改源代码、DB、公开产物来假造通过。
只在当前任务目录写入，读取仅限指定源包、论文和本次批次。不要读取旧组结果或其他项目，
不要读取凭据文件或打印环境。可以按源规则访问公开 bibliography API；metadata evidence review 不联网。
这是后台已授权执行，无需向用户提问。不启动服务器、不提交 Git。完成后原样输出 runtime 最终 stdout JSON，
不加围栏或解释，不截短字段；未完成则如实按源错误契约报告。
