请完整执行 `/home/joshua/Workspace/Code/Skill/literature_digest/literature-analysis/SKILL.md` 所定义的 literature-analysis 技能。先读该 SKILL.md，仅在相应阶段读取包内参考和 runtime JIT 指令。不要修改源 Skill 或输入文件。

任务 payload：

```json
{
  "source_path": "/home/joshua/Workspace/Code/Skill/skill_to_graph/tests/acceptance/literature-analysis-attention/input/mineru/attention-is-all-you-need.md",
  "language": "zh-CN",
  "score_only": false,
  "identifier": "arXiv:1706.03762"
}
```

本次 cwd 是独立的对照组工作目录；将它作为 init_runtime 的 working_dir，最终产物输出至该目录下 artifacts/，使用该目录下独立 DB 和结果镜像。model provenance 填 `minimax-code-cn/MiniMax-M3.1-Flash`。

Python 运行使用：`uv run --project /home/joshua/.ar --locked --no-sync -- python -B <源Skill>/scripts/run_analysis.py ...`，保持当前工作目录。环境已具有该脚本依赖，不安装或更新依赖。

必须完成正常全流程（不是 score_only）：计划、digest、评分、参考文献、metadata evidence review、citation semantic review及runtime最终渲染。runtime返回batch路径时按源Skill默认委派；使用 task 工具的 task agent，已通过本次配置将主模型和task模型均设为 `minimax-code-cn/MiniMax-M3.1-Flash`。主agent是唯一DB writer。subagent只处理runtime给定batch、按batch内容做语义判断并生成draft；不得运行runtime写DB或写最终产物。

摘要、大纲、scope、评分、参考文献边界/元数据、引用语义等均由LLM按源文判断。脚本仅用于原技能允许的读取、序列化、已完成决策的合并与校验。不要通过关键词模板或批量规则代替语义工作。校验失败按源技能恢复，不修改源代码或最终产物来通过检查。

这是后台任务，不向用户提问。仅在本次对照组目录写入工作文件和产物；可以读取指定源Skill和论文，可以按技能允许规则访问公开bibliography API，metadata evidence review不得联网。不要读取凭据文件、打印环境密钥、提交Git或启动服务器。

最终答复只输出runtime返回的最终JSON。未完成时如实输出源Skill规定的错误，不自制成功JSON，不宣称后续已完成。
