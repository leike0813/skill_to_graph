"""Run the generated application with the same user-selected model as the control."""
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent


def main():
    os.environ.update(MODEL_PROVIDER="anthropic", MODEL_ID="MiniMax-M3.1-Flash",
        MODEL_BASE_URL="https://api.minimax.cn/anthropic", MODEL_API_KEY_ENV="MINIMAX_CN_API_KEY",
        MODEL_OPTIONS=json.dumps({"max_tokens": 32768, "reasoning_effort": "high", "thinking": {"type": "adaptive"}}),
        RUNTIME_PYTHON="uv run --project /home/joshua/.ar --locked --no-sync -- python -B")
    path = ROOT / "graph-app/skill_graph/graph.py"
    spec = importlib.util.spec_from_file_location("literature_graph", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    started = time.time()
    payload = {"source_path": str(ROOT / "input/mineru/attention-is-all-you-need.md"),
               "language": "zh-CN", "score_only": False, "identifier": "arXiv:1706.03762"}
    try:
        state = module.make_graph().invoke(payload, {"configurable": {
            "working_dir": str(ROOT / "graph-run"), "model_label": "minimax-code-cn/MiniMax-M3.1-Flash"},
            "recursion_limit": 300})
        result = state["result"]
    except Exception as exc:
        result = module.final_failure(type(exc).__name__, str(exc))
    (ROOT / "graph-run/run-observation.json").write_text(json.dumps({"elapsed_seconds": time.time()-started,
        "model": "minimax-code-cn/MiniMax-M3.1-Flash", "result": result}, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
